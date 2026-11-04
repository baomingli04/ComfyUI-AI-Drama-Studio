<template>
  <div class="创作模块">
    <!-- 返回 / 剧名 / 集数 -->
    <div class="行间" style="margin-bottom:16px">
      <span class="面包屑条" style="margin:0">
        <span class="可点" @click="$router.push('/script')">← 返回</span>
      </span>
      <span class="剧名">{{ 剧名 }}</span>
      <span class="集数标签">{{ 集数 }}集</span>
    </div>

    <!-- 四步进度条：点任意一步即跳到那一步（第 2~4 步各是独立页） -->
    <step-bar :步骤="步骤" :当前步="当前序号" @切换="跳到步骤页($event)"></step-bar>

    <!-- 信息条 -->
    <div class="提示条">
      <span>创作方案由 AI 生成并自动保存；选一张方案卡再进方案详情。</span>
      <el-button type="text" class="黄链" @click="前往分集大纲()">前往分集目录调整</el-button>
    </div>

    <!-- 载入中 / 载入报错 -->
    <div v-if="载入中" class="卡片" style="text-align:center;padding:48px 0;color:var(--字弱)">
      <i class="el-icon-loading" style="font-size:22px"></i>
      <div style="margin-top:10px;font-size:13px">正在载入剧与方案…</div>
    </div>
    <div v-else-if="载入报错" class="卡片" style="text-align:center;padding:40px 0">
      <div style="color:#ef4444;font-size:13px;margin-bottom:12px">{{ 载入报错 }}</div>
      <el-button size="mini" @click="载入()">重试</el-button>
    </div>

    <template v-else>
    <!-- Tabs：选方案 / 创作方案（参考页 11 里「选方案」为当前项） -->
    <div class="行间" style="justify-content:center;margin-bottom:16px">
      <div class="标签组">
        <button class="项 当前">选方案</button>
        <button class="项" @click="下一步()">创作方案</button>
      </div>
    </div>

    <!-- 方案卡 -->
    <div class="卡片">
      <div class="提示语">内容由 AI 生成，请仔细阅读重要信息</div>

      <div class="网格 二">
        <div
          v-for="(方案, 序) in 方案列表"
          :key="方案.id || 序"
          class="方案卡"
          :class="{ 选中: 选中 === 方案.id }"
          @click="选方案(方案.id)">
          <div class="行间" style="margin-bottom:12px">
            <span class="方案序">{{ 方案.版本号 || ('方案 ' + (序 + 1)) }}</span>
            <span v-if="选中 === 方案.id" class="小标签">已选</span>
            <div style="flex:1"></div>
            <!-- 编辑：@click.stop 免得点编辑顺带把卡片选中 -->
            <el-button size="mini" icon="el-icon-edit" @click.stop="打开编辑(序)">编辑</el-button>
          </div>
          <div class="方案标题">{{ 方案.标题 }}</div>
          <div class="字段行"><div class="名">故事线</div><div class="值">{{ 方案.故事线 }}</div></div>
          <div class="字段行"><div class="名">推荐题材</div><div class="值">{{ 方案.题材 }}</div></div>
          <div class="字段行"><div class="名">基调</div><div class="值">{{ 方案.基调 }}</div></div>
          <div class="字段行"><div class="名">结局类型</div><div class="值">{{ 方案.结局 }}</div></div>
          <div class="字段行"><div class="名">核心驱动</div><div class="值">{{ 方案.驱动 }}</div></div>
          <div class="字段行"><div class="名">风险展示</div><div class="值">{{ 方案.风险 }}</div></div>
        </div>
      </div>

      <!-- AI 返回的原文兜底：格式没认出「方案 N / 字段：值」时放这里，不硬塞进卡片 -->
      <div v-if="原始结果" class="原始结果">
        <div class="行间" style="margin-bottom:8px">
          <div class="意见标题">AI 原文（格式未识别，没有写入方案卡）</div>
          <div style="flex:1"></div>
          <el-button type="text" size="mini" @click="原始结果 = ''">收起</el-button>
        </div>
        <pre class="原文">{{ 原始结果 }}</pre>
      </div>

      <!-- 底部操作条：修改意见 -->
      <div class="意见条">
        <div class="行间">
          <div class="行间">
            <div class="AI标">AI</div>
            <div>
              <div class="意见标题">修改意见</div>
              <div class="意见价">0.2 积分/次</div>
            </div>
          </div>
          <div style="flex:1"></div>
          <div class="意见例如">例如：加强师徒感、女主更主动、反转再早一点...</div>
          <el-button size="mini" icon="el-icon-setting" @click="打开技能弹窗()">技能</el-button>
          <el-button size="mini" type="primary" plain :loading="生成方案中" @click="生成方案()">
            AI 生成 4 个方案
          </el-button>
        </div>

        <div class="行间" style="margin-top:12px;flex-wrap:wrap">
          <div
            v-for="议 in 意见选项"
            :key="议"
            class="意见chip"
            :class="{ 选中: 意见.indexOf(议) >= 0 }"
            @click="切换意见(议)">{{ 议 }}</div>
          <div style="flex:1"></div>
          <div class="行间">
            <span class="意见价">10 积分</span>
            <div class="上传钮" title="上传参考文档（.txt/.md，内容会作为修改参考喂给 AI）" @click="上传()">
              <i class="el-icon-upload2"></i>
            </div>
            <input
              ref="参考文件"
              type="file"
              accept=".txt,.md,.markdown,text/plain"
              style="display:none"
              @change="读参考文件($event)" />
          </div>
          <div v-if="上传参考名" class="行间" style="margin-top:8px">
            <el-tag size="mini" closable @close="清参考()">
              <i class="el-icon-document"></i> 参考：{{ 上传参考名 }}（{{ 参考字数 }} 字）
            </el-tag>
          </div>
        </div>

        <div class="行间 右" style="margin-top:16px">
          <el-button @click="$router.push('/script/new')">上一步：故事起点</el-button>
          <el-button :loading="保存中" @click="保存方案()">保存</el-button>
          <el-button type="primary" @click="下一步()">下一步：方案详情</el-button>
        </div>
      </div>

      <!-- AI 生成进度条遮罩：首次进页自动生成 / 手动重新生成 时都走它 -->
      <div v-if="生成方案中" class="生成遮罩">
        <div class="生成框">
          <div class="生成标题"><i class="el-icon-loading"></i> AI 正在生成 4 个候选方案…</div>
          <el-progress :percentage="Math.floor(生成进度)" :stroke-width="10"></el-progress>
          <div class="生成注">生成完成会自动保存到数据库，可离开本页稍后回来</div>
        </div>
      </div>
    </div>
    </template>

    <!-- 技能生成：点「技能」打开弹窗配置（技能 + 技能引导提示词 + 引入数据），
         点「AI 生成 4 个方案」用这套配置 + 实时剧信息重新产出 4 张方案卡。
         注意：in-DOM 模板只认 ASCII 标签名，必须用 skill-dialog 别名（见 docs/09 第 8 节）。 -->
    <skill-dialog
      :显示.sync="技能弹窗显示"
      :技能列表="技能列表"
      :技能id.sync="扩写技能id"
      :引导.sync="技能引导"
      :默认引导="页规则"
      :配置类型="页配置类型"
      :引入数据="引入数据列表"
      目标名="创作方案"
      @保存="技能已存过 = true"></skill-dialog>

    <!-- 方案编辑弹窗：点方案卡上的「编辑」打开，改完点保存写回这张卡 -->
    <el-dialog
      :visible.sync="编辑显示"
      width="640px"
      top="7vh"
      custom-class="方案编辑弹窗"
      :show-close="false"
      :close-on-click-modal="false">
      <div class="弹窗头">
        <div>
          <div class="弹窗标题">编辑方案 {{ 编辑序 + 1 }}</div>
          <div class="弹窗副题">改完点保存，直接写回这张方案卡</div>
        </div>
        <i class="el-icon-close 弹窗关闭" title="关闭" @click="编辑显示 = false"></i>
      </div>

      <div class="弹窗体">
        <el-form label-width="90px" size="small">
          <el-form-item label="标题">
            <el-input v-model="草稿.标题" maxlength="30" placeholder="这一版的核心卖点，12 字内最好"></el-input>
          </el-form-item>
          <el-form-item label="故事线">
            <el-input type="textarea" :rows="3" v-model="草稿.故事线" placeholder="谁遇上什么事、怎么走"></el-input>
          </el-form-item>
          <el-form-item label="推荐题材">
            <el-input v-model="草稿.题材" placeholder="2~4 个词，空格分隔"></el-input>
          </el-form-item>
          <el-form-item label="基调">
            <el-input v-model="草稿.基调" placeholder="例：热血向、轻松幽默"></el-input>
          </el-form-item>
          <el-form-item label="结局类型">
            <el-input v-model="草稿.结局" placeholder="例：大团圆（HE）"></el-input>
          </el-form-item>
          <el-form-item label="核心驱动">
            <el-input type="textarea" :rows="2" v-model="草稿.驱动" placeholder="推着故事往前走的那个东西"></el-input>
          </el-form-item>
          <el-form-item label="风险展示">
            <el-input type="textarea" :rows="2" v-model="草稿.风险" placeholder="这一版最容易翻车的点"></el-input>
          </el-form-item>
        </el-form>
      </div>

      <div class="弹窗底">
        <span class="底注">保存只改这一张卡，不影响其他方案。</span>
        <el-button size="small" @click="编辑显示 = false">取消</el-button>
        <el-button size="small" type="primary" @click="保存编辑()">保存</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import 步骤条 from '@/共用/步骤条/index.vue'
