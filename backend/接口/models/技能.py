# -*- coding: utf-8 -*-
"""技能表模型：对应 aicg.技能 表。"""
from django.db import models


class 技能(models.Model):
    """技能表：上传的技能包，归属一个分类。"""

    id = models.BigAutoField(primary_key=True, db_column='id', verbose_name='主键')
    目录名 = models.CharField(max_length=255, unique=True, db_column='目录名', verbose_name='目录名')
    名称 = models.CharField(max_length=255, db_column='名称', verbose_name='名称')
    简介 = models.TextField(blank=True, null=True, db_column='简介', verbose_name='简介')
    分类id = models.ForeignKey('技能分类', on_delete=models.RESTRICT, db_column='分类id', verbose_name='分类')
    来源 = models.CharField(max_length=50, default='上传压缩包', db_column='来源', verbose_name='来源')
    原压缩包名 = models.CharField(max_length=255, blank=True, null=True, db_column='原压缩包名', verbose_name='原压缩包名')
    创建时间 = models.DateTimeField(db_column='创建时间', verbose_name='创建时间')
    更新时间 = models.DateTimeField(db_column='更新时间', verbose_name='更新时间')

    class Meta:
        db_table = '技能'
        verbose_name = '技能'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.名称
