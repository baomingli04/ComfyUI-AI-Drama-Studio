# -*- coding: utf-8 -*-
"""提示词模板表模型：对应 aicg.提示词模板 表。"""
from django.db import models


class 提示词模板(models.Model):
    """提示词模板表：按类型存放一套提示词（系统提示词 + 生成提示词）。

    类型取值见 docs/02 第 8 节：如 剧本 / 分集 / 人物设定 / 分镜；
    测试页 AI扩写 的配置用 `扩写:<前端路由>`，规则文本存在 系统提示词 列。
    """

    id = models.BigAutoField(primary_key=True, db_column='id', verbose_name='主键')
    类型 = models.CharField(max_length=50, db_column='类型', verbose_name='类型')
    系统提示词 = models.TextField(blank=True, null=True, db_column='系统提示词', verbose_name='系统提示词')
    生成提示词 = models.TextField(blank=True, null=True, db_column='生成提示词', verbose_name='生成提示词')
    创建时间 = models.DateTimeField(db_column='创建时间', verbose_name='创建时间')
    更新时间 = models.DateTimeField(db_column='更新时间', verbose_name='更新时间')

    class Meta:
        db_table = '提示词模板'
        verbose_name = '提示词模板'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.类型
