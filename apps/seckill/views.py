from django.views import View
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import redis
import time
import json
from utils.redis_scripts import RATE_LIMIT_SCRIPT, SECKILL_STOCK_SCRIPT, BATCH_RATE_LIMIT_SCRIPT
from utils.lock import RedisLock
from apps.seckill.models import Order, SeckillActivity, Product
from apps.seckill.tasks import create_order_task
from django_redis import get_redis_connection

User = get_user_model()

@method_decorator(csrf_exempt, name='dispatch')
class SeckillView(View):
    """秒杀视图"""
    
    def post(self, request):
        try:
            # 获取用户 ID 和活动 ID
            user_id = request.POST.get('user_id')
            activity_id = request.POST.get('activity_id')
            
            if not user_id or not activity_id:
                return JsonResponse({'code': 400, 'message': '参数错误'})
            
            # 1. 校验活动时间
            try:
                activity = SeckillActivity.objects.get(id=activity_id)
            except SeckillActivity.DoesNotExist:
                return JsonResponse({'code': 404, 'message': '活动不存在'})
            
            from django.utils import timezone
            current_time = timezone.now()
            if current_time < activity.start_time:
                return JsonResponse({'code': 400, 'message': '活动尚未开始'})
            if current_time > activity.end_time:
                return JsonResponse({'code': 400, 'message': '活动已结束'})
            
            order = None
            
            try:
                # 尝试使用 Redis 进行库存管理
                # 2. 获取 Redis 连接
                r = get_redis_connection('default')
                
                # 3. 限流检查
                ip = request.META.get('REMOTE_ADDR', 'unknown')
                if not self._batch_rate_limit(r, user_id, ip):
                    return JsonResponse({'code': 429, 'message': '请求过于频繁，请稍后再试'})
                
                # 4. 使用 Redis 分布式锁防止用户重复秒杀
                lock_key = f'seckill:lock:user:{user_id}:activity:{activity_id}'
                redis_lock = RedisLock(r, lock_key, timeout=10)
                
                # 尝试多次获取锁和扣减库存
                for i in range(5):  # 增加重试次数到 5 次
                    try:
                        if redis_lock.acquire():
                            # 4. 使用 Lua 脚本扣减库存
                            stock_key = f'seckill:stock:{activity_id}'
                            stock_field = 'stock'
                            
                            # 执行库存扣减脚本
                            result = r.eval(SECKILL_STOCK_SCRIPT, 2, stock_key, stock_field, 1)
                            
                            if result == -1:
                                return JsonResponse({'code': 400, 'message': '已售罄'})
                            
                            # 5. 确保用户存在
                            try:
                                user = User.objects.get(id=user_id)
                            except User.DoesNotExist:
                                # 如果用户不存在，创建一个测试用户
                                # 使用时间戳确保用户名唯一性
                                timestamp = int(time.time() * 1000)
                                user = User.objects.create_user(
                                    username=f'test_user_{user_id}_{timestamp}',
                                    email=f'test_{user_id}_{timestamp}@example.com',
                                    password='test123456'
                                )
                            
                            # 6. 使用 Celery 异步创建订单
                            create_order_task.delay(user_id, activity_id)
                            
                            order = True
                            break  # 成功后退出循环
                        else:
                            # 未获取到锁，等待后重试
                            time.sleep(0.1)
                            continue
                    
                    except Exception as e:
                        # 发生异常，等待后重试
                        time.sleep(0.1)
                        continue
                    finally:
                        # 释放锁
                        redis_lock.release()
            
            except Exception as e:
                # Redis 不可用，回退到数据库事务
                import django.db.transaction
                
                # 尝试多次获取锁
                for i in range(5):  # 增加重试次数到 5 次
                    try:
                        with django.db.transaction.atomic():
                            # 获取活动和商品，使用 select_for_update 锁定
                            activity = SeckillActivity.objects.select_for_update().get(id=activity_id)
                            product = Product.objects.select_for_update().get(id=activity.product.id)
                            
                            if product.stock <= 0:
                                return JsonResponse({'code': 400, 'message': '已售罄'})
                            
                            # 扣减库存
                            product.stock -= 1
                            product.save()
                        
                        # 确保用户存在
                        try:
                            user = User.objects.get(id=user_id)
                        except User.DoesNotExist:
                            # 如果用户不存在，创建一个测试用户
                            # 使用时间戳确保用户名唯一性
                            timestamp = int(time.time() * 1000)
                            user = User.objects.create_user(
                                username=f'test_user_{user_id}_{timestamp}',
                                email=f'test_{user_id}_{timestamp}@example.com',
                                password='test123456'
                            )
                        
                        # 使用 Celery 异步创建订单
                        create_order_task.delay(user_id, activity_id)
                        
                        order = True
                        break  # 成功后退出循环
                    
                    except django.db.utils.OperationalError as e:
                        if 'database is locked' in str(e):
                            # 数据库锁，等待后重试
                            time.sleep(0.1)
                            continue
                        else:
                            raise
                    except Exception as e:
                        raise
            
            if order:
                return JsonResponse({'code': 200, 'message': '秒杀成功，订单正在处理中'})
            else:
                return JsonResponse({'code': 500, 'message': '秒杀失败: 系统繁忙，请重试'})
                
        except Exception as e:
            return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'})
    
    def _rate_limit(self, r, user_id):
        """使用 Redis + Lua 脚本实现滑动窗口限流"""
        import time
        # 限流窗口大小（秒）
        window_size = 10
        # 窗口内最大请求数
        max_requests = 5
        # 当前时间戳
        now = int(time.time())
        
        # 生成限流 key
        rate_key = f'seckill:rate:{user_id}'
        
        # 执行限流脚本
        result = r.eval(RATE_LIMIT_SCRIPT, 1, rate_key, max_requests, window_size, now)
        return bool(result)
    
    def _batch_rate_limit(self, r, user_id, ip):
        """使用 Redis + Lua 脚本实现批量限流"""
        import time
        # 限流窗口大小（秒）
        window_size = 10
        # 窗口内最大请求数
        max_requests = 5
        # 当前时间戳
        now = int(time.time())
        
        # 生成限流 key
        user_rate_key = f'seckill:rate:{user_id}'
        ip_rate_key = f'seckill:rate:ip:{ip}'
        global_rate_key = f'seckill:rate:global'
        
        # 执行批量限流脚本
        result = r.eval(BATCH_RATE_LIMIT_SCRIPT, 3, user_rate_key, ip_rate_key, global_rate_key, max_requests, window_size, now)
        return bool(result)

