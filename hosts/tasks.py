from celery import shared_task
from .models import Host, HostCount, City, Datacenter
import random
import string
from django.utils import timezone

@shared_task
def update_host_passwords():
    """每隔8小时随机修改每台主机的密码并加密记录"""
    hosts = Host.objects.all()
    for host in hosts:
        # 生成随机密码
        password = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=16))
        host.root_password = password
        host.save()
    return f'Updated passwords for {len(hosts)} hosts'

@shared_task
def count_hosts_by_city_datacenter():
    """每天 00:00 按城市和机房维度统计主机数量，并把统计数据写入数据库"""
    datacenters = Datacenter.objects.all()
    today = timezone.now().date()
    
    for datacenter in datacenters:
        # 统计该机房的主机数量
        host_count = Host.objects.filter(datacenter=datacenter, is_active=True).count()
        
        # 检查是否已存在今天的统计数据
        existing_count, created = HostCount.objects.get_or_create(
            city=datacenter.city,
            datacenter=datacenter,
            date=today,
            defaults={'count': host_count}
        )
        
        # 如果已存在，则更新数量
        if not created:
            existing_count.count = host_count
            existing_count.save()
    
    return f'Stats updated for {len(datacenters)} datacenters'
