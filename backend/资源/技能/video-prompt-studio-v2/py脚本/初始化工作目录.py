#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能 1：初始化工作目录
按新需求与目录结构，在工作目录直接创建 工作配置.yaml + 三份空骨架文件。

参数：
  --工作目录        必传，配置与产物根目录
  --角色资源目录    可选，角色参考图目录
  --背景资源目录    可选，背景图目录

创建内容：
  <工作目录>/工作配置.yaml         8 个中文字段（角色/背景资源目录、图片/视频输出目录、角色背景一览表、剧情生成文件、提示词生成文件、世界书）
  <工作目录>/角色背景一览表.md      骨架（含 现有资源角色清单 / 背景清单 / 剧情角色清单 三章节）
  <工作目录>/剧情生成.md            空骨架
  <工作目录>/提示词生成.md          空骨架（主要工作文件）
  <工作目录>/世界书.md              空骨架（世界观锚点，功能 3 填充）
  <工作目录>/图片  <工作目录>/视频  默认输出目录（已创建）
"""

import argparse
import os


def main():
    parser = argparse.ArgumentParser(description="初始化工作目录")
    parser.add_argument("--工作目录", required=True, help="配置与产物根目录（必传）")
    parser.add_argument("--角色资源目录", default="", help="角色参考图目录（可选）")
    parser.add_argument("--背景资源目录", default="", help="背景图目录（可选）")
    args = parser.parse_args()

    work_dir = os.path.abspath(args.工作目录)
    role_dir = os.path.abspath(args.角色资源目录) if args.角色资源目录 else ""
    bg_dir = os.path.abspath(args.背景资源目录) if args.背景资源目录 else ""

    os.makedirs(work_dir, exist_ok=True)

    # 默认输出目录置于工作目录下，并直接创建
    img_out = os.path.join(work_dir, "图片")
    vid_out = os.path.join(work_dir, "视频")
    os.makedirs(img_out, exist_ok=True)
    os.makedirs(vid_out, exist_ok=True)

    config_path = os.path.join(work_dir, "工作配置.yaml")
    if os.path.exists(config_path):
        print(f"[跳过] 已存在 {config_path}，未覆盖（如需重建请先手动删除）")
    else:
        lines = [
            "# 工作配置（自动生成，可按需修改）",
            f"角色资源所在目录: {role_dir}",
            f"背景资源所在目录: {bg_dir}",
            f"图片输出目录: {img_out}",
            f"视频输出目录: {vid_out}",
            "角色背景一览表: 角色背景一览表.md",
            "剧情生成文件: 剧情生成.md",
            "提示词生成文件: 提示词生成.md",
            "世界书: 世界书.md",
            "",
        ]
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"[完成] 生成 {config_path}")

    # 剧情生成.md / 提示词生成.md：空骨架（不存在才创建，避免覆盖）
    for name in ["剧情生成.md", "提示词生成.md", "世界书.md"]:
        p = os.path.join(work_dir, name)
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8") as f:
                f.write("")
            print(f"[完成] 生成骨架 {p}")
        else:
            print(f"[跳过] 已存在 {p}")

    # 角色背景一览表.md：含「现有资源角色清单 / 背景清单 / 剧情角色清单」三章节骨架
    ov = os.path.join(work_dir, "角色背景一览表.md")
    if not os.path.exists(ov):
        with open(ov, "w", encoding="utf-8") as f:
            f.write(
                "# 角色背景一览表\n\n"
                "## 现有资源角色清单\n"
                "（由 重命名.py 自动追加；每行：`- `参考图文件名` | 简述`）\n\n"
                "## 背景清单\n"
                "（由 重命名.py 自动追加）\n\n"
                "## 剧情角色清单\n"
                "| 剧情角色 | 匹配资源角色（参考图） | 角色定位简短描述 | 匹配方式 | 备注 |\n"
                "|---|---|---|---|---|\n"
            )
        print(f"[完成] 生成骨架 {ov}（含三章节）")
    else:
        print(f"[跳过] 已存在 {ov}")


if __name__ == "__main__":
    main()
