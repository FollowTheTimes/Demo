from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'chinese_name', 'username', 'email', 'phone', 'is_staff', 'status', 'is_superuser', 'date_joined')
    search_fields = ('username', 'first_name', 'email', 'phone')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'date_joined')
    list_per_page = 10
    ordering = ('-date_joined',)
    readonly_fields = ('last_login', 'date_joined')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )
    actions = ['edit_selected']
    
    def edit_selected(self, request, queryset):
        if queryset.count() == 1:
            obj = queryset.first()
            from django.http import HttpResponseRedirect
            from django.urls import reverse
            return HttpResponseRedirect(reverse('admin:users_user_change', args=[obj.id]))
        else:
            self.message_user(request, '请选择一个用户进行修改')
    edit_selected.short_description = '修改所选用户'
    
    def status(self, obj):
        if obj.is_active:
            return mark_safe('<span class="status-tag status-normal">正常</span>')
        else:
            return mark_safe('<span class="status-tag status-danger">禁用</span>')
    status.short_description = '状态'
    
    def chinese_name(self, obj):
        return obj.first_name if obj.first_name else obj.username
    chinese_name.short_description = '中文名'
    chinese_name.admin_order_field = 'first_name'
