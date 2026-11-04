# -*- coding: utf-8 -*-
"""接口 app 路由：一条路由一个函数。"""
from django.urls import path

from 接口.controllers.登录 import 登录
from 接口.controllers.当前用户 import 当前用户
from 接口.controllers.模型配置查询 import 模型配置查询
from 接口.controllers.模型配置保存 import 模型配置保存
from 接口.controllers.技能分类列表 import 技能分类列表
from 接口.controllers.技能分类新增 import 技能分类新增, 技能分类删除
from 接口.controllers.技能列表 import 技能列表
from 接口.controllers.任务提交 import 任务提交
from 接口.controllers.任务列表 import 任务列表
from 接口.controllers.任务取消 import 任务取消
from 接口.controllers.任务删除 import 任务删除
from 接口.controllers.任务日志 import 任务日志
from 接口.controllers.上传 import 上传
from 接口.controllers.技能上传 import 技能上传, 技能修改
from 接口.controllers.技能删除 import 技能删除
from 接口.controllers.工作流列表 import 工作流列表
from 接口.controllers.工作流下载 import 工作流下载
from 接口.controllers.工作流上传 import 工作流上传
from 接口.controllers.媒体文件 import 媒体文件
from 接口.controllers.提示词技能列表 import 提示词技能列表
from 接口.controllers.提示词扩写 import 提示词扩写
from 接口.controllers.提示词配置查询 import 提示词配置查询
from 接口.controllers.提示词配置保存 import 提示词配置保存
from 接口.controllers.提示词资源库列表 import 提示词资源库列表
from 接口.controllers.提示词资源库详情 import 提示词资源库详情
from 接口.controllers.音频提取 import 音频提取
from 接口.controllers.音频合成 import 音频合成
from 接口.controllers.音频信息 import 音频信息
from 接口.controllers.剧列表 import 剧列表
from 接口.controllers.剧新增 import 剧新增
from 接口.controllers.剧删除 import 剧删除, 剧修改
from 接口.controllers.剧详情 import 剧详情
from 接口.controllers.标签列表 import 标签列表
from 接口.controllers.标签新增 import 标签新增
from 接口.controllers.方案列表 import 方案列表
from 接口.controllers.方案保存 import 方案保存
from 接口.controllers.方案分区 import 方案分区
from 接口.controllers.方案分区保存 import 方案分区保存
from 接口.controllers.人物列表 import 人物列表
from 接口.controllers.人物保存 import 人物保存
from 接口.controllers.人物关系保存 import 人物关系保存
from 接口.controllers.分集列表 import 分集列表
from 接口.controllers.分集保存 import 分集保存
from 接口.controllers.剧本列表 import 剧本列表
from 接口.controllers.剧本保存 import 剧本保存
from 接口.controllers.视频剧列表 import 视频剧列表
from 接口.controllers.分镜列表 import 分镜列表
from 接口.controllers.分镜保存 import 分镜保存
from 接口.controllers.分镜视频保存 import 分镜视频接口
from 接口.controllers.分镜图保存 import 分镜图接口
from 接口.controllers.成片合成 import 成片合成接口
from 接口.controllers.资产列表 import 资产列表
from 接口.controllers.资产全部 import 资产全部
from 接口.controllers.资产保存 import 资产保存
from 接口.controllers.美术列表 import 美术列表
from 接口.controllers.美术初始化 import 美术初始化
from 接口.controllers.美术保存 import 美术保存
from 接口.controllers.美术新增 import 美术新增
from 接口.controllers.参考图保存 import 参考图保存

urlpatterns = [
    path('api/登录', 登录),
    path('api/当前用户', 当前用户),
    path('api/模型配置', 模型配置查询),
    path('api/模型配置/保存', 模型配置保存),
    path('api/技能分类', 技能分类列表),
    path('api/技能分类/新增', 技能分类新增),
    path('api/技能分类/删除', 技能分类删除),
    path('api/技能', 技能列表),
    path('api/技能/上传', 技能上传),
    path('api/技能/修改', 技能修改),
    path('api/技能/删除', 技能删除),
    path('api/任务/提交', 任务提交),
    path('api/任务列表', 任务列表),
    path('api/任务/取消', 任务取消),
    path('api/任务/删除', 任务删除),
    path('api/任务/日志', 任务日志),
    path('api/上传', 上传),
    path('api/工作流列表', 工作流列表),
    path('api/工作流/下载', 工作流下载),
    path('api/工作流/上传', 工作流上传),
    path('api/媒体/<path:相对路径>', 媒体文件),
    path('api/提示词/技能列表', 提示词技能列表),
    path('api/提示词/扩写', 提示词扩写),
    path('api/提示词/配置', 提示词配置查询),
    path('api/提示词/配置/保存', 提示词配置保存),
    path('api/提示词资源库/列表', 提示词资源库列表),
    path('api/提示词资源库/详情', 提示词资源库详情),
    path('api/音频/提取', 音频提取),
    path('api/音频/合成', 音频合成),
    path('api/音频/信息', 音频信息),
    path('api/剧列表', 剧列表),
    path('api/剧/详情', 剧详情),
    path('api/剧/新增', 剧新增),
    path('api/剧/修改', 剧修改),
    path('api/剧/删除', 剧删除),
    path('api/标签', 标签列表),
    path('api/标签/新增', 标签新增),
    path('api/方案列表', 方案列表),
    path('api/方案/保存', 方案保存),
    path('api/方案/分区', 方案分区),
    path('api/方案/分区保存', 方案分区保存),
    path('api/人物/列表', 人物列表),
    path('api/人物/保存', 人物保存),
    path('api/人物/关系保存', 人物关系保存),
    path('api/分集/列表', 分集列表),
    path('api/分集/保存', 分集保存),
    path('api/剧本/列表', 剧本列表),
    path('api/剧本/保存', 剧本保存),
    path('api/视频/剧列表', 视频剧列表),
    path('api/分镜/列表', 分镜列表),
    path('api/分镜/保存', 分镜保存),
    path('api/分镜/视频', 分镜视频接口),
    path('api/分镜/视频保存', 分镜视频接口),
    path('api/分镜/图', 分镜图接口),
    path('api/分镜/图保存', 分镜图接口),
    path('api/成片/列表', 成片合成接口),
    path('api/成片/合成', 成片合成接口),
    path('api/资产/列表', 资产列表),
    path('api/资产/全部', 资产全部),
    path('api/资产/保存', 资产保存),
    path('api/美术/列表', 美术列表),
    path('api/美术/初始化', 美术初始化),
    path('api/美术/保存', 美术保存),
    path('api/美术/新增', 美术新增),
    path('api/美术/参考图保存', 参考图保存),
]
