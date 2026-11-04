# -*- coding: utf-8 -*-
"""一次性脚本：给 task 表加 `产物图片2` 列（文生图8K 出两张：1x + 4x）。"""
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

if "产物图片2" not in 现有列:
    cur.execute(
        "ALTER TABLE task ADD COLUMN `产物图片2` VARCHAR(512) DEFAULT NULL "
        "COMMENT '成功时产出的第 2 张图片路径，相对 backend/资源/产物/；目前仅文生图8K 使用（产物图片=1x 原尺寸，产物图片2=4x 放大）'"
    )
    print("ADDED_产物图片2")
else:
    print("SKIP_产物图片2")

conn.commit()

cur.execute("SHOW COLUMNS FROM task")
现有列2 = [row[0] for row in cur.fetchall()]
print("AFTER=" + ",".join(现有列2))
print("HAS_产物图片2=" + str("产物图片2" in 现有列2))

cur.close()
conn.close()
