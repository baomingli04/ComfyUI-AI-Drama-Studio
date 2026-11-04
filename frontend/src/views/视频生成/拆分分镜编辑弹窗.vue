<template>
  <!-- 编辑分镜弹窗（自「拆分分镜.vue」纯拆出：模板/表单/保存逻辑/样式与原实现一致） -->
  <el-dialog title="编辑分镜" :visible.sync="弹窗显示" width="620px" append-to-body>
    <div v-if="缓冲" class="编辑单">
      <div class="编格">
        <label class="编项"><span class="编名">镜号</span><el-input :value="缓冲.镜号" size="small" disabled /></label>
        <label class="编项"><span class="编名">所属场次</span><el-input v-model="缓冲.场次" size="small" /></label>
      </div>
      <div class="编格 编格三">
        <label class="编项"><span class="编名">景别</span><el-input v-model="缓冲.景别" size="small" /></label>
        <label class="编项"><span class="编名">运镜</span><el-input v-model="缓冲.运镜" size="small" /></label>
        <label class="编项"><span class="编名">时长（如 3s）</span><el-input v-model="缓冲.时长" size="small" /></label>
      </div>
      <label class="编项"><span class="编名">画面描述</span><el-input v-model="缓冲.画面" type="textarea" :rows="4" /></label>
      <label class="编项"><span class="编名">台词（无台词写「（无）」或留空）</span><el-input v-model="缓冲.台词" size="small" /></label>
    </div>
    <div slot="footer">
      <el-button size="small" @click="取消()">取消</el-button>
      <el-button size="small" type="primary" :loading="存编辑中" @click="保存编辑()">保存</el-button>
    </div>
  </el-dialog>
</template>

<script>
/* 编辑分镜弹窗组件：表单编辑 + 即时落库保存（原「拆分分镜.vue」内嵌弹窗拆出） */
export default {
  name: 'ShotSplitEditDialog',
  props: {
    /* 显隐由父组件控制（:显示.sync） */
    显示: { type: Boolean, default: false },
    /* 编辑缓冲对象（父组件 打开编辑 时构造；表单 v-model 直接改其字段，与原实现一致） */
    缓冲: { type: Object, default: null },
    /* 分镜列表（保存时按镜号替换生成新列表，子组件只读使用） */
    分镜列表: { type: Array, default: function () { return [] } },
    /* 落库方法（父组件 存全库；Vue 会把 methods 绑定到父实例，this 指向不变） */
    存全库: { type: Function, required: true }
  },
  data() {
    return {
      存编辑中: false
    }
  },
  computed: {
    /* :visible.sync 需要可写值，用计算属性转发为 update:显示 事件 */
    弹窗显示: {
      get() { return this.显示 },
      set(值) { this.$emit('update:显示', 值) }
    }
  },
  methods: {
    取消() {
      this.$emit('update:显示', false)
    },
    async 保存编辑() {
      const 页 = this
      const 缓 = 页.缓冲
      if (!缓 || !缓.画面.trim()) {
        页.$message.warning('画面描述不能为空')
        return
      }
      页.存编辑中 = true
      try {
        const 新列表 = 页.分镜列表.map(function (镜) {
          if (镜.镜号 !== 缓.镜号) return 镜
          return Object.assign({}, 镜, {
            场次: 缓.场次 || 镜.场次, 景别: 缓.景别, 运镜: 缓.运镜,
            画面: 缓.画面, 台词: 缓.台词 || '（无）', 时长: 缓.时长
          })
        })
        await 页.存全库(新列表)
        页.$emit('已保存', 新列表)
        页.$emit('update:显示', false)
        页.$message.success('已保存 ' + 缓.镜号 + '（已落库）')
      } catch (e) {
        页.$message.error('保存失败：' + ((e && e.message) || e))
      }
      页.存编辑中 = false
    }
  }
}
</script>

<style scoped>
/* ---- 编辑弹窗 ---- */
.编辑单 { display: flex; flex-direction: column; gap: 12px; }
.编项 { display: flex; flex-direction: column; gap: 4px; }
.编名 { font-size: 12px; color: var(--字弱); }
.编格 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.编格三 { grid-template-columns: 1fr 1fr 1fr; }
</style>
