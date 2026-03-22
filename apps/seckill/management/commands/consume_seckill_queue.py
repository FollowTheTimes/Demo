from django.core.management.base import BaseCommand
import redis
import json
import time
from apps.seckill.tasks import create_order_task

class Command(BaseCommand):
    help = '从 Redis 队列中消费秒杀任务并处理'

    def handle(self, *args, **options):
        # 连接 Redis
        r = redis.Redis(host='redis', port=6379, db=1)
        queue_name = 'seckill:queue'
        
        self.stdout.write(self.style.SUCCESS('开始消费秒杀队列...'))
        
        # 无限循环消费队列
        while True:
            try:
                # 从队列中弹出数据（阻塞式，等待时间为 1 秒）
                task_data = r.brpop(queue_name, timeout=1)
                
                if task_data:
                    # 解析任务数据
                    task_info = json.loads(task_data[1])
                    user_id = task_info.get('user_id')
                    activity_id = task_info.get('activity_id')
                    
                    self.stdout.write(self.style.SUCCESS(f'处理秒杀任务: user_id={user_id}, activity_id={activity_id}'))
                    
                    try:
                        # 调用 Celery 任务处理，传入参数
                        create_order_task.delay(user_id, activity_id)
                    except Exception as e:
                        # 处理异常，重新入队
                        self.stdout.write(self.style.ERROR(f'处理任务失败: {e}，重新入队'))
                        r.lpush(queue_name, json.dumps(task_info))
                
                # 短暂休眠，避免 CPU 占用过高
                time.sleep(0.1)
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'消费队列时出错: {e}'))
                # 短暂休眠，避免异常时循环过快
                time.sleep(1)
