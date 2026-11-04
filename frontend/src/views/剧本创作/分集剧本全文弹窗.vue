<template>
  <!-- 全文弹窗（已从 分集剧本.vue 拆分为独立组件，逻辑与视觉保持不变） -->
  <el-dialog
    :visible="显示"
    @update:visible="$emit('update:显示', $event)"
    width="820px"
    top="6vh"
    :show-close="false"
    :close-on-click-modal="false">
    <div class="弹窗头">
      <div>
        <div class="弹窗标题">第 {{ 当前集 }} 集全文</div>
        <div class="弹窗副题">正文 + 五个档案块，可直接整段复制走</div>
      </div>
      <i class="el-icon-close 弹窗关闭" title="关闭" @click="$emit('update:显示', false)"></i>
    </div>
    <div class="弹窗体">
      <pre class="原文 高">{{ 全文内容 }}</pre>
    </div>
    <div class="弹窗底">
      <div style="flex:1"></div>
      <el-button @click="$emit('update:显示', false)">关闭</el-button>
      <el-button type="primary" @click="复制全文()">复制全文</el-button>
    </div>
  </el-dialog>
</template>

<script>
import { 拼全文 } from '@/共用/剧本档案'
import { 复制到剪贴板 } from '@/共用/复制文本'

// 全文弹窗（分集剧本页专用）。显隐由父组件 全文显示 字段控制（:显示.sync）。
export default {
  name: 'EpisodeFulltextDialog',
  props: {
    显示: { type: Boolean, default: false },
    当前集: { type: Number, default: 1 },
    当前剧: { type: Object, default: null }
  },
  computed: {
    全文内容() {
      return 拼全文(this.当前剧)
    }
  },
  methods: {
    async 复制全文() {
      const 成功 = await 复制到剪贴板(this.全文内容)
      this.$message[成功 ? 'success' : 'error'](成功 ? '已复制全文' : '复制失败，请手动选择复制')
    }
  }
}
</script>

<style scoped>
/* ---- 弹窗（全文专用部分） ---- */
.弹窗头 {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding-bottom: 14px; border-bottom: 1px solid var(--描边);
}
.弹窗标题 { font-size: 16px; font-weight: 700; color: var(--字); }
.弹窗副题 { font-size: 12px; color: var(--字弱); margin-top: 4px; }
.弹窗关闭 { cursor: pointer; color: var(--字弱); font-size: 16px; }
.弹窗体 { padding: 16px 0 4px; max-height: 64vh; overflow-y: auto; }
.弹窗底 {
  display: flex; align-items: center; justify-content: flex-end; gap: 12px;
  padding-top: 14px; border-top: 1px solid var(--描边);
}
.原文 {
  margin: 0;
  max-height: 320px;
  overflow: auto;
  padding: 12px;
  border-radius: 8px;
  background: var(--卡片二);
  font-family: inherit;
  font-size: 12px;
  line-height: 1.9;
  color: var(--字次);
  white-space: pre-wrap;
  word-break: break-word;
}
.原文.高 { max-height: 64vh; font-size: 13px; }
</style>
