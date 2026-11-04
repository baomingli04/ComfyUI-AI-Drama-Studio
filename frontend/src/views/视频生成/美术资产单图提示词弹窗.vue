<template>
  <!-- 单图提示词编辑弹窗（从 美术资产.vue 拆出）。
       编辑图对象由父组件 打开图提示词() 传入，保存逻辑（存图提示词）保留在父组件，
       本组件点「保存」发 保存 事件，取消/关闭经 update:visible 通知父组件。 -->
  <el-dialog :visible="visible" :title="编辑图 ? '参考图提示词' : ''" width="560px" append-to-body
             @update:visible="$emit('update:visible', $event)">
    <el-input v-if="编辑图" type="textarea" :rows="6" v-model="编辑图.提示词"
              placeholder="这张图自己的出图/编辑提示词说明；可用「解析提示词」让 AI 自动生成" />
    <div slot="footer">
      <el-button size="small" @click="$emit('update:visible', false)">取消</el-button>
      <el-button size="small" type="primary" :loading="图存中" @click="$emit('保存')">保存</el-button>
    </div>
  </el-dialog>
</template>

<script>
/* 单图提示词编辑弹窗（从 美术资产.vue 拆出）：纯表单模板，业务方法保留在父组件 */
export default {
  name: 'ArtImagePromptDialog',
  props: {
    visible: { type: Boolean, default: false },
    编辑图: { type: Object, default: null },
    图存中: { type: Boolean, default: false }
  }
}
</script>
