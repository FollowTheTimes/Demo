from django.core.management.base import BaseCommand
from apps.seckill.models import SeckillActivity, Product
from django_redis import get_redis_connection

class Command(BaseCommand):
    """缓存预热命令"""
    help = '预热缓存，将商品库存和活动信息加载到Redis中'
    
    def handle(self, *args, **options):
        # 获取Redis连接
        r = get_redis_connection('default')
        
        # 遍历所有秒杀活动
        activities = SeckillActivity.objects.select_related('product').all()
        
        for activity in activities:
            # 加载库存信息到Redis
            stock_key = f'seckill:stock:{activity.id}'
            r.hset(stock_key, 'stock', activity.product.stock)
            r.expire(stock_key, 86400)  # 设置过期时间为24小时
            
            # 加载活动信息到Redis
            activity_key = f'seckill:activity:{activity.id}'
            r.hset(activity_key, 'product_id', activity.product.id)
            r.hset(activity_key, 'start_time', activity.start_time.timestamp())
            r.hset(activity_key, 'end_time', activity.end_time.timestamp())
            r.hset(activity_key, 'status', activity.status)
            r.expire(activity_key, 86400)  # 设置过期时间为24小时
            
            self.stdout.write(self.style.SUCCESS(f'已预热活动 {activity.id} 的缓存'))
        
        # 加载所有商品信息到Redis
        products = Product.objects.all()
        for product in products:
            product_key = f'seckill:product:{product.id}'
            r.hset(product_key, 'name', product.name)
            r.hset(product_key, 'original_price', str(product.original_price))
            r.hset(product_key, 'seckill_price', str(product.seckill_price))
            r.hset(product_key, 'stock', product.stock)
            r.expire(product_key, 86400)  # 设置过期时间为24小时
            
            self.stdout.write(self.style.SUCCESS(f'已预热商品 {product.id} 的缓存'))
        
        self.stdout.write(self.style.SUCCESS('缓存预热完成'))