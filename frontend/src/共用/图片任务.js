// 图片类任务统一链路：提交任务 → 轮询到终态 → 返回任务行。
// 与 /test 各图片任务页同一条链路（任务进 task 表，有记录可查日志）。
// 适用：图片解析（回传 回复 文本）、多图编辑多人合并版 / 动漫转真人 / 三图编辑一致版（回传 产物图片）。
import { 发, 取 } from '@/接口/请求'

const 终态们 = ['成功', '失败', '中断', '已取消']

/* 选项 { 类型, 参数:{...任务载荷}, 轮询间隔, 最长等待 } → Promise<任务行> */
export function 提交图片任务(选项) {
  const 选项值 = 选项 || {}
  const 类型 = 选项值.类型
  const 参数 = 选项值.参数 || {}
  const 轮询间隔 = 选项值.轮询间隔 || 3000
  const 最长等待 = 选项值.最长等待 || 900000
  if (!类型) return Promise.reject(new Error('缺少任务类型'))
  let 任务id = 0
  const 开始时刻 = Date.now()
  return 发('/api/任务/提交', Object.assign({ 类型: 类型 }, 参数))
    .then(function (数据) {
      任务id = (数据 && 数据.id) || 0
      if (!任务id) throw new Error('任务提交失败：后端没有返回任务 id')
      return 等待任务(类型, 任务id, 开始时刻, 轮询间隔, 最长等待)
    })
}

function 等待任务(类型, 任务id, 开始时刻, 间隔, 最长) {
  return 取('/api/任务列表?类型=' + encodeURIComponent(类型) + '&条数=100')
    .then(function (数据) {
      const 行们 = (数据 && 数据.列表) || []
      let 行 = null
      for (let i = 0; i < 行们.length; i++) {
        if (行们[i].id === 任务id) { 行 = 行们[i]; break }
      }
      if (行 && 终态们.indexOf(行.状态) >= 0) {
        if (行.状态 !== '成功') {
          throw new Error('任务' + 行.状态 + '（任务 ' + 任务id + '）' + (行.错误信息 ? '：' + 行.错误信息 : ''))
        }
        return 行
      }
      if (Date.now() - 开始时刻 > 最长) {
        throw new Error('任务超时未完成（任务 ' + 任务id + '），可稍后在测试台任务列表查看结果')
      }
      return new Promise(function (解决) { setTimeout(解决, 间隔) }).then(function () {
        return 等待任务(类型, 任务id, 开始时刻, 间隔, 最长)
      })
    })
}
