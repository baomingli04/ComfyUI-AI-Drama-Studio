<template>
  <!-- 钩子台账：行 = 七种动作，列 = 集号，格 = 该集该动作的点位。
       数据由每集卡上的「点位」派生（见 共用/节奏工具.js），不单独存一份。
       点任意一格 emit 点格，页面滚到那一集。 -->
  <div class="钩子台账">
    <div class="台账卡">
      <table class="台账表">
        <thead>
          <tr>
            <th class="左">动作</th>
            <th v-for="集 in 集们" :key="'头' + 集.集">EP{{ 集.集 }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="类 in 钩子类型们" :key="类">
            <td class="左">
              <span class="类名" :style="{ color: 钩子色[类] }">{{ 类 }}</span>
              <span class="类数">{{ 计数(类) }}</span>
            </td>
            <td
              v-for="集 in 集们"
              :key="类 + '-' + 集.集"
              class="格位"
              @click="点格(集.集, 类)">
              <span
                v-if="格(类, 集.集).length"
                class="格"
                :style="格样式(类)"
                :title="格说明(类, 集.集)">{{ 格(类, 集.集).map(点 => 点.点).join(' ') }}</span>
              <span v-else class="空格">·</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="台账外">
      <div class="未收">
        <div class="未题">未回收 {{ 未回收.length }} 条 · 建议在收尾前三集补兑</div>
        <div class="未列">
          <div v-if="!未回收.length" class="未条">埋下的钩子都找到了对应的兑或回收。</div>
          <div v-for="(条, 序) in 未回收" :key="'未' + 序" class="未条">
            EP{{ 条.集 }} {{ 条.点 }}「{{ 条.内容 }}」——全剧未找到对应兑/回收
          </div>
        </div>
        <div class="未注">
          内容比对只做初筛：像「埋 小组积分制」→「转 轮值小队长制」这种升级关系字符串比不出来，
          在集卡的点位弹窗里勾「已关联」即可从清单里去掉。
        </div>
      </div>
      <div class="读法">
        <div class="读法题">读法</div>
        <div class="读法文">
          一行一个动作，一格一集。<b class="黄">假兑</b>是「看起来兑现了其实没有」，必须在后面三集内补一次真兑；
          <b class="紫">转</b>是转向，用来换气口，连着两格转就说明戏在绕圈。
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { 钩子类型们, 钩子色, 建台账, 找未回收 } from '../节奏工具'

export default {
  name: '钩子台账',
  props: {
    集们: { type: Array, default: () => [] }
  },
  data() {
    return {
      钩子类型们: 钩子类型们,
      钩子色: 钩子色
    }
  },
  computed: {
    表() {
      return 建台账(this.集们)
    },
    未回收() {
      return 找未回收(this.集们)
    }
  },
  methods: {
    格(类, 集号) {
      const 行 = this.表[类] || {}
      return 行[集号] || []
    },
    计数(类) {
      const 行 = this.表[类] || {}
      let 数 = 0
      Object.keys(行).forEach(function (集号) { 数 += 行[集号].length })
      return 数
    },
    格说明(类, 集号) {
      return this.格(类, 集号).map(function (点) { return 点.点 + ' ' + 点.内容 }).join('\n')
    },
    格样式(类) {
      const 色 = 钩子色[类] || '#94a3b8'
      return {
        color: 色,
        background: 色 + '1f',
        border: '1px solid ' + 色 + '55'
      }
    },
    点格(集号, 类) {
      this.$emit('点格', 集号, 类)
    }
  }
}
</script>

<style src="./index.css"></style>