import 技能生成弹窗 from '@/共用/技能生成弹窗/index.vue'
import 剧本页混入 from '@/共用/剧本页混入'
import { 读引导, 读技能id, 适配技能id } from '@/共用/技能生成配置'
import { 取, 发 } from '@/接口/请求'
import { 提交AI任务 } from '@/共用/AI任务'

// 本页（创作方案）默认引导提示词：库里没存本页配置时用它，用户可在「技能」弹窗里改。
// 第 2 条把输出格式写死，前端才能按「方案 N / 字段：值」拆成 4 张卡（见 写入方案卡）。
const 创作方案默认规则 = [
  '1. 你要写的是短剧「创作方案」文案，不是视频/图片提示词：禁止输出 <Picture N>、<Video N>、<Audio N> 之类标签，也不要写镜头、光影、音效。',
  '2. 一次输出 4 个互不相同的方案，严格按下面格式；每个方案 7 行，字段名一个字都不能改，方案之间空一行：',
  '方案 1',
  '标题：（12 字内，点明这一版的核心卖点）',
  '故事线：（2~3 句，谁遇上什么事、怎么走）',
  '推荐题材：（2~4 个词，空格分隔）',
  '基调：（1~2 个词 + 一句说明）',
  '结局类型：（HE / BE / OE + 一句说明）',
  '核心驱动：（1~2 句，推着故事往前走的那个东西）',
  '风险展示：（1~2 句，这一版最容易翻车的点）',
  '（方案 2、方案 3、方案 4 同上面这 7 行格式，只换内容）',
  '3. 用户给了修改意见时，只在原方案上改被点名的部分，不推倒重写，不动没被要求的部分。',
  '4. 不新增用户没提的角色、情节和元素。',
  '5. 只输出正文，不要解释、不要前后缀。'
].join('\n')