class OrderStatusView(View):
    """订单状态查询视图"""
    
    def get(self, request):
        # 获取订单号
        order_id = request.GET.get('order_id')
        
        if not order_id:
            return JsonResponse({'code': 400, 'message': '参数错误'})
        
        try:
            # 查询订单
            order = Order.objects.get(id=order_id)
            
            # 根据订单状态返回对应信息
            status_map = {
                'pending': '处理中',
                'paid': '成功',
                'cancelled': '失败',
                'refunded': '失败'
            }
            
            status_text = status_map.get(order.status, '处理中')
            
            return JsonResponse({
                'code': 200,
                'message': '查询成功',
                'data': {
                    'order_id': order.id,
                    'status': order.status,
                    'status_text': status_text,
                    'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'paid_at': order.paid_at.strftime('%Y-%m-%d %H:%M:%S') if order.paid_at else None
                }
            })
        except Order.DoesNotExist:
            return JsonResponse({'code': 404, 'message': '订单不存在'})
        except Exception as e:
            return JsonResponse({'code': 500, 'message': f'查询失败: {e}'})

@method_decorator(csrf_exempt, name='dispatch')
class CreateActivityView(View):
    """创建秒杀活动视图"""
    
    def post(self, request):
        try:
            # 获取参数
            product_id = request.POST.get('product_id')
            seckill_price = request.POST.get('seckill_price')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            
            if not product_id or not seckill_price or not start_time or not end_time:
                return JsonResponse({'code': 400, 'message': '参数错误'})
            
            # 转换价格为浮点数
            try:
                seckill_price = float(seckill_price)
            except ValueError:
                return JsonResponse({'code': 400, 'message': '秒杀价格格式错误'})
            
            # 转换时间
            from datetime import datetime
            try:
                start_time = datetime.fromisoformat(start_time)
                end_time = datetime.fromisoformat(end_time)
            except ValueError:
                return JsonResponse({'code': 400, 'message': '时间格式错误'})
            
            # 验证时间
            if start_time > end_time:
                return JsonResponse({'code': 400, 'message': '开始时间不能晚于结束时间'})
            
            # 获取商品
            from apps.seckill.models import Product
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return JsonResponse({'code': 404, 'message': '商品不存在'})
            
            # 验证秒杀价格至少比原价优惠300元
            from decimal import Decimal
            if product.original_price - Decimal(str(seckill_price)) < Decimal('300'):
                return JsonResponse({'code': 400, 'message': '秒杀价优惠太低，至少比原价优惠300元'})
            
            # 创建秒杀活动
            from apps.seckill.models import SeckillActivity
            activity = SeckillActivity.objects.create(
                product=product,
                start_time=start_time,
                end_time=end_time,
                status='pending'
            )
            
            # 更新商品的秒杀价格
            product.seckill_price = seckill_price
            product.save()
            
            return JsonResponse({
                'code': 200,
                'message': '活动创建成功',
                'activity_id': activity.id
            })
        except Exception as e:
            return JsonResponse({'code': 500, 'message': f'创建活动失败: {str(e)}'})

