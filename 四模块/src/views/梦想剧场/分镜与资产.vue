<template>
  <div>
    <!-- 面包屑 -->
    <div class="面包屑条">
      <span class="可点" @click="$router.push('/theater')">梦想剧场</span>
      <span> / </span>
      <span class="可点" @click="上一页()">{{ 剧名 }}</span>
      <span> / </span>
      <span style="color:var(--字次)">分镜与美术资产</span>
    </div>

    <!-- 进度步骤 -->
    <div class="卡片" style="margin-bottom:16px">
      <div class="步骤条" style="margin:0">
        <div class="步 完成"><span class="圈"><i class="el-icon-check"></i></span><span class="字">剧本编辑</span></div>
        <span class="连"></span>
        <div class="步 当前"><span class="圈">2</span><span class="字">分镜与美术资产</span></div>
        <span class="连"></span>
        <div class="步"><span class="圈">3</span><span class="字">导演台</span></div>
        <span class="连"></span>
        <div class="步"><span class="圈">4</span><span class="字">短片</span></div>
      </div>

      <!-- 三个子步骤 -->
      <div class="行间" style="padding-top:8px;border-top:1px solid var(--描边)">
        <div
          v-for="(子, i) in 子步骤"
          :key="子.名"
          class="chip"
          :class="{ 选中: 子序 === i }"
          @click="子序 = i"
        >
          <span>{{ i + 1 }}</span>
          <span>{{ 子.名 }}</span>
          <span style="font-size:12px;opacity:.75">{{ 子.状态 }}</span>
        </div>
        <div style="flex:1"></div>
        <span style="font-size:12px;color:var(--字弱)">{{ 子步骤[子序].说明 }}</span>
      </div>
    </div>

    <!-- 子步骤 1：资产清单 -->
    <div v-if="子序 === 0" class="卡片">
      <div class="页头" style="margin-bottom:12px">
        <div class="左">
          <h2 class="区标题">资产清单</h2>
          <div class="副题">从剧本中识别出的角色、场景、道具、服装与风格，共 {{ 资产清单.length }} 项待提取</div>
        </div>
        <div class="右">
          <el-button size="small" @click="重新识别()">重新识别</el-button>
          <el-button size="small" type="primary" @click="提取全部()">提取全部资产</el-button>
        </div>
      </div>

      <el-table :data="资产清单" style="width:100%">
        <el-table-column prop="类型" label="类型" width="90">
          <template slot-scope="s"><span class="小标签 灰">{{ s.row.类型 }}</span></template>
        </el-table-column>
        <el-table-column prop="名" label="资产名称" width="160" />
        <el-table-column prop="描述" label="外观描述" min-width="260" />
        <el-table-column prop="状态" label="状态" width="110">
          <template slot-scope="s">
            <el-tag size="mini" :type="s.row.状态 === '已提取' ? 'success' : 'warning'">{{ s.row.状态 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="关联镜头" width="100" align="center">
          <template slot-scope="s">{{ s.row.关联 }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="right">
          <template slot-scope="s">
            <el-button type="text" size="mini" @click="提取(s.row)">提取</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 子步骤 2：美术资产 -->
    <div v-if="子序 === 1">
      <div class="卡片" style="margin-bottom:16px">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
          <div>
            <h2 class="区标题" style="margin:0 0 4px">美术资产</h2>
            <div class="副题">图片 {{ 已生成 }}/{{ 美术资产.length }} · 待审核 {{ 待审核 }} 项</div>
          </div>
          <div class="行间" style="flex-wrap:wrap">
            <span
              v-for="类 in 类型组"
              :key="类"
              class="chip"
              :class="{ 选中: 类型筛选 === 类 }"
              @click="类型筛选 = 类"
            >{{ 类 }}</span>
          </div>
        </div>
      </div>

      <div class="网格 四">
        <div v-for="资 in 过滤资产" :key="资.id" class="卡片" style="padding:12px">
          <div class="占位图" :style="{ height:'140px', background:'linear-gradient(135deg,' + 资.色 + ',#0f172a)' }">
            <span>原图：{{ 资.名 }}</span>
          </div>
          <div style="display:flex;align-items:center;justify-content:space-between;margin-top:10px">
            <span style="font-size:14px;color:var(--字)">{{ 资.名 }}</span>
            <el-tag size="mini" :type="资.状态 === '已通过' ? 'success' : 'warning'">{{ 资.状态 }}</el-tag>
          </div>
          <div style="font-size:12px;color:var(--字弱);margin-top:4px">{{ 资.类型 }}</div>
          <div class="行间" style="margin-top:10px">
            <el-button size="mini" plain style="flex:1" @click="重绘(资)">重绘</el-button>
            <el-button size="mini" type="primary" style="flex:1" @click="通过(资)">通过</el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 子步骤 3：拆分分镜 -->
    <div v-if="子序 === 2" class="卡片">
      <div class="页头" style="margin-bottom:12px">
        <div class="左">
          <h2 class="区标题">拆分分镜</h2>
          <div class="副题">按场次把剧本拆成镜头，当前 {{ 分镜列表.length }} 个镜头</div>
        </div>
        <div class="右">
          <el-button size="small" @click="清空()">清空分镜</el-button>
          <el-button size="small" type="primary" @click="拆分()">开始拆分分镜</el-button>
        </div>
      </div>

      <el-table :data="分镜列表" style="width:100%">
        <el-table-column prop="镜号" label="镜号" width="90" />
        <el-table-column prop="场次" label="场次" width="100" />
        <el-table-column prop="画面" label="画面内容" min-width="240" />
        <el-table-column prop="台词" label="台词" width="160" />
        <el-table-column prop="时长" label="时长" width="80" align="center" />
        <el-table-column prop="状态" label="状态" width="110">
          <template slot-scope="s">
            <el-tag size="mini" :type="标签类型(s.row.状态)">{{ s.row.状态 }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 底部 -->
    <div class="行间 右" style="margin-top:16px">
      <el-button @click="上一页()">上一步：剧本编辑</el-button>
      <el-button type="primary" @click="下一步()">下一步：导演台</el-button>
    </div>
  </div>
</template>

<script>
import { 资产清单, 美术资产, 分镜列表 } from '../../假数据'

export default {
  name: 'Storyboard',
  data() {
    return {
      子序: 0,
      子步骤: [
        { 名: '资产清单', 状态: '待提取', 说明: '从剧本识别出的可复用资产' },
        { 名: '美术资产', 状态: '图片 0/12', 说明: '为每项资产生成参考图并审核' },
        { 名: '拆分分镜', 状态: '待拆分', 说明: '把剧本按场次拆成可生成的镜头' }
      ],
      资产清单: 资产清单.map(x => Object.assign({}, x)),
      美术资产: 美术资产.map(x => Object.assign({}, x)),
      分镜列表: 分镜列表.map(x => Object.assign({}, x)),
      类型筛选: '全部'
    }
  },
  computed: {
    剧名() {
      return this.$route.query.name || '火影之禁术教师'
    },
    类型组() {
      return ['全部'].concat(Array.from(new Set(this.美术资产.map(x => x.类型))))
    },
    过滤资产() {
      return this.类型筛选 === '全部'
        ? this.美术资产
        : this.美术资产.filter(x => x.类型 === this.类型筛选)
    },
    已生成() {
      return this.美术资产.filter(x => x.状态 === '已通过').length
    },
    待审核() {
      return this.美术资产.filter(x => x.状态 === '待审核').length
    }
  },
  methods: {
    标签类型(状态) {
      if (状态 === '已生成') return 'success'
      if (状态 === '生成中') return 'warning'
      return 'info'
    },
    提取(行) {
      行.状态 = '已提取'
      行.关联 = 3
      this.$message.success('已提取：' + 行.名)
    },
    提取全部() {
      this.资产清单.forEach(x => { x.状态 = '已提取'; x.关联 = 3 })
      this.$message.success('已提交提取任务，共 ' + this.资产清单.length + ' 项')
    },
    重新识别() {
      this.资产清单.forEach(x => { x.状态 = '待提取'; x.关联 = 0 })
      this.$message.info('已重新识别剧本')
    },
    重绘(资) {
      this.$message.success('已提交重绘：' + 资.名)
    },
    通过(资) {
      资.状态 = '已通过'
    },
    拆分() {
      this.分镜列表.forEach(x => { if (x.状态 === '待生成') x.状态 = '生成中' })
      this.$message.success('已提交拆分任务，共 ' + this.分镜列表.length + ' 个镜头')
    },
    清空() {
      this.分镜列表.forEach(x => { x.状态 = '待生成' })
      this.$message.info('已清空分镜拆分结果')
    },
    上一页() {
      this.$router.push({ path: '/theater/script', query: this.$route.query })
    },
    下一步() {
      this.$router.push({ path: '/theater/director', query: this.$route.query })
    }
  }
}
</script>
