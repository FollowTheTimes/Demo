from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """扩展用户模型"""
    # 手机号
    phone = models.CharField(max_length=11, unique=True, null=True, blank=True, verbose_name='手机号')
    # 头像
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='头像')
    # 性别
    GENDER_CHOICES = (
        ('male', '男'),
        ('female', '女'),
        ('other', '其他'),
    )
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True, verbose_name='性别')
    # 出生日期
    birthday = models.DateField(null=True, blank=True, verbose_name='出生日期')
    # 个人简介
    bio = models.TextField(null=True, blank=True, verbose_name='个人简介')

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        return self.first_name if self.first_name else self.username
