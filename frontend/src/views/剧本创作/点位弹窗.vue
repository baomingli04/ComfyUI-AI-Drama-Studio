<template>
  <!-- 打点位弹窗（从 分集目录.vue 拆出，模板/样式与拆分前完全一致） -->
  <el-dialog
    :visible.sync="弹窗显示"
    width="560px"
    top="10vh"
    :show-close="false"
    :close-on-click-modal="false">
    <div class="弹窗头">
      <div>
        <div class="弹窗标题">EP{{ 点位对象 ? 点位对象.集 : '' }} · 钩子点位</div>
        <div class="弹窗副题">这里打一条，上面的台账和「未回收」立刻跟着变</div>
      </div>
      <i class="el-icon-close 弹窗关闭" title="关闭" @click="弹窗显示 = false"></i>
    </div>
    <div class="弹窗体">
      <div v-if="点位对象 && (点位对象.点位 || []).length" class="已有点">
        <div v-for="(点, 序) in 点位对象.点位" :key="'已' + 序" class="已有点行">
          <span class="点" :class="'点-' + 点.类型">{{ 点.类型 }} {{ 点.点 }}</span>
          <span class="已有点文">{{ 点.内容 }}</span>
          <el-button type="text" size="mini" class="删点" @click="删点位(序)">删除</el-button>
        </div>
      </div>
      <div v-else class="已有点 空">这一集还没有点位</div>

      <el-form label-width="64px" size="small" style="margin-top:14px">
        <div class="表单两列">
          <el-form-item label="动作">
            <el-select v-model="点位草稿.类型" style="width:130px">
              <el-option v-for="类 in 钩子类型们" :key="类" :label="类" :value="类"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="点位">
            <el-select v-model="点位草稿.点" style="width:110px">
              <el-option label="P01" value="P01"></el-option>
              <el-option label="P02" value="P02"></el-option>
              <el-option label="P03" value="P03"></el-option>
              <el-option label="P04" value="P04"></el-option>
              <el-option label="P05" value="P05"></el-option>
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="内容">
          <el-input v-model="点位草稿.内容" maxlength="40" placeholder="一句话，例如：宣布小组积分制"></el-input>
        </el-form-item>
      </el-form>
    </div>
    <div class="弹窗底">
      <div style="flex:1"></div>
      <el-button @click="弹窗显示 = false">关闭</el-button>
      <el-button type="primary" @click="保存点位()">加一条</el-button>
    </div>
  </el-dialog>
</template>

<script>
import { 钩子类型们 } from '@/共用/节奏工具'

// 打点位弹窗（从 分集目录.vue 拆出）。
//  - 点位草稿 是弹窗专属数据，搬进本组件；每次打开（显示 变 true）重置，与拆分前
//    父组件 打开点位() 里先重置草稿再开弹窗的行为一致；
//  - 点位对象 经 prop 传入（就是父组件 目录表 里的那一条集卡对象），加/删点位直接改它，
//    页面台账等派生数据随之响应；
//  - 落库（存全库）与其成功/失败提示留在父组件，见父组件的 点位保存落库 / 点位删除落库。
export default {
  name: 'OutlineHookPointDialog',
  props: {
    显示: { type: Boolean, default: false },
    点位对象: { type: Object, default: null }
  },
  data() {
    return {
      点位草稿: { 类型: '埋', 点: 'P01', 内容: '' },
      钩子类型们: 钩子类型们
    }
  },
  watch: {
    显示(值) {
      if (值) this.点位草稿 = { 类型: '埋', 点: 'P01', 内容: '' }
    }
  },
  computed: {
    弹窗显示: {
      get() { return this.显示 },
      set(值) { this.$emit('update:显示', 值) }
    }
  },
  methods: {
    保存点位() {
      const 集 = this.点位对象
      if (!集) return
      const 文 = String(this.点位草稿.内容 || '').trim()
      if (!文) {
        this.$message.warning('写一句这个点位是什么')
        return
      }
      if (!集.点位) this.$set(集, '点位', [])
      集.点位.push({ 类型: this.点位草稿.类型, 点: this.点位草稿.点, 内容: 文 })
      this.点位草稿.内容 = ''
      this.$emit('保存')
    },
    删点位(序) {
      const 集 = this.点位对象
      if (!集 || !集.点位) return
      集.点位.splice(序, 1)
      this.$emit('删除')
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

.表单两列 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 16px;
}

/* ---------- 点位弹窗 ---------- */
.已有点 {
  background: var(--卡片二);
  border: 1px solid var(--描边);
  border-radius: 8px;
  padding: 8px 10px;
}
.已有点.空 { font-size: 12px; color: var(--字弱); text-align: center; padding: 14px 10px; }
.已有点行 { display: flex; align-items: center; gap: 8px; padding: 3px 0; }
.已有点文 { flex: 1; min-width: 0; font-size: 12px; color: var(--字次); }
.删点 { color: #ef4444 !important; }
.已有点行 .点 {
  font-size: 10px;
  line-height: 16px;
  border-radius: 4px;
  padding: 0 6px;
  border: 1px solid;
  font-family: Consolas, 'Courier New', monospace;
}
.已有点行 .点-埋 { color: #93c5fd; border-color: rgba(96, 165, 250, 0.4); background: rgba(96, 165, 250, 0.12); }
.已有点行 .点-露 { color: #a5b4fc; border-color: rgba(129, 140, 248, 0.4); background: rgba(129, 140, 248, 0.12); }
.已有点行 .点-压 { color: #fca5a5; border-color: rgba(239, 68, 68, 0.4); background: rgba(239, 68, 68, 0.12); }
.已有点行 .点-兑 { color: #86efac; border-color: rgba(34, 197, 94, 0.4); background: rgba(34, 197, 94, 0.12); }
.已有点行 .点-假兑 { color: #fcd34d; border-color: rgba(245, 158, 11, 0.45); background: rgba(245, 158, 11, 0.12); }
.已有点行 .点-回收 { color: #5eead4; border-color: rgba(45, 212, 191, 0.4); background: rgba(45, 212, 191, 0.12); }
.已有点行 .点-转 { color: #d8b4fe; border-color: rgba(192, 132, 252, 0.4); background: rgba(192, 132, 252, 0.12); }

@media (max-width: 1100px) {
  .表单两列 { grid-template-columns: 1fr; }
}
</style>
