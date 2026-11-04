<template>
  <!-- 编辑资产弹窗（自 资产清单.vue 拆出：模板与样式原样搬移，业务逻辑不变）。
       显隐控制字段（编辑弹窗显示）与编辑缓冲/保存逻辑留在父页面，prop+emit 模式。 -->
  <el-dialog title="编辑资产" :visible="visible" width="560px" append-to-body
             @update:visible="$emit('update:visible', $event)">
    <div v-if="缓冲" class="编辑单">
      <label class="编项"><span class="编名">资产 ID</span><el-input :value="缓冲.资产id" size="small" disabled /></label>
      <div class="编格">
        <label class="编项"><span class="编名">名称</span><el-input v-model="缓冲.名称" size="small" /></label>
        <label class="编项"><span class="编名">级别</span><el-input v-model="缓冲.级别" size="small" /></label>
      </div>
      <label class="编项"><span class="编名">别名（用 、 分隔）</span><el-input v-model="缓冲.别名" size="small" /></label>
      <label class="编项"><span class="编名">本集关系</span>
        <el-radio-group v-model="缓冲.关系" size="small">
          <el-radio label="新增">新增</el-radio>
          <el-radio label="引用">引用</el-radio>
        </el-radio-group>
      </label>
      <label class="编项"><span class="编名">摘要</span><el-input v-model="缓冲.摘要" type="textarea" :rows="6" /></label>
    </div>
    <div slot="footer">
      <el-button size="small" @click="$emit('update:visible', false)">取消</el-button>
      <el-button size="small" type="primary" :loading="存中" @click="$emit('保存')">保存</el-button>
    </div>
  </el-dialog>
</template>

<script>
export default {
  name: 'AssetEditDialog',
  props: {
    /* 显隐控制字段留在父组件（:visible.sync） */
    visible: { type: Boolean, default: false },
    /* 编辑缓冲对象：父组件 打开编辑 构造，字段级 v-model 直接改对象内部属性 */
    缓冲: { type: Object, default: null },
    /* 保存中状态：保存逻辑（保存编辑）在父组件，落库依赖父组件的 行们/存本集 */
    存中: { type: Boolean, default: false }
  }
}
</script>

<style scoped>
/* ---- 编辑弹窗 ---- */
.编辑单 { display: flex; flex-direction: column; gap: 12px; }
.编项 { display: flex; flex-direction: column; gap: 4px; }
.编名 { font-size: 12px; color: var(--字弱); }
.编格 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
</style>
