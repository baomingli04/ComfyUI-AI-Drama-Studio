# -*- coding: utf-8 -*-
"""美术定装表模型：对应 aicg.美术定装 表（/video/art 美术资产页数据源）。

一行 = 一条资产行的美术设定（出图提示词/必须保持/禁止出现/生图状态/音色）。
2026-11-02 重构：去掉 6 个 json 列（参考图/历史/保持/禁止的手改分层）与乐观锁，
参考图拆独立表 参考图（一图一行带标注）；必须保持/禁止出现 用换行分隔文本列。
见 docs/02-数据库文档.md 第 14 节。
"""
from django.db import models


class 美术定装(models.Model):
    """美术定装行：一资产的视觉/听觉设定。"""

    id = models.BigAutoField(primary_key=True, db_column='id', verbose_name='行主键')
    资产行id = models.BigIntegerField(db_column='资产行id', verbose_name='所属 资产.id（一资产一定装行）')
    全局风格 = models.CharField(max_length=100, null=True, blank=True, db_column='全局风格', verbose_name='提取风格，如 校园青春日系胶片风')
    画幅 = models.CharField(max_length=20, default='9:16', db_column='画幅', verbose_name='画幅，默认 9:16 竖屏')
    分辨率 = models.CharField(max_length=20, default='480p', db_column='分辨率', verbose_name='参考图分辨率档')
    生图提示词 = models.TextField(null=True, blank=True, db_column='生图提示词', verbose_name='出图正向提示词（编辑提示词的载体）')
    必须保持 = models.TextField(null=True, blank=True, db_column='必须保持', verbose_name='必须保持的视觉特征，多条换行分隔')
    禁止出现 = models.TextField(null=True, blank=True, db_column='禁止出现', verbose_name='禁止出现的元素，多条换行分隔')
    生图状态 = models.CharField(max_length=10, default='待生成', db_column='生图状态', verbose_name='待生成/生成中/已生成')
    音色提示词 = models.TextField(null=True, blank=True, db_column='音色提示词', verbose_name='人物音色提示词（仅人物资产有值）')
    音色名 = models.CharField(max_length=100, null=True, blank=True, db_column='音色名', verbose_name='选中的音色库名（如 沈砚）')
    音色url = models.CharField(max_length=512, null=True, blank=True, db_column='音色url', verbose_name='已合成音色文件相对路径')
    音色模型 = models.CharField(max_length=100, null=True, blank=True, db_column='音色模型', verbose_name='TTS 模型名')
    音色积分 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_column='音色积分', verbose_name='本次音色合成消耗积分')
    音色状态 = models.CharField(max_length=10, default='待生成', db_column='音色状态', verbose_name='待生成/生成中/已生成')
    创建时间 = models.DateTimeField(db_column='创建时间', verbose_name='创建时间')
    更新时间 = models.DateTimeField(db_column='更新时间', verbose_name='最后更新时间')

    class Meta:
        db_table = '美术定装'
        verbose_name = '美术定装'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '定装#%s 资产行%s' % (self.id, self.资产行id)
