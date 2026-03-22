import redis
import psutil
import time
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def health_check(request):
    """健康检查端点"""
    try:
        # 检查数据库连接
        from django.db import connection
        connection.cursor()
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"
        logger.error(f"Database health check failed: {str(e)}")

    try:
        # 检查Redis连接
        import redis
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=1,
            decode_responses=True
        )
        redis_client.ping()
        redis_status = "ok"
    except Exception as e:
        redis_status = f"error: {str(e)}"
        logger.error(f"Redis health check failed: {str(e)}")

    # 系统状态
    system_status = {
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "uptime": time.time() - psutil.boot_time()
    }

    return JsonResponse({
        "status": "ok",
        "timestamp": time.time(),
        "checks": {
            "database": db_status,
            "redis": redis_status,
            "system": system_status
        }
    })

@csrf_exempt
def metrics(request):
    """监控指标端点"""
    try:
        # 获取系统指标
        metrics_data = {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_used": psutil.virtual_memory().used / (1024 * 1024 * 1024),
            "memory_total": psutil.virtual_memory().total / (1024 * 1024 * 1024),
            "disk_used": psutil.disk_usage('/').used / (1024 * 1024 * 1024),
            "disk_total": psutil.disk_usage('/').total / (1024 * 1024 * 1024),
            "process_count": len(psutil.pids()),
            "uptime": time.time() - psutil.boot_time()
        }

        return JsonResponse(metrics_data)
    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def seckill_stats(request):
    """秒杀系统统计信息"""
    try:
        from apps.seckill.models import Product, SeckillActivity, Order
        import redis

        # 获取统计数据
        total_products = Product.objects.count()
        total_activities = SeckillActivity.objects.count()
        total_orders = Order.objects.count()
        successful_orders = Order.objects.filter(status='success').count()

        # 从Redis获取库存信息
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=1,
            decode_responses=True
        )

        stock_info = {}
        activities = SeckillActivity.objects.all()
        for activity in activities:
            stock_key = f"seckill:stock:{activity.id}"
            try:
                stock = redis_client.hget(stock_key, 'stock')
                if stock:
                    stock_info[activity.id] = int(stock)
            except Exception:
                pass

        return JsonResponse({
            "total_products": total_products,
            "total_activities": total_activities,
            "total_orders": total_orders,
            "successful_orders": successful_orders,
            "stock_info": stock_info
        })
    except Exception as e:
        logger.error(f"Seckill stats collection failed: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)