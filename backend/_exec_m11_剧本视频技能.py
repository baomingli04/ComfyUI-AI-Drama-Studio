# -*- coding: utf-8 -*-
# M11：剧本创作 +5、视频生成 +2（幂等，登记前校验 SKILL.md 存在）
import os
from datetime import datetime

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '后端.settings')
django.setup()

from django.conf import settings
from 接口.models.技能分类 import 技能分类
from 接口.models.技能 import 技能

# (目录名, 展示名, 分类名, 简介供前端显示)
新技能 = [
    ('zenstory-short-drama-write', '短剧单集剧本写作', '剧本创作',
     'zenstory（3.3k star）：编写/修订可拍摄的单集 Markdown 剧本，去模板感、去 AI 味润色、续写下一集'),
    ('zenstory-short-drama-novel-analyze', '短剧原著小说解析', '剧本创作',
     'zenstory：把长篇小说/网文拆成可追溯的原著分析（章节索引、改编价值、剧情单元、人物归并、改编路线）'),
    ('zenstory-short-drama-review', '短剧剧本审校', '剧本创作',
     'zenstory：按项目流水线审查剧本/资产/分镜/提示词，出结构化审稿意见'),
    ('drama-creator-emotion-spring', '情绪弹簧短剧创作', '剧本创作',
     '情绪弹簧理论：每集必须「压弹簧或放弹簧」，钩子-反转-再钩单集闭环，情绪K线节奏控制'),
    ('drama-planner-emotion-spring', '短剧策划方案', '剧本创作',
     '情绪价值分析、黄金三秒钩子、三幕结构规划等短剧项目前期策划与商业方案'),
    ('zenstory-short-drama-video-prompts', '短剧视频提示词', '视频生成',
     'zenstory：把分镜和冻结关键帧写成可直接复制的视频提示词（文生/图生视频动作、运镜、口型、镜头时长、起止状态）+ 时间线配乐意图'),
    ('zenstory-short-drama-produce', '短剧出片生产流程', '视频生成',
     'zenstory：短剧项目图片/视频/TTS配音/时间线音乐的生产调度与运行记录规范'),
]

分类缓存 = {}
for 目录, 名称, 分类名, 简介 in 新技能:
    if 分类名 not in 分类缓存:
        分类缓存[分类名] = 技能分类.objects.get(名称=分类名)
    if not (settings.SKILL_DIR / 目录 / 'SKILL.md').is_file():
        print('跳过（缺 SKILL.md）:', 目录)
        continue
    行, 建 = 技能.objects.get_or_create(
        目录名=目录,
        defaults={'名称': 名称, '分类id': 分类缓存[分类名], '简介': 简介, '来源': '内置登记',
                  '创建时间': datetime.now(), '更新时间': datetime.now()},
    )
    print(('新增' if 建 else '已存在'), 行.id, '|', 行.名称, '|', 分类名)

print('全站技能总数:', 技能.objects.count())
