import time
import logging
from datetime import datetime
from django.conf import settings
import redis

logger = logging.getLogger(__name__)

class AlertSystem:
    """告警系统"""
    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=1,
                decode_responses=True
            )
        except Exception:
            self.redis_client = None
        
        self.alert_thresholds = {
            "cpu_usage": 80,  # CPU使用率阈值
            "memory_usage": 80,  # 内存使用率阈值
            "disk_usage": 90,  # 磁盘使用率阈值
            "response_time": 2,  # 响应时间阈值（秒）
            "error_rate": 5  # 错误率阈值（%）
        }
        
        self.alert_history = []
        self.cooldown_period = 300  # 告警冷却时间（秒）
    
    def check_system_health(self):
        """检查系统健康状态"""
        import psutil
        alerts = []
        
        # 检查CPU使用率
        cpu_usage = psutil.cpu_percent(interval=1)
        if cpu_usage > self.alert_thresholds["cpu_usage"]:
            alerts.append({
                "type": "cpu_usage",
                "message": f"CPU使用率过高: {cpu_usage}%",
                "severity": "warning",
                "timestamp": datetime.now().isoformat()
            })
        
        # 检查内存使用率
        memory_usage = psutil.virtual_memory().percent
        if memory_usage > self.alert_thresholds["memory_usage"]:
            alerts.append({
                "type": "memory_usage",
                "message": f"内存使用率过高: {memory_usage}%",
                "severity": "warning",
                "timestamp": datetime.now().isoformat()
            })
        
        # 检查磁盘使用率
        disk_usage = psutil.disk_usage('/').percent
        if disk_usage > self.alert_thresholds["disk_usage"]:
            alerts.append({
                "type": "disk_usage",
                "message": f"磁盘使用率过高: {disk_usage}%",
                "severity": "critical",
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts
    
    def check_redis_health(self):
        """检查Redis健康状态"""
        alerts = []
        
        try:
            if self.redis_client:
                self.redis_client.ping()
                # 检查Redis内存使用
                info = self.redis_client.info()
                used_memory = info.get('used_memory_rss', 0) / (1024 * 1024 * 1024)  # GB
                if used_memory > 1:
                    alerts.append({
                        "type": "redis_memory",
                        "message": f"Redis内存使用过高: {used_memory:.2f}GB",
                        "severity": "warning",
                        "timestamp": datetime.now().isoformat()
                    })
        except Exception as e:
            alerts.append({
                "type": "redis_connection",
                "message": f"Redis连接失败: {str(e)}",
                "severity": "critical",
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts
    
    def check_database_health(self):
        """检查数据库健康状态"""
        alerts = []
        
        try:
            from django.db import connection
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
        except Exception as e:
            alerts.append({
                "type": "database_connection",
                "message": f"数据库连接失败: {str(e)}",
                "severity": "critical",
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts
    
    def check_seckill_status(self):
        """检查秒杀系统状态"""
        alerts = []
        
        try:
            from apps.seckill.models import SeckillActivity
            
            # 检查活动状态
            active_activities = SeckillActivity.objects.filter(status='active')
            if not active_activities.exists():
                alerts.append({
                    "type": "no_active_activities",
                    "message": "当前没有活跃的秒杀活动",
                    "severity": "info",
                    "timestamp": datetime.now().isoformat()
                })
            
            # 检查库存
            if self.redis_client:
                for activity in active_activities:
                    stock_key = f"seckill:stock:{activity.id}"
                    stock = self.redis_client.hget(stock_key, 'stock')
                    if stock and int(stock) <= 0:
                        alerts.append({
                            "type": "stock_depleted",
                            "message": f"活动 {activity.id} 库存已耗尽",
                            "severity": "info",
                            "timestamp": datetime.now().isoformat()
                        })
        except Exception as e:
            alerts.append({
                "type": "seckill_check_error",
                "message": f"秒杀系统检查失败: {str(e)}",
                "severity": "error",
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts
    
    def process_alerts(self):
        """处理所有告警"""
        all_alerts = []
        
        # 收集所有告警
        all_alerts.extend(self.check_system_health())
        all_alerts.extend(self.check_redis_health())
        all_alerts.extend(self.check_database_health())
        all_alerts.extend(self.check_seckill_status())
        
        # 过滤重复告警
        filtered_alerts = self._filter_repeated_alerts(all_alerts)
        
        # 发送告警
        for alert in filtered_alerts:
            self.send_alert(alert)
        
        return filtered_alerts
    
    def _filter_repeated_alerts(self, alerts):
        """过滤重复告警"""
        filtered = []
        current_time = time.time()
        
        for alert in alerts:
            # 检查是否在冷却期内
            is_repeated = False
            for history_alert in self.alert_history:
                if (history_alert["type"] == alert["type"] and
                    current_time - history_alert["timestamp_epoch"] < self.cooldown_period):
                    is_repeated = True
                    break
            
            if not is_repeated:
                alert["timestamp_epoch"] = current_time
                filtered.append(alert)
                self.alert_history.append(alert)
        
        # 清理过期的历史告警
        self.alert_history = [
            alert for alert in self.alert_history
            if current_time - alert["timestamp_epoch"] < self.cooldown_period
        ]
        
        return filtered
    
    def send_alert(self, alert):
        """发送告警"""
        # 这里可以实现不同的告警方式
        # 1. 日志记录
        # 2. 邮件通知
        # 3. 短信通知
        # 4. 企业微信/钉钉通知
        
        severity_map = {
            "critical": logging.CRITICAL,
            "error": logging.ERROR,
            "warning": logging.WARNING,
            "info": logging.INFO
        }
        
        severity_level = severity_map.get(alert["severity"], logging.INFO)
        logger.log(severity_level, f"[ALERT] {alert['type']}: {alert['message']}")
        
        # 可以在这里添加其他告警方式
        # 例如发送邮件
        # self.send_email_alert(alert)
        
    def send_email_alert(self, alert):
        """发送邮件告警"""
        # 实现邮件发送逻辑
        pass

# 创建全局告警系统实例
alert_system = AlertSystem()

def run_alert_check():
    """运行告警检查"""
    return alert_system.process_alerts()