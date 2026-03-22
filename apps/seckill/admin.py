from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Product, SeckillActivity, Order

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'stock', 'original_price', 'seckill_price', 'created_at', 'status')
    search_fields = ('name',)
    list_filter = ('created_at',)
    list_per_page = 10
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('name', 'stock', 'original_price', 'seckill_price')}),
        ('时间信息', {'fields': ('created_at', 'updated_at')}),
    )
    actions = ['edit_selected']
    
    def edit_selected(self, request, queryset):
        if queryset.count() == 1:
            obj = queryset.first()
            from django.http import HttpResponseRedirect
            from django.urls import reverse
            return HttpResponseRedirect(reverse('admin:seckill_product_change', args=[obj.id]))
        else:
            self.message_user(request, '请选择一个商品进行修改')
    edit_selected.short_description = '修改所选商品'
    
    def status(self, obj):
        if obj.stock > 0:
            return mark_safe('<span class="status-tag status-normal">正常</span>')
        else:
            return mark_safe('<span class="status-tag status-danger">缺货</span>')
    status.short_description = '状态'

@admin.register(SeckillActivity)
class SeckillActivityAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'start_time', 'end_time', 'status_display', 'get_seckill_price')
    search_fields = ('product__name',)
    list_filter = ('status', 'start_time', 'end_time')
    list_per_page = 10
    ordering = ('-start_time',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('product', 'start_time', 'end_time', 'status')}),
        ('时间信息', {'fields': ('created_at', 'updated_at')}),
    )
    actions = ['edit_selected']
    
    def edit_selected(self, request, queryset):
        if queryset.count() == 1:
            obj = queryset.first()
            from django.http import HttpResponseRedirect
            from django.urls import reverse
            return HttpResponseRedirect(reverse('admin:seckill_seckillactivity_change', args=[obj.id]))
        else:
            self.message_user(request, '请选择一个秒杀活动进行修改')
    edit_selected.short_description = '修改所选秒杀活动'
    
    def status_display(self, obj):
        from django.utils import timezone
        current_time = timezone.now()
        
        # 根据当前时间动态计算状态
        if current_time < obj.start_time:
            status = 'pending'
        elif current_time > obj.end_time:
            status = 'ended'
        else:
            status = 'ongoing'
        
        status_map = {
            'pending': mark_safe('<span class="status-tag status-warning">待开始</span>'),
            'ongoing': mark_safe('<span class="status-tag status-normal">进行中</span>'),
            'ended': mark_safe('<span class="status-tag status-info">已结束</span>')
        }
        return status_map.get(status, status)
    status_display.short_description = '状态'
    
    def get_seckill_price(self, obj):
        return f'¥{obj.product.seckill_price}'
    get_seckill_price.short_description = '秒杀价格'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'activity', 'get_product_name', 'get_seckill_price', 'status_display', 'created_at', 'paid_at')
    search_fields = ('user__username', 'activity__product__name', 'id')
    list_filter = ('status', 'created_at', 'paid_at')
    list_per_page = 10
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'paid_at')
    fieldsets = (
        (None, {'fields': ('user', 'activity', 'status')}),
        ('时间信息', {'fields': ('created_at', 'paid_at')}),
    )
    actions = ['edit_selected']
    
    def edit_selected(self, request, queryset):
        if queryset.count() == 1:
            obj = queryset.first()
            from django.http import HttpResponseRedirect
            from django.urls import reverse
            return HttpResponseRedirect(reverse('admin:seckill_order_change', args=[obj.id]))
        else:
            self.message_user(request, '请选择一个订单进行修改')
    edit_selected.short_description = '修改所选订单'
    
    def get_product_name(self, obj):
        return obj.activity.product.name
    get_product_name.short_description = '商品名称'
    
    def get_seckill_price(self, obj):
        return f'¥{obj.activity.product.seckill_price}'
    get_seckill_price.short_description = '秒杀价格'
    
    def status_display(self, obj):
        status_map = {
            'pending': mark_safe('<span class="status-tag status-warning">待支付</span>'),
            'paid': mark_safe('<span class="status-tag status-normal">已支付</span>'),
            'cancelled': mark_safe('<span class="status-tag status-danger">已取消</span>'),
            'refunded': mark_safe('<span class="status-tag status-info">已退款</span>')
        }
        return status_map.get(obj.status, obj.status)
    status_display.short_description = '状态'
