# -*- coding: utf-8 -*-
"""用户表模型：对应 aicg.用户 表。"""
from django.db import models


class 用户(models.Model):
    """用户表：仅本机管理员，含登录名与密码哈希（pbkdf2_sha256）。"""

    id = models.BigAutoField(primary_key=True, db_column='id', verbose_name='主键')
    用户名 = models.CharField(max_length=50, unique=True, db_column='用户名', verbose_name='用户名')
    密码哈希 = models.CharField(max_length=128, db_column='密码哈希', verbose_name='密码哈希')
    昵称 = models.CharField(max_length=50, blank=True, null=True, db_column='昵称', verbose_name='昵称')
    启用 = models.BooleanField(default=True, db_column='启用', verbose_name='是否启用')
    创建时间 = models.DateTimeField(db_column='创建时间', verbose_name='创建时间')
    更新时间 = models.DateTimeField(db_column='更新时间', verbose_name='更新时间')

    class Meta:
        db_table = '用户'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.用户名
