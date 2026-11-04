# -*- coding: utf-8 -*-
"""分镜视频模型：对应 aicg.分镜视频 表（单镜生成页的历史版本记录）。

一行 = 某镜的一次成功生成产物。挂业务键 (剧id, 集号, 镜号)——分镜保存是全量替换
（行 id 会变），不能挂分镜行主键。一镜多版，选中=1 的那版进成片合成。
"""
from django.db import models


class 分镜视频(models.Model):
    """分镜视频版本行：一次成功生成的视频产物。"""

    id = models.BigAutoField(primary_key=True, db_column='id', verbose_name='行主键')
    剧id = models.BigIntegerField(db_column='剧id', verbose_name='所属剧')
    集号 = models.IntegerField(db_column='集号', verbose_name='集号')
    镜号 = models.CharField(max_length=20, db_column='镜号', verbose_name='镜号，如 SH001')
    方式 = models.CharField(max_length=50, null=True, blank=True, db_column='方式', verbose_name='生成方式：导演台全能·i2v/参考生视频/多参考生视频/二采重绘')
    提示词 = models.TextField(null=True, blank=True, db_column='提示词', verbose_name='本次生成的正向提示词')
    任务id = models.BigIntegerField(null=True, blank=True, db_column='任务id', verbose_name='来源任务 id（任务表）')
    url = models.CharField(max_length=512, null=True, blank=True, db_column='url', verbose_name='视频相对路径')
    状态 = models.CharField(max_length=16, default='已生成', db_column='状态', verbose_name='已生成/失败')
    选中 = models.BooleanField(default=False, db_column='选中', verbose_name='1=该镜当前选用这版（成片取这版）')
    创建时间 = models.DateTimeField(db_column='创建时间', verbose_name='创建时间')
    更新时间 = models.DateTimeField(db_column='更新时间', verbose_name='最后更新时间')

    class Meta:
        db_table = '分镜视频'
        verbose_name = '分镜视频'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self):
        return 'EP%s %s 版#%s' % (self.集号, self.镜号, self.id)
