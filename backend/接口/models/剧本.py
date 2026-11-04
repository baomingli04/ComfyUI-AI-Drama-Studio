# -*- coding: utf-8 -*-
"""剧本表模型：对应 aicg.剧本 表（/script/episode 分集剧本页数据源）。

一行 = 某剧某一集某一版本类型的剧本行，唯一键 (剧id, 集号, 版本类型, 版本)。
2026-11-02 扩 7 个实体列（见 docs/02-数据库文档.md 第 12 节）：正文 + 5 档案块 + 状态。
档案块内存「键：值」行文本；场次不再走本表 `场次` json 列（已弃用不动），新数据走 `场次` 实体表。
"""
from django.db import models


class 剧本(models.Model):
    """每集剧本行：创作版/定稿版分离 + 版本链；定稿版是视频线的唯一事实源。"""

    id = models.BigAutoField(primary_key=True, db_column='id', verbose_name='行主键')
    剧id = models.BigIntegerField(db_column='剧id', verbose_name='所属剧')
    集号 = models.IntegerField(db_column='集号', verbose_name='集号')
    版本类型 = models.CharField(max_length=10, default='创作版', db_column='版本类型', verbose_name='创作版/定稿版')
    版本 = models.IntegerField(default=1, db_column='版本', verbose_name='同版本类型内的版本号')
    标题 = models.CharField(max_length=100, null=True, blank=True, db_column='标题', verbose_name='集标题')
    总字数 = models.IntegerField(default=0, db_column='总字数', verbose_name='总字数；定稿前校验单集 800~5000 字')
    # —— 2026-11-02 分集剧本线 7 列 ——
    正文 = models.TextField(null=True, blank=True, db_column='正文', verbose_name='本集正文全文，按场次排，换行分段')
    能力档案 = models.TextField(null=True, blank=True, db_column='能力档案', verbose_name='键值行文本：所属势力…目前目标 10 键')
    世界状态 = models.TextField(null=True, blank=True, db_column='世界状态', verbose_name='键值行文本：当前世界…附近动向 11 键')
    关系网络 = models.TextField(null=True, blank=True, db_column='关系网络', verbose_name='键值行文本：当前主线/预告1/预告2/蝴蝶效应/历史进程/角色记录')
    记忆回廊 = models.TextField(null=True, blank=True, db_column='记忆回廊', verbose_name='键值行文本：长期记忆+短期记忆1-6')
    行动推荐 = models.TextField(null=True, blank=True, db_column='行动推荐', verbose_name='行文本，每行 N. 内容')
    状态 = models.CharField(max_length=16, default='待复核', db_column='状态', verbose_name='待复核/已复核（页面复核语义）')
    # 既有列沿用原用途
    场次 = models.TextField(db_column='场次', verbose_name='【已弃用】场次数组JSON，新数据走 场次 实体表')
    定稿 = models.BooleanField(default=False, db_column='定稿', verbose_name='【C1】1=已定稿锁定')
    定稿时间 = models.DateTimeField(null=True, blank=True, db_column='定稿时间', verbose_name='定稿时间')
    创建时间 = models.DateTimeField(db_column='创建时间', verbose_name='创建时间')
    更新时间 = models.DateTimeField(db_column='更新时间', verbose_name='最后更新时间')

    class Meta:
        db_table = '剧本'
        verbose_name = '剧本'
        verbose_name_plural = verbose_name
        ordering = ['集号', '版本类型', '版本']

    def __str__(self):
        return 'EP%s %s v%s' % (self.集号, self.版本类型, self.版本)
