# -*- coding: utf-8 -*-
"""分镜表模型：对应 aicg.分镜 表（/video/shot 拆分分镜页数据源）。

一行 = 某剧某一集的一个镜头，按 排序 升序展示；唯一业务键 (剧id, 集号, 镜号)。
2026-11-02 新建（见 docs/02-数据库文档.md 第 13 节）：视频线分镜正文，全部实体列。
"""
from django.db import models


class 分镜(models.Model):
    """镜头级分镜行：由本集剧本拆分而来，单镜可编辑、可按技能重新生成。"""

    id = models.BigAutoField(primary_key=True, db_column='id', verbose_name='行主键')
    剧id = models.BigIntegerField(db_column='剧id', verbose_name='所属剧')
    集号 = models.IntegerField(db_column='集号', verbose_name='集号')
    镜号 = models.CharField(max_length=20, db_column='镜号', verbose_name='镜号，如 SH001')
    场次 = models.CharField(max_length=100, db_column='场次', verbose_name='所属场次，如 场次 1 · 教室')
    景别 = models.CharField(max_length=20, null=True, blank=True, db_column='景别', verbose_name='特写/近景/中景/全景等')
    运镜 = models.CharField(max_length=50, null=True, blank=True, db_column='运镜', verbose_name='固定/缓推/横移/跟拍等')
    画面 = models.TextField(db_column='画面', verbose_name='画面描述：主体动作与可拍细节')
    台词 = models.TextField(null=True, blank=True, db_column='台词', verbose_name='本镜台词，无台词留空')
    时长 = models.CharField(max_length=16, null=True, blank=True, db_column='时长', verbose_name='单镜时长，如 3s')
    首帧url = models.CharField(max_length=512, null=True, blank=True, db_column='首帧url', verbose_name='首帧参考图（视频生成线预留）')
    尾帧url = models.CharField(max_length=512, null=True, blank=True, db_column='尾帧url', verbose_name='尾帧参考图（视频生成线预留）')
    视频状态 = models.CharField(max_length=16, default='待生成', db_column='视频状态', verbose_name='待生成/生成中/已生成')
    生成方式 = models.CharField(max_length=50, null=True, blank=True, db_column='生成方式', verbose_name='本镜选用的生成方式（单镜页四方式卡）')
    生成提示词 = models.TextField(null=True, blank=True, db_column='生成提示词', verbose_name='本镜出视频的正向提示词（单镜页生成用）')
    排序 = models.IntegerField(default=0, db_column='排序', verbose_name='镜头顺序')
    创建时间 = models.DateTimeField(db_column='创建时间', verbose_name='创建时间')
    更新时间 = models.DateTimeField(db_column='更新时间', verbose_name='最后更新时间')

    class Meta:
        db_table = '分镜'
        verbose_name = '分镜'
        verbose_name_plural = verbose_name
        ordering = ['集号', '排序', 'id']

    def __str__(self):
        return 'EP%s %s' % (self.集号, self.镜号)
