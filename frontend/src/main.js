import Vue from 'vue'
import VueRouter from 'vue-router'
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'
import './全局主题.css'
import './模块主题.css'
import 壳 from './views/壳/index.vue'
import 登录 from './views/登录/index.vue'
import 用户 from './views/用户/index.vue'
import 模型配置 from './views/模型配置/index.vue'
import 技能管理 from './views/技能管理/index.vue'
import T1文本回复 from './views/测试/文本回复/index.vue'
import T2图片解析 from './views/测试/图片解析/index.vue'
import T3生成图片 from './views/测试/生成图片/index.vue'
import T3B生成图片8K from './views/测试/生成图片8K/index.vue'
import 三图编辑一致版 from './views/测试/三图编辑一致版/index.vue'
import 多图编辑多人合并版 from './views/测试/多图编辑多人合并版/index.vue'
import 动漫转真人 from './views/测试/动漫转真人/index.vue'
import T6人物替换 from './views/测试/人物替换/index.vue'
import T7首尾帧 from './views/测试/首尾帧/index.vue'
import T8参考生视频 from './views/测试/参考生视频/index.vue'
import T9去水印 from './views/测试/去水印/index.vue'
import T10二采重绘 from './views/测试/二采重绘/index.vue'
import T11音频剪辑 from './views/测试/音频剪辑/index.vue'
import D1文生视频 from './views/测试/文生视频/index.vue'
import D2多参考生视频 from './views/测试/多参考生视频/index.vue'
import D全导演台全能 from './views/测试/导演台全能/index.vue'
import D3首尾帧生视频 from './views/测试/首尾帧生视频/index.vue'
import D4视频生视频 from './views/测试/视频生视频/index.vue'
import D5参考视频生视频 from './views/测试/参考视频生视频/index.vue'
import D6加速版生视频 from './views/测试/加速版生视频/index.vue'
import D7二采加速生视频 from './views/测试/二采加速生视频/index.vue'
import D8外部分组图生视频 from './views/测试/外部分组图生视频/index.vue'
import D9外部分组多参考生视频 from './views/测试/外部分组多参考生视频/index.vue'
import 工作流下载 from './views/工作流下载/index.vue'
import 剧本列表 from './views/剧本创作/剧本列表.vue'
import 新建剧本 from './views/剧本创作/新建剧本.vue'
import 创作方案 from './views/剧本创作/创作方案.vue'
import 方案详情 from './views/剧本创作/方案详情.vue'
import 人物设定 from './views/剧本创作/人物设定.vue'
import 分集目录 from './views/剧本创作/分集目录.vue'
import 分集剧本 from './views/剧本创作/分集剧本.vue'
import 剧集列表 from './views/视频生成/剧集列表.vue'
import 剧集详情 from './views/视频生成/剧集详情/index.vue'
import 剧本编辑 from './views/视频生成/剧本编辑.vue'
import 关卡详情 from './views/视频生成/关卡详情.vue'
import 资产清单 from './views/视频生成/资产清单.vue'
import 美术资产 from './views/视频生成/美术资产.vue'
import 拆分分镜 from './views/视频生成/拆分分镜.vue'
import 导演台 from './views/视频生成/导演台.vue'
import 成片剪辑 from './views/视频生成/成片剪辑.vue'
import 资产库 from './views/我的资产/资产库.vue'
import 音色库 from './views/音色库/音色库.vue'

Vue.use(VueRouter)
Vue.use(ElementUI)

const 路由 = new VueRouter({
  routes: [
    { path: '/login', component: 登录 },
    {
      path: '/',
      component: 壳,
      redirect: '/user',
      children: [
        { path: 'user', component: 用户 },
        { path: 'model-config', component: 模型配置 },
        { path: 'skill-manage', component: 技能管理 },
        { path: 'test/t1-text', component: T1文本回复 },
        { path: 'test/t2-image-parse', component: T2图片解析 },
        { path: 'test/t3-text2img', component: T3生成图片 },
        { path: 'test/t3b-text2img8k', component: T3B生成图片8K },
        { path: 'test/t4-edit-3img', component: 三图编辑一致版 },
        { path: 'test/t5-edit-multi', component: 多图编辑多人合并版 },
        { path: 'test/t5b-anime2real', component: 动漫转真人 },
        { path: 'test/t6-face-swap', component: T6人物替换 },
        { path: 'test/t7-frame2frame', component: T7首尾帧 },
        { path: 'test/t8-ref2video', component: T8参考生视频 },
        { path: 'test/t9-dewatermark', component: T9去水印 },
        { path: 'test/t10-repaint', component: T10二采重绘 },
        { path: 'test/t11-audio-edit', component: T11音频剪辑 },
        { path: 'test/d1-t2v', component: D1文生视频 },
        { path: 'test/d2-r2v', component: D2多参考生视频 },
        { path: 'test/d-all', component: D全导演台全能 },
        { path: 'test/d3-fl2v', component: D3首尾帧生视频 },
        { path: 'test/d4-v2v', component: D4视频生视频 },
        { path: 'test/d5-rv2v', component: D5参考视频生视频 },
        { path: 'test/d6-acc', component: D6加速版生视频 },
        { path: 'test/d7-refine', component: D7二采加速生视频 },
        { path: 'test/d8-i2v-groups', component: D8外部分组图生视频 },
        { path: 'test/d9-r2v-groups', component: D9外部分组多参考生视频 },
        { path: 'tool/workflow', component: 工作流下载 },
        { path: 'script', component: 剧本列表 },
        { path: 'script/new', component: 新建剧本 },
        { path: 'script/plan', component: 创作方案 },
        { path: 'script/detail', component: 方案详情 },
        { path: 'script/character', component: 人物设定 },
        { path: 'script/outline', component: 分集目录 },
        { path: 'script/episode', component: 分集剧本 },
        // 「合规审查」已下线：老链接与浏览器历史落到分集剧本页，不留空白页
        { path: 'script/audit', redirect: '/script/episode' },
        { path: 'video', component: 剧集列表 },
        { path: 'video/drama', component: 剧集详情 },
        { path: 'video/script', component: 剧本编辑 },
        { path: 'video/episode', component: 关卡详情 },
        { path: 'video/assets', component: 资产清单 },
        { path: 'video/art', component: 美术资产 },
        { path: 'video/shot', component: 拆分分镜 },
        { path: 'video/director', component: 导演台 },
        { path: 'video/film', component: 成片剪辑 },
        { path: 'assets', component: 资产库 },
        { path: 'voices', component: 音色库 }
      ]
    }
  ]
})

路由.beforeEach(function (到, 从, 下一步) {
  const 有令牌 = !!localStorage.getItem('token')
  if (到.path === '/login') {
    下一步()
  } else if (!有令牌) {
    下一步('/login')
  } else {
    下一步()
  }
})

new Vue({
  router: 路由,
  render: function (h) {
    return h('router-view')
  }
}).$mount('#app')
