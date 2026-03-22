from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver
from django_redis import get_redis_connection

@receiver(user_login_failed)
def handle_login_failed(sender, credentials, request, **kwargs):
    """处理登录失败事件"""
    if request:
        # 获取客户端IP
        ip = request.META.get('REMOTE_ADDR', 'unknown')
        # 获取Redis连接
        r = get_redis_connection('default')
        # 生成限流key
        login_attempt_key = f'login:attempt:{ip}'
        
        # 增加登录尝试次数
        attempts = r.incr(login_attempt_key)
        
        # 如果是第一次尝试，设置过期时间为1小时
        if attempts == 1:
            r.expire(login_attempt_key, 3600)