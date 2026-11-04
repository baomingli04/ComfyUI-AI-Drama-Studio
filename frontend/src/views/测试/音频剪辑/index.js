// T11 音频剪辑：视频提取音频 + 音频选段/合并导出。
// 本页不落 task 表、不走任务队列：后端只提供两个同步接口（提取 / 合成），
// 编辑状态（片段列表）只在前端内存里，刷新即丢。
import { 发, 基础地址, 取令牌 } from '@/接口/请求'
import { 媒体地址 } from '@/接口/媒体'

const 波形宽 = 1200
const 波形高 = 170

export default {
  name: 'T11音频剪辑页',
  data() {
    return {
      上传地址: 基础地址 + '/api/上传',
      上传头: { Authorization: 'Bearer ' + 取令牌() },

      // 区1：视频提取音频
      视频路径: '',
      视频原名: '',
      输出格式: 'wav',
      输出采样率: 0,
      提取中: false,

      // 区2：音频剪辑
      音频路径: '',
      音频时长: 0,
      音频采样率: 0,
      音频声道: 0,
      载入中: false,
      有波形: false,
      片段列表: [],
      选区: null,
      播放中: false,
      播放位置: 0,

      // 导出
      导出模式: '合并',
      导出格式: 'wav',
      导出中: false,
      导出结果: []
    }
  },
  computed: {
    当前音频地址() {
      return this.音频路径 ? 媒体地址(this.音频路径) : ''
    },
    声道文字() {
      if (this.音频声道 === 1) return '单声道'
      if (this.音频声道 === 2) return '立体声'
      return this.音频声道 ? this.音频声道 + ' 声道' : '未知'
    }
  },
  mounted() {
    this.画波形()
  },
  methods: {
    格式化秒(值) {
      const 秒 = Number(值) || 0
      const 分 = Math.floor(秒 / 60)
      const 余 = 秒 - 分 * 60
      return (分 < 10 ? '0' + 分 : 分) + ':' + (余 < 10 ? '0' : '') + 余.toFixed(2)
    },
    报错(e) {
      const 位置 = e && e.file ? '（' + e.file + ':' + e.line + ' ' + e.func + '）' : ''
      this.$message.error(((e && e.message) || '请求失败') + 位置)
      if (e && e.状态码 === 401) {
        this.$router.push('/login')
      }
    },

    // ---- 上传 ----
    视频成功(响应) {
      if (响应 && 响应.ok) {
        this.视频路径 = 响应.路径
        this.视频原名 = 响应.原名 || 响应.路径
      } else {
        this.$message.error((响应 && 响应.error) || '上传失败')
      }
    },
    音频成功(响应) {
      if (响应 && 响应.ok) {
        this.载入音频(响应.路径, 0)
      } else {
        this.$message.error((响应 && 响应.error) || '上传失败')
      }
    },

    // ---- 区1：提取音频 ----
    async 提取音频() {
      if (!this.视频路径) {
        this.$message.warning('请先上传视频')
        return
      }
      this.提取中 = true
      try {
        const 数据 = await 发('/api/音频/提取', {
          视频路径: this.视频路径,
          格式: this.输出格式,
          采样率: this.输出采样率
        })
        this.音频采样率 = 数据.采样率
        this.音频声道 = 数据.声道
        this.$message.success('已提取音频，时长 ' + this.格式化秒(数据.时长))
        await this.载入音频(数据.路径, 数据.时长)
      } catch (e) {
        this.报错(e)
      } finally {
        this.提取中 = false
      }
    },

    // ---- 区2：载入音频 + 波形 ----
    async 载入音频(路径, 已知时长) {
      this.音频路径 = 路径
      this.音频时长 = 已知时长 || 0
      this.片段列表 = []
      this.导出结果 = []
      this.选区 = null
      this.播放位置 = 0
      this._音频缓冲 = null
      this.有波形 = false
      this.载入中 = true
      this.画波形()
      try {
        const 响应 = await fetch(媒体地址(路径))
        const 数据 = await 响应.arrayBuffer()
        this._音频缓冲 = await this.取音频上下文().decodeAudioData(数据)
        this.音频时长 = this._音频缓冲.duration
        this.有波形 = true
      } catch (e) {
        this.$message.error('波形解码失败（' + ((e && e.message) || '浏览器不支持该编码') + '），播放和导出仍可用')
      } finally {
        this.载入中 = false
        this.画波形()
      }
    },
    取音频上下文() {
      if (!this._音频上下文) {
        const 构造 = window.AudioContext || window.webkitAudioContext
        this._音频上下文 = new 构造()
      }
      return this._音频上下文
    },
    抽峰值(桶数) {
      const 缓冲 = this._音频缓冲
      if (!缓冲 || !桶数) return []
      const 数据 = 缓冲.getChannelData(0)
      const 每桶 = Math.max(1, Math.floor(数据.length / 桶数))
      const 峰值 = []
      for (let i = 0; i < 桶数; i++) {
        const 起 = i * 每桶
        const 止 = Math.min(起 + 每桶, 数据.length)
        let 最大 = 0
        for (let j = 起; j < 止; j++) {
          const 值 = Math.abs(数据[j])
          if (值 > 最大) 最大 = 值
        }
        峰值.push(最大)
      }
      return 峰值
    },
    时间转X(秒) {
      if (!this.音频时长) return 0
      return (秒 / this.音频时长) * 波形宽
    },
    X转时间(客户端X) {
      const 画布 = this.$refs.波形
      if (!画布 || !this.音频时长) return 0
      const 框 = 画布.getBoundingClientRect()
      const 比例 = (客户端X - 框.left) / (框.width || 1)
      return Math.min(Math.max(比例, 0), 1) * this.音频时长
    },
    画刻度(笔) {
      if (!this.音频时长) return
      笔.fillStyle = '#6b7280'
      笔.font = '11px sans-serif'
      for (let i = 0; i <= 4; i++) {
        const 秒 = (this.音频时长 * i) / 4
        const x = this.时间转X(秒)
        笔.fillText(this.格式化秒(秒), Math.min(x + 3, 波形宽 - 48), 波形高 - 5)
      }
    },
    画波形() {
      const 画布 = this.$refs.波形
      if (!画布) return
      const 笔 = 画布.getContext('2d')
      笔.clearRect(0, 0, 波形宽, 波形高)
      笔.fillStyle = '#0d1424'
      笔.fillRect(0, 0, 波形宽, 波形高)
      笔.strokeStyle = '#1e293b'
      笔.beginPath()
      笔.moveTo(0, 波形高 / 2)
      笔.lineTo(波形宽, 波形高 / 2)
      笔.stroke()

      if (!this._音频缓冲) {
        笔.fillStyle = '#6b7280'
        笔.font = '13px sans-serif'
        笔.fillText(this.载入中 ? '正在解码波形…' : '未载入音频', 12, 波形高 / 2 - 10)
        this.画刻度(笔)
        return
      }

      // 片段底色
      for (const 段 of this.片段列表) {
        const 起 = this.时间转X(段.开始)
        const 止 = this.时间转X(段.结束)
        笔.fillStyle = 'rgba(34, 197, 94, 0.16)'
        笔.fillRect(起, 0, Math.max(1, 止 - 起), 波形高)
      }

      // 波形柱：片段内绿色，片段外灰
      const 峰值 = this.抽峰值(波形宽)
      const 半高 = 波形高 / 2 - 14
      for (let i = 0; i < 峰值.length; i++) {
        const 高度 = Math.max(1, 峰值[i] * 半高)
        笔.fillStyle = this.在片段内(i / 波形宽) ? '#22c55e' : '#475569'
        笔.fillRect(i, 波形高 / 2 - 高度, 1, 高度 * 2)
      }

      // 拖拽中的选区
      if (this.选区) {
        const 起 = this.时间转X(Math.min(this.选区.开始, this.选区.结束))
        const 止 = this.时间转X(Math.max(this.选区.开始, this.选区.结束))
        笔.fillStyle = 'rgba(234, 179, 8, 0.22)'
        笔.fillRect(起, 0, Math.max(1, 止 - 起), 波形高)
        笔.strokeStyle = '#eab308'
        笔.strokeRect(起 + 0.5, 0.5, Math.max(1, 止 - 起), 波形高 - 1)
      }

      this.画刻度(笔)

      // 播放头
      const 头 = this.时间转X(this.播放位置)
      笔.strokeStyle = '#ffffff'
      笔.beginPath()
      笔.moveTo(头, 0)
      笔.lineTo(头, 波形高)
      笔.stroke()
    },
    在片段内(比例) {
      const 秒 = 比例 * this.音频时长
      return this.片段列表.some(段 => 秒 >= 段.开始 && 秒 <= 段.结束)
    },

    // ---- 选段 ----
    波形按下(事件) {
      if (!this.音频时长) return
      const 时间 = this.X转时间(事件.clientX)
      this.选区 = { 开始: 时间, 结束: 时间 }
      this._拖拽中 = true
      this.画波形()
    },
    波形移动(事件) {
      if (!this._拖拽中 || !this.选区) return
      this.选区.结束 = this.X转时间(事件.clientX)
      this.画波形()
    },
    波形抬起() {
      if (!this._拖拽中) return
      this._拖拽中 = false
      const 选区 = this.选区
      this.选区 = null
      if (!选区) return
      const 开始 = Math.min(选区.开始, 选区.结束)
      const 结束 = Math.max(选区.开始, 选区.结束)
      if (结束 - 开始 < 0.05) {
        this.画波形()
        return
      }
      this.片段列表.push({ 开始: Number(开始.toFixed(3)), 结束: Number(结束.toFixed(3)) })
      this.画波形()
    },
    删除片段(索引) {
      this.片段列表.splice(索引, 1)
      this.画波形()
    },
    上移片段(索引) {
      if (索引 <= 0) return
      const 段 = this.片段列表.splice(索引, 1)[0]
      this.片段列表.splice(索引 - 1, 0, 段)
      this.画波形()
    },
    下移片段(索引) {
      if (索引 >= this.片段列表.length - 1) return
      const 段 = this.片段列表.splice(索引, 1)[0]
      this.片段列表.splice(索引 + 1, 0, 段)
      this.画波形()
    },
    清空片段() {
      this.片段列表 = []
      this.画波形()
    },
    片段改了() {
      this.画波形()
    },

    // ---- 播放 / 试听 ----
    音频元素() {
      return this.$refs.音频
    },
    切换播放() {
      const 元素 = this.音频元素()
      if (!元素 || !this.音频路径) return
      if (this.播放中) {
        元素.pause()
        this.播放中 = false
        this._试听终点 = 0
        this._连播中 = false
        return
      }
      this._试听终点 = 0
      this._连播中 = false
      if (元素.currentTime >= this.音频时长 - 0.05) 元素.currentTime = 0
      元素.play()
      this.播放中 = true
    },
    回到开头() {
      const 元素 = this.音频元素()
      if (!元素) return
      元素.currentTime = 0
      this.播放位置 = 0
      this.画波形()
    },
    试听片段(段) {
      const 元素 = this.音频元素()
      if (!元素) return
      this._连播中 = false
      元素.currentTime = 段.开始
      this._试听终点 = 段.结束
      元素.play()
      this.播放中 = true
    },
    连播片段() {
      if (!this.片段列表.length) return
      this._连播中 = true
      this._连播索引 = 0
      this.播连播段()
    },
    播连播段() {
      const 元素 = this.音频元素()
      const 段 = this.片段列表[this._连播索引]
      if (!元素 || !段) {
        if (元素) 元素.pause()
        this.播放中 = false
        this._连播中 = false
        this._试听终点 = 0
        return
      }
      元素.currentTime = 段.开始
      this._试听终点 = 段.结束
      元素.play()
      this.播放中 = true
    },
    时间更新() {
      const 元素 = this.音频元素()
      if (!元素) return
      this.播放位置 = 元素.currentTime
      if (this._试听终点 && 元素.currentTime >= this._试听终点) {
        if (this._连播中) {
          this._连播索引 += 1
          this.播连播段()
        } else {
          元素.pause()
          this.播放中 = false
          this._试听终点 = 0
        }
      }
      this.画波形()
    },

    // ---- 导出 ----
    async 导出() {
      if (!this.音频路径) {
        this.$message.warning('请先载入音频')
        return
      }
      if (!this.片段列表.length) {
        this.$message.warning('请先在波形上拖拽选段')
        return
      }
      const 片段 = this.片段列表.map(段 => ({ 开始: 段.开始, 结束: 段.结束 }))
      this.导出中 = true
      try {
        const 数据 = await 发('/api/音频/合成', {
          源路径: this.音频路径,
          片段列表: 片段,
          模式: this.导出模式,
          格式: this.导出格式
        })
        if (this.导出模式 === '合并') {
          this.导出结果 = [{ 名称: '合并结果.' + this.导出格式, 路径: 数据.路径, 地址: 媒体地址(数据.路径) }]
        } else {
          this.导出结果 = (数据.路径列表 || []).map((路径, i) => ({
            名称: '片段' + (i + 1) + '.' + this.导出格式,
            路径: 路径,
            地址: 媒体地址(路径)
          }))
        }
        this.$message.success('导出完成，共 ' + this.导出结果.length + ' 个文件')
      } catch (e) {
        this.报错(e)
      } finally {
        this.导出中 = false
      }
    }
  }
}
