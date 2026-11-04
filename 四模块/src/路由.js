import Vue from 'vue'
import VueRouter from 'vue-router'

Vue.use(VueRouter)

export default new VueRouter({
  mode: 'history',
  routes: [
    { path: '/', redirect: '/script' },

    { path: '/script', name: '剧本列表', component: () => import('./views/剧本创作/剧本列表.vue') },
    { path: '/script/new', name: '新建剧本', component: () => import('./views/剧本创作/新建剧本.vue') },
    { path: '/script/plan', name: '创作方案', component: () => import('./views/剧本创作/创作方案.vue') },
    { path: '/script/outline', name: '分集大纲', component: () => import('./views/剧本创作/分集大纲.vue') },

    { path: '/theater', name: '剧集列表', component: () => import('./views/梦想剧场/剧集列表.vue') },
    { path: '/theater/script', name: '剧本编辑', component: () => import('./views/梦想剧场/剧本编辑.vue') },
    { path: '/theater/assets', name: '分镜与美术资产', component: () => import('./views/梦想剧场/分镜与资产.vue') },
    { path: '/theater/director', name: '导演台', component: () => import('./views/梦想剧场/导演台.vue') },
    { path: '/theater/film', name: '成片剪辑', component: () => import('./views/梦想剧场/成片剪辑.vue') },

    { path: '/assets', name: '我的资产', component: () => import('./views/我的资产/资产库.vue') },
    { path: '/voices', name: '音色库', component: () => import('./views/音色库/音色库.vue') },

    { path: '*', redirect: '/script' }
  ]
})
