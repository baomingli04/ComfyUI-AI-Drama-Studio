#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成剧情角色表.py — 功能 3 配套：枚举剧情角色 → 生成 / 更新 角色背景一览表.md 的「剧情角色清单」。

逻辑：
  - 读取 角色背景一览表.md 的「现有资源角色清单」（已入库的角色参考图文件名）。
  - 读取已有的「剧情角色清单」（已登记的剧情角色）。
  - 对每个传入的剧情角色：
        已在 剧情角色清单 → 跳过（不加）。
        不在 → 新增一行，按【性别】匹配参考图：
              从「角色资源所在目录」走查 父目录名(男/女)=性别、子目录名=角色名，
              得到该角色的性别；再筛「现有资源角色清单」中同性别的参考图，确定性取首个；
              无性别信息时回落默认首图；无现有资源则标记「待补（无现有资源）」。
              （替代旧版 random.choice 全池随机——那会男角配女图。）
传参：
  --config PATH       工作配置.yaml（定位 角色背景一览表.md）
  --project-dir PATH  一览表所在目录（无 --config 时用）
  --角色 NAME         可重复，剧情角色名（如 鸣人）
  --文件 PATH         每行一个剧情角色名的文本文件（与 --角色 可混用）
  --seed N            随机种子（可选，便于复现）
示例：
  python 生成剧情角色表.py --config "D:/proj/工作配置.yaml" --角色 鸣人 --角色 佐助
  python 生成剧情角色表.py --config "D:/proj/工作配置.yaml" --文件 剧情角色.txt
