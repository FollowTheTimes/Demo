from celery import shared_task
from apps.monitor.alerts import run_alert_check
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_alerts_task():
    """定期运行告警检查的Celery任务"""
    logger.info('开始运行定时告警检查...')
    alerts = run_alert_check()
    logger.info(f'定时告警检查完成，发现 {len(alerts)} 个告警')
    return len(alerts)

@shared_task
def check_system_health_task():
    """检查系统健康状态的任务"""
    from apps.monitor.alerts import alert_system
    alerts = alert_system.check_system_health()
    for alert in alerts:
        alert_system.send_alert(alert)
    return len(alerts)

@shared_task
def check_redis_health_task():
    """检查Redis健康状态的任务"""
    from apps.monitor.alerts import alert_system
    alerts = alert_system.check_redis_health()
    for alert in alerts:
        alert_system.send_alert(alert)
    return len(alerts)

@shared_task
def check_database_health_task():
    """检查数据库健康状态的任务"""
    from apps.monitor.alerts import alert_system
    alerts = alert_system.check_database_health()
    for alert in alerts:
        alert_system.send_alert(alert)
    return len(alerts)