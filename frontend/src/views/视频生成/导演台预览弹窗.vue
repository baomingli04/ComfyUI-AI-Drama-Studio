<template>
  <!-- 媒体预览弹窗（从 导演台.vue 拆出）：
       显隐 预览显 留在父组件用 :visible.sync 控制，预览的图/视频地址 预览图 由父组件传入 -->
  <el-dialog :visible.sync="显" title="预览" width="720px" append-to-body>
    <video v-if="图 && 是视频路径(图)" :src="媒体地址(图)" style="width:100%" controls playsinline></video>
    <img v-else-if="图" :src="媒体地址(图)" style="width:100%" />
  </el-dialog>
</template>

<script>
import { 媒体地址, 是视频 } from '@/接口/媒体'

export default {
  name: 'DirectorPreviewDialog',
  props: {
    /* 显隐由父组件控制（预览显），这里只透传 */
    visible: { type: Boolean, default: false },
    /* 要预览的媒体路径（图片或视频），空串=无内容 */
    图: { type: String, default: '' }
  },
  computed: {
    /* 显隐代理：父组件 :visible.sync 直通 el-dialog 的 visible.sync */
    显: {
      get() { return this.visible },
      set(v) { this.$emit('update:visible', v) }
    }
  },
  methods: {
    媒体地址,
    是视频路径(路径) { return 是视频(路径) }
  }
}
</script>
