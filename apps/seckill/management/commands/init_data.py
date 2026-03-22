from django.core.management.base import BaseCommand
from apps.seckill.models import Product, SeckillActivity
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = '初始化商品和秒杀活动数据'

    def handle(self, *args, **options):
        # 创建商品
        products = [
            Product(
                name='iPhone 15 Pro',
                stock=100,
                original_price=9999.00,
                seckill_price=7999.00
            ),
            Product(
                name='MacBook Pro 14',
                stock=50,
                original_price=14999.00,
                seckill_price=12999.00
            ),
            Product(
                name='AirPods Pro 2',
                stock=200,
                original_price=1899.00,
                seckill_price=1499.00
            ),
            Product(
                name='iPad Pro 12.9',
                stock=80,
                original_price=8999.00,
                seckill_price=7499.00
            ),
            Product(
                name='Apple Watch Ultra 2',
                stock=120,
                original_price=6299.00,
                seckill_price=5299.00
            )
        ]

        for product in products:
            product.save()
            self.stdout.write(self.style.SUCCESS(f'创建商品: {product.name}'))

        # 创建秒杀活动
        for product in Product.objects.all():
            # 创建一个即将开始的活动
            start_time = datetime.now() + timedelta(minutes=30)
            end_time = start_time + timedelta(hours=2)
            activity1 = SeckillActivity(
                product=product,
                start_time=start_time,
                end_time=end_time,
                status='pending'
            )
            activity1.save()
            self.stdout.write(self.style.SUCCESS(f'创建秒杀活动: {product.name} - 待开始'))

            # 创建一个正在进行的活动
            start_time = datetime.now() - timedelta(hours=1)
            end_time = start_time + timedelta(hours=2)
            activity2 = SeckillActivity(
                product=product,
                start_time=start_time,
                end_time=end_time,
                status='ongoing'
            )
            activity2.save()
            self.stdout.write(self.style.SUCCESS(f'创建秒杀活动: {product.name} - 进行中'))

        self.stdout.write(self.style.SUCCESS('初始化数据完成'))
