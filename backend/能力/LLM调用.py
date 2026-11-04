# -*- coding: utf-8 -*-
"""LLM 调用：读模型配置的 LLM地址/模型名/密钥，OpenAI 兼容 chat/completions。"""
import base64
import json
import urllib.error
import urllib.request


# 内网直连：本机环境变量可能带 HTTP_PROXY（沙箱代理），访问 Comfy/LLM 必须绕开，
# 否则代理会间歇性掐断连接（10053/10054/503），任务被误判中断。
直连opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

from 能力.提交并等待 import 补协议, 取模型配置


def 调用LLM(消息列表, 超时=300):
    """消息列表 = [{'role':..., 'content':...}]，返回模型回复文本。"""
    配置 = 取模型配置()
    地址 = 补协议(配置.LLM地址)
    if not 地址:
        raise RuntimeError('模型配置未填写 LLM地址，请先到「模型配置」页保存。')
    模型名 = 配置.LLM模型名 or 配置.大模型名称 or ''
    body = {'model': 模型名, 'messages': 消息列表, 'stream': False}
    头 = {'Content-Type': 'application/json'}
    if 配置.LLM密钥:
        头['Authorization'] = 'Bearer ' + 配置.LLM密钥
    req = urllib.request.Request(
        地址 + '/v1/chat/completions',
        data=json.dumps(body).encode('utf-8'), headers=头)
    try:
        with 直连opener.open(req, timeout=超时) as resp:
            数据 = json.loads(resp.read().decode('utf-8', 'replace'))
    except urllib.error.HTTPError as e:
        明细 = e.read().decode('utf-8', 'replace')[:300]
        raise RuntimeError('LLM 返回 HTTP %s：%s' % (e.code, 明细))
    try:
        return 数据['choices'][0]['message']['content']
    except (KeyError, IndexError):
        raise RuntimeError('LLM 返回格式异常：%s' % json.dumps(数据, ensure_ascii=False)[:300])


def 图片转数据URI(文件路径):
    后缀 = 文件路径.rsplit('.', 1)[-1].lower() or 'png'
    with open(文件路径, 'rb') as f:
        数据 = f.read()
    return 'data:image/%s;base64,%s' % (后缀, base64.b64encode(数据).decode('ascii'))
