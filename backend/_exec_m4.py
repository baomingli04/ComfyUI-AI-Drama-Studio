# -*- coding: utf-8 -*-
"""M4 补插（走 ORM，避开游标参数绑定问题）+ 全库终验。幂等可重复执行。"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '后端.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from 接口.models.提示词模板 import 提示词模板  # noqa: E402
from django.utils import timezone  # noqa: E402

现在 = timezone.now()

M4 = [
    ('生成:/video/shot',
     '你是短剧分镜师。依据给定剧本与资产，把一集拆成镜头级分镜。只输出分镜，不解释。',
     '把本集剧本拆分为镜头。逐镜一行，格式固定为：镜号｜场次｜景别｜运镜｜画面｜台词｜时长。\n'
     '要求：镜号 SH+三位数递增；场次写「第N场·地点」；景别用 远景/全景/中景/近景/特写；运镜一句话；'
     '画面写清人物+动作+环境（用到资产名称时与资产清单保持一致）；台词沿用剧本原句，无台词写（无）；'
     '时长为秒数且遵守所选时长档；每场次 2~4 镜；单镜时长不超过所选档上限。只输出这些行，不要表头、不要解释。'),
    ('生成:/video/assets',
     '你是短剧资产统筹。从给定剧本中提取可直接拍摄使用的资产清单。只输出清单，不解释。',
     '从本集剧本提取资产。逐项一行，格式固定为：资产ID｜类型｜名称｜别名｜本集关系｜级别｜摘要。\n'
     '要求：类型 ∈ 人物/场景/道具/服装；人物 ID=CHAR_三位数、场景=SCN_、道具=PROP_、服装=COST_；'
     '别名多个用 、 分隔，无写 —；本集关系 ∈ 新增/引用；人物级别 ∈ 主角/核心配角/功能配角，'
     '场景级别 ∈ 主场景/次主场景/一次性场景，道具写 关键道具；人物摘要必须写满外观细节'
     '（发型发色、五官、体型、服装、随身物、神态习惯），其他类型摘要一两句写清视觉特征与数量状态。'
     '只输出这些行，不要表头、不要解释。'),
    ('生成:/video/director',
     '你是单镜导演。只重写当前这一镜的拍摄脚本，保持与前后镜头的衔接。只输出脚本，不解释。',
     '重写当前镜头的脚本。输出格式固定为：场次｜景别｜运镜｜时长｜台词｜画面描述｜时间线｜光线｜道具提示｜入点｜出点｜负面提示'
     '（每行一个字段，用全角冒号）。\n'
     '要求：镜号与场次不变；台词沿用剧本原句或按引入的修改要求微调；画面描述与前后镜头衔接、'
     '不引入未在资产清单中的元素；时间线按 0s~时长 拆解动作节拍；负面提示保留原有禁止句式。只输出这些行，不要解释。'),
]

print('=== M4 提示词模板插入 ===')
for 类型, 系统, 生成 in M4:
    obj, created = 提示词模板.objects.get_or_create(
        类型=类型,
        defaults={'系统提示词': 系统, '生成提示词': 生成,
                  '创建时间': 现在, '更新时间': 现在})
    print('[%s] %s (id=%s)' % ('新增' if created else '已存在', 类型, obj.id))

# ---------- 终验 ----------
from django.db import connection  # noqa: E402

with connection.cursor() as cur:
    print('\n=== 终验 ===')
    cur.execute("SELECT `名称`,`编码`,`系统内置` FROM `技能分类` ORDER BY `排序`,`id`")
    print('技能分类（应无重复/垃圾行）:')
    for r in cur.fetchall():
        print('  ', r)
    cur.execute("SELECT `类型` FROM `提示词模板` WHERE `类型` LIKE '生成:%'")
    print('业务页提示词模板:', [r[0] for r in cur.fetchall()])
    cur.execute("SELECT `价目` FROM `模型配置` LIMIT 1")
    print('模型配置.价目:', cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='task'")
    print('task 列数:', cur.fetchone()[0], '（原 56 + M2 六列 = 62）')
    cur.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='模型配置'")
    print('模型配置 列数:', cur.fetchone()[0], '（原 8 + M5 四列 = 12）')
    # 业务表行数（应全为 0，空表待接后端）
    cur.execute("SELECT table_name, table_rows FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name IN ('剧','方案','方案历史','人物','分集','剧本','资产','美术定装','分镜','镜头脚本','镜头视频','成片','积分流水')")
    print('业务表行数:')
    for r in cur.fetchall():
        print('  %s: %s' % (r[0], r[1]))
    # 抽查关键契约字段
    checks = [
        ('方案', '基础版本', 'C9 乐观锁'),
        ('剧本', '定稿时间', 'C1 定稿锁'),
        ('资产', '手改字段', 'C2 手改分层'),
        ('美术定装', '手改必须保持', 'C2 手改分层'),
        ('美术定装', '音色url', 'C3 音色前置'),
        ('分镜', '视频状态', 'C5 状态回写'),
        ('成片', 'AIGC显式标识', 'C7 合规'),
        ('积分流水', 'request_id', 'C8 幂等'),
    ]
    print('契约字段抽查:')
    for 表, 列, 契约 in checks:
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name=%s AND column_name=%s",
            [表, 列])
        print('  [%s] %s.%s（%s）' % ('有' if cur.fetchone()[0] else '缺!', 表, 列, 契约))
