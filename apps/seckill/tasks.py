from celery import shared_task
from django.db import transaction
import redis
import json
from apps.seckill.models import SeckillActivity, Order
from apps.users.models import User

@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def create_order_task(self, user_id, activity_id):
    """处理秒杀记录，写入 MySQL Order 表"""
    try:
        if not user_id or not activity_id:
            return "任务数据不完整"
        
        # 使用数据库事务
        with transaction.atomic():
            # 获取用户和活动
            user = User.objects.get(id=user_id)
            activity = SeckillActivity.objects.get(id=activity_id)
            
            # 创建订单
            order = Order.objects.create(
                user=user,
                activity=activity,
                status='pending'
            )
            
        return f"成功创建订单 {order.id}"
        
    except Exception as e:
        # 重试机制
        self.retry(exc=e)

@shared_task
def process_seckill_queue():
    """定时处理秒杀队列"""
    # 连接 Redis
    r = redis.Redis(host='redis', port=6379, db=1)
    
    # 获取队列长度
    queue_length = r.llen('seckill:queue')
    
    # 处理队列中的所有任务
    for _ in range(queue_length):
        create_order_task.delay()

