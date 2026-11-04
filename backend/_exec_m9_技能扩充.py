# -*- coding: utf-8 -*-
"""批量登记技能（M9，幂等）：磁盘既有包 + 新下载的 MiniMax 系，凑满 30 个。
分类归属：写作技能=小说创作类；剧本创作=剧本改编类；分镜技能=分镜类；minimax=MiniMax 模型能力类。
跳过：小黄文（内容不合适）、video-prompt-studio-v2（骨架未完成）。
"""
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '后端.settings')
django.setup()

from django.conf import settings  # noqa: E402
from django.utils import timezone  # noqa: E402
from 接口.models.技能分类 import 技能分类  # noqa: E402
from 接口.models.技能 import 技能  # noqa: E402

# (目录名, 名称, 分类名, 简介)
清单 = [
    # ---- 写作技能（11）----
    ('g113593__skillhub', '番茄小说章节助手', '写作技能',
     '番茄小说平台优化的分章节创作：10-50 章长篇、每章 2200-2800 字、结尾悬念钩子、爆点分布、去 AI 痕迹润色。'),
    ('oh-story-claudecode/story-long-write', '长篇故事写作', '写作技能',
     '长篇故事系统化写作（story-long-write），附 references 参考文档。'),
    ('novel-writer-cn__skillhub', '小说框架生成器', '写作技能',
     '创建小说创作框架：人物设定、人物关系、剧情发展、多版本结局。'),
    ('novelist__skillhub', '小说创作引导', '写作技能',
     '从主线/梗概引导完成整本小说：收集创作信息→确认章节大纲→逐章写作，每章前确认走向。'),
    ('novel-writing-assistant__skillhub', '小说结构化助手', '写作技能',
     '面向写作新手的长篇小说系统化创作指导：结构化写作辅助。'),
    ('novel-writing-new__skillhub', '小说写作全流程 v6', '写作技能',
     '12 层技能体系（L0 心法→L11 融合实战）、104+ 参考文档、三级标星系统。'),
    ('novel-writing-skill', '英文小说全流程', '写作技能',
     'AI-assisted novel writing：项目管理、世界观、人物、情节控制、卷章大纲（英文）。'),
    ('fiction-crafter__skillhub', '爽文创作工坊', '写作技能',
     '自动生成提示词并创作长篇爽文：维护角色/地点/情节连续性，支持都市/修仙/玄幻/重生/系统流。'),
    ('novel-continuity-fix__skillhub', '章节衔接检查', '写作技能',
     '小说章节衔接问题检查与修正：前后文矛盾、设定漂移、时间线错乱。'),
    ('novel-evaluator__skillhub', '小说六维评分', '写作技能',
     '六维度（情节/人物/文笔/世界观/情感/创新）量化评分并给专业反馈。'),
    ('novel-inspiration-generator__skillhub', '灵感脑洞生成器', '写作技能',
     '小说创意/灵感/角色设定/世界观脑洞；爽文开头（扮猪吃虎/重生复仇/系统流/退婚打脸）与黄金三章、对标拆解；内置敏感词过滤。'),
    # ---- 剧本创作（2）----
    ('novel-script-adapter__skillhub', '短剧剧本创作Pro', '剧本创作',
     '三模式：忠实改编/优化改编/原创短剧；3 秒钩子+名场面+悬念三段式；输出分集剧本与 AI 漫剧分镜提示词（即梦/可灵可用）。'),
    ('novel-to-skitscreenplay__skillhub', '小说转漫剧剧本', '剧本创作',
     '长篇小说转漫剧视频规范剧本：3 秒入戏、每分钟 3 冲突、连续反转节奏。'),
    # ---- 分镜技能（1）----
    ('dashboard-analytics-skill__skillhub', '网文转豆包分镜', '分镜技能',
     '中文小说/网文段落转豆包视频分镜提示词表；默认网文短视频风（短促/特写/密集爽点），可切电影感。'),
    # ---- minimax（5）----
    ('MiniMaxTTS', 'MiniMax 语音合成', 'minimax',
     'MiniMax Voice API 文本转语音：多音色、有声书/播客、声音克隆（10s~5min 样本）、音色设计、音频后处理。'),
    ('MiniMaxMusicMaker', 'MiniMax 音乐生成', 'minimax',
     'MiniMax Music API 作曲：带歌词歌曲/纯音乐/哼唱旋律，结构化提示词，交互式细粒度控制。'),
    ('MiniMaxVideoMaker', 'MiniMax 视频生成', 'minimax',
     'Hailuo-2.3/02/S2V-01 视频生成：文生视频/图生视频/首尾帧/主体参考（人脸一致性），多风格，BGM 挂载，30s+ 长视频场景链。'),
    ('MiniMax-Multimodal-Toolkit', 'MiniMax 多模态工具箱', 'minimax',
     '语音+音乐+视频三合一：TTS/克隆/音色设计、歌曲/纯音乐、T2V/I2V/模板/长片多场景、媒体格式转换拼接裁剪。'),
    ('minimax-mmx-cli', 'MiniMax 官方 CLI 技能', 'minimax',
     'MiniMax 官方 mmx-cli：文本(M3)/图片(image-01)/视频(Hailuo-2.3)/语音(speech-2.8-hd, 300+音色)/音乐(music-2.6)/联网搜索。'),
]

分类缓存 = {}
ok = 跳过 = 0
for 目录名, 名称, 分类名, 简介 in 清单:
    if 分类名 not in 分类缓存:
        分类缓存[分类名] = 技能分类.objects.filter(名称=分类名).first()
    分类 = 分类缓存[分类名]
    if 分类 is None:
        print('缺分类，跳过:', 分类名)
        跳过 += 1
        continue
    if not (settings.SKILL_DIR / 目录名 / 'SKILL.md').is_file():
        print('缺 SKILL.md，跳过:', 目录名)
        跳过 += 1
        continue
    行 = 技能.objects.filter(目录名=目录名).first()
    if 行 is not None:
        print('已存在:', 行.名称)
        continue
    now = timezone.now()
    技能.objects.create(目录名=目录名, 名称=名称, 简介=简介, 分类id=分类,
                        来源='内置登记', 创建时间=now, 更新时间=now)
    print('已登记:', 名称, '->', 分类名)
    ok += 1

print('---- 新登记', ok, '个，跳过', 跳过, '个 ----')
按分类 = {}
for s in 技能.objects.select_related('分类id').all():
    按分类.setdefault(s.分类id.名称, []).append(s.名称)
total = 0
for c, 名单 in sorted(按分类.items(), key=lambda x: -len(x[1])):
    total += len(名单)
    print(c, len(名单), '个')
print('全站总数:', total)
