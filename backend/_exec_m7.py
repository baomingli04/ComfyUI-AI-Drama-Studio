# -*- coding: utf-8 -*-
"""M7 迁移（幂等，可重复跑）：
1) 方案 表补 候选卡 JSON 列（/script/plan 方案卡七字段）
2) 建 题材标签 表（/script/new 题材 chips 数据源）并种子 16 个内置标签
3) 在 剧本创作 分类注册一个可用技能（指向磁盘上现成的 hf-novel-to-drama-script__skillhub）
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '后端.settings')
django.setup()

from django.utils import timezone
from django.db import connection

# ---------- 1. 方案.候选卡 ----------
c = connection.cursor()
c.execute(
    "SELECT COUNT(*) FROM information_schema.COLUMNS "
    "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='方案' AND COLUMN_NAME='候选卡'"
)
if c.fetchone()[0] == 0:
    c.execute("ALTER TABLE `方案` ADD COLUMN `候选卡` json NULL COMMENT "
              "'/script/plan 方案卡七字段：{标题,故事线,题材,基调,结局,驱动,风险}' AFTER `是否选定`")
    print('[1] 方案.候选卡 列已添加')
else:
    print('[1] 方案.候选卡 列已存在，跳过')

# ---------- 2. 题材标签 表 ----------
c.execute(
    "SELECT COUNT(*) FROM information_schema.TABLES "
    "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='题材标签'"
)
if c.fetchone()[0] == 0:
    c.execute(
        "CREATE TABLE `题材标签` ("
        "  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',"
        "  `名称` varchar(50) NOT NULL COMMENT '标签名，全局唯一',"
        "  `系统内置` tinyint(1) NOT NULL DEFAULT 0 COMMENT '1=内置标签（种子写入）',"
        "  `排序` int(11) NOT NULL DEFAULT 0 COMMENT '显示顺序，小在前',"
        "  `用户id` bigint(20) NULL COMMENT '添加人；内置为 NULL',"
        "  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',"
        "  PRIMARY KEY (`id`) USING BTREE,"
        "  UNIQUE KEY `uk_题材标签_名称` (`名称`) USING BTREE"
        ") ENGINE=InnoDB CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci "
        "COMMENT='题材标签库：/script/new 题材 chips 数据源，手动添加也写这里'"
    )
    print('[2] 题材标签 表已创建')
else:
    print('[2] 题材标签 表已存在，跳过')

from 接口.models.标签 import 标签

内置标签 = ['都市', '校园', '玄幻', '职场', '年代', '科幻', '悬疑', '古装',
            '家庭伦理', '甜宠', '武侠', '喜剧', '军事', '医疗', '宫斗', '青春']
现在 = timezone.now()
新建 = 0
for 序, 名 in enumerate(内置标签):
    _, created = 标签.objects.get_or_create(
        名称=名,
        defaults={'系统内置': True, '排序': 序, '用户id': None, '创建时间': 现在},
    )
    if created:
        新建 += 1
print('[2] 内置标签种子完成，本次新插 %d 个，当前共 %d 个' % (新建, 标签.objects.count()))

# ---------- 3. 剧本创作 分类注册技能 ----------
from 接口.models.技能分类 import 技能分类
from 接口.models.技能 import 技能

分类 = 技能分类.objects.filter(名称='剧本创作').first()
if 分类 is None:
    raise SystemExit('[3] 未找到「剧本创作」分类，先跑分类内置化脚本')
技能行 = 技能.objects.filter(目录名='hf-novel-to-drama-script__skillhub').first()
if 技能行 is None:
    技能.objects.create(
        目录名='hf-novel-to-drama-script__skillhub',
        名称='短剧剧本改编',
        简介='按短剧商业套路产出创作方案与结构化剧本：爆点前置、强冲突开场、可拍可剪的场次化输出。',
        分类id=分类,
        来源='内置注册',
        创建时间=现在, 更新时间=现在,
    )
    print('[3] 已注册技能「短剧剧本改编」→ 剧本创作 分类')
else:
    if 技能行.分类id_id != 分类.id:
        技能行.分类id = 分类
        技能行.更新时间 = 现在
        技能行.save(update_fields=['分类id', '更新时间'])
        print('[3] 技能「短剧剧本改编」已归入 剧本创作 分类')
    else:
        print('[3] 技能已存在且分类正确，跳过')

print('M7 迁移完成')
