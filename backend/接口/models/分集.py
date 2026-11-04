# -*- coding: utf-8 -*-
"""分集表模型：对应 aicg.分集 表（/script/outline 分集目录页数据骨架）。

一行 = 一集的目录卡。2026-11-02 扩 10 个实体列（见 docs/02-数据库文档.md 第 11 节）：
多值字段按 02 文档第 7 节纪律用分隔文本存——出场=顿号分隔人名，
点位=换行分隔、每行「类型｜点｜内容」，不存 JSON、不建子表。
"""
from django.db import models


class 分集(models.Model):
    """分集目录卡：/script/outline 逐集卡与节奏体检共用一行。"""

    id = models.BigAutoField(primary_key=True, db_column='id', verbose_name='行主键')
    剧id = models.BigIntegerField(db_column='剧id', verbose_name='所属剧')
    集号 = models.IntegerField(db_column='集号', verbose_name='集号，剧内连续唯一')
    标题 = models.CharField(max_length=100, null=True, blank=True, db_column='标题', verbose_name='集标题')
    梗概 = models.CharField(max_length=500, db_column='梗概', verbose_name='本集梗概')
    钩子 = models.CharField(max_length=500, null=True, blank=True, db_column='钩子', verbose_name='开篇钩子')
    状态 = models.CharField(max_length=10, default='待创作', db_column='状态', verbose_name='待创作/进行中/已完成')
    # —— 2026-11-02 分集目录线 10 列 ——
    幕 = models.CharField(max_length=50, null=True, blank=True, db_column='幕', verbose_name='所属幕')
    关键 = models.BooleanField(default=False, db_column='关键', verbose_name='关键集标记')
    卡点 = models.BooleanField(default=False, db_column='卡点', verbose_name='付费卡点集标记')
    情绪分 = models.IntegerField(null=True, blank=True, db_column='情绪分', verbose_name='情绪强度1-5')
    字数 = models.IntegerField(default=0, db_column='字数', verbose_name='本集预估/实际字数')
    目标 = models.IntegerField(default=3000, db_column='目标', verbose_name='目标字数')
    尾钩 = models.CharField(max_length=500, null=True, blank=True, db_column='尾钩', verbose_name='本集结尾钩子')
    中心句 = models.CharField(max_length=255, null=True, blank=True, db_column='中心句', verbose_name='本集中心句')
    出场 = models.TextField(null=True, blank=True, db_column='出场', verbose_name='出场人物，顿号分隔')
    点位 = models.TextField(null=True, blank=True, db_column='点位', verbose_name='钩子点位，换行分隔，每行 类型|点|内容')
    创建时间 = models.DateTimeField(db_column='创建时间', verbose_name='创建时间')
    更新时间 = models.DateTimeField(db_column='更新时间', verbose_name='最后更新时间')

    class Meta:
        db_table = '分集'
        verbose_name = '分集'
        verbose_name_plural = verbose_name
        ordering = ['集号']

    def __str__(self):
        return 'EP%s %s' % (self.集号, self.标题 or '')
