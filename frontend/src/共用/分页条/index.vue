<template>
  <!-- 分页条：目录页 / 台账页共用一套页码。
       1000 集也不怕：页码自动折叠成「1 … 7 8 9 … 50」，并支持每页条数切换。 -->
  <div class="分页条" :class="{ 紧凑: 紧凑 }">
    <div class="计数">
      共 {{ 总数 }} {{ 单位 }}
      <span v-if="总数">· 当前第 {{ 起 }}–{{ 止 }} {{ 单位 }}</span>
    </div>
    <div class="右">
      <span class="页钮" :class="{ 禁用: 当前页 <= 1 }" @click="跳(当前页 - 1)">上一页</span>
      <span
        v-for="(页, 序) in 页码们"
        :key="'页' + 序"
        class="页钮"
        :class="{ 当: 页 === 当前页, 省略: 页 === '…' }"
        @click="跳(页)">{{ 页 }}</span>
      <span class="页钮" :class="{ 禁用: 当前页 >= 总页数 }" @click="跳(当前页 + 1)">下一页</span>

      <span class="隔"></span>
      <el-select v-if="!紧凑" :value="每页" size="mini" class="每页选" @change="改每页">
        <el-option
          v-for="数 in 每页选项"
          :key="'每' + 数"
          :label="数 + ' 条/页'"
          :value="数"></el-option>
      </el-select>

      <span v-if="!紧凑" class="跳转">
        跳至
        <input
          class="跳框"
          type="text"
          :value="跳值"
          @input="跳值 = $event.target.value"
          @keyup.enter="执行跳转()">
        页
      </span>
    </div>
  </div>
</template>

<script>
export default {
  name: '分页条',
  props: {
    总数: { type: Number, default: 0 },
    每页: { type: Number, default: 20 },
    当前页: { type: Number, default: 1 },
    每页选项: { type: Array, default: () => [10, 20, 50, 100] },
    单位: { type: String, default: '集' },
    // 紧凑模式：只留页码，去掉每页条数与跳页输入（侧栏等窄容器用）
    紧凑: { type: Boolean, default: false }
  },
  data() {
    return {
      跳值: ''
    }
  },
  computed: {
    总页数() {
      const 总 = Number(this.总数) || 0
      const 每 = Number(this.每页) || 1
      const 页 = Math.ceil(总 / 每)
      return 页 > 0 ? 页 : 1
    },
    起() {
      if (!this.总数) return 0
      return (this.当前页 - 1) * this.每页 + 1
    },
    止() {
      const 值 = this.当前页 * this.每页
      return 值 > this.总数 ? this.总数 : 值
    },
    // 页码折叠：总页数 ≤7 全显示，否则首尾固定、中间跟着当前页滑动
    页码们() {
      const 总 = this.总页数
      const 当 = this.当前页
      const 出 = []
      if (总 <= 7) {
        for (let i = 1; i <= 总; i++) 出.push(i)
        return 出
      }
      let 起 = Math.max(2, 当 - 2)
      let 止 = Math.min(总 - 1, 当 + 2)
      if (当 <= 4) { 起 = 2; 止 = 5 }
      if (当 >= 总 - 3) { 起 = 总 - 4; 止 = 总 - 1 }
      出.push(1)
      if (起 > 2) 出.push('…')
      for (let i = 起; i <= 止; i++) 出.push(i)
      if (止 < 总 - 1) 出.push('…')
      出.push(总)
      return 出
    }
  },
  methods: {
    跳(页) {
      if (页 === '…') return
      const 值 = Number(页)
      if (isNaN(值)) return
      if (值 < 1) return
      if (值 > this.总页数) return
      if (值 === this.当前页) return
      this.$emit('换页', 值)
    },
    改每页(值) {
      this.$emit('换每页', Number(值) || 20)
    },
    执行跳转() {
      const 值 = parseInt(String(this.跳值).replace(/[^0-9]/g, ''), 10)
      this.跳值 = ''
      if (!值) return
      this.跳(值)
    }
  }
}
</script>

<style src="./index.css"></style>
