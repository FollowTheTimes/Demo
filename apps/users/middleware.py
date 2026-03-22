from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
import redis
from django_redis import get_redis_connection
import time

class LoginAttemptLimitMiddleware:
    """登录尝试限制中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.path == '/admin/login/':
            # 获取客户端IP
            ip = request.META.get('REMOTE_ADDR', 'unknown')
            # 获取Redis连接
            r = get_redis_connection('default')
            # 生成限流key
            login_attempt_key = f'login:attempt:{ip}'
            
            # 检查登录尝试次数
            attempts = r.get(login_attempt_key)
            if attempts and int(attempts) >= 5:
                # 获取过期时间
                ttl = r.ttl(login_attempt_key)
                return HttpResponseForbidden(f'登录尝试次数过多，请{ttl}秒后再试')
        
        response = self.get_response(request)
        return response