from django.core.management.base import BaseCommand
from apps.seckill.models import SeckillActivity
import redis

class Command(BaseCommand):
    help = '将秒杀活动库存加载到 Redis'

    def handle(self, *args, **options):
        # 连接 Redis
        r = redis.Redis(host='redis', port=6379, db=1)
        
        # 遍历所有秒杀活动
        activities = SeckillActivity.objects.all()
        
        for activity in activities:
            # 获取对应商品的剩余库存
            stock = activity.product.stock
            
            # 构建 Redis key
            redis_key = f'seckill:stock:{activity.id}'
            
            # 将库存存入 Redis hash 结构
            r.hset(redis_key, 'stock', stock)
            
            # 输出加载结果
            self.stdout.write(self.style.SUCCESS(f'加载活动 {activity.id} 库存到 Redis: {stock}'))
        
        self.stdout.write(self.style.SUCCESS('库存加载完成'))
