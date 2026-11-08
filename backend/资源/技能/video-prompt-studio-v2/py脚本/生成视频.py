#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成视频.py — 功能 6 / 7 官方执行器（随技能分发，单一可信执行入口）。

读 工作配置.yaml + 提示词生成.md，按每段「生成视频的工作流」路由：
  - 视频-首尾帧  → FL2VA首尾帧视频.py（首帧桥接 + 单行星提示词；尾帧可选，缺省复用首帧为尾帧）
  - 视频-多参考  → Ref2VA多参考视频.py（--images = 角色参考图 + 背景图末张）

统一规则（详见 参考文档/分镜转视频.md 与 调用规范.md）：
  - --megapixels：默认 0.1（抽卡草稿）。mp<=0.2 不传 --seed（底层随机并回写顶部
    视频抽卡种子）；mp>=0.3 必须复用该段抽卡种子（读 段内 视频抽卡种子 传 --seed），
    绝不重新随机。
  - 底层把 视频抽卡种子 写到【顶部全局】字段；批量多段会互相覆盖 → 本执行器在每段
    跑完后立刻把该值【按段固化】到段内 视频抽卡种子，保证成品档精准复用（不串段）。
  - 成片 FINAL_VIDEO 回写 提示词生成.md 的 生成视频地址（幂等）。
  - 单段底层脚本失败 → 直接跳到下一段继续后续段（不取消 ComfyUI 任务、不清理队列；等待时间无限）
    （每段是独立视频，互不影响；与功能5「失败即终止整轮」不同）。

用法：
  python 生成视频.py --config "D:/proj/工作配置.yaml"
  python 生成视频.py --config "D:/proj/工作配置.yaml" --only 段2,段3
  python 生成视频.py --config "D:/proj/工作配置.yaml" --mp 0.6 --only 段2
  python 生成视频.py --config "D:/proj/工作配置.yaml" --frames first   # 首帧-only（默认，无视尾帧）
  python 生成视频.py --config "D:/proj/工作配置.yaml" --frames both    # 首+尾（尾帧存在时才用）
