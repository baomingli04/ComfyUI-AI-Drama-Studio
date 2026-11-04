# -*- coding: utf-8 -*-
"""参考图表模型：对应 aicg.参考图 表（美术定装的参考图，一图一行带标注）。

2026-11-02 新建：替代 美术定装 表原 json 参考图数组。
一个资产可有多张当前参考图（每张带各自标注），重新生成后旧图状态转 历史。
"""
from django.db import models


class 参考图(models.Model):
    """参考图行：定装的一张参考图（当前或历史）。"""

    id = models.BigAutoField(primary_key=True, db_column='id', verbose_name='行主键')
    资产行id = models.BigIntegerField(db_column='资产行id', verbose_name='所属 美术定装.id')
    url = models.CharField(max_length=512, db_column='url', verbose_name='图片相对路径，如 上传/xxx.png')
    标注 = models.CharField(max_length=200, null=True, blank=True, db_column='标注', verbose_name='图片标注，如 正面定装/侧面/Q版')
    提示词 = models.TextField(null=True, blank=True, db_column='提示词', verbose_name='这张图自己的出图/编辑提示词说明（T2 图片解析回写）')
    分类 = models.CharField(max_length=10, null=True, blank=True, db_column='分类', verbose_name='图片分类：人物/场景/道具/服装，默认继承父资产类型')
    形态 = models.CharField(max_length=50, null=True, blank=True, db_column='形态', verbose_name='形态标签：同一资产的不同服装/状态，如 常服/受伤')
    关联人物 = models.CharField(max_length=50, null=True, blank=True, db_column='关联人物', verbose_name='关联人物id：人物类型图关联到哪个角色档案（空=按资产id自动匹配）')
    来源 = models.CharField(max_length=10, default='生成', db_column='来源', verbose_name='生成/上传')
    状态 = models.CharField(max_length=10, default='当前', db_column='状态', verbose_name='当前/历史')
    排序 = models.IntegerField(default=0, db_column='排序', verbose_name='显示顺序')
    创建时间 = models.DateTimeField(db_column='创建时间', verbose_name='创建时间')
    更新时间 = models.DateTimeField(db_column='更新时间', verbose_name='最后更新时间')

    class Meta:
        db_table = '参考图'
        verbose_name = '参考图'
        verbose_name_plural = verbose_name
        ordering = ['排序', 'id']

    def __str__(self):
        return '图#%s %s' % (self.id, self.标注 or self.url)
