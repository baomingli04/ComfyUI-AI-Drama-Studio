# -*- coding: utf-8 -*-
"""一次性脚本：给 task 表加导演台全能所需 4 列（沿用 _tmp_add_task_cols.py 约定）。

- 模式：t2v / i2v / fl2v / r2v / v2v / rv2v（节点 7 个可选值里除了 mixed），
  提交侧透传，后端自动切换底膜 ref2va ↔ fl2va。库里的列注释已同步更新。
- 生成声音：TRUE/FALSE（NULL=未设，后端按 True 处理），写 Director output.audioMode。
- 步数：采样步数（Director 节点 steps，默认 8）。
- 采样器：Director 节点 sampler（如 res_multistep），可空走工作流默认。
"""
import pymysql

conn = pymysql.connect(
    host="127.0.0.1",
    port=3306,
    user="root",
    password="root",
    database="aicg",
    charset="utf8mb4",
)
cur = conn.cursor()

cur.execute("SHOW COLUMNS FROM task")
现有列 = [row[0] for row in cur.fetchall()]
print("BEFORE=" + ",".join(现有列))

待加 = [
    ("模式", "VARCHAR(16) DEFAULT NULL "
     "COMMENT '导演台全能生成模式：t2v=文生视频 / i2v=图生视频 / fl2v=首尾帧 / r2v=参考主体 / v2v=视频转视频 / rv2v=参考改视频；后端按此自动切换底膜 ref2va↔fl2va'"),
    ("生成声音", "TINYINT(1) DEFAULT NULL "
     "COMMENT '是否生成声音：1=生成(generate) / 0=静音(mute)；NULL 后端按 1 处理，写 Director output.audioMode'"),
    ("步数", "INT DEFAULT NULL "
     "COMMENT '采样步数，写 Director 节点 steps（默认 8，Turbo 8step LoRA 下用 8）'"),
    ("采样器", "VARCHAR(50) DEFAULT NULL "
     "COMMENT '采样器名，写 Director 节点 sampler（如 res_multistep）；NULL 走工作流默认'"),
]

for 列名, ddl in 待加:
    if 列名 not in 现有列:
        cur.execute("ALTER TABLE task ADD COLUMN `%s` %s" % (列名, ddl))
        print("ADDED_" + 列名)
    else:
        print("SKIP_" + 列名)

conn.commit()

cur.execute("SHOW COLUMNS FROM task")
现有列2 = [row[0] for row in cur.fetchall()]
print("AFTER=" + ",".join(现有列2))
for 列名, _ in 待加:
    print("HAS_%s=%s" % (列名, str(列名 in 现有列2)))

cur.close()
conn.close()
