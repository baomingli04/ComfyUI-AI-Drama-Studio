# -*- coding: utf-8 -*-
"""技能分类表模型：对应 aicg.技能分类 表。"""
from django.db import models


class 技能分类(models.Model):
    """技能分类表：技能包的分类目录，含系统内置预置。"""

    id = models.BigAutoField(primary_key=True, db_column='id', verbose_name='主键')
    名称 = models.CharField(max_length=50, db_column='名称', verbose_name='名称')
    编码 = models.CharField(max_length=50, unique=True, db_column='编码', verbose_name='编码')
    排序 = models.IntegerField(default=0, db_column='排序', verbose_name='排序')
    系统内置 = models.BooleanField(default=False, db_column='系统内置', verbose_name='是否系统内置')
    创建时间 = models.DateTimeField(db_column='创建时间', verbose_name='创建时间')

    class Meta:
        db_table = '技能分类'
        verbose_name = '技能分类'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.名称
