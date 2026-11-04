<template>
  <!-- 从资产引入弹窗：参考图 / 音色 两页签，搜索 + 类型筛选 + 分页
       （从 导演台.vue 拆出：弹窗专属 data/methods/computed 整体搬入本组件；
         显隐 资产窗显 留在父组件，用 :visible.sync；打开时的页签经 开签 prop 传入；
         共享数据 资产行们/音色行们 由父组件 props 传入；
         引入动作回传父组件落库：@引入图 → 父 引入资产图，@引入音色 → 父 引入音色） -->
  <el-dialog title="从资产引入" :visible.sync="显" width="880px" append-to-body custom-class="资窗弹窗" @open="资产窗页 = 1">
    <div class="资窗说明">只复制引用到本镜资源区，不改美术资产。</div>
    <el-tabs v-model="资产窗标签" @tab-click="资产窗页 = 1">
      <!-- 页签一：参考图 -->
      <el-tab-pane label="参考图" name="图">
        <div class="资窗筛">
          <el-input v-model="资产窗搜索" size="small" placeholder="搜资产名 / 别名 / 资产id" prefix-icon="el-icon-search"
                    style="width:230px" clearable @input="资产窗页 = 1" />
          <span class="资窗筛题">类型</span>
          <span v-for="类 in ['全部', '人物', '场景', '道具', '服装']" :key="'f' + 类"
                class="chip" :class="{ 选中: 资产窗类型 === 类 }" @click="资产窗选类型(类)">{{ 类 }}</span>
          <span style="flex:1"></span>
          <el-pagination v-if="资产窗图分页.length > 1" layout="prev, pager, next" small
                         :page-size="6" :total="资产窗图行们.length" :current-page.sync="资产窗页" />
        </div>
        <div v-if="资产窗图分页.length" class="资窗卡栅">
          <div v-for="行 in 资产窗图分页" :key="'a' + 行.资产行id" class="资窗卡">
            <div class="资窗卡头">
              <b class="资窗卡名">{{ 行.名称 }}</b>
              <span class="小标签 灰">{{ 行.类型 }}</span>
              <code class="资窗卡id">{{ 行.资产id }}</code>
            </div>
            <div class="资窗图行">
              <div v-for="图 in 行.图们.filter(function (g) { return g.状态 === '当前' })" :key="'ai' + 图.id"
                   class="资窗图块" :title="'引入：' + (图.标注 || 图.形态 || '参考图')" @click="引入资产图(行, 图)">
                <img class="资窗图" :src="媒体地址(图.url)" />
                <div class="资窗标">{{ 图.标注 || 图.形态 || '参考图' }}</div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="资窗空">没有匹配的资产（换个关键词或类型试试）</div>
      </el-tab-pane>
      <!-- 页签二：音色 -->
      <el-tab-pane label="音色" name="音色">
        <div class="资窗筛">
          <el-input v-model="资产窗搜索" size="small" placeholder="搜角色名 / 别名" prefix-icon="el-icon-search"
                    style="width:230px" clearable @input="资产窗页 = 1" />
          <span style="flex:1"></span>
          <el-pagination v-if="资产窗音分页.length > 1" layout="prev, pager, next" small
                         :page-size="6" :total="资产窗音行们.length" :current-page.sync="资产窗页" />
        </div>
        <div v-if="资产窗音分页.length" class="资窗卡栅">
          <div v-for="行 in 资产窗音分页" :key="'v' + 行.资产行id" class="资窗卡">
            <div class="资窗卡头">
              <b class="资窗卡名">{{ 行.名称 }}</b>
              <span class="小标签 灰">{{ 行.定装.音色名 || '音色' }}</span>
              <span style="flex:1"></span>
              <el-button size="mini" type="primary" plain @click="引入音色(行)">引入为参考音频</el-button>
            </div>
            <audio class="资窗音预" :src="音色地址(行.定装.音色url)" controls preload="none"></audio>
          </div>
        </div>
        <div v-else class="资窗空">还没有已合成音色的角色：去 美术资产 页给人物卡合成音色后，这里就能引入</div>
      </el-tab-pane>
    </el-tabs>
  </el-dialog>
</template>

<script>
import { 媒体地址 } from '@/接口/媒体'

