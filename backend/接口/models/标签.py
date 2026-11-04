# -*- coding: utf-8 -*-
"""题材标签表模型：对应 aicg.题材标签 表。

/script/new 的题材 chips 从这里读；手动添加的新标签也写进这张表，
所有新项目共用同一份标签库（系统内置 + 用户自建）。
"""
from django.db import models


class 标签(models.Model):
    """题材标签：主 + 辅最多选 2 个；系统内置的不可删，用户自建的来自 /script/new 手动添加。"""

    id = models.BigAutoField(primary_key=True, db_column='id', verbose_name='主键')
    名称 = models.CharField(max_length=50, unique=True, db_column='名称', verbose_name='标签名，全局唯一')
    系统内置 = models.BooleanField(default=False, db_column='系统内置', verbose_name='1=内置标签（种子写入，页面不提供删除）')
    排序 = models.IntegerField(default=0, db_column='排序', verbose_name='显示顺序，小在前')
    用户id = models.BigIntegerField(null=True, blank=True, db_column='用户id', verbose_name='添加人；内置为 NULL')
    创建时间 = models.DateTimeField(db_column='创建时间', verbose_name='创建时间')

    class Meta:
        db_table = '题材标签'
        verbose_name = '题材标签'
        verbose_name_plural = verbose_name
        ordering = ['排序', 'id']

    def __str__(self):
        return self.名称
