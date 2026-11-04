# -*- coding: utf-8 -*-
"""按《表结构.sql》把库落到目标态（幂等，可重复执行）：
- 现有 6 表：不重建，只补缺失列/索引/注释（M2/M3/M5 的增量 ALTER）
- 业务表 13 张：CREATE TABLE IF NOT EXISTS 全新建
- 数据：M1 两条内置分类（查重后插入）+ M4 三条业务页提示词模板（查重后插入）
执行前打印现状，执行后打印差异报告。
"""
import os
import re
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '后端.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db import connection  # noqa: E402

SQL_PATH = r'D:\视频图片素材\aicg\表结构.sql'

ACTIONS = []   # (类别, 说明)
ERRORS = []


def run(cur, sql, label, category):
    try:
        cur.execute(sql)
        ACTIONS.append((category, label))
        print('[OK] %s | %s' % (category, label))
    except Exception as e:  # noqa: BLE001
        ERRORS.append((category, label, str(e)))
        print('[FAIL] %s | %s\n       %s' % (category, label, str(e)))


def table_exists(cur, name):
    cur.execute(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema=DATABASE() AND table_name=%s", [name])
    return cur.fetchone()[0] > 0


def columns(cur, table):
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema=DATABASE() AND table_name=%s", [table])
    return set(r[0] for r in cur.fetchall())


def indexes(cur, table):
    cur.execute("SHOW INDEX FROM `%s`" % table)
    return set(r[2] for r in cur.fetchall())


def scalars(cur, sql, params=None):
    cur.execute(sql, params or [])
    return [r[0] for r in cur.fetchall()]


with connection.cursor() as cur:
    # ---------- 0. 现状 ----------
    print('=== 库现状 ===')
    print('数据库:', scalars(cur, 'SELECT DATABASE()')[0])
    have = set(scalars(cur, 'SHOW TABLES'))
    print('现有表:', ', '.join(sorted(have)) or '(空)')

    # ---------- 1. M2/M3：task 增量 ----------
    if table_exists(cur, 'task'):
        tcols = columns(cur, 'task')
        tidx = indexes(cur, 'task')
        task_alter = [
            ("request_id", "ADD COLUMN `request_id` varchar(64) NULL DEFAULT NULL COMMENT '【M2】幂等键：同 创建人id+request_id 重复提交返回原任务（uk_task_幂等）；存量任务可空'"),
            ("进度", "ADD COLUMN `进度` tinyint(4) NULL DEFAULT NULL COMMENT '【M2】执行进度 0~100；NULL=该类型不支持进度'"),
            ("积分", "ADD COLUMN `积分` decimal(10,2) NULL DEFAULT NULL COMMENT '【M2】本任务积分消耗；提交预扣→成功落账/失败回退（流水见 积分流水 表）；NULL=免费'"),
            ("重试次数", "ADD COLUMN `重试次数` int(11) NOT NULL DEFAULT 0 COMMENT '【M2】失败自动重试次数，上限 3（指数退避）'"),
            ("页面来源", "ADD COLUMN `页面来源` varchar(64) NULL DEFAULT NULL COMMENT '【M2】提交页面路由，如 /video/shot；按页聚合统计与权限校验'"),
            ("业务实体", "ADD COLUMN `业务实体` varchar(128) NULL DEFAULT NULL COMMENT '【M2】关联业务实体，任务完成据此回写业务状态（契约 C5），如 1:1:SH002（剧:集:镜）或 CHAR_001（资产id）'"),
        ]
        for col, ddl in task_alter:
            if col not in tcols:
                run(cur, "ALTER TABLE `task` " + ddl, "task 补列 %s" % col, "M2")
            else:
                print('[SKIP] task.%s 已存在' % col)
        if 'uk_task_幂等' not in tidx:
            run(cur, "ALTER TABLE `task` ADD UNIQUE INDEX `uk_task_幂等`(`创建人id` ASC, `request_id` ASC) USING BTREE COMMENT '【M2】同用户同 request_id 唯一，实现提交幂等'",
                "task 唯一索引 uk_task_幂等", "M2")
        if 'idx_task_页面来源' not in tidx:
            run(cur, "ALTER TABLE `task` ADD INDEX `idx_task_页面来源`(`页面来源` ASC) USING BTREE",
                "task 索引 idx_task_页面来源", "M2")
        if 'idx_task_业务实体' not in tidx:
            run(cur, "ALTER TABLE `task` ADD INDEX `idx_task_业务实体`(`业务实体` ASC) USING BTREE",
                "task 索引 idx_task_业务实体", "M2")
        # M3：类型列注释补全 23 种
        run(cur, "ALTER TABLE `task` MODIFY `类型` varchar(50) NOT NULL COMMENT '【M3】任务种类，后端白名单 23 种：文本回复/图片解析/文生图/生成图片/编辑图片单图/编辑图片三图/三图编辑一致版/多图编辑多人合并版/文生图8K/动漫转真人/首尾帧/文生视频/参考生视频/多参考生视频/首尾帧生视频/加速版生视频/外部分组图生视频/外部分组多参考生视频/二采重绘/二采加速生视频/去水印/资产提取/分镜拆分'",
            "task.类型 注释补全 23 种", "M3")
    else:
        print('[WARN] task 表不存在，跳过 M2/M3（请先从 aicg.sql 恢复基础六表）')

    # ---------- 2. M5：模型配置 增量 ----------
    if table_exists(cur, '模型配置'):
        mcols = columns(cur, '模型配置')
        for col, ddl in [
            ("生图模型", "ADD COLUMN `生图模型` varchar(100) NULL DEFAULT NULL COMMENT '【M5】美术资产生图模型名，如 gpt-image 2；/video/art 页头下拉从这里读'"),
            ("生视频模型", "ADD COLUMN `生视频模型` varchar(100) NULL DEFAULT NULL COMMENT '【M5】镜头生成视频模型名；/video/director 生成条从这里读'"),
            ("TTS模型", "ADD COLUMN `TTS模型` varchar(100) NULL DEFAULT NULL COMMENT '【M5】音色合成模型名，如 Qwen3 TTS；/video/art 音色区从这里读'"),
            ("价目", "ADD COLUMN `价目` json NULL DEFAULT NULL COMMENT '【M5】积分价目表 JSON，如 {\"重提取\":50,\"TTS\":10,\"生图\":10,\"生视频\":10,\"合成\":20}；一处改全局生效'"),
        ]:
            if col not in mcols:
                run(cur, "ALTER TABLE `模型配置` " + ddl, "模型配置 补列 %s" % col, "M5")
            else:
                print('[SKIP] 模型配置.%s 已存在' % col)
        # 价目默认值：给唯一一行填上默认价目（只有一行且为空才填）
        run(cur, "UPDATE `模型配置` SET `价目` = JSON_OBJECT('重提取',50,'TTS',10,'生图',10,'生视频',10,'合成',20) WHERE `价目` IS NULL",
            "模型配置.价目 写入默认价目", "M5")

    # ---------- 3. 业务表 13 张：CREATE IF NOT EXISTS ----------
    with open(SQL_PATH, 'r', encoding='utf-8') as f:
        raw = f.read()
    # 取第二部分（业务表）起点到 M1 INSERT 结束
    start = raw.index('-- 第二部分 阶段二业务表')
    end = raw.index('-- 【M4·阶段二】')
    segment = raw[start:end]
    # 去注释行
    lines = [ln for ln in segment.split('\n') if not ln.strip().startswith('--')]
    clean = '\n'.join(lines)
    # 全部改成 IF NOT EXISTS，幂等
    clean = re.sub(r'DROP TABLE IF EXISTS\s+`([^`]+)`\s*;', '', clean)
    clean = re.sub(r'CREATE TABLE(\s+IF NOT EXISTS)?\s+`', lambda m: 'CREATE TABLE IF NOT EXISTS `', clean)
    # 按分号切语句（本文件字符串内无英文分号）
    statements = [s.strip() for s in clean.split(';') if s.strip()]
    for st in statements:
        m = re.match(r'CREATE TABLE IF NOT EXISTS `([^`]+)`', st)
        name = m.group(1) if m else '?'
        if m and name in have:
            print('[SKIP] 业务表 %s 已存在' % name)
            continue
        run(cur, st, '建业务表 %s' % name, '建表')

    # ---------- 4. M1：内置分类（查重插入） ----------
    exist_cats = set(scalars(cur, "SELECT `名称` FROM `技能分类`"))
    for 名称, 编码, 排序 in [('剧本创作', 'script_writing', 10), ('视频生成', 'video_gen', 11)]:
        if 名称 in exist_cats:
            print('[SKIP] 技能分类「%s」已存在' % 名称)
            continue
        run(cur, "INSERT INTO `技能分类` (`名称`,`编码`,`排序`,`系统内置`) VALUES (%s,%s,%s,1)",
            '技能分类内置分类「%s」' % 名称, 'M1')

    # ---------- 5. M4：业务页提示词模板（查重插入） ----------
    exist_types = set(scalars(cur, "SELECT `类型` FROM `提示词模板`"))
    m4_rows = [
        ('生成:/video/shot',
         '你是短剧分镜师。依据给定剧本与资产，把一集拆成镜头级分镜。只输出分镜，不解释。',
         '把本集剧本拆分为镜头。逐镜一行，格式固定为：镜号｜场次｜景别｜运镜｜画面｜台词｜时长。\n'
         '要求：镜号 SH+三位数递增；场次写「第N场·地点」；景别用 远景/全景/中景/近景/特写；运镜一句话；画面写清人物+动作+环境（用到资产名称时与资产清单保持一致）；台词沿用剧本原句，无台词写（无）；时长为秒数且遵守所选时长档；每场次 2~4 镜；单镜时长不超过所选档上限。只输出这些行，不要表头、不要解释。'),
        ('生成:/video/assets',
         '你是短剧资产统筹。从给定剧本中提取可直接拍摄使用的资产清单。只输出清单，不解释。',
         '从本集剧本提取资产。逐项一行，格式固定为：资产ID｜类型｜名称｜别名｜本集关系｜级别｜摘要。\n'
         '要求：类型 ∈ 人物/场景/道具/服装；人物 ID=CHAR_三位数、场景=SCN_、道具=PROP_、服装=COST_；别名多个用 、 分隔，无写 —；本集关系 ∈ 新增/引用；人物级别 ∈ 主角/核心配角/功能配角，场景级别 ∈ 主场景/次主场景/一次性场景，道具写 关键道具；人物摘要必须写满外观细节（发型发色、五官、体型、服装、随身物、神态习惯），其他类型摘要一两句写清视觉特征与数量状态。只输出这些行，不要表头、不要解释。'),
        ('生成:/video/director',
         '你是单镜导演。只重写当前这一镜的拍摄脚本，保持与前后镜头的衔接。只输出脚本，不解释。',
         '重写当前镜头的脚本。输出格式固定为：场次｜景别｜运镜｜时长｜台词｜画面描述｜时间线｜光线｜道具提示｜入点｜出点｜负面提示（每行一个字段，用全角冒号）。\n'
         '要求：镜号与场次不变；台词沿用剧本原句或按引入的修改要求微调；画面描述与前后镜头衔接、不引入未在资产清单中的元素；时间线按 0s~时长 拆解动作节拍；负面提示保留原有禁止句式。只输出这些行，不要解释。'),
    ]
    for 类型, 系统提示词, 生成提示词 in m4_rows:
        if 类型 in exist_types:
            print('[SKIP] 提示词模板「%s」已存在' % 类型)
            continue
        run(cur, "INSERT INTO `提示词模板` (`类型`,`系统提示词`,`生成提示词`) VALUES (%s,%s,%s)",
            '提示词模板「%s」' % 类型, 'M4')

    # ---------- 6. 终态报告 ----------
    print('\n=== 终态 ===')
    final = set(scalars(cur, 'SHOW TABLES'))
    print('表（%d 张）:' % len(final), ', '.join(sorted(final)))
    print('技能分类:', scalars(cur, "SELECT `名称` FROM `技能分类` ORDER BY `排序`"))
    print('提示词模板类型数:', len(scalars(cur, "SELECT `类型` FROM `提示词模板`")))

print('\n=== 执行汇总 ===')
print('成功动作 %d 项，失败 %d 项' % (len(ACTIONS), len(ERRORS)))
for c, l, e in ERRORS:
    print('  [失败] %s | %s | %s' % (c, l, e))
