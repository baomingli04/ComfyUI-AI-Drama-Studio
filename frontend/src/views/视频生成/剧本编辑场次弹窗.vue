<template>
  <!-- 场次编辑 / 新增弹窗（自 剧本编辑.vue 拆出，行为保持不变） -->
  <el-dialog
    :visible="显示"
    width="720px"
    top="6vh"
    custom-class="场次编辑弹窗"
    :show-close="false"
    :close-on-click-modal="false"
    @close="$emit('关闭')">
    <div class="弹窗头">
      <div>
        <div class="弹窗标题">{{ 新增模式 ? '新增一场' : '编辑 ' + 草稿.场 }}</div>
        <div class="弹窗副题">{{ 新增模式 ? '填完点「加入本集」，这一场会排到最后' : '改完点保存，直接写回真库这一场' }}</div>
      </div>
      <i class="el-icon-close 弹窗关闭" title="关闭" @click="$emit('关闭')"></i>
    </div>
    <div class="弹窗体">
      <el-form label-width="72px" size="small">
        <el-form-item label="场次号">
          <el-input v-model="草稿.场" maxlength="10" placeholder="例：1-1"></el-input>
        </el-form-item>
        <el-form-item label="地点">
          <el-input v-model="草稿.地点" maxlength="40" placeholder="例：内 · 高三教室 · 日"></el-input>
        </el-form-item>
        <el-form-item label="人物">
          <el-input v-model="草稿.人物" maxlength="80" placeholder="这一场出场的人，顿号分隔"></el-input>
        </el-form-item>
        <el-form-item label="道具">
          <el-input v-model="草稿.道具" maxlength="120" placeholder="这一场要用到的道具，顿号分隔"></el-input>
        </el-form-item>
        <el-form-item label="正文">
          <el-input
            v-model="草稿.正文"
            type="textarea"
            :rows="14"
            placeholder="一行一句。动作行以 △ 开头；台词写成「角色名（动作）：台词」"></el-input>
          <div class="字段注">一行一句，保存时按行拆开；动作行以 △ 开头，台词写「角色名（动作）：台词」</div>
        </el-form-item>
      </el-form>
    </div>
    <div class="弹窗底">
      <el-button v-if="!新增模式" type="text" class="删除钮" @click="$emit('删除', 草稿)">删除这一场</el-button>
      <div style="flex:1"></div>
      <el-button @click="$emit('关闭')">取消</el-button>
      <el-button type="primary" :loading="存库中" @click="$emit('保存', 草稿)">{{ 新增模式 ? '加入本集' : '保存' }}</el-button>
    </div>
  </el-dialog>
</template>

<script>
export default {
  name: 'ScriptSceneDialog',
  props: {
    /* 显隐控制留父组件（父组件的 编辑显示） */
    显示: { type: Boolean, default: false },
    新增模式: { type: Boolean, default: false },
    存库中: { type: Boolean, default: false },
    /* 父组件打开弹窗前先填好的初始草稿 */
    初始草稿: { type: Object, default: null }
  },
  data() {
    return {
      /* 弹窗内实际编辑的草稿，打开时从初始草稿拷贝，点保存/删除时整体回传父组件 */
      草稿: { 场: '', 地点: '', 人物: '', 道具: '', 正文: '' }
    }
  },
  watch: {
    /* 原页面是先设 草稿 再把 编辑显示 置 true，这里在每次打开时同步拷贝一份 */
    显示(值) {
      if (值) {
        this.草稿 = Object.assign({}, this.初始草稿 || {})
      }
    }
  }
}
</script>

<style scoped>
/* ---- 弹窗（自 剧本编辑.vue 拆出） ---- */
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
.删除钮 { color: #ef4444; }
.字段注 { margin-top: 6px; font-size: 12px; color: var(--字弱); line-height: 1.6; }
</style>
