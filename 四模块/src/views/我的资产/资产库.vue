<template>
  <div>
    <!-- 页头 -->
    <div class="页头">
      <div class="左">
        <h1 class="标题">我的资产</h1>
        <div class="副题">收藏可跨项目复用的角色、场景、道具、服装与风格</div>
      </div>
      <div class="右">
        <el-button size="small" icon="el-icon-upload2">批量导入</el-button>
        <el-button size="small" type="primary" icon="el-icon-plus" @click="新建()">新建资产</el-button>
      </div>
    </div>

    <!-- 筛选 -->
    <div class="卡片" style="margin-bottom:16px">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
        <div class="行间" style="flex-wrap:wrap">
          <span style="font-size:13px;color:var(--字弱);margin-right:4px">类型</span>
          <span v-for="类 in 类型组" :key="'类型-' + 类" class="chip" :class="{ 选中: 类型 === 类 }" @click="类型 = 类">{{ 类 }}</span>
          <span style="width:16px"></span>
          <span style="font-size:13px;color:var(--字弱);margin-right:4px">性别</span>
          <span v-for="性 in 性别组" :key="'性别-' + 性" class="chip" :class="{ 选中: 性别 === 性 }" @click="性别 = 性">{{ 性 }}</span>
        </div>
        <div class="行间">
          <el-input v-model="关键词" placeholder="搜索资产" prefix-icon="el-icon-search" size="small" style="width:220px" clearable />
          <span style="font-size:13px;color:var(--字弱)">共 {{ 过滤后.length }} 项</span>
        </div>
      </div>
    </div>

    <!-- 网格 -->
    <div v-if="过滤后.length" class="网格 四">
      <div v-for="资 in 过滤后" :key="资.id" class="卡片" style="padding:12px">
        <div style="position:relative">
          <div class="占位图" :style="{ height:'150px', background:'linear-gradient(135deg,' + 资.色 + ',#0f172a)' }">
            <span>原图：{{ 资.名 }}</span>
          </div>
          <span style="position:absolute;top:8px;left:8px" class="小标签 灰">{{ 资.类型 }}</span>
        </div>
        <div style="display:flex;align-items:center;justify-content:space-between;margin-top:10px">
          <span style="font-size:14px;color:var(--字);font-weight:500">{{ 资.名 }}</span>
          <span class="小标签 灰" v-if="资.性别 !== '-'">{{ 资.性别 }}</span>
        </div>
        <div style="font-size:12px;color:var(--字弱);margin-top:4px">来源：{{ 资.来源 }}</div>
        <div style="font-size:12px;color:var(--字弱);margin-top:2px">{{ 资.时间 }}</div>
        <div class="行间" style="margin-top:10px">
          <el-button size="mini" plain style="flex:1" @click="复用(资)">复用到项目</el-button>
          <el-button size="mini" type="text" @click="取消收藏(资)">取消收藏</el-button>
        </div>
      </div>
    </div>

    <!-- 空态 -->
    <div v-else class="卡片">
      <div class="空态">
        <div class="大">收藏可跨项目复用的资产</div>
        <div>还没有符合条件的资产。前往项目，把生成好的角色与场景收藏到这里。</div>
        <el-button type="primary" style="margin-top:16px" @click="$router.push('/theater')">前往项目</el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { 我的资产 } from '../../假数据'

export default {
  name: 'AssetLib',
  data() {
    return {
      全部: 我的资产.map(x => Object.assign({}, x)),
      类型: '全部',
      性别: '全部',
      关键词: ''
    }
  },
  computed: {
    类型组() {
      return ['全部'].concat(Array.from(new Set(this.全部.map(x => x.类型))))
    },
    性别组() {
      return ['全部', '男', '女']
    },
    过滤后() {
      const 词 = this.关键词.trim()
      return this.全部.filter(x =>
        (this.类型 === '全部' || x.类型 === this.类型) &&
        (this.性别 === '全部' || x.性别 === this.性别) &&
        (!词 || x.名.indexOf(词) >= 0 || x.来源.indexOf(词) >= 0)
      )
    }
  },
  methods: {
    复用(资) {
      this.$message.success('已把「' + 资.名 + '」加入当前项目资产清单')
    },
    取消收藏(资) {
      this.全部 = this.全部.filter(x => x.id !== 资.id)
      this.$message.info('已取消收藏：' + 资.名)
    },
    新建() {
      this.$message.success('纯前端演示：新建资产未接入后端')
    }
  }
}
</script>