// 「方案 N」后面跟的字段名 → 卡片字段，容错几种常见写法
const 字段对照 = {
  标题: '标题', 方案标题: '标题',
  故事线: '故事线', 故事主线: '故事线',
  推荐题材: '题材', 题材: '题材',
  基调: '基调', 整体基调: '基调',
  结局类型: '结局', 结局: '结局',
  核心驱动: '驱动', 驱动: '驱动',
  风险展示: '风险', 风险: '风险'
}

const 卡字段 = ['标题', '故事线', '题材', '基调', '结局', '驱动', '风险']

export default {
  name: 'ScriptPlan',
  mixins: [剧本页混入],
  components: { 'step-bar': 步骤条, 'skill-dialog': 技能生成弹窗 },
  created() {
    this.载入技能配置()
    this.载入()
  },
  data() {
    return {
      // 剧：从数据库实时取（/api/剧/详情），标题/题材/起点方式都以后端为准
      剧: null,
      载入中: true,
      载入报错: '',
      // 方案卡：后端 方案 表的行（候选卡 JSON 摊平成七个字段直接用）
      方案列表: [],
      选中: 0,
      意见: [],
      上传参考文本: '',
      上传参考名: '',
      意见选项: ['加强师徒感', '女主更主动', '反转再早一点', '结局改成大团圆'],
      // 技能生成弹窗：技能 + 引导 + 引入数据，保存后「AI 生成 4 个方案」用这套
      技能弹窗显示: false,
      技能引导: '',
      技能已存过: false,
      生成方案中: false,
      生成进度: 0,
      原始结果: '',
      保存中: false,
      // 方案编辑弹窗
      编辑显示: false,
      编辑序: 0,
      草稿: { 标题: '', 故事线: '', 题材: '', 基调: '', 结局: '', 驱动: '', 风险: '' }
    }
  },
  computed: {
    参考字数() {
      return (this.上传参考文本 || '').length
    },
    剧名() {
      return (this.剧 && this.剧.剧名) || this.$route.query.剧名 || ''
    },
    集数() {
      return (this.剧 && this.剧.集数) || this.$route.query.集数 || '1'
    },
    题材() {
      return (this.剧 && this.剧.题材) || this.$route.query.题材 || ''
    },
    剧id() {
      return (this.剧 && this.剧.id) || parseInt(this.$route.query.id, 10) || 0
    },
    页规则() {
      return 创作方案默认规则
    },
    // 技能弹窗第 3 段「引入数据」：取剧记录当前值（实时最新），来自 /script/new 的故事起点
    引入数据列表() {
      return [
        { 键: '起点', 名: '故事起点', 值: (this.剧 && this.剧.起点方式) || '原创', 提示: '/script/new 的故事起点方式' },
        { 键: '标题', 名: '标题', 值: this.剧名, 提示: '剧名' },
        { 键: '标签', 名: '题材标签', 值: this.题材, 提示: '/script/new 选择的题材（最多 2 个）' },
        { 键: '创意', 名: '一句话创意', 值: (this.剧 && this.剧.创意) || this.$route.query.创意 || '', 可编辑: true, 提示: '方案生成的种子' }
      ]
    }
  },
  methods: {
    // 进页面：先实时取剧，再取方案；库里一个方案都没有就当场让 AI 生成（带进度条）
    async 载入() {
      this.载入中 = true
      this.载入报错 = ''
      try {
        await this.取剧()
        if (!this.剧id) {
          this.载入报错 = '找不到这部剧：请从「我的剧」或「新建剧本」进入本页'
          return
        }
        await this.取方案()
        if (!this.方案列表.length) {
          // 第一次进来没有数据：四个方案由 AI 当场生成
          this.$message({ message: '还没有方案，AI 正在为本剧生成 4 个候选方案…', type: 'info' })
          await this.生成方案({ 静默: true })
        }
      } catch (e) {
        this.载入报错 = (e && e.message) || '载入失败'
      } finally {
        this.载入中 = false
      }
    },
    // 实时取剧：优先用路由 id，没有就在我的剧列表里按剧名找
    async 取剧() {
      const id = parseInt(this.$route.query.id, 10)
      if (id) {
        try {
          const 数据 = await 取('/api/剧/详情?id=' + id)
          if (数据 && 数据.ok) {
            this.剧 = 数据.剧
            return
          }
        } catch (e) { /* 落到按剧名找 */ }
      }
      if (this.$route.query.剧名) {
        const 列表 = await 取('/api/剧列表')
        const 自身 = this
        const 命中 = ((列表 && 列表.列表) || []).find(function (一) { return 一.剧名 === 自身.$route.query.剧名 })
        if (命中) {
          const 数据 = await 取('/api/剧/详情?id=' + 命中.id)
          if (数据 && 数据.ok) this.剧 = 数据.剧
        }
      }
    },
    async 取方案() {
      const 数据 = await 取('/api/方案列表?剧id=' + this.剧id)
      const 行们 = (数据 && 数据.列表) || []
      this.方案列表 = 行们.map(function (行) {
        return Object.assign({ id: 行.id, 版本号: 行.版本号 }, 行.候选卡 || {})
      })
      const 选定行 = 行们.find(function (行) { return 行.是否选定 })
      this.选中 = 选定行 ? 选定行.id : (this.方案列表[0] ? this.方案列表[0].id : 0)
    },
    // 方案卡落库：全量把当前卡片写回 方案 表，并带上选定 id
    async 落库() {
      if (!this.剧id || !this.方案列表.length) return
      const 自身 = this
      const 方案们 = this.方案列表.map(function (卡, 序) {
        const 候选卡 = {}
        for (let i = 0; i < 卡字段.length; i++) 候选卡[卡字段[i]] = 卡[卡字段[i]] || ''
        const 版本字 = '一二三四五六七八九十'
        return {
          id: 卡.id || 0,
          版本号: 卡.版本号 || ('方案' + (版本字[序] || (序 + 1))),
          候选卡: 候选卡
        }
      })
      const 数据 = await 发('/api/方案/保存', { 剧id: this.剧id, 方案们: 方案们, 选定id: this.选中 })
      if (数据 && 数据.ok) {
        // 后端返回带 id 的全量列表：回填，保证新建行拿到 id
        this.方案列表 = 数据.列表.map(function (行) {
          return Object.assign({ id: 行.id, 版本号: 行.版本号 }, 行.候选卡 || {})
        })
        this.选中 = 数据.选定id || 自身.选中
      }
    },
    // 点方案卡=选定：立即落库（是否选定 只在一行上）
    选方案(id) {
      this.选中 = id
      this.落库().catch(function () { /* 落库失败不阻塞选中 */ })
    },
    // 底部「保存」：手动把当前卡片（含手改）全量写回 方案 表
    async 保存方案() {
      if (!this.方案列表.length) {
        this.$message.warning('还没有方案可保存')
        return
      }
      this.保存中 = true
      try {
        await this.落库()
        this.$message.success('方案已保存到数据库')
      } catch (e) {
        this.扩写报错(e)
      } finally {
        this.保存中 = false
      }
    },
    // 铺 n 张空卡（保留已有行 id，解析不出的字段留空由 兜底区 承接）
    铺空卡(n) {
      const 旧 = this.方案列表
      const 版本字 = '一二三四五六七八九十'
      this.方案列表 = Array.apply(null, { length: n }).map(function (_, 序) {
        return Object.assign(
          { id: 旧[序] ? 旧[序].id : 0, 版本号: '方案' + (版本字[序] || (序 + 1)) },
          { 标题: '', 故事线: '', 题材: '', 基调: '', 结局: '', 驱动: '', 风险: '' }
        )
      })
    },
    // 打开某一版方案的编辑弹窗：把卡片字段拷进草稿，改草稿不影响卡片
    打开编辑(序) {
      const 源 = this.方案列表[序]
      if (!源) return
      this.编辑序 = 序
      this.草稿 = {
        标题: 源.标题 || '',
        故事线: 源.故事线 || '',
        题材: 源.题材 || '',
        基调: 源.基调 || '',
        结局: 源.结局 || '',
        驱动: 源.驱动 || '',
        风险: 源.风险 || ''
      }
      this.编辑显示 = true
    },
    // 保存：草稿写回这张卡并落库（只改这一张，不动其他方案）
    async 保存编辑() {
      const 卡 = this.方案列表[this.编辑序]
      if (!卡) {
        this.编辑显示 = false
        return
      }
      if (!(this.草稿.标题 || '').trim()) {
        this.$message.warning('标题不能为空')
        return
      }
      for (let i = 0; i < 卡字段.length; i++) {
        const 键 = 卡字段[i]
        卡[键] = (this.草稿[键] || '').trim()
      }
      this.编辑显示 = false
      try {
        await this.落库()
        this.$message.success('方案 ' + (this.编辑序 + 1) + ' 已保存')
      } catch (e) {
        this.扩写报错(e)
      }
    },
    // 打开「技能 + 技能引导提示词」配置弹窗
    打开技能弹窗() {
      this.技能弹窗显示 = true
    },
    // 进页面先把本页已存的配置带出来
    async 载入技能配置() {
      const 已存引导 = await 读引导(this.页配置类型)
      if (已存引导) {
        this.技能引导 = 已存引导
        this.技能已存过 = true
      }
      const 已存技能 = 读技能id(this.页配置类型)
      if (已存技能) this.扩写技能id = 已存技能
    },
    // AI 生成 4 个方案：技能（剧本创作分类）+ 引导 + 引入数据（实时剧信息）→ 4 张卡 → 落库
    // 首次进页自动生成时带进度条遮罩（生成进度 0→90 随机步进，回包后冲 100）
    async 生成方案(选项) {
      const 静默 = !!(选项 && 选项.静默)
      if (!this.扩写技能id && this.技能列表.length) {
        this.扩写技能id = 适配技能id(this.技能列表, this.页配置类型)
      }
      if (!this.扩写技能id) {
        if (!静默) {
          this.$message.warning('「剧本创作」分类下还没有可用技能，先到技能管理页建一个')
        }
        return
      }
      if (!this.剧id) {
        this.$message.warning('找不到这部剧，无法生成方案')
        return
      }
      const 意见 = this.意见.length ? this.意见.join('、') : ''
      const 引入 = this.引入数据列表
      const 需求 = [
        '故事起点：' + (引入[0].值 || '原创'),
        '剧名：' + this.剧名,
        '题材标签：' + (this.题材 || '未分类'),
        '集数：' + this.集数 + ' 集',
        (引入[3].值 ? '一句话创意：' + 引入[3].值 : ''),
        (this.上传参考文本 ? '【上传参考（结合这份材料出方案）】\n' + this.上传参考文本 : ''),
        意见 ? '修改意见：' + 意见 : '按上面的剧名与题材，产出 4 个方向明显不同的方案'
      ].filter(Boolean).join('\n')
      this.生成方案中 = true
      this.生成进度 = 0
      const 自身 = this
      const 计时 = setInterval(function () {
        if (自身.生成进度 < 90) 自身.生成进度 = Math.min(90, 自身.生成进度 + Math.random() * 6 + 2)
      }, 400)
      try {
        // 统一走任务链路（/api/任务/提交 → 文本回复 → 轮询），测试台任务列表可查、多个 AI 内容排队顺序执行
        const 文本 = await 提交AI任务({
          正向: 需求,
          系统: this.技能引导 || this.页规则
        })
        const 结果 = String(文本 || '').trim()
        if (!文本) {
          this.$message.warning('AI 没有返回内容，可稍后重试')
          return
        }
        // 先铺 4 张空卡再解析写入，保证「一次 4 个」；解析失败要恢复原列表，别把已有方案毁了
        const 旧列表 = this.方案列表
        this.铺空卡(4)
        const 数量 = this.写入方案卡(文本)
        if (数量) {
          this.原始结果 = ''
          await this.落库()
          this.$message.success('已生成 ' + 数量 + ' 个方案并保存，点卡片选一个')
        } else {
          this.方案列表 = 旧列表
          this.原始结果 = 文本
          this.$message.warning('AI 返回的格式没认出「方案 N / 字段：值」，原文放在下面了')
        }
      } catch (e) {
        if (!静默) this.扩写报错(e)
        else this.载入报错 = (e && e.message) || '生成失败'
      } finally {
        clearInterval(计时)
        this.生成进度 = 100
        setTimeout(function () { 自身.生成方案中 = false; 自身.生成进度 = 0 }, 400)
      }
    },
    // 把 AI 文本按「方案 N」切块，再按「字段：值」拆到卡片字段上；返回写入的卡片数
    写入方案卡(文本) {
      const 段们 = String(文本).split(/\n(?=\s*(?:【|\[)?\s*方案\s*[0-9一二三四])/)
      const 结果 = []
      for (let i = 0; i < 段们.length; i++) {
        const 段 = 段们[i].trim()
        if (!/^(?:【|\[)?\s*方案\s*[0-9一二三四]/.test(段)) continue
        const 行们 = 段.split('\n')
        const 项 = {}
        let 当前键 = ''
        for (let j = 0; j < 行们.length; j++) {
          const 行 = 行们[j].replace(/^\s*[-*·]\s*/, '').trim()
          if (!行) continue
          if (/^(?:【|\[)?\s*方案\s*[0-9一二三四]\s*(?:】|\])?\s*$/.test(行)) continue
          const 配 = 行.match(/^([^：:]{2,10})[：:]\s*(.*)$/)
          if (配) {
            当前键 = 字段对照[配[1].trim()] || ''
            if (当前键) 项[当前键] = 配[2].trim()
          } else if (当前键) {
            项[当前键] = (项[当前键] ? 项[当前键] + ' ' : '') + 行
          }
        }
        if (Object.keys(项).length >= 2) 结果.push(项)
      }
      const 数量 = Math.min(this.方案列表.length, 结果.length)
      for (let i = 0; i < 数量; i++) {
        const 卡 = this.方案列表[i]
        const 源 = 结果[i]
        const 键们 = ['标题', '故事线', '题材', '基调', '结局', '驱动', '风险']
        for (let k = 0; k < 键们.length; k++) {
          const 键 = 键们[k]
          if (源[键]) 卡[键] = 源[键]
        }
      }
      return 数量
    },
    切换意见(议) {
      const 位置 = this.意见.indexOf(议)
      if (位置 >= 0) {
        this.意见.splice(位置, 1)
      } else {
        this.意见.push(议)
      }
    },
    上传() {
      this.$refs.参考文件.click()
    },
    读参考文件(ev) {
      const 页 = this
      const 文件 = ev.target.files && ev.target.files[0]
      ev.target.value = ''
      if (!文件) return
      if (文件.size > 2 * 1024 * 1024) {
        页.$message.warning('参考文档超过 2MB，请拆小后再传')
        return
      }
      const 读 = new FileReader()
      读.onload = function () {
        页.上传参考文本 = String(读.result || '').trim().slice(0, 8000)
        页.上传参考名 = 文件.name
        页.$message.success('已读入参考文档「' + 文件.name + '」，重新生成方案时生效')
      }
      读.onerror = function () { 页.$message.error('文件读取失败') }
      读.readAsText(文件, 'utf-8')
    },
    清参考() {
      this.上传参考文本 = ''
      this.上传参考名 = ''
    },
    下一步() {
      if (!this.选中) {
        this.$message.warning('先点一张方案卡选定，才能进方案详情')
        return
      }
      this.$router.push({
        path: '/script/detail',
        query: {
          id: this.剧id,
          剧名: this.剧名,
          集数: this.集数,
          题材: this.题材,
          方案: this.选中,
          // 一句话创意继续往下带，方案详情页「引入数据」要用
          创意: (this.剧 && this.剧.创意) || this.$route.query.创意 || ''
        }
      })
    },
    前往分集大纲() {
      this.$router.push({
        path: '/script/outline',
        query: {
          id: this.剧id,
          剧名: this.剧名,
          集数: this.集数,
          题材: this.题材,
          方案: this.选中,
          创意: (this.剧 && this.剧.创意) || this.$route.query.创意 || ''
        }
      })
    }
  }
}
</script>

<style scoped>
.剧名 { font-size: 14px; font-weight: 500; color: var(--字); }
.集数标签 { font-size: 12px; color: var(--字弱); }

.步骤条.居中 { max-width: 720px; margin: 0 auto 24px; }

.黄链 { color: #f59e0b; font-size: 13px; padding: 0; }

.提示语 { font-size: 12px; color: var(--字弱); margin-bottom: 16px; }

/* AI 生成进度条遮罩：盖在方案卡区上，生成完成自动消失 */
.生成遮罩 {
  position: fixed;
  inset: 0;
  background: rgba(6, 10, 20, 0.62);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1200;
}
.生成框 {
  width: 420px;
  background: #0d1424;
  border: 1px solid #1e293b;
  border-radius: 12px;
  padding: 24px;
}
.生成标题 { font-size: 14px; font-weight: 600; color: var(--字); margin-bottom: 14px; }
.生成注 { margin-top: 12px; font-size: 12px; color: var(--字弱); }

.方案卡 {
  background: var(--卡片二);
  border: 1px solid var(--描边);
  border-radius: 10px;
  padding: 16px;
  cursor: pointer;
  transition: border-color .15s;
}
.方案卡:hover { border-color: var(--描边亮); }
.方案卡.选中 { border-color: var(--主); }
.方案序 { font-size: 13px; font-weight: 500; color: var(--字); }
.方案标题 { font-size: 14px; font-weight: 600; color: var(--字); margin-bottom: 12px; }

.意见条 {
  margin-top: 16px;
  background: var(--卡片二);
  border: 1px solid var(--描边);
  border-radius: 10px;
  padding: 16px;
}
.AI标 {
  width: 40px; height: 40px; border-radius: 999px;
  background: var(--主); color: #06210f;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700;
  flex: 0 0 40px;
}
.意见标题 { font-size: 14px; color: var(--字); font-weight: 500; }
.意见价 { font-size: 12px; color: var(--字弱); }
.意见例如 { font-size: 13px; color: var(--字弱); }

/* AI 原文兜底块：格式没认出时把原文摊开给人看，不硬塞进方案卡 */
.原始结果 {
  margin-top: 16px;
  background: var(--卡片二);
  border: 1px solid var(--描边);
  border-radius: 10px;
  padding: 14px 16px;
}
.原始结果 .原文 {
  margin: 0;
  max-height: 240px;
  overflow: auto;
  font-family: inherit;
  font-size: 12px;
  line-height: 1.8;
  color: var(--字次);
  white-space: pre-wrap;
  word-break: break-word;
}

.意见chip {
  height: 28px; padding: 0 12px;
  border-radius: 6px;
  border: 1px solid var(--描边);
  background: var(--卡片);
  color: var(--字次);
  font-size: 12px;
  display: inline-flex; align-items: center;
  cursor: pointer;
  margin-right: 8px;
}
.意见chip:hover { border-color: var(--描边亮); }
.意见chip.选中 { background: var(--主); border-color: var(--主); color: #06210f; }

.上传钮 {
  width: 32px; height: 32px;
  border-radius: 6px;
  border: 1px solid var(--描边);
  background: var(--卡片);
  display: flex; align-items: center; justify-content: center;
  color: var(--字);
  cursor: pointer;
}
.上传钮:hover { border-color: var(--描边亮); }

/* ---- 方案编辑弹窗（内容部分，scoped 生效）---- */
.弹窗头 {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--描边);
}
.弹窗标题 { font-size: 16px; font-weight: 700; color: var(--字); }
.弹窗副题 { margin-top: 4px; font-size: 12px; color: var(--字弱); }
.弹窗关闭 { margin-left: auto; font-size: 18px; color: var(--字次); cursor: pointer; }
.弹窗关闭:hover { color: #ef4444; }
.弹窗体 { padding: 18px 20px 2px; max-height: 62vh; overflow-y: auto; }
.弹窗底 {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid var(--描边);
  background: var(--卡片二);
}
.弹窗底 .底注 { flex: 1; font-size: 12px; color: var(--字弱); }
</style>

<style>
/* 方案编辑弹窗的外壳：el-dialog 根节点在子组件里，scoped 选不中，单独一段 */
.方案编辑弹窗 {
  background: #0d1424;
  border: 1px solid #1e293b;
  border-radius: 12px;
  box-shadow: 0 16px 56px rgba(0, 0, 0, 0.65);
  overflow: hidden;
}
.方案编辑弹窗 .el-dialog__header { display: none; }
.方案编辑弹窗 .el-dialog__body { padding: 0; }
</style>
