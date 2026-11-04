// 统一走任务链路的 AI 文本生成：提交「文本回复」任务 → 轮询到终态 → 返回回复文本。
// 与 /test/t1-text 同一条链路：任务进 task 表有记录、多个 AI 内容排队顺序执行。
// 正向提示词 = 本次需求；系统提示词 = 页面引导规则/技能引导。
import { 发, 取 } from '@/接口/请求'

const 终态们 = ['成功', '失败', '中断', '已取消']

export function 提交AI任务(选项) {
  const 选项值 = 选项 || {}
  const 正向 = (选项值.正向 || '').trim()
  const 系统 = 选项值.系统 || ''
  const 技能id = 选项值.技能id || ''
  const 轮询间隔 = 选项值.轮询间隔 || 2000
  const 最长等待 = 选项值.最长等待 || 600000
  // 可选进度回调：生成中后端把已生成部分文本写回 task.回复，
  // 每次轮询都会带着它回调 进度回调(部分文本, 任务id)，页面可实时显示进度
  const 进度回调 = 选项值.进度回调 || null
  if (!正向) return Promise.reject(new Error('生成需求为空'))
  let 任务id = 0
  const 开始时刻 = Date.now()
  const 载荷 = { 类型: '文本回复', 正向提示词: 正向, 系统提示词: 系统 }
  // 带技能 id：后端把该技能 SKILL.md 规范注入系统提示词（口径同 提示词/扩写）
  if (技能id) 载荷.技能id = 技能id
  return 发('/api/任务/提交', 载荷)
    .then(function (数据) {
      任务id = (数据 && 数据.id) || 0
      if (!任务id) throw new Error('任务提交失败：后端没有返回任务 id')
      return 等待任务(任务id, 开始时刻, 轮询间隔, 最长等待, 进度回调)
    })
}

function 等待任务(任务id, 开始时刻, 间隔, 最长, 进度回调) {
  return 取('/api/任务列表?类型=' + encodeURIComponent('文本回复') + '&条数=100')
    .then(function (数据) {
      const 行们 = (数据 && 数据.列表) || []
      let 行 = null
      for (let i = 0; i < 行们.length; i++) {
        if (行们[i].id === 任务id) { 行 = 行们[i]; break }
      }
      if (行 && 进度回调 && 行.回复 && 终态们.indexOf(行.状态) < 0) {
        try { 进度回调(行.回复, 任务id) } catch (e) { /* 进度回调不许打断等待 */ }
      }
      if (行 && 终态们.indexOf(行.状态) >= 0) {
        if (行.状态 === '成功') return 行.回复 || ''
        throw new Error('AI 任务' + 行.状态 + '（任务 ' + 任务id + '）' + (行.错误信息 ? '：' + 行.错误信息 : ''))
      }
      if (Date.now() - 开始时刻 > 最长) {
        throw new Error('AI 任务超时未完成（任务 ' + 任务id + '），可稍后在测试台任务列表查看结果')
      }
      return new Promise(function (解决) { setTimeout(解决, 间隔) }).then(function () {
        return 等待任务(任务id, 开始时刻, 间隔, 最长, 进度回调)
      })
    })
}
