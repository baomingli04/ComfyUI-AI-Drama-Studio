import Vue from 'vue'
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'
import './主题.css'
import 路由 from './路由'
import 壳 from './壳.vue'

Vue.use(ElementUI)
Vue.config.productionTip = false

new Vue({
  router: 路由,
  render: h => h(壳)
}).$mount('#app')
