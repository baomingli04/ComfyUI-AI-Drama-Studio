# -*- coding: utf-8 -*-
"""M10：分镜技能扩充（幂等）—— 4 个 MiniMax 海螺系分镜技能 -> 分镜技能 分类。"""
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '后端.settings')
django.setup()

from django.conf import settings  # noqa: E402
from django.utils import timezone  # noqa: E402
from 接口.models.技能分类 import 技能分类  # noqa: E402
from 接口.models.技能 import 技能  # noqa: E402

清单 = [
    ('minimax-h3-prompt', 'MiniMax H3 分镜脚本', 
     '海螺 H3 双模式分镜：A=叙事分镜制作简报（逐镜时间轴 S.S~S.Ss、镜头/台词/环境声/配乐）；B=结构化参考提示词（Image1/Video1/Audio1 令牌、[SHOT LIST]、Omni Reference/首尾帧/动效迁移/声音迁移）。附 H3 规格参考文档。'),
    ('hailuo-prompting', '海螺动作节拍分镜',
     'Hailuo 2.3/02/video-01 系提示词法：动作按节拍顺序编排（first/then/as/finally）、Director 端点 15 个方括号镜头指令（每括号限 3 条）、prompt_optimizer 开关时机、无负面提示词的补偿写法、图生视频只写增量。'),
    ('brand-promo-video-generator', '品牌宣传短片分镜',
     'MiniMax 官方模板（Hub 端 2.6k 安装）：品牌/产品宣传短片——资产核验→叙事方向→精确节拍与镜头规划→配图配乐→组装交付；镜头/节拍规划部分可直接指导文本任务，Hub 工具调用由平台任务链路替代。'),
    ('music-video-subtitle-generator', 'MV 字幕短片分镜',
     'MiniMax 官方模板（Hub 端 2.6k 安装）：音乐 MV/字幕短片——按音乐节拍规划镜头与画面切换、字幕卡点；镜头规划部分可直接指导文本任务，Hub 工具调用由平台任务链路替代。'),
]

分类 = 技能分类.objects.filter(名称='分镜技能').first()
if 分类 is None:
    raise SystemExit('缺分类：分镜技能')

ok = 0
for 目录名, 名称, 简介 in 清单:
    if not (settings.SKILL_DIR / 目录名 / 'SKILL.md').is_file():
        print('缺 SKILL.md，跳过:', 目录名)
        continue
    行 = 技能.objects.filter(目录名=目录名).first()
    if 行 is not None:
        print('已存在:', 行.名称)
        continue
    now = timezone.now()
    技能.objects.create(目录名=目录名, 名称=名称, 简介=简介, 分类id=分类,
                        来源='内置登记', 创建时间=now, 更新时间=now)
    print('已登记:', 名称, '-> 分镜技能')
    ok += 1

print('---- 新登记', ok, '个 ----')
print('分镜技能现有:', [s.名称 for s in 技能.objects.filter(分类id=分类).order_by('id')])
print('全站总数:', 技能.objects.count())
