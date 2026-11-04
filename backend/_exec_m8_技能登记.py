# -*- coding: utf-8 -*-
"""登记 4 个技能到 技能 表（幂等）：
1) 长篇小说创作助手  full-length-novel-writer__skillhub  -> 写作技能
2) 故事转分镜脚本    story-to-video-script__skillhub      -> 分镜技能
3) 小说推文视频导演  novel-promo-video-maker__skillhub    -> 视频生成
4) 文生图提示词优化  text-to-image-prompt-optimizer       -> 图片提示词扩写
"""
import os
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '后端.settings')
django.setup()

from django.utils import timezone  # noqa: E402
from 接口.models.技能分类 import 技能分类  # noqa: E402
from 接口.models.技能 import 技能  # noqa: E402

清单 = [
    ('full-length-novel-writer__skillhub', '长篇小说创作助手', '写作技能',
     '网络小说创作助手：新开书/续写/讨论创作，结构化工作流 + AI 创造力，覆盖大纲、人设、章节管理。'),
    ('story-to-video-script__skillhub', '故事转分镜脚本', '分镜技能',
     '把小说段落/故事文本转成可直接生成视频的生产包：角色/场景/物品资产卡(文生图提示词) + 分镜表(每镜头完整提示词) + 人物场景一致性方案。'),
    ('novel-promo-video-maker__skillhub', '小说推文视频导演', '视频生成',
     '把一章小说/故事脚本改编成带旁白竖屏视频片段：自动拆钩子和分镜、每分镜配插画、角色跨镜头一致、旁白音色可选，按分镜顺序交付成片。'),
    ('text-to-image-prompt-optimizer', '文生图提示词优化', '图片提示词扩写',
     '生成并优化 AI 绘画提示词：主攻 Nano Banana/Gemini 自然语言风格，兼容 Midjourney/SD/DALL-E，中英双语输出，带模板库与平台参数参考。'),
]

for 目录名, 名称, 分类名, 简介 in 清单:
    分类 = 技能分类.objects.filter(名称=分类名).first()
    if 分类 is None:
        print('缺分类，跳过:', 分类名)
        continue
    行 = 技能.objects.filter(目录名=目录名).first()
    if 行 is not None:
        改了 = False
        if 行.分类id_id != 分类.id:
            行.分类id_id = 分类.id
            改了 = True
        if 行.名称 != 名称:
            行.名称 = 名称
            改了 = True
        if 改了:
            行.更新时间 = timezone.now()
            行.save(update_fields=['分类id', '名称', '更新时间'])
            print('已更新:', 名称, '->', 分类名)
        else:
            print('已存在，无需改动:', 名称)
        continue
    now = timezone.now()
    技能.objects.create(
        目录名=目录名,
        名称=名称,
        简介=简介,
        分类id=分类,
        来源='内置登记',
        创建时间=now,
        更新时间=now,
    )
    print('已登记:', 名称, '->', 分类名)

print('---- 当前全量 ----')
for s in 技能.objects.select_related('分类id').order_by('id'):
    print(s.id, '|', s.名称, '|', s.分类id.名称, '|', s.目录名)
