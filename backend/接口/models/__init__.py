# -*- coding: utf-8 -*-
"""模型包：集中导入全部模型，供 Django 加载。"""
from 接口.models.用户 import 用户
from 接口.models.模型配置 import 模型配置
from 接口.models.技能分类 import 技能分类
from 接口.models.技能 import 技能
from 接口.models.task import task
from 接口.models.提示词模板 import 提示词模板
from 接口.models.剧 import 剧
from 接口.models.标签 import 标签
from 接口.models.方案 import 方案

__all__ = ['用户', '模型配置', '技能分类', '技能', 'task', '提示词模板', '剧', '标签', '方案']
