# -*- coding: utf-8 -*-
"""资产表模型：对应 aicg.资产 表（/video/assets 资产清单页数据源）。

一行 = 某剧某一集的一项资产（人物/场景/道具/服装），按 排序 升序展示。
资产id 沿用 CHAR_/SCN_/PROP_/COST_ 前缀编号；别名用顿号分隔的实体文本列。
2026-11-02 新建（见 docs/02-数据库文档.md 第 13 节）。
"""
from django.db import models


class 资产(models.Model):
    """资产清单行：从本集剧本提取的可拍资产，逐项可编辑、可按技能重新提取。"""

    id = models.BigAutoField(primary_key=True, db_column='id', verbose_name='行主键')
    剧id = models.BigIntegerField(db_column='剧id', verbose_name='所属剧')
    集号 = models.IntegerField(db_column='集号', verbose_name='集号')
    资产id = models.CharField(max_length=32, db_column='资产id', verbose_name='CHAR_001/SCN_001/PROP_001/COST_001')
    类型 = models.CharField(max_length=10, db_column='类型', verbose_name='人物/场景/道具/服装')
    名称 = models.CharField(max_length=100, db_column='名称', verbose_name='资产名')
    别名 = models.CharField(max_length=300, null=True, blank=True, db_column='别名', verbose_name='顿号分隔的别名')
    关系 = models.CharField(max_length=10, default='新增', db_column='关系', verbose_name='新增/引用')
    级别 = models.CharField(max_length=50, null=True, blank=True, db_column='级别', verbose_name='主角/次主场景/关键道具等')
    摘要 = models.TextField(db_column='摘要', verbose_name='可拍细节摘要（外观/物件/状态）')
    排序 = models.IntegerField(default=0, db_column='排序', verbose_name='列表顺序')
    创建时间 = models.DateTimeField(db_column='创建时间', verbose_name='创建时间')
    更新时间 = models.DateTimeField(db_column='更新时间', verbose_name='最后更新时间')

    class Meta:
        db_table = '资产'
        verbose_name = '资产'
        verbose_name_plural = verbose_name
        ordering = ['集号', '排序', 'id']

    def __str__(self):
        return 'EP%s %s %s' % (self.集号, self.资产id, self.名称)
