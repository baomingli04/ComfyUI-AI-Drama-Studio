# -*- coding: utf-8 -*-
"""分镜图模型：对应 aicg.分镜图 表（单镜页的每镜独立创作资源区）。

一行 = 某镜专属的一张参考图（上传/AI 生成）。资产图（美术定装参考图）只引用不落这里，
挂业务键 (剧id, 集号, 镜号)，归属走 剧.用户id 校验。
"""
from django.db import models


class 分镜图(models.Model):
    """分镜专属参考图行。"""

    id = models.BigAutoField(primary_key=True, db_column='id', verbose_name='行主键')
    剧id = models.BigIntegerField(db_column='剧id', verbose_name='所属剧')
    集号 = models.IntegerField(db_column='集号', verbose_name='集号')
    镜号 = models.CharField(max_length=20, db_column='镜号', verbose_name='镜号，如 SH001')
    url = models.CharField(max_length=512, db_column='url', verbose_name='图片相对路径，如 上传/xxx.png')
    标注 = models.CharField(max_length=200, null=True, blank=True, db_column='标注', verbose_name='标注，如 首帧/李宝明参考')
    来源 = models.CharField(max_length=10, default='上传', db_column='来源', verbose_name='上传/资产/生成')
    提示词 = models.TextField(null=True, blank=True, db_column='提示词', verbose_name='本图生成提示词（来源=生成时）')
    排序 = models.IntegerField(default=0, db_column='排序', verbose_name='显示顺序')
    创建时间 = models.DateTimeField(db_column='创建时间', verbose_name='创建时间')
    更新时间 = models.DateTimeField(db_column='更新时间', verbose_name='最后更新时间')

    class Meta:
        db_table = '分镜图'
        verbose_name = '分镜图'
        verbose_name_plural = verbose_name
        ordering = ['排序', 'id']

    def __str__(self):
        return 'EP%s %s 图#%s' % (self.集号, self.镜号, self.id)
