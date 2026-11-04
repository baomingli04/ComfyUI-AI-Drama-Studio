# -*- coding: utf-8 -*-
"""人物表模型：对应 aicg.人物 表（/script/character 人物设定页数据骨架）。

一行 = 一个人物卡。人物设定线 22 个实体字段（2026-11-02 补列，见 docs/02-数据库文档.md 第 10 节）：
「可分段」字段存文本格式「第1-5集：…；第6集起：…」，与前端 人物工具.js 值文本()/文本转值() 互逆。
"""
from django.db import models


class 人物(models.Model):
    """人物卡：/script/character 角色卡视图与 /video/assets 人物分区共用一行。"""

    id = models.BigAutoField(primary_key=True, db_column='id', verbose_name='行主键')
    剧id = models.BigIntegerField(db_column='剧id', verbose_name='所属剧')
    人物id = models.CharField(max_length=32, db_column='人物id', verbose_name='业务编号 CHAR_xxx，剧内唯一')
    名 = models.CharField(max_length=50, db_column='名', verbose_name='人物名')
    别名 = models.JSONField(null=True, blank=True, db_column='别名', verbose_name='别名数组')
    性别 = models.CharField(max_length=10, default='男', db_column='性别', verbose_name='男/女')
    年龄档 = models.CharField(max_length=20, null=True, blank=True, db_column='年龄档', verbose_name='年龄档/年龄')
    外观全文 = models.TextField(null=True, blank=True, db_column='外观全文', verbose_name='可拍级外观描述（资产提取来源）')
    性格 = models.TextField(null=True, blank=True, db_column='性格', verbose_name='性格要点')
    关系 = models.TextField(null=True, blank=True, db_column='关系', verbose_name='本剧关系：主角/反派/核心成员…')
    # —— 2026-11-02 人物设定线 22 列 ——
    简介 = models.CharField(max_length=255, null=True, blank=True, db_column='简介', verbose_name='一句话简介')
    分组 = models.CharField(max_length=50, null=True, blank=True, db_column='分组', verbose_name='卡片分组')
    卡色 = models.CharField(max_length=10, null=True, blank=True, db_column='卡色', verbose_name='卡片配色')
    身份 = models.TextField(null=True, blank=True, db_column='身份', verbose_name='身份（可分段）')
    关系变化 = models.TextField(null=True, blank=True, db_column='关系变化', verbose_name='与主角关系随集变化（可分段）')
    态度 = models.TextField(null=True, blank=True, db_column='态度', verbose_name='立场态度（可分段）')
    外貌 = models.TextField(null=True, blank=True, db_column='外貌', verbose_name='外貌（可分段）')
    身材 = models.CharField(max_length=255, null=True, blank=True, db_column='身材', verbose_name='身材')
    穿搭 = models.TextField(null=True, blank=True, db_column='穿搭', verbose_name='穿搭（可分段）')
    身体情况 = models.TextField(null=True, blank=True, db_column='身体情况', verbose_name='身体情况（可分段）')
    情感情况 = models.TextField(null=True, blank=True, db_column='情感情况', verbose_name='情感情况（可分段）')
    精神情况 = models.TextField(null=True, blank=True, db_column='精神情况', verbose_name='精神情况（可分段）')
    当前状态 = models.TextField(null=True, blank=True, db_column='当前状态', verbose_name='当前状态（可分段）')
    当前姿势 = models.CharField(max_length=255, null=True, blank=True, db_column='当前姿势', verbose_name='当前姿势（可分段）')
    内心想法 = models.TextField(null=True, blank=True, db_column='内心想法', verbose_name='内心想法（可分段）')
    技能 = models.TextField(null=True, blank=True, db_column='技能', verbose_name='角色技能（可分段）')
    核心目标 = models.TextField(null=True, blank=True, db_column='核心目标', verbose_name='核心目标（可分段）')
    关系网 = models.TextField(null=True, blank=True, db_column='关系网', verbose_name='和谁是什么关系的概述')
    背景故事 = models.TextField(null=True, blank=True, db_column='背景故事', verbose_name='背景故事')
    台词风格 = models.CharField(max_length=255, null=True, blank=True, db_column='台词风格', verbose_name='台词风格')
    口头禅 = models.CharField(max_length=255, null=True, blank=True, db_column='口头禅', verbose_name='口头禅')
    概括 = models.CharField(max_length=500, null=True, blank=True, db_column='概括', verbose_name='人物概括（下游浓缩版）')
    音色提示词 = models.TextField(null=True, blank=True, db_column='音色提示词', verbose_name='音色提示词（C3 音色前置种子）')
    基础版本 = models.IntegerField(default=1, db_column='基础版本', verbose_name='C9 乐观锁版本号')
    创建时间 = models.DateTimeField(db_column='创建时间', verbose_name='创建时间')
    更新时间 = models.DateTimeField(db_column='更新时间', verbose_name='更新时间')

    class Meta:
        db_table = '人物'
        verbose_name = '人物'
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return self.名
