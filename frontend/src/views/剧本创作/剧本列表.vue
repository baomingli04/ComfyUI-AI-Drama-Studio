<template>
  <div class="创作模块">
    <!-- 页头 -->
    <div class="页头">
      <div class="左">
        <h1 class="标题">剧本创作</h1>
        <div class="副题">从立项到全剧定稿：方案 → 人物 → 分集 → 剧本，全部落库保存</div>
      </div>
      <div class="右">
        <el-button @click="打开导入()">导入剧本</el-button>
        <el-button type="primary" @click="$router.push('/script/new')">新建剧本</el-button>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="卡片" style="margin-bottom:16px">
      <div class="行间">
        <el-input
          v-model="关键词"
          placeholder="搜索剧名或题材"
          prefix-icon="el-icon-search"
          style="width:260px" clearable>
        </el-input>
        <div class="行间" style="flex-wrap:wrap">
          <div
            v-for="项 in 状态选项"
            :key="项"
            class="chip"
            :class="{ 选中: 当前状态 === 项 }"
            @click="当前状态 = 项">{{ 项 }}</div>
        </div>
        <div style="flex:1"></div>
        <el-select v-model="排序" style="width:150px">
          <el-option label="最近更新" value="最近更新"></el-option>
          <el-option label="进度优先" value="进度优先"></el-option>
          <el-option label="集数最多" value="集数最多"></el-option>
        </el-select>
        <el-button size="small" icon="el-icon-refresh" :loading="加载中" @click="载入()">刷新</el-button>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="加载中" class="空态">
      <i class="el-icon-loading" style="font-size:28px;color:var(--主)"></i>
      <div class="大" style="margin-top:10px">正在读取剧库…</div>
    </div>

    <!-- 加载失败 -->
    <div v-else-if="报错" class="空态">
      <div class="大" style="color:var(--危险, #f56c6c)">加载失败：{{ 报错 }}</div>
      <el-button size="small" style="margin-top:12px" @click="载入()">重试</el-button>
    </div>

    <!-- 剧本卡片网格 -->
    <template v-else>
      <div class="网格 三">
        <div
          v-for="剧 in 展示列表"
          :key="剧.id"
          class="卡片 剧卡"
          @click="打开剧本(剧)">
          <!-- 封面：有图显示图，无图显示占位 -->
          <img
            v-if="剧.封面图片"
            class="封面"
            :src="媒体地址(剧.封面图片)"
            :alt="剧.剧名 + ' 封面'">
          <div v-else class="封面 封面占位" :style="{ background: 封面色(剧.剧名) }">
            <span class="占位字">{{ 剧.剧名 }}</span>
          </div>

          <div class="行间" style="margin-top:12px">
            <div style="font-size:16px;font-weight:600">{{ 剧.剧名 }}</div>
            <div style="flex:1"></div>
            <span class="状态签" :class="状态类(剧.状态)">{{ 剧.状态 }}</span>
          </div>
          <div style="margin-top:8px;font-size:12px;color:var(--字弱)">
            <el-tag size="mini">{{ 剧.题材 }}</el-tag>
            <span style="margin-left:8px">{{ 剧.集数 }} 集</span>
            <span style="margin-left:8px">· {{ 剧.起点方式 }}</span>
          </div>
          <div style="margin-top:10px;font-size:12px;color:var(--字次);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
            {{ 剧.创意 }}
          </div>
          <div style="margin-top:10px">
            <el-progress :percentage="剧.创作进度" :stroke-width="6" :show-text="false"></el-progress>
          </div>
          <div class="行间" style="margin-top:8px;font-size:12px;color:var(--字弱)">
            <span>完成度 {{ 剧.创作进度 }}%</span>
            <div style="flex:1"></div>
            <span>更新 {{ 剧.更新时间 }}</span>
          </div>
          <div
            v-if="剧.保存地址"
            class="行间 存址"
            :title="'保存地址：' + 剧.保存地址">
            <i class="el-icon-folder-opened"></i>
            <span class="存址文">{{ 剧.保存地址 }}</span>
          </div>
          <div class="行间" style="margin-top:12px">
            <el-button type="primary" size="mini" @click.stop="打开剧本(剧)">继续创作</el-button>
            <el-button size="mini" icon="el-icon-picture" @click.stop="开编辑(剧)">封面</el-button>
            <el-button size="mini" type="danger" plain icon="el-icon-delete" @click.stop="删除(剧)">删除</el-button>
          </div>
        </div>
      </div>

      <div v-if="展示列表.length === 0" class="空态">
        <div class="大">{{ 全部.length === 0 ? '剧库还是空的' : '没有符合条件的剧本' }}</div>
        <div>{{ 全部.length === 0 ? '点右上角「新建剧本」，写下剧名和一句创意开始' : '换个关键词或状态筛选试试' }}</div>
      </div>

      <div style="margin-top:16px;font-size:12px;color:var(--字弱)">
        共 {{ 展示列表.length }} 部剧（库内 {{ 全部.length }} 部） · 数据来自 aicg.剧 表 · 删除会级联清除方案/剧本/分镜/成片，不可恢复
      </div>
    </template>

    <!-- 编辑弹窗：封面 / 保存地址 / 状态 -->
    <el-dialog title="编辑剧集信息" :visible.sync="编辑显示" width="460px" append-to-body>
      <div class="编块">
        <div class="编名">封面图片（PNG/JPG，上传后自动保存）</div>
        <div class="行间">
          <img v-if="草稿.封面图片" class="封面预览" :src="媒体地址(草稿.封面图片)">
          <div v-else class="封面预览 封面占位"><span style="font-size:12px;color:#fff">无封面</span></div>
          <div style="flex:1"></div>
          <el-upload
            :auto-upload="false"
            :show-file-list="false"
            accept="image/*"
            :on-change="传封面">
            <el-button size="small" icon="el-icon-upload2" :loading="传图中">{{ 传图中 ? '上传中…' : '选择图片上传' }}</el-button>
          </el-upload>
          <el-button v-if="草稿.封面图片" size="small" @click="草稿.封面图片 = ''">移除</el-button>
        </div>
      </div>
      <div class="编块">
        <div class="编名">保存地址（工程 / 产物保存目录）</div>
        <el-input v-model="草稿.保存地址" placeholder="如 D:/产物/火影之禁术教师" clearable></el-input>
      </div>
      <div class="编块">
        <div class="编名">创作状态</div>
        <el-radio-group v-model="草稿.状态">
          <el-radio-button v-for="s in ['草稿', '创作中', '已完成']" :key="s" :label="s">{{ s }}</el-radio-button>
        </el-radio-group>
      </div>
      <div slot="footer">
        <el-button @click="编辑显示 = false">取消</el-button>
        <el-button type="primary" :loading="保存中" @click="保存编辑()">保存</el-button>
      </div>
    </el-dialog>

    <!-- 导入剧本弹窗：粘贴单集文本 → 解析场次 → 覆盖写入该集 -->
    <el-dialog :visible.sync="导入显示" title="导入剧本" width="640px" top="6vh" :close-on-click-modal="false">
      <el-form label-width="80px" size="small">
        <el-form-item label="目标剧">
          <el-select v-model="导入剧id" placeholder="选择要写入的剧" style="width:100%">
            <el-option v-for="剧 in 全部" :key="剧.id" :label="剧.剧名" :value="剧.id"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="集号">
          <el-input-number v-model="导入集" :min="1" :max="500"></el-input-number>
          <span style="margin-left:10px;font-size:12px;color:var(--字弱)">该集现有剧本会被覆盖，其余集不受影响</span>
        </el-form-item>
        <el-form-item label="剧本文本">
          <el-input
            v-model="导入文本"
            type="textarea"
            :rows="10"
            placeholder="粘贴单集剧本。支持「场次号 · 内/外 · 地点 · 日/夜」开头的场次格式，识别不出场次就整段作为该集正文"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="导入显示 = false">取消</el-button>
        <el-button type="primary" :loading="导入中" @click="确认导入()">解析并写入</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { 请求, 基础地址, 取令牌, 取, 发 } from '@/接口/请求'
