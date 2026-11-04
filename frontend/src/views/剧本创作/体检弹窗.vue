<template>
  <!-- 目录体检弹窗（从 分集目录.vue 拆出，模板/样式与拆分前完全一致） -->
  <el-dialog
    :visible.sync="弹窗显示"
    width="640px"
    top="8vh"
    :show-close="false"
    :close-on-click-modal="false">
    <div class="弹窗头">
      <div>
        <div class="弹窗标题">目录体检 · {{ 体检项.length }} 条</div>
        <div class="弹窗副题">全部是前端算出来的：情绪分、目标字数、点位、集数，没有一条靠 AI 猜</div>
      </div>
      <i class="el-icon-close 弹窗关闭" title="关闭" @click="弹窗显示 = false"></i>
    </div>
    <div class="弹窗体">
      <div v-if="!体检项.length" class="体检空">没查出问题：集数对得上、字数在目标 ±20% 内、没有连续低谷、钩子都兑了。</div>
      <div v-for="(项, 序) in 体检项" :key="'检' + 序" class="体检项">
        <span class="体检级" :class="项.级">{{ 项.级 === '红' ? '重' : '轻' }}</span>
        <div>
          <div class="体检类">{{ 项.类 }}</div>
          <div class="体检文">{{ 项.文 }}</div>
        </div>
      </div>
    </div>
    <div class="弹窗底">
      <div style="flex:1"></div>
      <el-button type="primary" @click="弹窗显示 = false">知道了</el-button>
    </div>
  </el-dialog>
</template>

<script>
// 纯展示弹窗：体检项全部由父组件（分集目录.vue）的 computed 算好后传入；
// 显隐由父组件持有（:显示.sync），这里用可写 computed 透传给 el-dialog。
export default {
  name: 'OutlineHealthDialog',
  props: {
    显示: { type: Boolean, default: false },
    体检项: { type: Array, default: function () { return [] } }
  },
  computed: {
    弹窗显示: {
      get() { return this.显示 },
      set(值) { this.$emit('update:显示', 值) }
    }
  }
}
</script>

<style scoped>
/* ---------- 弹窗骨架（与拆分前分集目录页相同） ---------- */
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

/* ---------- 体检弹窗 ---------- */
.体检空 { padding: 24px 0; text-align: center; font-size: 13px; color: var(--字弱); }
.体检项 {
  display: flex;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px dashed var(--描边);
}
.体检项:last-child { border-bottom: 0; }
.体检级 {
  flex: 0 0 auto;
  height: 20px;
  line-height: 18px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 11px;
  border: 1px solid;
}
.体检级.红 { color: #fca5a5; border-color: rgba(239, 68, 68, 0.45); background: rgba(239, 68, 68, 0.12); }
.体检级.黄 { color: #fcd34d; border-color: rgba(245, 158, 11, 0.45); background: rgba(245, 158, 11, 0.12); }
.体检类 { font-size: 13px; font-weight: 650; color: var(--字); }
.体检文 { font-size: 12.5px; line-height: 1.7; color: var(--字次); }
</style>
