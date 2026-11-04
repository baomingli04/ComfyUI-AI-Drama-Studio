<template>
  <!-- 视频预览弹窗（自「拆分分镜.vue」纯拆出：模板与行为一致） -->
  <el-dialog :visible.sync="弹窗显示" title="本镜视频" width="680px" append-to-body>
    <video v-if="地址" :src="媒体地址(地址)" style="width:100%;border-radius:8px;background:#000" controls playsinline></video>
  </el-dialog>
</template>

<script>
import { 媒体地址 } from '@/接口/媒体'

/* 视频预览弹窗组件：播放某个镜头已生成的视频 */
export default {
  name: 'ShotSplitPreviewDialog',
  props: {
    /* 显隐由父组件控制（:显示.sync） */
    显示: { type: Boolean, default: false },
    /* 预览的视频地址 */
    地址: { type: String, default: '' }
  },
  computed: {
    /* :visible.sync 需要可写值，用计算属性转发为 update:显示 事件 */
    弹窗显示: {
      get() { return this.显示 },
      set(值) { this.$emit('update:显示', 值) }
    }
  },
  methods: {
    媒体地址
  }
}
</script>
