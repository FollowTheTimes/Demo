import time
from django.http import HttpResponse

class RequestTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 开始时间
        start_time = time.time()
        
        # 处理请求
        response = self.get_response(request)
        
        # 结束时间
        end_time = time.time()
        
        # 计算耗时
        duration = end_time - start_time
        
        # 将耗时添加到响应头
        response['X-Request-Time'] = str(duration)
        
        # 打印耗时
        print(f'Request to {request.path} took {duration:.4f} seconds')
        
        return response
