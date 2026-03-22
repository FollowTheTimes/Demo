from django.core.management.base import BaseCommand
from apps.seckill.models import Product, SeckillActivity, Order
from apps.users.models import User
from django.utils import timezone
import datetime
import random

class Command(BaseCommand):
    help = '生成测试数据，包括商品、秒杀活动、订单和用户'

    def handle(self, *args, **kwargs):
        self.stdout.write('开始生成测试数据...')
        
        # 清理现有数据
        self._clean_existing_data()
        self.stdout.write('已清理现有数据')
        
        # 生成用户
        users = self._generate_users()
        self.stdout.write(f'生成了 {len(users)} 个用户')
        
        # 生成商品
        products = self._generate_products()
        self.stdout.write(f'生成了 {len(products)} 个商品')
        
        # 生成秒杀活动
        activities = self._generate_activities(products)
        self.stdout.write(f'生成了 {len(activities)} 个秒杀活动')
        
        # 生成订单
        orders = self._generate_orders(users, activities)
        self.stdout.write(f'生成了 {len(orders)} 个订单')
        
        self.stdout.write('测试数据生成完成！')
    
    def _clean_existing_data(self):
        """清理现有数据"""
        Order.objects.all().delete()
        SeckillActivity.objects.all().delete()
        Product.objects.all().delete()
        # 保留超级用户
        User.objects.filter(is_superuser=False).delete()
    
    def _generate_users(self):
        users = []
        # 真实的中文名字列表
        chinese_names = [
            '王五', '李高星', '刘大爷', '张三', '李四', 
            '赵六', '钱七', '孙八', '周九', '吴十'
        ]
        
        # 对应的英文用户名列表
        english_usernames = [
            'wangwu', 'ligaoxing', 'liudaye', 'zhangsan', 'lisi',
            'zhaoliu', 'qianqi', 'sunba', 'zhoujiu', 'wushi'
        ]
        
        for i, (name, username) in enumerate(zip(chinese_names, english_usernames), 1):
            # 生成随机的创建时间，范围为1-60天前
            random_days = random.randint(1, 60)
            date_joined = timezone.now() - datetime.timedelta(days=random_days, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'phone': f'138001380{i:02d}',
                    'password': 'test123456'
                }
            )
            # 强制更新date_joined字段和first_name
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE users_user SET date_joined = %s, first_name = %s WHERE id = %s",
                    [date_joined, name, user.id]
                )
            user.refresh_from_db()
            users.append(user)
        return users
    
    def _generate_products(self):
        products = []
        product_names = [
            'iPhone 15 Pro',
            'MacBook Pro 14',
            'AirPods Pro 2',
            'iPad Pro 12.9',
            'Apple Watch Ultra 2',
            'Samsung Galaxy S24',
            'Google Pixel 8 Pro',
            'Sony WH-1000XM5',
            'Nintendo Switch OLED',
            'PlayStation 5'
        ]
        
        for i, name in enumerate(product_names):
            # 生成随机的创建时间，范围为1-60天前
            random_days = random.randint(1, 60)
            created_at = timezone.now() - datetime.timedelta(days=random_days, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            
            # 先创建商品
            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'stock': 100,
                    'original_price': 5000 + i * 1000,
                    'seckill_price': 4000 + i * 800
                }
            )
            # 强制更新created_at字段，绕过auto_now_add
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE seckill_product SET created_at = %s WHERE id = %s",
                    [created_at, product.id]
                )
            # 重新获取商品以获取更新后的值
            product.refresh_from_db()
            products.append(product)
        return products
    
    def _generate_activities(self, products):
        activities = []
        now = timezone.now()
        
        # 生成50条秒杀活动数据
        for i in range(50):
            # 随机选择一个商品
            product = random.choice(products)
            
            # 生成随机的创建时间，范围为1-50天前
            random_days = random.randint(1, 50)
            created_at = timezone.now() - datetime.timedelta(days=random_days, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            
            # 随机决定活动状态，进行中的概率更大
            status_choice = random.choices(
                ['pending', 'ongoing', 'ended'],
                weights=[20, 60, 20],  # 20%待开始，60%进行中，20%已结束
                k=1
            )[0]
            
            if status_choice == 'ongoing':
                # 进行中：开始时间在过去，结束时间在未来
                start_time_random_days = random.randint(1, 10)
                start_time = timezone.now() - datetime.timedelta(days=start_time_random_days, hours=random.randint(0, 23), minutes=random.randint(0, 59))
                end_time_random_days = random.randint(1, 5)
                end_time = timezone.now() + datetime.timedelta(days=end_time_random_days, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            elif status_choice == 'pending':
                # 待开始：开始时间在未来
                start_time_random_days = random.randint(1, 7)
                start_time = timezone.now() + datetime.timedelta(days=start_time_random_days, hours=random.randint(0, 23), minutes=random.randint(0, 59))
                end_time = start_time + datetime.timedelta(days=3)
            else:  # ended
                # 已结束：结束时间在过去
                end_time_random_days = random.randint(1, 20)
                end_time = timezone.now() - datetime.timedelta(days=end_time_random_days, hours=random.randint(0, 23), minutes=random.randint(0, 59))
                start_time = end_time - datetime.timedelta(days=3)
            
            # 创建活动
            activity, created = SeckillActivity.objects.get_or_create(
                product=product,
                start_time=start_time,
                end_time=end_time,
                defaults={
                    'status': status_choice
                }
            )
            # 强制更新created_at字段
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE seckill_seckillactivity SET created_at = %s WHERE id = %s",
                    [created_at, activity.id]
                )
            activity.refresh_from_db()
            activities.append(activity)
        
        return activities
    
    def _generate_orders(self, users, activities):
        orders = []
        now = timezone.now()
        
        for i, user in enumerate(users):
            for j, activity in enumerate(activities[:20]):  # 为前20个活动生成订单
                # 生成随机的创建时间，范围为1-40天前
                random_days = random.randint(1, 40)
                created_at = timezone.now() - datetime.timedelta(days=random_days, hours=random.randint(0, 23), minutes=random.randint(0, 59))
                
                if i % 3 == 0:
                    # 已支付订单
                    order, created = Order.objects.get_or_create(
                        user=user,
                        activity=activity,
                        defaults={
                            'status': 'paid',
                            'paid_at': created_at + datetime.timedelta(minutes=15)
                        }
                    )
                elif i % 3 == 1:
                    # 待处理订单
                    order, created = Order.objects.get_or_create(
                        user=user,
                        activity=activity,
                        defaults={
                            'status': 'pending'
                        }
                    )
                else:
                    # 已取消订单
                    order, created = Order.objects.get_or_create(
                        user=user,
                        activity=activity,
                        defaults={
                            'status': 'cancelled'
                        }
                    )
                
                # 强制更新created_at字段
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE seckill_order SET created_at = %s WHERE id = %s",
                        [created_at, order.id]
                    )
                order.refresh_from_db()
                orders.append(order)
        
        return orders