"""
import argparse
import atexit
import os
import re
import signal
import shutil
import subprocess
import sys

# 本文件与底层脚本同目录，路径自定位（不写死 J:/...）
SKILL_PY = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SKILL_PY)
import 生成首尾帧与背景 as g   # parse_storyboard / load_role_map / get_role_names / read_config / _unquote / _safe_name
import 项目路径 as pp
import Comfy客户端 as cc

DEFAULT_COMFY_URL = getattr(cc, "DEFAULT_URL", "http://127.0.0.1:8188")


def parse_dur(s):
    """'7s' / '7' / '' → float 秒；默认 6。"""
    s = (s or "").strip().rstrip("s").strip()
    try:
        return float(s) if s else 6.0
    except ValueError:
        return 6.0


def resolve_bg(fields, img_out, bg_dir):
    """背景图查找顺序：
    图片输出目录(img_out，功能5 生成的) → 背景资源所在目录(bg_dir，复用现成图)
    → 字段原值(raw path) → <场景ID>_背景.png 回退。
    注意：配置里的「背景资源所在目录」必须纳入查找，否则复用现成背景图（是否生成背景图片=否）
    的段会解析失败（正是 端到端验证 段1 整段被跳过的原因）。"""
    bg_name = g._unquote(fields.get("场景背景图"))
    scene_id = g._unquote(fields.get("场景ID")) or ""
    cands = []
    if bg_name:
        cands.append(os.path.join(img_out, bg_name))
        if bg_dir:
            cands.append(os.path.join(bg_dir, bg_name))
        cands.append(bg_name)  # raw path
    if scene_id:
        cands.append(os.path.join(img_out, f"{g._safe_name(scene_id)}_背景.png"))
        if bg_dir:
            cands.append(os.path.join(bg_dir, f"{g._safe_name(scene_id)}_背景.png"))
    for c in cands:
        if c and os.path.exists(c):
            return c
    return None


def run_fl2va(key, fields, img_out, vid_out, storyboard, config, comfy_url, comfy_output, mp, frames_mode="first"):
    first = g._unquote(fields.get("生成图片首帧地址"))
    if not first or not os.path.exists(first):
        print(f"[FL2VA][错误] {key} 首帧缺失：{first}")
        return False
    last = g._unquote(fields.get("生成图片尾帧地址"))
    # 首帧-only（默认）：无视尾帧，永远不传 --last-dir；仅 --frames both 且尾帧存在才用
    have_last = (frames_mode == "both") and bool(last) and os.path.exists(last)
    dur = parse_dur(g._unquote(fields.get("视频时长")))
    prompt = g._unquote(fields.get("生成视频的提示词")) or (fields.get("生成视频的提示词") or "").strip()
    fd = os.path.join(vid_out, f"_fl2va_{key}_first")
    os.makedirs(fd, exist_ok=True)
    shutil.copy(first, os.path.join(fd, os.path.basename(first)))
    pf = os.path.join(vid_out, f"_fl2va_{key}_prompt.txt")
    with open(pf, "w", encoding="utf-8") as f:
        f.write(prompt + "\n")
    prefix = f"video/MiniMax_H3_{key}"
    seed_arg = _seed_args(mp, storyboard, key)
    cmd = [sys.executable, os.path.join(SKILL_PY, "FL2VA首尾帧视频.py"),
           "--first-dir", fd]
    if have_last:
        ld = os.path.join(vid_out, f"_fl2va_{key}_last")
        os.makedirs(ld, exist_ok=True)
        shutil.copy(last, os.path.join(ld, os.path.basename(last)))
        cmd += ["--last-dir", ld]
    else:
        print(f"[FL2VA] {key} 无尾帧 → 首帧-only（底层复用首帧为尾帧）")
    cmd += ["--prompts-file", pf,
            "--megapixels", str(mp), "--duration", str(dur), "--aspect", "9:16",
            "--output-prefix", prefix, "--comfy-output", comfy_output,
            "--comfy-url", comfy_url, "--config", config, "--storyboard", storyboard] + seed_arg
    print(f"\n=== FL2VA {key} （{dur}s, mp={mp}, {'首帧-only' if not have_last else '首+尾'}）===")
    final = _run_and_capture_final(cmd)
    ok = _after_run(final, storyboard, key, mp, vid_out)
    return ok


def run_ref2va(key, fields, role_dir, role_map, bg_dir, img_out, vid_out, storyboard, config, comfy_url, comfy_output, mp):
    names = g.get_role_names(fields.get("使用角色"))
    if not names:
        print(f"[Ref2VA][错误] {key} 使用角色为空")
        return False
    imgs = []
    for nm in names:
        fn = role_map.get(nm)
        if not fn:
            print(f"[Ref2VA][错误] {key} 角色「{nm}」在 角色背景一览表 找不到参考图")
            return False
        p = os.path.join(role_dir, fn)
        if not os.path.exists(p):
            print(f"[Ref2VA][错误] {key} 参考图不存在：{p}")
            return False
        imgs.append(p)
    bg = resolve_bg(fields, img_out, bg_dir)
    if not bg:
        print(f"[Ref2VA][错误] {key} 背景图未解析到（场景背景图 / <场景ID>_背景.png 均无）")
        return False
    imgs.append(bg)  # 背景必须末张（防串脸）
    prompt = (fields.get("生成视频的提示词") or "").strip()
    if not prompt:
        print(f"[Ref2VA][错误] {key} 生成视频的提示词 为空")
        return False
    dur = parse_dur(g._unquote(fields.get("视频时长")))
    prefix = f"video/MiniMax_H3_{key}"
    seed_arg = _seed_args(mp, storyboard, key)
    cmd = [sys.executable, os.path.join(SKILL_PY, "Ref2VA多参考视频.py"),
           "--images", *imgs,
           "--prompt", prompt,
           "--megapixels", str(mp), "--duration", str(dur), "--aspect", "9:16",
           "--output-prefix", prefix, "--comfy-output", comfy_output,
           "--comfy-url", comfy_url, "--config", config, "--storyboard", storyboard] + seed_arg
    print(f"\n=== Ref2VA {key} （{dur}s, mp={mp}, 图={len(imgs)} 张，背景末张）===")
    final = _run_and_capture_final(cmd)
    ok = _after_run(final, storyboard, key, mp, vid_out)
    return ok


def _after_run(final, storyboard, key, mp, vid_out):
    """成片回写 + 抽卡档按段固化种子；返回是否成功。"""
    if not final:
        print(f"  ⚠️ 未捕获 FINAL_VIDEO（检查底层脚本输出）")
        return False
    # 拷贝成片进工程视频输出目录（SKILL.md §4.2.3：视频落视频输出目录）
    try:
        os.makedirs(vid_out, exist_ok=True)
        dest = os.path.join(vid_out, os.path.basename(final))
        if os.path.abspath(final) != os.path.abspath(dest):
            shutil.copy(final, dest)
            print(f"  📁 已拷贝成片到工程目录: {dest}")
        final = dest
    except Exception as e:
        print(f"  ⚠️ 拷贝成片到视频输出目录失败（保留 ComfyUI 路径）：{e}")
    pp.write_back_field(storyboard, key, "生成视频地址", final)
    print(f"  ✅ 回写 生成视频地址={final}")
    if mp <= 0.2:
        pinned = _pin_segment_seed(storyboard, key)
        if pinned:
            print(f"  ✅ 按段固化 视频抽卡种子={pinned}（防全局覆盖）")
    return True


def _run_and_capture_final(cmd):
    """运行底层脚本，返回 FINAL_VIDEO 绝对路径（无则 None）。失败返回 None。"""
    print("  $ " + " ".join(cmd[:6]) + " ...")
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                             errors="replace")
    except Exception as e:
        print(f"  [异常] {e}")
        return None
    final = None
    for line in (out.stdout or "").splitlines():
        if line.startswith("FINAL_VIDEO:"):
            final = line.split(":", 1)[1].strip()
        if line.startswith("SEED:"):
            print("  " + line)
    for line in (out.stdout or "").splitlines():
        if any(k in line for k in ("⭐", "✅", "⚠️", "[error]", "[warn]", "[run]")):
            print("  " + line)
    if out.returncode != 0:
        print(f"  [返回码 {out.returncode}] stderr 末 20 行：")
        for ln in (out.stderr or "").splitlines()[-20:]:
            print("    " + ln)
    return final


def _read_top_seed(storyboard):
    """读 提示词生成.md 顶部全局 视频抽卡种子（行首无缩进）。无则返回 None。"""
    try:
        txt = open(storyboard, encoding="utf-8").read()
    except OSError:
        return None
    m = re.search(r'^(?![\t ])视频抽卡种子\s*[:：]\s*"?(\d+)"?', txt, re.M)
    return m.group(1) if m else None


def _read_seg_seed(storyboard, key):
    """读 提示词生成.md 指定段内的 视频抽卡种子（按段固化的抽卡种子）。无则返回 None。"""
    try:
        txt = open(storyboard, encoding="utf-8").read()
    except OSError:
        return None
    if not hasattr(pp, "_seg_blocks"):
        return None
    for start, end, name in pp._seg_blocks(txt):
        if pp.seg_key(name) == key:
            m = re.search(r'(?m)^[ \t]{2,}视频抽卡种子\s*[:：]\s*"?(\d+)"?', txt[start:end])
            return m.group(1) if m else None
    return None


def _pin_segment_seed(storyboard, key):
    """底层 FL2VA/Ref2VA 把 视频抽卡种子 写到【顶部全局】字段；批量多段会互相覆盖，
    导致后续成品档只能拿到【最后一段】的抽卡种子。这里在读完后立刻把顶部值【按段】固化
    （独立于全局），保证每段保留自己的抽卡种子，供 >=0.3 档 --seed 精准复用。幂等。"""
    top = _read_top_seed(storyboard)
    if not top:
        return None
    try:
        pp.write_back_field(storyboard, key, "视频抽卡种子", top)
        return top
    except Exception as e:
        print(f"  [warn] 按段固化 视频抽卡种子 失败：{e}")
        return top


def _seed_args(mp, storyboard, key):
    """种子铁律（用户定义，单一概念）：
    mp<=0.2（抽卡档）= 不传 --seed，底层随机并回写顶部；
    mp>=0.3（成品档）= 传 --seed 复用该段抽卡档生成的随机数，绝不重新随机。
    优先读【段内】固化值，缺失再读顶部全局并告警（多段批量时可能非本段值）。"""
    if mp <= 0.2:
        return []
    seg = _read_seg_seed(storyboard, key)
    if seg:
        print(f"  [seed] {key} 成品档复用段内抽卡种子 --seed {seg}")
        return ["--seed", seg]
    top = _read_top_seed(storyboard)
    if top:
        print(f"  [warn] {key} 段内未固化种子，退用顶部 --seed {top}（可能非本段抽卡值）")
        return ["--seed", top]
    print(f"  [warn] {key} mp={mp}>0.2 但找不到抽卡种子（0.1 抽卡未跑？），退化为随机")
    return []


def main():
    ap = argparse.ArgumentParser(description="功能6/7 官方执行器：按路由生成视频并回写")
    ap.add_argument("--config", required=True, help="工作配置.yaml")
    ap.add_argument("--only", default=None, help="只处理指定段，逗号分隔（如 段2,段3）")
    ap.add_argument("--mp", type=float, default=0.1, help="megapixels（默认 0.1 抽卡；>=0.3 复用抽卡种子）")
    ap.add_argument("--frames", default="first", choices=["first", "both"],
                    help="FL2VA 帧模式：first=首帧-only（默认，无视尾帧）；both=有尾帧则用首+尾")
    ap.add_argument("--comfy-url", default=DEFAULT_COMFY_URL, help="ComfyUI 地址")
    ap.add_argument("--comfy-output", default=None, help="ComfyUI 输出根（默认自动探测）")
    args = ap.parse_args()

    # ── 运行互斥锁（用户硬规则：防止多个出图/出视频进程并发抢 GPU）──
    # 复用 生成首尾帧与背景 的同一把锁 .gen_run_lock，确保出图/出视频不会同时跑。
    g.acquire_run_lock()
    atexit.register(g.release_run_lock)

    def _on_sig(signum, _frame):
        try:
            name = signal.Signals(signum).name
        except Exception:
            name = str(signum)
        print(f"\n[信号] 收到 {name}，释放运行锁后退出（不清理 ComfyUI 队列）...")
        g.release_run_lock()
        sys.exit(1)

    try:
        signal.signal(signal.SIGTERM, _on_sig)
        signal.signal(signal.SIGINT, _on_sig)
    except (ValueError, OSError) as e:
        print(f"  [warn] 注册信号处理器失败（不影响锁释放）：{e}")

    cfg = g.read_config(args.config)
    base = os.path.dirname(os.path.abspath(args.config))
    storyboard = os.path.join(base, cfg.get("提示词生成文件", "提示词生成.md"))
    role_dir = os.path.abspath(cfg.get("角色资源所在目录", "")) if cfg.get("角色资源所在目录") else ""
    bg_dir = os.path.abspath(cfg.get("背景资源所在目录", "")) if cfg.get("背景资源所在目录") else ""
    img_out = os.path.abspath(cfg.get("图片输出目录", os.path.join(base, "图片")))
    vid_out = os.path.abspath(cfg.get("视频输出目录", os.path.join(base, "视频")))
    overview = os.path.join(base, cfg.get("角色背景一览表", "角色背景一览表.md"))
    role_map = g.load_role_map(overview)
    comfy_output = args.comfy_output or pp.resolve_comfy_output()
    os.makedirs(vid_out, exist_ok=True)

    # 起跑前先清一次显存：best-effort 释放上轮残留；注意 free_vram 无法回收孤儿显存（见 调用规范 §7.1）
    cc.free_vram(args.comfy_url)

    text = open(storyboard, encoding="utf-8").read()
    segs = g.parse_storyboard(text)
    only = set(s.strip() for s in (args.only or "").split(",") if s.strip())

    print(f"[执行器] 段数={len(segs)}；视频输出={vid_out}；背景目录={bg_dir or '(无)'}；mp={args.mp}；comfy={args.comfy_url}")
    failures = []
    for name, key, fields in segs:
        if only and key not in only:
            continue
        wf = g._unquote(fields.get("生成视频的工作流"))
        try:
            if wf == "视频-首尾帧":
                ok = run_fl2va(key, fields, img_out, vid_out, storyboard, args.config,
                               args.comfy_url, comfy_output, args.mp, args.frames)
            elif wf == "视频-多参考":
                ok = run_ref2va(key, fields, role_dir, role_map, bg_dir, img_out, vid_out, storyboard,
                                args.config, args.comfy_url, comfy_output, args.mp)
            else:
                print(f"[skip] {key} 生成视频的工作流={wf!r}（非视频类），跳过")
                continue
        except Exception as e:
            # 单段底层失败（用户要求）：直接跳到下一段，不取消 ComfyUI 任务、不清理队列
            print(f"  [失败] {key} 底层脚本异常：{type(e).__name__}: {e}")
            print(f"  [跳过] {key} 已跳过，直接继续后续段")
            failures.append(key)
            cc.free_vram(args.comfy_url)  # 异常后清显存，避免脏模型占卡拖累下段
            continue
        if not ok:
            # 单段失败（底层正常退出但产出不符）：直接跳过，不取消 ComfyUI 任务
            print(f"  [失败] {key} 底层脚本返回失败，已跳过，直接继续后续段")
            failures.append(key)

        # 每段结束（成功或失败）卸载该段模型，让下段从干净显存起跑（v2 原默认逻辑）
        cc.free_vram(args.comfy_url)

    print(f"\n[执行器] 结束。失败段={failures if failures else '无'}")


if __name__ == "__main__":
    main()
