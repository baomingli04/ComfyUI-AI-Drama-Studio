# -*- coding: utf-8 -*-
"""极简 CDP 客户端：仅用标准库，连接本机 Chrome 调试端口（127.0.0.1:9223）。"""
import json
import os
import socket
import struct
import base64
import urllib.parse
import urllib.request

HOST, PORT = '127.0.0.1', 9223
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def http_json(path, method=None):
    url = 'http://%s:%d%s' % (HOST, PORT, path)
    if method:
        req = urllib.request.Request(url, method=method)
    else:
        req = url
    with _opener.open(req, timeout=15) as r:
        return json.loads(r.read().decode('utf-8'))


def 新标签(url='about:blank'):
    p = '/json/new?' + urllib.parse.quote(url, safe=':/?&=#')
    try:
        return http_json(p, method='PUT')['id']
    except Exception:
        return http_json(p)['id']


def 关标签(tid):
    try:
        http_json('/json/close/' + tid)
    except Exception:
        pass


class WS:
    def __init__(self, ws_url, timeout=20):
        assert ws_url.startswith('ws://')
        rest = ws_url[5:]
        hostport, _, path = rest.partition('/')
        host, _, port = hostport.partition(':')
        self.s = socket.create_connection((host, int(port or 80)), timeout=timeout)
        self.s.settimeout(timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (
            'GET /%s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\n'
            'Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n'
            'Sec-WebSocket-Version: 13\r\n\r\n' % (path, hostport, key)
        )
        self.s.sendall(req.encode())
        buf = b''
        while b'\r\n\r\n' not in buf:
            buf += self.s.recv(4096)
        self.buf = buf.split(b'\r\n\r\n', 1)[1]

    def _recv(self, n):
        while len(self.buf) < n:
            d = self.s.recv(65536)
            if not d:
                raise IOError('closed')
            self.buf += d
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def _帧头(self):
        b0, b1 = struct.unpack('!BB', self._recv(2))
        ln = b1 & 0x7F
        if ln == 126:
            ln = struct.unpack('!H', self._recv(2))[0]
        elif ln == 127:
            ln = struct.unpack('!Q', self._recv(8))[0]
        return b0, ln

    def 收(self):
        while True:
            b0, ln = self._帧头()
            payload = self._recv(ln)
            op = b0 & 0x0F
            if op == 1:
                return payload.decode('utf-8', 'replace')
            if op == 8:
                raise IOError('closed')
            if op == 9:
                self.发(payload, op=10)

    def 发(self, payload, op=1):
        if isinstance(payload, str):
            payload = payload.encode('utf-8')
        head = struct.pack('!BB', 0x80 | op, 0x80 | 127)
        head += struct.pack('!Q', len(payload))
        mask = os.urandom(4)
        self.s.sendall(head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

    def 关(self):
        try:
            self.s.close()
        except Exception:
            pass


class 会话:
    def __init__(self, ws_url, timeout=20):
        self.ws = WS(ws_url, timeout)
        self.id = 0

    def 命令(self, 方法, **参数):
        self.id += 1
        self.ws.发(json.dumps({'id': self.id, 'method': 方法, 'params': 参数}))
        while True:
            msg = json.loads(self.ws.收())
            if msg.get('id') == self.id:
                if 'error' in msg:
                    raise RuntimeError(msg['error'])
                return msg.get('result', {})

    def 求值(self, 表达式):
        r = self.命令('Runtime.evaluate', expression=表达式,
                     returnByValue=True, awaitPromise=True)
        if 'exceptionDetails' in r:
            return {'__异常__': str(r['exceptionDetails'])}
        return r.get('result', {}).get('value')

    def 截图(self, 文件):
        r = self.命令('Page.captureScreenshot', format='png')
        with open(文件, 'wb') as f:
            f.write(base64.b64decode(r['data']))
        return 文件

    def 关(self):
        self.ws.关()


def 连接(标签id=None, url=None, timeout=25):
    if 标签id is None:
        标签id = 新标签(url or 'about:blank')
    for t in http_json('/json/list'):
        if t['id'] == 标签id and t.get('webSocketDebuggerUrl'):
            s = 会话(t['webSocketDebuggerUrl'], timeout)
            s.标签id = 标签id
            return s
    raise RuntimeError('找不到标签 ' + 标签id)
