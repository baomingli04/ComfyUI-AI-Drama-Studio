# -*- coding: utf-8 -*-
"""人物关系表模型：对应 aicg.人物关系 表（/script/character 关系网视图数据骨架）。

一行 = 一条关系边（甲↔乙）。说明可存分段格式「第1-5集 协作（…）；第6集起 羁绊（…）」，
与前端 人物工具.js 的 关系一行()/解析关系阶段() 互逆。
2026-11-02 建，见 docs/02-数据库文档.md 第 10 节。
"""
from django.db import models


class 人物关系(models.Model):
    """关系网边：两端都是 人物.名，剧内成网。"""

    id = models.BigAutoField(primary_key=True, db_column='id', verbose_name='行主键')
    剧id = models.BigIntegerField(db_column='剧id', verbose_name='所属剧')
    边序 = models.IntegerField(null=True, blank=True, default=0, db_column='边序', verbose_name='展示顺序')
    甲 = models.CharField(max_length=50, db_column='甲', verbose_name='角色A名')
    乙 = models.CharField(max_length=50, db_column='乙', verbose_name='角色B名')
    类型 = models.CharField(max_length=20, null=True, blank=True, db_column='类型', verbose_name='羁绊/协作/认可/对立/利用/亲情')
    关键词 = models.CharField(max_length=255, null=True, blank=True, db_column='关键词', verbose_name='关键词，顿号分隔')
    说明 = models.TextField(null=True, blank=True, db_column='说明', verbose_name='关系说明（可分段）')
    创建时间 = models.DateTimeField(db_column='创建时间', verbose_name='创建时间')
    更新时间 = models.DateTimeField(db_column='更新时间', verbose_name='更新时间')

    class Meta:
        db_table = '人物关系'
        verbose_name = '人物关系'
        verbose_name_plural = verbose_name
        ordering = ['边序', 'id']

    def __str__(self):
        return self.甲 + ' ↔ ' + self.乙
