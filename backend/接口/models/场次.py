# -*- coding: utf-8 -*-
"""场次表模型：对应 aicg.场次 表（/script/episode 每集剧本下的场次与正文）。

docs/02-数据库文档.md 7.5 定稿实体表的落地（建 剧本 表时被 场次 json 列顶替，
2026-11-02 按用户"实体化"要求纠正）。一行 = 一集剧本里的一场。
"""
from django.db import models


class 场次(models.Model):
    """场次：挂剧本行（某剧某集创作版），场号+地点+人物+道具+正文行。"""

    id = models.BigAutoField(primary_key=True, db_column='id', verbose_name='行主键')
    剧id = models.BigIntegerField(db_column='剧id', verbose_name='所属剧')
    剧本行id = models.BigIntegerField(db_column='剧本行id', verbose_name='所属剧本行（某剧某集创作版）')
    场号 = models.CharField(max_length=16, db_column='场号', verbose_name='场次编号，如 1-1')
    地点 = models.CharField(max_length=100, null=True, blank=True, db_column='地点', verbose_name='内/外 · 地点 · 时间')
    人物 = models.CharField(max_length=200, null=True, blank=True, db_column='人物', verbose_name='出场人物，顿号分隔')
    道具 = models.CharField(max_length=200, null=True, blank=True, db_column='道具', verbose_name='出场道具，顿号分隔')
    正文 = models.TextField(null=True, blank=True, db_column='正文', verbose_name='本场正文，一行一个动作/台词，换行分隔')
    排序 = models.IntegerField(default=0, db_column='排序', verbose_name='场次顺序，数字越小越靠前')
    创建时间 = models.DateTimeField(db_column='创建时间', verbose_name='创建时间')
    更新时间 = models.DateTimeField(db_column='更新时间', verbose_name='最后更新时间')

    class Meta:
        db_table = '场次'
        verbose_name = '场次'
        verbose_name_plural = verbose_name
        ordering = ['剧本行id', '排序', 'id']

    def __str__(self):
        return '%s %s' % (self.场号, self.地点 or '')