class HomeView(View):
    """首页视图"""
    
    def get(self, request):
        # 获取所有进行中的秒杀活动，使用select_related预加载商品信息，减少N+1查询
        from django.utils import timezone
        current_time = timezone.now()
        active_activities = SeckillActivity.objects.select_related('product').filter(
            start_time__lte=current_time,
            end_time__gte=current_time
        )
        
        # 获取所有用户，只选择需要的字段
        from apps.users.models import User
        users = User.objects.only('id', 'username', 'email')
        
        # 构建HTML响应
        html = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>秒杀系统</title>
            <style>
                body {
                    font-family: 'Microsoft YaHei', Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 900px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #333;
                    text-align: center;
                    font-size: 28px;
                    margin-bottom: 30px;
                }
                h2 {
                    color: #555;
                    margin-top: 30px;
                    font-size: 20px;
                    border-bottom: 2px solid #4CAF50;
                    padding-bottom: 10px;
                }
                .nav {
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }
                .nav a {
                    color: #4CAF50;
                    text-decoration: none;
                    margin: 0 10px;
                    font-weight: bold;
                }
                .activity {
                    background-color: #f9f9f9;
                    padding: 20px;
                    margin: 15px 0;
                    border-radius: 8px;
                    border-left: 4px solid #4CAF50;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                }
                .activity h3 {
                    margin-top: 0;
                    color: #333;
                }
                .activity p {
                    margin: 8px 0;
                    color: #666;
                }
                .api-endpoint {
                    background-color: #f0f8ff;
                    padding: 12px;
                    margin: 10px 0;
                    border-radius: 4px;
                    font-family: monospace;
                    border-left: 3px solid #1E90FF;
                }
                .note {
                    background-color: #fff3cd;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 4px;
                    border-left: 3px solid #ffc107;
                }
                .form-container {
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin-top: 20px;
                }
                .form-group {
                    margin: 15px 0;
                }
                label {
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                    color: #333;
                }
                input, select {
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-size: 14px;
                }
                button {
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 4px;
                    font-size: 16px;
                    cursor: pointer;
                    margin-top: 10px;
                }
                button:hover {
                    background-color: #45a049;
                }
                .result {
                    margin-top: 20px;
                    padding: 15px;
                    border-radius: 4px;
                    font-family: monospace;
                }
                .success {
                    background-color: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }
                .error {
                    background-color: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }
                .footer {
                    margin-top: 40px;
                    text-align: center;
                    color: #666;
                    font-size: 14px;
                }
            </style>
            <script>
                function getCookie(name) {
                    let cookieValue = null;
                    if (document.cookie && document.cookie !== '') {
                        const cookies = document.cookie.split(';');
                        for (let i = 0; i < cookies.length; i++) {
                            const cookie = cookies[i].trim();
                            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                                break;
                            }
                        }
                    }
                    return cookieValue;
                }
                
                // 设置默认时间
                document.addEventListener('DOMContentLoaded', function() {
                    // 获取当前时间
                    const now = new Date();
                    
                    // 格式化开始时间为datetime-local格式
                    const startYear = now.getFullYear();
                    const startMonth = String(now.getMonth() + 1).padStart(2, '0');
                    const startDay = String(now.getDate()).padStart(2, '0');
                    const startHours = String(now.getHours()).padStart(2, '0');
                    const startMinutes = String(now.getMinutes()).padStart(2, '0');
                    const startTimeString = `${startYear}-${startMonth}-${startDay}T${startHours}:${startMinutes}`;
                    
                    // 设置结束时间为开始时间后三天
                    const endDate = new Date(now);
                    endDate.setDate(now.getDate() + 3);
                    const endYear = endDate.getFullYear();
                    const endMonth = String(endDate.getMonth() + 1).padStart(2, '0');
                    const endDay = String(endDate.getDate()).padStart(2, '0');
                    const endHours = String(endDate.getHours()).padStart(2, '0');
                    const endMinutes = String(endDate.getMinutes()).padStart(2, '0');
                    const endTimeString = `${endYear}-${endMonth}-${endDay}T${endHours}:${endMinutes}`;
                    
                    // 设置表单默认值
                    document.getElementById('start_time').value = startTimeString;
                    document.getElementById('end_time').value = endTimeString;
                });
                
                // 切换活动显示
                function toggleActivities() {
                    const moreActivities = document.getElementById('more-activities');
                    const button = event.target;
                    if (moreActivities.style.display === 'none') {
                        moreActivities.style.display = 'block';
                        button.textContent = '收起';
                    } else {
                        moreActivities.style.display = 'none';
                        button.textContent = '显示全部';
                    }
                }
                
                function submitSeckill() {
                    const userId = document.getElementById('user_id').value;
                    const productId = document.getElementById('product_id').value;
                    const seckillPrice = document.getElementById('seckill_price').value;
                    const startTime = document.getElementById('start_time').value;
                    const endTime = document.getElementById('end_time').value;
                    const resultDiv = document.getElementById('result');
                    
                    if (!userId || !productId || !seckillPrice || !startTime || !endTime) {
                        resultDiv.innerHTML = '<div class="error">请填写所有必填字段</div>';
                        return;
                    }
                    
                    if (new Date(startTime) > new Date(endTime)) {
                        resultDiv.innerHTML = '<div class="error">开始时间不能晚于结束时间</div>';
                        return;
                    }
                    
                    const csrftoken = getCookie('csrftoken');
                    
                    // 先创建秒杀活动
                    fetch('/api/create_activity/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-CSRFToken': csrftoken
                        },
                        body: `product_id=${productId}&seckill_price=${seckillPrice}&start_time=${startTime}&end_time=${endTime}`
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('创建活动失败: ' + response.status);
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.code === 200) {
                            const activityId = data.activity_id;
                            // 执行秒杀
                            return fetch('/api/seckill/', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/x-www-form-urlencoded',
                                    'X-CSRFToken': csrftoken
                                },
                                body: `user_id=${userId}&activity_id=${activityId}`
                            });
                        } else {
                            throw new Error(data.message);
                        }
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('秒杀失败: ' + response.status);
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.code === 200) {
                            resultDiv.innerHTML = `<div class="success">${data.message}</div>`;
                        } else {
                            resultDiv.innerHTML = `<div class="error">${data.message}</div>`;
                        }
                    })
                    .catch(error => {
                        resultDiv.innerHTML = `<div class="error">请求失败: ${error.message}</div>`;
                        console.error('详细错误:', error);
                    });
                }
                </script>
        </head>
        <body>
            <div class="container">
                <h1>秒杀系统</h1>
                
                <div class="nav">
                    <a href="/">首页</a>
                    <a href="/admin/">管理后台</a>
                </div>
                
                <p>这是一个基于Django的秒杀系统，支持高并发秒杀场景。无需技术知识，您可以直接在网页上测试秒杀功能。</p>
                
                <h2>当前秒杀活动</h2>
        """
        
        # 添加活动列表
        if active_activities:
            activity_count = len(active_activities)
            show_count = 5
            
            # 显示前5个活动
            for i, activity in enumerate(active_activities[:show_count]):
                html += f"""
                <div class="activity">
                    <h3>{activity.product.name} - 秒杀价: ¥{activity.product.seckill_price}</h3>
                    <p>活动时间: {activity.start_time.strftime('%Y-%m-%d %H:%M:%S')} 至 {activity.end_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>原价: ¥{activity.product.original_price} | 库存: {activity.product.stock}</p>
                    <p>活动ID: {activity.id}</p>
                </div>
                """
            
            # 如果活动数量超过5个，添加折叠功能
            if activity_count > show_count:
                html += f"""
                <div id="more-activities" style="display: none;">
                """
                for activity in active_activities[show_count:]:
                    html += f"""
                    <div class="activity">
                        <h3>{activity.product.name} - 秒杀价: ¥{activity.product.seckill_price}</h3>
                        <p>活动时间: {activity.start_time.strftime('%Y-%m-%d %H:%M:%S')} 至 {activity.end_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p>原价: ¥{activity.product.original_price} | 库存: {activity.product.stock}</p>
                        <p>活动ID: {activity.id}</p>
                    </div>
                    """
                html += """
                </div>
                <button onclick="toggleActivities()" style="margin-top: 10px; background-color: #f0f0f0; color: #333; padding: 8px 16px; border: 1px solid #ddd; border-radius: 4px; cursor: pointer;">显示全部 ({activity_count - show_count} 个更多)</button>
                """
        else:
            html += "<p>当前没有进行中的秒杀活动</p>"
        
        # 添加秒杀测试表单
        html += """
                <h2>测试秒杀功能</h2>
                <div class="form-container">
                    <p>选择以下信息，点击"执行秒杀"按钮测试秒杀功能：</p>
                    <div class="form-group">
                        <label for="user_id">用户</label>
                        <select id="user_id">
        """
        
        # 添加用户选项
        for user in users:
            html += f"<option value='{user.id}'>{user.username} ({user.email})</option>"
        
        html += """
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="product_id">商品</label>
                        <select id="product_id">
        """
        
        # 添加商品选项，只选择需要的字段
        from apps.seckill.models import Product
        products = Product.objects.only('id', 'name', 'stock', 'original_price')
        for product in products:
            html += f"<option value='{product.id}'>{product.name} (库存: {product.stock}, 原价: ¥{product.original_price})</option>"
        
        html += """
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="seckill_price">秒杀价格</label>
                        <input type="number" id="seckill_price" step="0.01" placeholder="请输入秒杀价格，至少比原价优惠300元">
                    </div>
                    <div class="form-group">
                        <label for="start_time">开始时间</label>
                        <input type="datetime-local" id="start_time">
                    </div>
                    <div class="form-group">
                        <label for="end_time">结束时间</label>
                        <input type="datetime-local" id="end_time">
                    </div>
                    <button onclick="submitSeckill()">执行秒杀</button>
                    <div id="result" class="result"></div>
                </div>
                
                <h2>系统功能</h2>
                <div class="api-endpoint">首页 - 查看当前秒杀活动</div>
                <div class="api-endpoint">管理后台 - 管理商品和活动</div>
                <div class="api-endpoint">秒杀测试 - 直接在网页上测试秒杀</div>
                
                <div class="note">
                    <strong>使用说明:</strong><br>
                    1. 在"测试秒杀功能"中选择用户和秒杀活动<br>
                    2. 点击"执行秒杀"按钮测试秒杀功能<br>
                    3. 查看秒杀结果反馈<br>
                    4. 如需管理商品和活动，请登录管理后台
                </div>
                
                <div class="footer">
                    <p>© 2026 秒杀系统 - 让秒杀变得简单</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HttpResponse(html)


