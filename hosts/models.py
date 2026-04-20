from django.db import models
from django.db.models import UniqueConstraint
import random
import string
from cryptography.fernet import Fernet
import os

# 生成加密密钥
if not os.path.exists('encryption_key.key'):
    key = Fernet.generate_key()
    with open('encryption_key.key', 'wb') as f:
        f.write(key)
else:
    with open('encryption_key.key', 'rb') as f:
        key = f.read()

cipher_suite = Fernet(key)

class City(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='城市名称')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '城市'
        verbose_name_plural = '城市管理'

    def __str__(self):
        return self.name

class Datacenter(models.Model):
    name = models.CharField(max_length=100, verbose_name='机房名称')
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name='所属城市')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '机房'
        verbose_name_plural = '机房管理'
        constraints = [
            UniqueConstraint(fields=['name', 'city'], name='unique_datacenter_in_city')
        ]

    def __str__(self):
        return f'{self.city.name} - {self.name}'

class Host(models.Model):
    hostname = models.CharField(max_length=255, unique=True, verbose_name='主机名')
    ip_address = models.GenericIPAddressField(unique=True, verbose_name='IP地址')
    datacenter = models.ForeignKey(Datacenter, on_delete=models.CASCADE, verbose_name='所属机房')
    _root_password = models.BinaryField(verbose_name='root密码')
    is_active = models.BooleanField(default=True, verbose_name='是否活跃')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '主机'
        verbose_name_plural = '主机管理'

    @property
    def root_password(self):
        try:
            return cipher_suite.decrypt(self._root_password).decode()
        except:
            return ''

    @root_password.setter
    def root_password(self, value):
        self._root_password = cipher_suite.encrypt(value.encode())

    def __str__(self):
        return self.hostname

class HostCount(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name='城市')
    datacenter = models.ForeignKey(Datacenter, on_delete=models.CASCADE, verbose_name='机房')
    count = models.IntegerField(verbose_name='主机数量')
    date = models.DateField(auto_now_add=True, verbose_name='统计日期')

    class Meta:
        verbose_name = '主机统计'
        verbose_name_plural = '主机统计管理'
        constraints = [
            UniqueConstraint(fields=['city', 'datacenter', 'date'], name='unique_host_count')
        ]

    def __str__(self):
        return f'{self.city.name} - {self.datacenter.name} - {self.date} - {self.count}'
