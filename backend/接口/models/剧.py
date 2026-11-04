# -*- coding: utf-8 -*-
"""剧表模型：对应 aicg.剧 表（/script 与 /video 两大模块共同的数据骨架）。"""
from django.db import models


class 剧(models.Model):
    """短剧立项记录：P0 立项写入，方案/剧本/分镜/成片全链引用它。"""

    id = models.BigAutoField(primary_key=True, db_column='id', verbose_name='主键')
    用户id = models.BigIntegerField(db_column='用户id', verbose_name='归属用户（列表按此隔离）')
    剧名 = models.CharField(max_length=100, unique=True, db_column='剧名', verbose_name='剧名，全局唯一')
    集数 = models.IntegerField(db_column='集数', verbose_name='总集数 2~100')
    题材 = models.CharField(max_length=50, db_column='题材', verbose_name='题材')
    创意 = models.TextField(db_column='创意', verbose_name='一句创意（方案生成的种子）')
    起点方式 = models.CharField(max_length=20, default='原创', db_column='起点方式', verbose_name='原创/模板/灵感启发')
    封面图片 = models.CharField(max_length=512, null=True, blank=True, db_column='封面图片', verbose_name='封面图相对路径；空=占位图')
    保存地址 = models.CharField(max_length=512, null=True, blank=True, db_column='保存地址', verbose_name='工程/产物保存目录')
    状态 = models.CharField(max_length=20, default='草稿', db_column='状态', verbose_name='草稿/创作中/已完成')
    创作进度 = models.SmallIntegerField(default=0, db_column='创作进度', verbose_name='创作线进度 0~100')
    视频进度 = models.SmallIntegerField(default=0, db_column='视频进度', verbose_name='视频线进度 0~100')
    创建时间 = models.DateTimeField(db_column='创建时间', verbose_name='创建时间')
    更新时间 = models.DateTimeField(db_column='更新时间', verbose_name='更新时间')

    class Meta:
        db_table = '剧'
        verbose_name = '剧'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.剧名