"""

import argparse
import os
import re
import random
import sys

IMG_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
ROLE_SEC = "## 现有资源角色清单"
BG_SEC = "## 背景清单"
STORY_SEC = "## 剧情角色清单"
STORY_HEADER = "| 剧情角色 | 匹配资源角色（参考图） | 角色定位简短描述 | 匹配方式 | 备注 |"
STORY_SEP = "|---|---|---|---|---|"


def read_config(config_path):
    """极简解析 工作配置.yaml 的扁平中文字段（不依赖 PyYAML）。"""
    d = {}
    if not config_path or not os.path.exists(config_path):
        return d
    with open(config_path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if ":" in line:
                k, _, v = line.partition(":")
                d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def overview_path(args, cfg):
    if args.project_dir:
        return os.path.join(args.project_dir, "角色背景一览表.md")
    if args.config:
        return os.path.join(os.path.dirname(os.path.abspath(args.config)), "角色背景一览表.md")
    return "角色背景一览表.md"


def section_text(content, header):
    """返回 header 之后、下一个 '## ' 之前的正文（不含 header 行）；不存在返回 None。

    按标题行（行首 '#' 锚定）定位，避免一览表中 blockquote 内联的
    「## 剧情角色清单」字样被当作真实章节起始而误命中（旧版子串 split 的坑）。
    """
    name = re.sub(r"^#+\s*", "", header).strip()
    m_head = re.search(r"(?m)^#{1,6}[ \t]*" + re.escape(name) + r"[ \t]*$", content)
    if not m_head:
        return None
    rest = content[m_head.end():]
    m = re.search(r"(?m)^## ", rest)
    return rest[: m.start()] if m else rest


def load_role_resources(content):
    """从「现有资源角色清单」章节解析已入库角色参考图文件名列表。"""
    body = section_text(content, ROLE_SEC)
    if body is None:
        return []
    return re.findall(r"`([^`]+\.(?:png|jpg|jpeg|webp|bmp))`", body, flags=re.IGNORECASE)


def load_story_rows(content):
    """解析「剧情角色清单」表格 → (rows, names_set)。rows 为 (name, ref, match, note) 列表。"""
    body = section_text(content, STORY_SEC)
    rows = []
    names = set()
    if body is None:
        return rows, names
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if "剧情角色" in line or re.match(r"\|[\s\-:|]+\|$", line):
            continue  # 表头或分隔行
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 2 or not cols[0]:
            continue
        name = cols[0]
        ref = cols[1]
        # 兼容 2/3/4/5 列各种写法，缺失列补空（避免 cols[2]/cols[3] 越界崩溃）：
        #   2 列：剧情角色 | 参考图
        #   3 列：剧情角色 | 参考图 | 匹配方式
        #   4 列：剧情角色 | 参考图 | 匹配方式 | 备注（无角色定位列）
        #   5 列：剧情角色 | 参考图 | 角色定位简短描述 | 匹配方式 | 备注
        pos = cols[2] if len(cols) >= 5 else ""
        if len(cols) >= 5:
            match, note = cols[3], cols[4]
        elif len(cols) == 4:
            match, note = cols[2], cols[3]
        elif len(cols) == 3:
            match, note = cols[2], ""
        else:
            match, note = "", ""
        if not name:
            continue
        rows.append((name, ref, pos, match, note))
        names.add(name)
    return rows, names


def ensure_skeleton(path):
    """若一览表不存在，创建含三个章节的空骨架。"""
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            "# 角色背景一览表\n\n"
            f"{ROLE_SEC}\n（由 重命名.py 自动追加；每行：`- `参考图文件名` | 简述`）\n\n"
            f"{BG_SEC}\n（由 重命名.py 自动追加）\n\n"
            f"{STORY_SEC}\n{STORY_HEADER}\n{STORY_SEP}\n"
        )
    print(f"[完成] 新建骨架 {path}")


def rebuild_story_section(rows):
    lines = [STORY_HEADER, STORY_SEP]
    for name, ref, pos, match, note in rows:
        lines.append(f"| {name} | {ref} | {pos} | {match} | {note} |")
    return "\n".join(lines) + "\n"


def write_story_section(path, rows):
    """把「剧情角色清单」章节替换为最新表格（保留其他章节）。

    按标题行（行首 '#' 锚定）定位章节，避免 blockquote 内联的「## 剧情角色清单」
    字样误命中（旧版子串 split 会把数据写到错误位置）。
    """
    with open(path, encoding="utf-8") as f:
        content = f.read()
    new_block = rebuild_story_section(rows)
    name = re.sub(r"^#+\s*", "", STORY_SEC).strip()
    m_head = re.search(r"(?m)^#{1,6}[ \t]*" + re.escape(name) + r"[ \t]*$", content)
    if m_head:
        rest = content[m_head.end():]
        m = re.search(r"(?m)^## ", rest)
        after = rest[m.start():] if m else ""
        before = content[: m_head.start()]
        content = before + m_head.group(0) + "\n" + new_block + after
    else:
        content = content.rstrip() + "\n\n" + STORY_SEC + "\n" + new_block
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def collect_inputs(args):
    names = []
    if args.角色:
        names.extend(args.角色)
    if args.文件:
        with open(args.文件, encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if s and not s.startswith("#"):
                    names.append(s)
    seen = set()
    out = []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


# ── 性别匹配（替代旧版 random.choice 全池随机，避免男角配女图）──
# 性别来源：角色资源目录结构「父目录名=性别(男/女)、子目录名=角色名」。
# 参考图性别：从文件名解析（含「男/男子/男性」→男；含「女/女性/女子」→女）。
GENDER_TOKENS_F = ("女", "女性", "女子", "姑娘")
GENDER_TOKENS_M = ("男", "男子", "男性", "爷们")


def build_gender_map(role_dir):
    """走查 角色资源所在目录：父目录名(男/女)=性别，子目录名=角色名 → {角色名: 性别}。"""
    m = {}
    if not role_dir or not os.path.isdir(role_dir):
        return m
    for gd in sorted(os.listdir(role_dir)):
        gpath = os.path.join(role_dir, gd)
        if not os.path.isdir(gpath):
            continue
        if "男" in gd:
            gender = "男"
        elif "女" in gd:
            gender = "女"
        else:
            continue
        for sub in sorted(os.listdir(gpath)):
            spath = os.path.join(gpath, sub)
            if os.path.isdir(spath):
                m[sub] = gender
    return m


def gender_of_filename(fn):
    for t in GENDER_TOKENS_F:
        if t in fn:
            return "女"
    for t in GENDER_TOKENS_M:
        if t in fn:
            return "男"
    return None


def match_resource(name, resources, gender_map):
    """按性别匹配：先由角色名查性别（来自目录结构），再筛同性别参考图，确定性取首个（不再随机）。
    无性别信息时回落确定性首图；无资源时标记待补。"""
    gender = gender_map.get(name)
    if gender:
        cands = [r for r in resources if gender_of_filename(r) == gender]
        if cands:
            cands.sort()
            return cands[0], f"按性别匹配({gender})"
    if resources:
        rs = sorted(resources)
        return rs[0], "无性别信息(默认首图)"
    return "", "待补（无现有资源）"


def main():
    ap = argparse.ArgumentParser(description="枚举剧情角色并生成 剧情角色清单")
    ap.add_argument("--config", default=None, help="工作配置.yaml（定位 角色背景一览表.md）")
    ap.add_argument("--project-dir", default=None, help="角色背景一览表.md 所在目录")
    ap.add_argument("--角色", action="append", default=[], help="剧情角色名，可重复")
    ap.add_argument("--文件", default=None, help="每行一个剧情角色名的文本文件")
    ap.add_argument("--seed", type=int, default=None, help="（保留兼容）性别匹配为确定性结果，本参数已不再影响匹配")
    args = ap.parse_args()

    if not args.角色 and not args.文件:
        print("[error] 必须提供 --角色 或 --文件，至少一个。")
        sys.exit(1)

    if args.seed is not None:
        random.seed(args.seed)

    cfg = read_config(args.config) if args.config else {}
    ov_path = overview_path(args, cfg)
    ensure_skeleton(ov_path)

    # 性别映射：从「角色资源所在目录」的 父目录(男/女)=性别、子目录名=角色名 建立
    role_dir = cfg.get("角色资源所在目录")
    gender_map = build_gender_map(role_dir) if role_dir else {}
    if role_dir:
        print(f"[info] 性别映射：从 {role_dir} 解析到 {len(gender_map)} 个角色性别")

    with open(ov_path, encoding="utf-8") as f:
        content = f.read()

    resources = load_role_resources(content)
    rows, existing = load_story_rows(content)
    print(f"[info] 现有资源角色 {len(resources)} 个；已登记剧情角色 {len(existing)} 个")

    inputs = collect_inputs(args)
    added = 0
    for name in inputs:
        if name in existing:
            print(f"  [跳过] 已登记：{name}")
            continue
        ref_name, match = match_resource(name, resources, gender_map)
        ref = f"`{ref_name}`" if ref_name else ""
        rows.append((name, ref, "", match, ""))
        existing.add(name)
        added += 1
        if ref:
            print(f"  [新增] {name} → 匹配 {ref}（{match}）")
        else:
            print(f"  [新增] {name} → {match}")

    if added:
        write_story_section(ov_path, rows)
        print(f"[完成] 写入 {added} 个剧情角色到 {ov_path} 的「剧情角色清单」")
    else:
        print("[完成] 无新增（全部已登记）")


if __name__ == "__main__":
    main()
