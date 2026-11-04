<template>
  <!-- 四步流程进度条：点任意一步即跳到那一步。样式沿用 模块主题.css 的
       .创作模块 .步骤条 体系，这里只补「可点击」的部分。
       修饰（竖向/居中）由页面传进来，保持和原来写死的 class 一致。 -->
  <div class="步骤条" :class="修饰">
    <template v-for="(步, 序) in 步骤">
      <div
        :key="'步' + 序"
        class="步 可点"
        :class="{ 当前: 序 === 当前步, 完成: 序 < 当前步 }"
        :title="'切换到：' + 步"
        @click="$emit('切换', 序)">
        <div class="圈">{{ 序 < 当前步 ? '✓' : (序 + 1) }}</div>
        <div class="字">{{ 步 }}</div>
      </div>
      <div v-if="序 < 步骤.length - 1" :key="'连' + 序" class="连"></div>
    </template>
  </div>
</template>

<script>
export default {
  name: '步骤条',
  props: {
    步骤: { type: Array, default: () => [] },
    // 当前进行到第几步（0 起）。小于它的显示成 ✓ 完成态。
    当前步: { type: Number, default: 0 },
    // 额外类名，页面上原来是「竖向 居中」
    修饰: { type: String, default: '竖向 居中' }
  }
}
</script>

<style src="./index.css"></style>
