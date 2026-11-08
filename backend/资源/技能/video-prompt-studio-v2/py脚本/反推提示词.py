#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
反推提示词.py — 调用「反推_图生提示词」工作流，把角色图反推出可用生成词。

【传参说明】
  --image PATH    必填。角色图（本地路径即可，脚本会自动上传到 ComfyUI；不要手填 input/ 文件名）。
  --out TEXT      可选。反推结果写出到此文本文件；不填则直接打印到控制台。
  --prompt TEXT   可选。覆盖节点 84 (AILab_QwenVL) 的 custom_prompt，改用自定义反推指令
                  （例如要求模型按固定字段输出，供 重命名.py 结构化解析）。
  --comfy-url     ComfyUI 地址（默认 http://127.0.0.1:8188）。
  --timeout       等待秒数（默认 600）。

【用途】
  对应技能 ② 角色对比匹配「拿到角色图第一件事」：反推得到人物关键属性，
  写进 {角色名}_反推.txt，并据此回填「角色背景一览表」与重命名角色图（结构化重命名见 重命名.py / 图片重命名规范.md）。
  工作流默认已内置中英双语反推提示词；结构化重命名请改用 重命名.py（它会传结构化 prompt）。

示例：
  python 反推提示词.py --image char_01.png --out char_01_反推.txt
  python 反推提示词.py --image char_01.png --prompt "只输出：性别 年龄 服饰"
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import Comfy客户端 as cc

WF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "工作流")
WF_FILE = "反推_图生提示词_中英双语 (1).json"

# 反推节点：class_type = AILab_QwenVL，提示词字段 = custom_prompt
REVERSE_NODE_CLASS = "AILab_QwenVL"
REVERSE_PROMPT_PARAM = "custom_prompt"


def run_reverse(image_path, prompt=None, url=cc.DEFAULT_URL, timeout=600):
    """对单张图跑反推，返回提取到的文本字符串。

    prompt=None 时使用工作流默认提示词；传 prompt 则覆盖节点 84 的 custom_prompt。
    """
    wf_path = os.path.join(WF_DIR, WF_FILE)
    if not os.path.exists(wf_path):
        raise FileNotFoundError(f"工作流不存在: {wf_path}")

    api = cc.load_workflow(wf_path)
    cc.set_image(api, "LoadImage", image_path, 0, url=url)
    if prompt:
        cc.set_param(api, REVERSE_NODE_CLASS, REVERSE_PROMPT_PARAM, prompt)

    out = cc.run(api, url=url, timeout=timeout)

    # 汇总所有文本输出（ShowText 等）
    texts = []
    for nid, kinds in out.items():
        for k, v in kinds.items():
            if k.startswith("text"):
                texts.append(v if isinstance(v, str) else str(v))
    result = "\n".join(texts).strip()
    return result or str(out)  # 兜底：打印原始输出以排查


def main():
    ap = argparse.ArgumentParser(description="角色图反推提示词调用")
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--prompt", default=None,
                    help="覆盖反推提示词（节点 84 custom_prompt）。不填用工作流默认。")
    ap.add_argument("--comfy-url", default=cc.DEFAULT_URL)
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()

    print(f"[run] 反推提示词 image={args.image}...")
    result = run_reverse(args.image, prompt=args.prompt,
                         url=args.comfy_url, timeout=args.timeout)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(result + "\n")
        print(f"[ok] 已写出: {args.out}")
    else:
        print("---- 反推结果 ----")
        print(result)


if __name__ == "__main__":
    main()
