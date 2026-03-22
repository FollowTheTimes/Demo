from django.db import models
from apps.users.models import User

class Product(models.Model):
    """商品表"""
    name = models.CharField(max_length=255, verbose_name='商品名称', db_index=True)
    stock = models.IntegerField(default=0, verbose_name='库存', db_index=True)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='原价')
    seckill_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='秒杀价')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '商品'
        verbose_name_plural = '商品'

    def __str__(self):
        return self.name

class SeckillActivity(models.Model):
    """秒杀活动表"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='关联商品', related_name='activities')
    start_time = models.DateTimeField(verbose_name='开始时间', db_index=True)
    end_time = models.DateTimeField(verbose_name='结束时间', db_index=True)
    STATUS_CHOICES = (
        ('pending', '待开始'),
        ('ongoing', '进行中'),
        ('ended', '已结束'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name='状态', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '秒杀活动'
        verbose_name_plural = '秒杀活动'

    def __str__(self):
        return f"{self.product.name} - {self.start_time} 至 {self.end_time}"

class Order(models.Model):
    """订单表"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='关联用户', related_name='orders')
    activity = models.ForeignKey(SeckillActivity, on_delete=models.CASCADE, verbose_name='关联活动', related_name='orders')
    ORDER_STATUS_CHOICES = (
        ('pending', '待支付'),
        ('paid', '已支付'),
        ('cancelled', '已取消'),
        ('refunded', '已退款'),
    )
    status = models.CharField(max_length=10, choices=ORDER_STATUS_CHOICES, default='pending', verbose_name='订单状态', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间', db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='支付时间')

    class Meta:
        verbose_name = '订单'
        verbose_name_plural = '订单'

    def __str__(self):
        return f"订单 {self.id} - {self.user.username}"
