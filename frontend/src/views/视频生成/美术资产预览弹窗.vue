<template>
  <!-- 图片预览弹窗（从 美术资产.vue 拆出；显隐由父组件 预览窗显 computed 控制） -->
  <el-dialog :visible="visible" title="预览" width="520px" append-to-body
             @update:visible="$emit('update:visible', $event)">
    <img v-if="图" style="width:100%" :src="媒体地址(图.url)" />
  </el-dialog>
</template>

<script>
import { 媒体地址 } from '@/接口/媒体'

/* 图片预览弹窗：纯展示，图对象由父组件传入，关闭时经 update:visible 通知父组件清空 预览图 */
export default {
  name: 'ArtPreviewDialog',
  props: {
    visible: { type: Boolean, default: false },
    图: { type: Object, default: null }
  },
  methods: { 媒体地址 }
}
</script>
