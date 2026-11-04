<template>
  <el-dialog
    :visible="显示"
    width="72%"
    top="6vh"
    custom-class="预览弹窗"
    :show-close="false"
    @close="$emit('关闭')"
  >
    <div class="预览容器" v-if="当前">
      <div class="预览头">
        <span class="预览名称">{{ 当前.名称 }}</span>
        <span class="预览计数">{{ 索引 + 1 }} / {{ 列表.length }}</span>
        <i class="el-icon-close 预览关闭" @click="$emit('关闭')"></i>
      </div>

      <div class="预览主体">
        <i class="el-icon-arrow-left 预览箭头" :class="{ 禁用: 列表.length < 2 }" @click="$emit('切换', -1)"></i>
        <div class="预览画框">
          <img v-if="当前.类型 === 'image'" :src="当前.地址" class="预览图" alt="" />
          <video v-else-if="当前.类型 === 'video'" :src="当前.地址" class="预览视频" controls autoplay></video>
          <audio v-else :src="当前.地址" class="预览音频" controls></audio>
        </div>
        <i class="el-icon-arrow-right 预览箭头" :class="{ 禁用: 列表.length < 2 }" @click="$emit('切换', 1)"></i>
      </div>
    </div>
  </el-dialog>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
