import { 取, 发 } from '@/接口/请求'

export default {
  name: '模型配置页',
  data() {
    return {
      加载中: false,
      保存中: false,
      错误文字: '',
      表单: {
        大模型名称: '',
        LLM地址: '',
        LLM密钥: '',
        LLM模型名: '',
        ComfyUI地址: '',
        ComfyUI工作流目录: '',
        ComfyUI输出目录: ''
      }
    }
  },
  created() {
    this.拉配置()
  },
  methods: {
    async 拉配置() {
      this.加载中 = true
      this.错误文字 = ''
      try {
        const 数据 = await 取('/api/模型配置')
        this.表单 = {
          大模型名称: 数据.大模型名称,
          LLM地址: 数据.LLM地址,
          LLM密钥: 数据.LLM密钥,
          LLM模型名: 数据.LLM模型名,
          ComfyUI地址: 数据.ComfyUI地址,
          ComfyUI工作流目录: 数据.ComfyUI工作流目录,
          ComfyUI输出目录: 数据.ComfyUI输出目录
        }
      } catch (e) {
        this.错误文字 = e.message
        if (e.状态码 === 401) {
          this.$router.push('/登录')
        }
      } finally {
        this.加载中 = false
      }
    },
    async 保存() {
      this.保存中 = true
      this.错误文字 = ''
      try {
        await 发('/api/模型配置/保存', this.表单)
        this.$message.success('已保存')
      } catch (e) {
        this.错误文字 = e.message
        if (e.状态码 === 401) {
          this.$router.push('/登录')
        }
      } finally {
        this.保存中 = false
      }
    }
  }
}
