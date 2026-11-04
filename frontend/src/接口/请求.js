// 统一请求封装：只写 主机:端口 的配置 + 协议拼接，见 docs/04 规范

const 应用配置 = window.__APP_CONFIG__ || {}
const 后端主机 = 应用配置.后端 || '127.0.0.1:8001'
export const 基础地址 = window.location.protocol + '//' + 后端主机

export function 取令牌() {
  return localStorage.getItem('token') || ''
}

export function 存令牌(令牌) {
  localStorage.setItem('token', 令牌)
}

export function 清令牌() {
  localStorage.removeItem('token')
  localStorage.removeItem('用户名')
  localStorage.removeItem('昵称')
}

// 请求(路径, { 方法, 数据 })
// 成功：返回后端 JSON（形如 { ok: true, ... }）
// 失败：抛出 Error，message 为后端 error 文案，并附带 file/line/func
export async function 请求(路径, 选项) {
  const 选项值 = 选项 || {}
  const 方法 = 选项值.方法 || 'GET'
  const 头 = { 'Content-Type': 'application/json' }
  const 令牌 = 取令牌()
  if (令牌) {
    头['Authorization'] = 'Bearer ' + 令牌
  }

  let 响应
  try {
    响应 = await fetch(基础地址 + 路径, {
      method: 方法,
      headers: 头,
      body: 选项值.数据 ? JSON.stringify(选项值.数据) : undefined
    })
  } catch (e) {
    const 网络错误 = new Error('后端连不上：' + 基础地址 + 路径)
    网络错误.状态码 = 0
    throw 网络错误
  }

  let 数据 = null
  try {
    数据 = await 响应.json()
  } catch (e) {
    数据 = null
  }

  if (!响应.ok || (数据 && 数据.ok === false)) {
    const 报错 = new Error((数据 && 数据.error) || ('请求失败（HTTP ' + 响应.status + '）'))
    报错.状态码 = 响应.status
    if (数据) {
      报错.file = 数据.file
      报错.line = 数据.line
      报错.func = 数据.func
    }
    if (响应.status === 401) {
      清令牌()
    }
    throw 报错
  }

  return 数据
}

export function 取(路径) {
  return 请求(路径, { 方法: 'GET' })
}

export function 发(路径, 数据) {
  return 请求(路径, { 方法: 'POST', 数据 })
}