import { 媒体地址 } from '@/接口/媒体'
import { 解析生成结果, 数字数 } from '@/共用/剧本档案'

export default {
  name: 'ScriptList',
  data() {
    return {
      全部: [],
      加载中: false,
      报错: '',
      关键词: '',
      /* 导入剧本弹窗 */
      导入显示: false,
      导入中: false,
      导入剧id: null,
      导入集: 1,
      导入文本: '',
      当前状态: '全部',
      状态选项: ['全部', '草稿', '创作中', '已完成'],
      排序: '最近更新',
      /* 编辑弹窗 */
      编辑显示: false,
      保存中: false,
      传图中: false,
      编辑id: 0,
      草稿: { 封面图片: '', 保存地址: '', 状态: '草稿' }
    }
  },
  computed: {
    展示列表() {
      const 词 = this.关键词.trim()
      let 结果 = this.全部.filter(function (剧) {
        const 匹配状态 = this.当前状态 === '全部' || 剧.状态 === this.当前状态
        const 匹配词 = !词 || 剧.剧名.indexOf(词) >= 0 || 剧.题材.indexOf(词) >= 0
        return 匹配状态 && 匹配词
      }, this)
      if (this.排序 === '进度优先') {
        结果 = 结果.slice().sort(function (a, b) { return b.创作进度 - a.创作进度 })
      } else if (this.排序 === '集数最多') {
        结果 = 结果.slice().sort(function (a, b) { return b.集数 - a.集数 })
      } else {
        结果 = 结果.slice().sort(function (a, b) { return a.更新时间 < b.更新时间 ? 1 : -1 })
      }
      return 结果
    }
  },
  created() {
    this.载入()
  },
  methods: {
    媒体地址,
    async 载入() {
      this.加载中 = true
      this.报错 = ''
      try {
        const 数据 = await 请求('/api/剧列表')
        this.全部 = 数据.列表 || []
      } catch (e) {
        this.报错 = e.message || '加载失败'
      } finally {
        this.加载中 = false
      }
    },
    封面色(名) {
      /* 按剧名取稳定渐变色，无封面时的占位 */
      const 色组 = [
        'linear-gradient(135deg,#3f5efb,#8e44ad)',
        'linear-gradient(135deg,#e96e5b,#c0392b)',
        'linear-gradient(135deg,#11998e,#38ef7d)',
        'linear-gradient(135deg,#fc4a1a,#f7b733)',
        'linear-gradient(135deg,#2193b0,#6dd5ed)'
      ]
      let h = 0
      for (let i = 0; i < String(名).length; i++) h = (h * 31 + String(名).charCodeAt(i)) >>> 0
      return 色组[h % 色组.length]
    },
    状态类(状态) {
      if (状态 === '创作中') return '进行'
      if (状态 === '已完成') return '完成'
      return '草稿态'
    },
    打开剧本(剧) {
      this.$router.push({ path: '/script/plan', query: { 剧名: 剧.剧名, 集数: 剧.集数, 题材: 剧.题材, id: 剧.id } })
    },
    开编辑(剧) {
      this.编辑id = 剧.id
      this.草稿 = { 封面图片: 剧.封面图片 || '', 保存地址: 剧.保存地址 || '', 状态: 剧.状态 }
      this.编辑显示 = true
    },
    async 传封面(文件) {
      const 原文件 = 文件.raw || 文件
      if (!原文件) return
      this.传图中 = true
      try {
        const 表单 = new FormData()
        表单.append('文件', 原文件)
        const 响应 = await fetch(基础地址 + '/api/上传', {
          method: 'POST',
          headers: { Authorization: 'Bearer ' + 取令牌() },
          body: 表单
        })
        const 数据 = await 响应.json()
        if (!响应.ok || 数据.ok === false) throw new Error(数据.error || '上传失败')
        this.草稿.封面图片 = 数据.路径 || 数据.url || ''
        this.$message.success('封面上传成功，点保存生效')
      } catch (e) {
        this.$message.error(e.message || '上传失败')
      } finally {
        this.传图中 = false
      }
    },
    async 保存编辑() {
      this.保存中 = true
      try {
        await 请求('/api/剧/修改', {
          方法: 'POST',
          数据: {
            id: this.编辑id,
            封面图片: this.草稿.封面图片,
            保存地址: this.草稿.保存地址,
            状态: this.草稿.状态
          }
        })
        this.$message.success('已保存')
        this.编辑显示 = false
        this.载入()
      } catch (e) {
        this.$message.error(e.message || '保存失败')
      } finally {
        this.保存中 = false
      }
    },
    async 删除(剧) {
      try {
        await this.$confirm(
          '确定删除《' + 剧.剧名 + '》？\n其方案、分集、剧本、分镜、成片将一并删除，不可恢复。',
          '删除剧', { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
        )
      } catch (e) { return }
      try {
        await 请求('/api/剧/删除', { 方法: 'POST', 数据: { id: 剧.id } })
        this.$message.success('已删除《' + 剧.剧名 + '》')
        this.载入()
      } catch (e) {
        this.$message.error(e.message || '删除失败')
      }
    },
    提示(文本) {
      this.$message({ message: 文本, type: 'info', duration: 2000 })
    },
    /* ---------------- 导入剧本（真链路：解析场次 → 覆盖该集落库） ---------------- */
    打开导入() {
      const 页 = this
      if (!(页.全部 || []).length) {
        页.$message.warning('还没有剧，先点「新建剧本」立项')
        return
      }
      页.导入剧id = 页.全部[0].id
      页.导入集 = 1
      页.导入显示 = true
    },
    async 确认导入() {
      const 页 = this
      if (!页.导入剧id) {
        页.$message.warning('先选目标剧')
        return
      }
      const 文本 = String(页.导入文本 || '').trim()
      if (!文本) {
        页.$message.warning('先粘贴剧本文本')
        return
      }
      页.导入中 = true
      try {
        const 解 = 解析生成结果(文本)
        if (!解.正文 && !(解.场们 || []).length) throw new Error('解析不出正文内容')
        /* 读现有剧本库，除目标集外原样保留（保存接口是全量替换语义） */
        const 数据 = await 取('/api/剧本/列表?剧id=' + 页.导入剧id)
        const 旧行们 = (数据 && 数据.剧本们) || []
        const 集们 = 旧行们.map(function (行) {
          return {
            集号: 行.集号, 标题: 行.标题 || '', 正文: 行.正文 || '',
            能力档案: 行.能力档案 || '', 世界状态: 行.世界状态 || '',
            关系网络: 行.关系网络 || '', 记忆回廊: 行.记忆回廊 || '', 行动推荐: 行.行动推荐 || '',
            状态: 行.状态 || '待复核',
            场们: (行.场次们 || []).map(function (场) {
              return { 场: 场.场, 地点: 场.地点, 人物: 场.人物, 道具: 场.道具, 正文: 场.正文 }
            })
          }
        }).filter(function (行) { return 行.集号 !== 页.导入集 })
        const 旧标题 = (旧行们.filter(function (行) { return 行.集号 === 页.导入集 })[0] || {}).标题 || ''
        集们.push({
          集号: 页.导入集, 标题: 旧标题 || ('第 ' + 页.导入集 + ' 集'),
          正文: 解.正文 || '',
          能力档案: '', 世界状态: '', 关系网络: '', 记忆回廊: '', 行动推荐: '',
          状态: '待复核',
          场们: (解.场们 || []).map(function (场) {
            return { 场: 场.场, 地点: 场.地点, 人物: 场.人物, 道具: 场.道具, 正文: 场.正文 }
          })
        })
        集们.sort(function (a, b) { return a.集号 - b.集号 })
        await 发('/api/剧本/保存', { 剧id: 页.导入剧id, 集们: 集们 })
        页.导入显示 = false
        页.导入文本 = ''
        页.$message.success('已导入第 ' + 页.导入集 + ' 集（' + 数字数(解.正文) + ' 字 · ' + (解.场们 || []).length + ' 场），状态：待复核')
        页.载入()
      } catch (e) {
        页.$message.error('导入失败：' + ((e && e.message) || e))
      }
      页.导入中 = false
    }
  }
}
</script>

<style scoped>
.剧卡 { cursor: pointer; transition: border-color .15s, transform .15s; min-width: 0; }
.剧卡:hover { border-color: var(--主); transform: translateY(-2px); }

.封面 {
  width: 100%;
  height: 130px;
  object-fit: cover;
  border-radius: 8px;
  display: block;
}
.封面占位 {
  display: flex;
  align-items: center;
  justify-content: center;
}
.占位字 {
  color: rgba(255,255,255,.92);
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 2px;
  text-shadow: 0 1px 4px rgba(0,0,0,.25);
}

.状态签 {
  font-size: 11px;
  border-radius: 4px;
  padding: 2px 8px;
  flex: 0 0 auto;
}
.状态签.草稿态 { color: var(--字次); background: var(--卡片二, var(--描边)); border: 1px solid var(--描边); }
.状态签.进行 { color: var(--主); background: var(--主浅, rgba(64,158,255,.12)); }
.状态签.完成 { color: var(--成, #67c23a); background: rgba(103,194,58,.12); }

.存址 { margin-top: 8px; gap: 6px; font-size: 11px; color: var(--字弱); min-width: 0; }
.存址文 { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.封面预览 {
  width: 96px;
  height: 54px;
  object-fit: cover;
  border-radius: 6px;
  display: block;
  background: var(--描边);
}

.编块 { margin-bottom: 16px; }
.编名 { font-size: 12px; color: var(--字次); margin-bottom: 6px; }
</style>
