from django.core.management.base import BaseCommand
from apps.monitor.alerts import run_alert_check
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '运行系统告警检查'

    def handle(self, *args, **options):
        logger.info('开始运行告警检查...')
        alerts = run_alert_check()
        
        if alerts:
            self.stdout.write(self.style.WARNING(f'发现 {len(alerts)} 个告警:'))
            for alert in alerts:
                self.stdout.write(self.style.WARNING(f"{alert['severity'].upper()}: {alert['message']}"))
        else:
            self.stdout.write(self.style.SUCCESS('未发现告警，系统运行正常'))
        
        logger.info(f'告警检查完成，发现 {len(alerts)} 个告警')