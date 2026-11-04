<template>
  <div class="外壳">
    <!-- 顶栏 56px -->
    <header class="顶栏">
      <div class="标志">
        <div class="方块">A</div>
        <div>
          <div class="名">AICG 漫剧工作台</div>
        </div>
      </div>
      <div class="右">
        <span>积分 <b style="color:#e2e8f0">0.485K</b></span>
        <el-button size="mini" type="primary">充值</el-button>
        <div class="行间">
          <div style="width:28px;height:28px;border-radius:999px;background:#334155;display:flex;align-items:center;justify-content:center;font-size:12px;color:#e2e8f0">
            用
          </div>
          <span>用户名</span>
        </div>
      </div>
    </header>

    <div class="主体">
      <!-- 左侧栏：直接四个项目 -->
      <aside class="侧栏">
        <div class="组名">创作</div>
        <router-link
          v-for="项 in 菜单"
          :key="项.路"
          :to="项.路"
          class="项"
          :class="{ 选中: 当前(项.路) }"
        >
          <span class="图" v-html="项.图标"></span>
          <span>{{ 项.名 }}</span>
        </router-link>
      </aside>

      <main class="内容">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script>
const 图标 = {
  笔: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5"/><path d="M18.5 2.5a2.1 2.1 0 013 3L12 15l-4 1 1-4z"/></svg>',
  幕: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>',
  箱: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2"/><path d="M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2"/></svg>',
  音: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>'
}

export default {
  name: 'Shell',
  data() {
    return {
      菜单: [
        { 名: '剧本创作', 路: '/script', 图标: 图标.笔 },
        { 名: '梦想剧场', 路: '/theater', 图标: 图标.幕 },
        { 名: '我的资产', 路: '/assets', 图标: 图标.箱 },
        { 名: '音色库', 路: '/voices', 图标: 图标.音 }
      ]
    }
  },
  methods: {
    当前(路) {
      if (路 === '/script') return this.$route.path.indexOf('/script') === 0
      if (路 === '/theater') return this.$route.path.indexOf('/theater') === 0
      return this.$route.path === 路
    }
  }
}
</script>
