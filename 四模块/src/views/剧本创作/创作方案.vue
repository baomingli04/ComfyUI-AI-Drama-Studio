<template>
  <div>
    <!-- 面包屑 -->
    <div class="面包屑条">
      <span class="可点" @click="$router.push('/script')">剧本创作</span>
      <span> / </span>
      <span>创作方案</span>
    </div>

    <!-- 页头 -->
    <div class="页头">
      <div class="左">
        <h1 class="标题">{{ 剧名 }}</h1>
        <div class="副题">{{ 集数 }} 集 · {{ 题材 }} · 已为你生成 3 套创作方案，选择一套继续</div>
      </div>
      <div class="右">
        <el-button @click="$router.push('/script')">返回列表</el-button>
        <el-button @click="重新生成()">重新生成方案</el-button>
      </div>
    </div>

    <!-- 提示条 -->
    <div class="卡片" style="margin-bottom:16px">
      <div class="行间">
        <div style="font-size:13px;color:var(--字次)">
          内容由 AI 生成，请仔细阅读重要信息；方案一经采用，人物设定与分集目录将按此方案生成
        </div>
        <div style="flex:1"></div>
        <el-button size="mini" @click="跳大纲()">查看分集大纲</el-button>
      </div>
    </div>

    <!-- 方案卡 -->
    <div class="网格 三">
      <div
        v-for="方案 in 方案列表"
        :key="方案.id"
        class="卡片 方案卡"
        :class="{ 选中: 选中 === 方案.id }"
        @click="选中 = 方案.id">
        <div class="行间">
          <div style="font-size:16px;font-weight:600">{{ 方案.标题 }}</div>
          <div style="flex:1"></div>
          <span v-if="选中 === 方案.id" class="小标签">已选</span>
        </div>
        <div style="margin-top:10px;font-size:13px;color:var(--字次);line-height:1.7">
          {{ 方案.一句话 }}
        </div>
        <div style="margin-top:12px;font-size:12px;color:var(--字弱)">核心亮点</div>
        <ul style="margin:6px 0 0;padding-left:18px;font-size:13px;color:var(--字)">
          <li v-for="点 in 方案.亮点" :key="点" style="line-height:1.9">{{ 点 }}</li>
        </ul>
        <div style="margin-top:12px">
          <el-tag v-for="标 in 方案.标签" :key="标" size="mini" style="margin-right:6px">{{ 标 }}</el-tag>
        </div>
        <div style="margin-top:12px;font-size:12px;color:var(--字弱)">规划 {{ 方案.集数 }} 集 · 单集 2-3 分钟</div>
      </div>
    </div>

    <!-- 修改意见 -->
    <div class="卡片" style="margin-top:16px">
      <div class="行间">
        <div class="行间">
          <div style="width:36px;height:36px;border-radius:999px;background:var(--主浅);color:var(--主);display:flex;align-items:center;justify-content:center">AI</div>
          <div>
            <div style="font-size:14px">修改意见</div>
            <div style="font-size:12px;color:var(--字弱)">0.2 积分 / 次</div>
          </div>
        </div>
        <div style="flex:1"></div>
        <div style="font-size:12px;color:var(--字弱)">例如：加强师徒感、女主更主动、反转再早一点...</div>
      </div>
      <div class="行间" style="margin-top:12px;flex-wrap:wrap">
        <div
          v-for="议 in 意见选项"
          :key="议"
          class="chip"
          :class="{ 选中: 意见.indexOf(议) >= 0 }"
          @click="切换意见(议)">{{ 议 }}</div>
        <div style="flex:1"></div>
        <el-button size="mini" @click="提交意见()">按意见优化</el-button>
      </div>
    </div>

    <!-- 底部 -->
    <div class="行间 右" style="margin-top:20px">
      <el-button @click="$router.push('/script/new')">上一步：故事起点</el-button>
      <el-button type="primary" @click="采用并继续()">采用此方案并继续</el-button>
    </div>
  </div>
</template>

<script>
import { 创作方案 } from '../../假数据'

export default {
  name: 'ScriptPlan',
  data() {
    return {
      方案列表: 创作方案,
      选中: 'A',
      意见: [],
      意见选项: ['加强师徒感', '女主更主动', '反转再早一点', '结局改成大团圆', '爽点再密一点']
    }
  },
  computed: {
    剧名() {
      return this.$route.query.剧名 || '重生之禁术教师'
    },
    集数() {
      return this.$route.query.集数 || '24'
    },
    题材() {
      return this.$route.query.题材 || '都市'
    }
  },
  methods: {
    切换意见(议) {
      const 位置 = this.意见.indexOf(议)
      if (位置 >= 0) {
        this.意见.splice(位置, 1)
      } else {
        this.意见.push(议)
      }
    },
    重新生成() {
      this.$message({ message: '已重新生成 3 套方案，未消耗额外额度', type: 'success' })
    },
    提交意见() {
      if (this.意见.length === 0) {
        this.$message({ message: '请先选择或填写修改意见', type: 'warning' })
        return
      }
      this.$message({ message: '已按「' + this.意见.join('、') + '」优化方案', type: 'success' })
    },
    采用并继续() {
      this.$router.push({
        path: '/script/outline',
        query: {
          剧名: this.剧名,
          集数: this.集数,
          题材: this.题材,
          方案: this.选中
        }
      })
    },
    跳大纲() {
      this.采用并继续()
    }
  }
}
</script>

<style scoped>
.方案卡 { cursor: pointer; transition: border-color .15s, box-shadow .15s; }
.方案卡:hover { border-color: var(--描边亮); }
.方案卡.选中 { border-color: var(--主); box-shadow: 0 0 0 1px var(--主) inset; }
</style>
