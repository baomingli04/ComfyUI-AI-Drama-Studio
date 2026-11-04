# -*- coding: utf-8 -*-
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

if "比例" not in 现有列:
    cur.execute(
        "ALTER TABLE task ADD COLUMN `比例` VARCHAR(16) DEFAULT NULL "
        "COMMENT '视频宽高比标签键（如 16:9 / 9:16 / 1:1 / 4:3 等），提交侧透传，后端映射为 Comfy 完整标签写 ResolutionSelector；仅参考生视频填写（二采不含比例）；非视频任务可空'"
    )
    print("ADDED_比例")
else:
    print("SKIP_比例")

if "视频时长" not in 现有列:
    cur.execute(
        "ALTER TABLE task ADD COLUMN `视频时长` DECIMAL(6,2) DEFAULT NULL "
        "COMMENT '请求的视频生成时长（秒），写入 Comfy PrimitiveFloat 时长节点；参考生视频默认 5，二采默认 7；非视频任务可空'"
    )
    print("ADDED_视频时长")
else:
    print("SKIP_视频时长")

conn.commit()

cur.execute("SHOW COLUMNS FROM task")
现有列2 = [row[0] for row in cur.fetchall()]
print("AFTER=" + ",".join(现有列2))
print("HAS_比例=" + str("比例" in 现有列2))
print("HAS_视频时长=" + str("视频时长" in 现有列2))

cur.close()
conn.close()
