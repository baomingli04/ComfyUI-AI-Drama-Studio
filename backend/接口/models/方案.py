# -*- coding: utf-8 -*-
"""方案表模型：对应 aicg.方案 表（/script/plan 创作方案页的数据骨架）。

一行 = 一个候选方案（版本号 方案一/方案二…）；同剧仅一行 是否选定=1。
候选卡 = /script/plan 方案卡的七个字段（JSON）；
时空背景/故事线/爽点矩阵/商业卖点/结局设计 五个 JSON 列由 /script/detail 方案详情页填充。
"""
from django.db import models


class 方案(models.Model):
    """创作方案候选行：方案卡（候选卡）与方案详情（五分区）共用一行。"""

    id = models.BigAutoField(primary_key=True, db_column='id', verbose_name='方案主键')
    剧id = models.BigIntegerField(db_column='剧id', verbose_name='所属剧；一剧多候选方案')
    版本号 = models.CharField(max_length=50, default='方案一', db_column='版本号', verbose_name='方案版本名，如 方案一/方案二')
    是否选定 = models.BooleanField(default=False, db_column='是否选定', verbose_name='1=当前选定方案；同剧仅一行=1')
    # /script/plan 方案卡七字段：{标题,故事线,题材,基调,结局,驱动,风险}（2026-10-29 补列，见 表结构.sql）
    候选卡 = models.JSONField(null=True, blank=True, db_column='候选卡', verbose_name='方案卡七字段 JSON')
    时空背景 = models.JSONField(null=True, blank=True, db_column='时空背景', verbose_name='五分区之一')
    故事线 = models.JSONField(null=True, blank=True, db_column='故事线', verbose_name='五分区之二')
    爽点矩阵 = models.JSONField(null=True, blank=True, db_column='爽点矩阵', verbose_name='五分区之三')
    商业卖点 = models.JSONField(null=True, blank=True, db_column='商业卖点', verbose_name='五分区之四')
    结局设计 = models.JSONField(null=True, blank=True, db_column='结局设计', verbose_name='五分区之五')
    基础版本 = models.IntegerField(default=1, db_column='基础版本', verbose_name='C9 乐观锁版本号')
    创建时间 = models.DateTimeField(db_column='创建时间', verbose_name='创建时间')
    更新时间 = models.DateTimeField(db_column='更新时间', verbose_name='更新时间')

    class Meta:
        db_table = '方案'
        verbose_name = '方案'
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return self.版本号