export default {
  name: 'DirectorAssetDialog',
  props: {
    /* 显隐由父组件控制（资产窗显），这里只透传 */
    visible: { type: Boolean, default: false },
    /* 打开时要落的页签：'图' = 参考图，'音色' = 音色（父组件 开资产窗(标签) 规整后传入） */
    开签: { type: String, default: '图' },
    资产行们: { type: Array, default: function () { return [] } },
    音色行们: { type: Array, default: function () { return [] } }
  },
  data() {
    return {
      资产窗标签: '图',
      资产窗搜索: '',
      资产窗类型: '全部',
      资产窗页: 1
    }
  },
  computed: {
    /* 显隐代理：父组件 :visible.sync 直通 el-dialog 的 visible.sync */
    显: {
      get() { return this.visible },
      set(v) { this.$emit('update:visible', v) }
    },
    /* 引入弹窗：按页签+类型+关键词过滤后分页 */
    资产窗图行们() {
      const 词 = this.资产窗搜索.trim()
      return this.资产行们.filter(function (行) {
        return (this.资产窗类型 === '全部' || 行.类型 === this.资产窗类型) &&
          (!词 || (行.名称 || '').indexOf(词) >= 0 || (行.别名 || '').indexOf(词) >= 0 || (行.资产id || '').indexOf(词) >= 0)
      }, this)
    },
    资产窗图分页() {
      return this.资产窗图行们.slice((this.资产窗页 - 1) * 6, this.资产窗页 * 6)
    },
    资产窗音行们() {
      const 词 = this.资产窗搜索.trim()
      return this.音色行们.filter(function (行) {
        return !词 || (行.名称 || '').indexOf(词) >= 0 || (行.别名 || '').indexOf(词) >= 0
      })
    },
    资产窗音分页() {
      return this.资产窗音行们.slice((this.资产窗页 - 1) * 6, this.资产窗页 * 6)
    }
  },
  watch: {
    /* 原 父组件.开资产窗(标签) 里的重置逻辑随弹窗状态搬进本组件：
       打开时按 开签 定页签、清搜索/类型、回到第一页（时序与拆分前一致：先重置再显示） */
    visible(v) {
      if (!v) return
      this.资产窗标签 = this.开签 || '图'
      this.资产窗搜索 = ''
      this.资产窗类型 = '全部'
      this.资产窗页 = 1
    }
  },
  methods: {
    媒体地址,
    资产窗选类型(类) {
      this.资产窗类型 = 类
      this.资产窗页 = 1
    },
    /* 引入动作回传父组件落库（父组件 @引入图="引入资产图"） */
    引入资产图(行, 图) { this.$emit('引入图', 行, 图) },
    /* 引入音色回传父组件（父组件 @引入音色="引入音色"，≤3 上限判断在父组件 参考音频们 上做） */
    引入音色(行) { this.$emit('引入音色', 行) },
    /* 音色文件播放地址：/voices/ 开头是前端静态目录直出，其余走后端媒体接口（与美术资产页同规则） */
    音色地址(url) {
      if (!url) return ''
      if (url.indexOf('/voices/') === 0) return url
      return this.媒体地址(url)
    }
  }
}
</script>

<style scoped>
/* 资产引入弹窗（参考图/音色 两页签，搜索+类型+分页） */
/* 弹窗 append-to-body 传到了 .创作模块 外，全局 .chip/.小标签 样式够不着，这里自带一份 */
.资窗筛 .chip {
  display: inline-flex; align-items: center;
  height: 28px; padding: 0 12px;
  border-radius: 999px;
  border: 1px solid var(--描边);
  background: transparent;
  color: var(--字次);
  font-size: 12px;
  cursor: pointer;
  user-select: none;
}
.资窗筛 .chip:hover { border-color: var(--描边亮); color: var(--字); }
.资窗筛 .chip.选中 { background: var(--主); border-color: var(--主); color: #06210f; font-weight: 500; }
.资窗卡 .小标签 { display: inline-flex; align-items: center; height: 20px; padding: 0 8px; border-radius: 999px; border: 1px solid var(--描边); background: var(--描边); color: var(--字次); font-size: 10px; }
.资窗说明 { font-size: 12px; color: var(--字弱); margin-bottom: 10px; }
.资窗筛 { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 12px; }
.资窗筛题 { font-size: 12px; color: var(--字弱); }
.资窗卡栅 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; min-height: 180px; align-content: start; }
.资窗卡 { border: 1px solid var(--描边); border-radius: 10px; padding: 10px 12px; }
.资窗卡:hover { border-color: var(--主); }
.资窗卡头 { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.资窗卡名 { font-size: 13px; color: var(--字); }
.资窗卡id { font-size: 10px; color: var(--字弱); margin-left: auto; }
.资窗图行 { display: flex; gap: 8px; flex-wrap: wrap; }
.资窗图块 { width: 96px; cursor: pointer; border: 1px solid var(--描边); border-radius: 8px; overflow: hidden; }
.资窗图块:hover { border-color: var(--主); }
.资窗图 { width: 100%; height: 72px; object-fit: contain; display: block; background: var(--面板弱, rgba(0,0,0,.03)); }
.资窗标 { font-size: 10px; color: var(--字弱); text-align: center; padding: 3px 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.资窗音预 { width: 100%; height: 36px; display: block; }
.资窗空 { text-align: center; color: var(--字弱); font-size: 13px; padding: 48px 0; }
</style>

<style>
/* 引入弹窗 append-to-body 挂在 .创作模块 外，主题变量继承不到（var(--描边) 等整条失效），
   这里在弹窗根上补挂同一套色板（与 模块主题.css 一致） */
.资窗弹窗 {
  --底: #0a0f1a;
  --卡片: #151e32;
  --卡片二: #0f172a;
  --描边: #1e293b;
  --描边亮: #334155;
  --主: #22c55e;
  --主暗: #16a34a;
  --主浅: rgba(34, 197, 94, 0.12);
  --字: #e2e8f0;
  --字次: #94a3b8;
  --字弱: #64748b;
  background: var(--卡片二);
  color: var(--字);
}
.资窗弹窗 .el-dialog__title { color: var(--字); }
.资窗弹窗 .el-dialog__body { padding-top: 12px; }
</style>
