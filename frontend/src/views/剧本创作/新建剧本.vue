<template>
  <div class="创作模块">
    <!-- 页头 -->
    <div class="页头">
      <div class="左">
        <h1 class="标题">新建剧本</h1>
        <div class="副题">定义故事起始场景，再用推荐标签与集数规划项目</div>
      </div>
      <div class="右">
        <el-button @click="$router.push('/script')">返回列表</el-button>
      </div>
    </div>

    <!-- 四步进度条：新建剧本是四步之前的故事起点，四步都还没开始，点任一步可直接跳过去 -->
    <step-bar :步骤="步骤" :当前步="-1" @切换="跳到步骤页($event)"></step-bar>

    <!-- 第 1 步：故事起点（单步页：填完点「开始制作」直接创建项目进方案页） -->
    <div>
      <div class="卡片" style="margin-bottom:16px">
        <div class="行间">
          <!-- 随机开头：点击随机生成 标题/一句话创意/题材标签，填进下面表单可自由修改 -->
          <div class="随机开头钮" :class="{ 忙: 随机中 }" title="点击让 AI 随机生成标题、创意和题材标签" @click="随机开头()">
            {{ 随机中 ? 'AI 生成中…' : '宏观版：随机开头' }}
          </div>
        </div>
      </div>

      <div class="网格 二">
        <div class="卡片">
          <div class="区标题">故事梗概</div>
          <div style="margin-bottom:12px">
            <div style="font-size:13px;color:var(--字次);margin-bottom:6px">剧名</div>
            <el-input v-model="表单.剧名" placeholder="可点选推荐剧名，或自行拟定" maxlength="30"></el-input>
            <div style="font-size:12px;color:var(--字弱);margin-top:4px">{{ 表单.剧名.length }} / 30</div>
          </div>
          <div>
            <div class="行间" style="margin-bottom:8px">
              <div style="font-size:13px;color:var(--字次)">一句话创意</div>
              <div style="flex:1"></div>
              <el-button size="mini" icon="el-icon-setting" @click="打开技能弹窗()">技能</el-button>
              <el-button size="mini" type="primary" plain :loading="扩写中" @click="丰富创意()">AI 丰富梗概</el-button>
            </div>
            <el-input
              type="textarea"
              :rows="9"
              maxlength="500"
              v-model="表单.创意"
              placeholder="例：某日清晨他发现身边人另有身份，两人在误会与信任里从敌对走向彼此并肩...">
            </el-input>
            <div style="font-size:12px;color:var(--字弱);margin-top:4px">{{ 表单.创意.length }} / 500</div>
          </div>
        </div>

        <div class="卡片">
          <div class="区标题">题材标签 · 最多 2 个（主 + 辅）</div>
          <div class="chip组">
            <div
              v-for="项 in 题材选项"
              :key="项.名称"
              class="chip"
              :class="{ 选中: 表单.题材.indexOf(项.名称) >= 0 }"
              @click="切换题材(项.名称)">{{ 项.名称 }}</div>
          </div>
          <!-- 手动添加：新标签写进 题材标签 表，之后所有新项目的标签下拉都能看到它 -->
          <div class="行间" style="margin-top:10px;gap:8px">
            <el-input
              v-model="新标签名"
              size="mini"
              style="width:140px"
              maxlength="20"
              placeholder="添加自定义标签"
              @keyup.enter.native="添加标签()"></el-input>
            <el-button size="mini" icon="el-icon-plus" :loading="加标签中" @click="添加标签()">添加</el-button>
          </div>
          <div style="font-size:12px;color:var(--主);margin-top:8px">
            * 标签保存在数据库，所有新项目共用；未选择标签将使用默认推荐
          </div>

          <el-divider></el-divider>

          <div class="行间" style="margin-bottom:12px">
            <div style="font-size:13px;color:var(--字次);width:48px">集数</div>
            <el-input v-model="表单.集数" style="width:110px">
              <template slot="append">集</template>
            </el-input>
            <div style="font-size:12px;color:var(--字弱)">集数 2~100 集</div>
          </div>

          <div class="行间">
            <div style="font-size:13px;color:var(--字次);width:48px">时长</div>
            <el-select v-model="表单.单集时长" style="width:130px">
              <el-option label="每集 2 分钟" value="2 分钟"></el-option>
              <el-option label="每集 3 分钟" value="3 分钟"></el-option>
              <el-option label="每集 5 分钟" value="5 分钟"></el-option>
            </el-select>
            <div style="font-size:12px;color:var(--字弱)">
              本剧预计 {{ 预计时长 }} 分钟，分集时长仅作参考
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 技能生成：点「技能」打开弹窗配置（技能 + 技能引导提示词 + 保存），
         点「AI 丰富梗概」直接用这套配置生成，结果回填到「一句话创意」。
         注意：in-DOM 模板只认 ASCII 标签名，必须用 skill-dialog 这种别名，
         直接写中文标签名会被浏览器当纯文本显示出来（见 docs/09 第 8 节）。 -->
    <skill-dialog
      :显示.sync="技能弹窗显示"
      :技能列表="技能列表"
      :技能id.sync="扩写技能id"
      :引导.sync="技能引导"
      :默认引导="页规则"
      :配置类型="页配置类型"
      :引入数据="引入数据列表"
      目标名="梗概"
      @保存="技能已存过 = true"></skill-dialog>

    <!-- 底部按钮 -->
    <div class="行间 右" style="margin-top:20px">
      <el-button @click="保存()">保存</el-button>
      <el-button type="primary" :loading="保存中" @click="开始创作()">开始制作</el-button>
    </div>
  </div>
</template>

<script>
import 步骤条 from '@/共用/步骤条/index.vue'
import 技能生成弹窗 from '@/共用/技能生成弹窗/index.vue'
import 剧本页混入 from '@/共用/剧本页混入'
import { 读引导, 读技能id, 适配技能id } from '@/共用/技能生成配置'
import { 取, 发 } from '@/接口/请求'
import { 提交AI任务 } from '@/共用/AI任务'

// 未走完「开始创作」的内容暂存本机：创意不满 20 字进不了库，刷新/返回也不丢
const 草稿键 = '剧本草稿:script/new'

// 本页（故事起点）默认扩写规则：库里没存本页配置时用它，用户可在「技能」弹窗里改。
// 第 2 条把输出格式写死：固定「标题：/创意：」两行，前端按行解析回填（见 解析丰富结果）。
const 故事起点默认规则 = [
  '1. 你要写的是短剧「故事起点」信息，不是视频/图片提示词：禁止输出 <Picture N>、<Video N>、<Audio N> 之类标签，也不要写镜头、光影、音效。',
  '2. 只输出下面两行，字段名一个字都不能改：',
  '标题：（最多 30 字，短、好记、有钩子）',
  '创意：（不超过 500 字，一句话说清主角、处境、转折，以及为什么想看下一集）',
  '3. 用户已给标题时沿用原标题（只润色创意）；没给标题时新起一个。已有创意时在其基础上丰富，不推倒重写。',
  '4. 不新增用户没提的角色、情节和元素。',
  '5. 只输出正文，不要解释、不要前后缀。'
].join('\n')

export default {
  name: 'ScriptNew',
  mixins: [剧本页混入],
  components: { 'step-bar': 步骤条, 'skill-dialog': 技能生成弹窗 },
  created() {
    this.载入技能配置()
    this.载入标签()
    this.恢复草稿()
  },
  data() {
    return {
      // 本页是四步之前的故事起点：四步进度条上没有任何一步是“当前/完成”
      当前序号: -1,
      // 技能生成弹窗：技能 + 技能引导提示词，保存后「AI 丰富梗概」用这套生成
      技能弹窗显示: false,
      技能引导: '',
      技能已存过: false,
      保存中: false,
      // 「开始制作」正式创建项目时拿到的剧 id / 当前状态；本会话是否由本页新建（重复创建按同名续用）
      剧id: 0,
      剧状态: '',
      本会话已建: false,
      随机中: false,
      // 题材标签：全部从数据库 题材标签 表读（[{id,名称,系统内置}]），手动添加也写回这张表
      题材选项: [],
      新标签名: '',
      加标签中: false,
      表单: {
        剧名: '',
        集数: '24',
        创意: '',
        题材: [],
        风格: '写实校园',
        单集时长: '2 分钟'
      }
    }
  },
  computed: {
    预计时长() {
      const 集数 = parseInt(this.表单.集数, 10)
      const 单集 = parseInt(this.表单.单集时长, 10)
      if (isNaN(集数) || isNaN(单集)) return 0
      return 集数 * 单集
    },
    页规则() {
      return 故事起点默认规则
    },
    // 技能弹窗第 3 段「引入数据」：始终取表单当前值（实时最新），弹窗每次打开重新拷贝
    引入数据列表() {
      return [
        { 键: '创意', 名: '一句话创意', 值: this.表单.创意, 可编辑: true, 提示: 'AI 在这句的基础上丰富' },
        { 键: '标题', 名: '标题', 值: this.表单.剧名, 提示: '为空时 AI 会新起一个' },
        { 键: '标签', 名: '题材标签', 值: this.表单.题材.join('、'), 提示: '最多 2 个（主 + 辅）' }
      ]
    }
  },
  methods: {
    // 「保存」= 存草稿：够入库条件就落库（新剧状态=草稿），不够暂存本机
    async 保存() {
      this.暂存草稿()
      if (await this.尝试落库()) {
        this.$message.success('已保存到数据库（剧列表里可见）')
      } else {
        this.$message({ message: '已暂存本机为草稿；创意满 20 字、集数 2~100 后可入库', type: 'info' })
      }
    },
    // 本地草稿：任何时刻切走都先暂存，刷新/返回不丢
    暂存草稿() {
      try {
        localStorage.setItem(草稿键, JSON.stringify(this.表单))
      } catch (e) { /* 存不进就算了，不阻塞 */ }
    },
    恢复草稿() {
      try {
        const 原文 = localStorage.getItem(草稿键)
        if (!原文) return
        const 草稿 = JSON.parse(原文)
        if (!草稿 || typeof 草稿 !== 'object') return
        const 键们 = ['剧名', '集数', '创意', '题材', '风格', '单集时长']
        for (let i = 0; i < 键们.length; i++) {
          const 键 = 键们[i]
          if (草稿[键] !== undefined && 草稿[键] !== null) this.表单[键] = 草稿[键]
        }
        if (草稿.剧名 || 草稿.创意) {
          this.$message({ message: '已恢复上次「保存」暂存的草稿', type: 'info' })
        }
      } catch (e) { /* 草稿坏了就当没有 */ }
    },
    // 内容够入库条件（剧名 + 创意≥20字 + 集数 2~100）时落库；返回 true/false
    async 尝试落库() {
      const 创意 = (this.表单.创意 || '').trim()
      const 集数 = parseInt(this.表单.集数, 10)
      if (!this.表单.剧名.trim() || 创意.length < 20 || !(集数 >= 2 && 集数 <= 100)) return false
      try {
        await this.存剧库()
        return true
      } catch (e) {
        return false
      }
    },
    // 落库本体：先试新增；剧名已被用过时找到同名剧续用（同一部剧，不重复建）
    async 存剧库() {
      const 集数 = parseInt(this.表单.集数, 10)
      try {
        const 数据 = await 发('/api/剧/新增', {
          剧名: this.表单.剧名.trim(),
          集数: 集数,
          题材: this.表单.题材.join('、') || '未分类',
          创意: (this.表单.创意 || '').trim(),
          起点方式: '原创'
        })
        this.剧id = (数据 && 数据.id) || 0
        this.剧状态 = '草稿'
        this.本会话已建 = true
      } catch (新增错) {
        const 列表 = await 取('/api/剧列表')
        const 命中 = ((列表 && 列表.列表) || []).find(
          (function (名) { return function (一) { return 一.剧名 === 名 } })(this.表单.剧名.trim())
        )
        if (!命中) throw 新增错
        this.剧id = 命中.id
        this.剧状态 = 命中.状态 || ''
        // 续用已有剧时，把最新的创意同步过去（/api/剧/修改 允许改 创意；≥20 字才走到这）
        if ((this.表单.创意 || '').trim() && (this.表单.创意 || '').trim() !== (命中.创意 || '').trim()) {
          发('/api/剧/修改', { id: this.剧id, 创意: this.表单.创意.trim() })
            .catch(function () { /* 同步失败不阻塞，跳转时 query 里仍带最新创意 */ })
        }
        if (!this.本会话已建) {
          this.$message({ message: '剧「' + 命中.剧名 + '」已存在，继续用这部剧创作', type: 'info' })
        }
      }
      return this.剧id
    },
    // 正式进入创作流程：状态推到「创作中」；已完成的剧不翻回去。失败不阻塞
    置创作中(剧id) {
      if (!剧id || this.剧状态 === '已完成') return
      发('/api/剧/修改', { id: 剧id, 状态: '创作中' }).catch(function () { /* 静默 */ })
      this.剧状态 = '创作中'
    },
    // 随机开头：走任务链路（/api/任务/提交 → 文本回复 任务 → 轮询结果），和 /test/t1-text 同链。
    // AI 随机生成 标题/创意/标签 三件套；解析不出格式时整段放进创意框。
    随机开头() {
      const 自身 = this
      const 需求 = [
        '请为一个短剧项目随机生成开局三件套：风格、年代、题材、主角身份、故事底色都要随机，和常见套路拉开差距。',
        '严格按下面三行输出，字段名一个字都不能改：',
        '标题：（最多 30 字，短、好记、有钩子）',
        '创意：（80~200 字，写清主角、处境、转折、为什么想看下一集）',
        '标签：（2 个词，用「、」分隔，从常见短剧题材里挑，如 都市/逆袭/甜宠/玄幻/悬疑/年代/末世/古装/校园/职场）'
      ].join('\n')
      this.随机中 = true
      提交AI任务({
        正向: 需求,
        系统: '你是短剧项目开局生成器。只输出正文三行（标题/创意/标签），不要解释、不要前后缀。'
      })
        .then(function (文本) {
          const 结果 = String(文本 || '').trim()
          if (!结果) {
            自身.$message.warning('AI 没有返回内容，可稍后重试')
            return
          }
          if (!自身.解析随机结果(结果)) {
            自身.表单.创意 = 结果.slice(0, 500)
            自身.$message.warning('AI 返回格式没认出，已整段放进创意框')
          }
          自身.暂存草稿()
          自身.$message.success('已随机生成 标题 / 一句话创意 / 题材标签，可自由修改')
        })
        .catch(function (e) { 自身.扩写报错(e) })
        .then(function () { 自身.随机中 = false })
    },
    // 解析「标题：/创意：/标签：」三行格式；返回写入的字段数（0=没认出）
    解析随机结果(文本) {
      let 写入数 = 0
      let 标题 = ''
      const 创意行们 = []
      let 标签词们 = []
      let 收创意 = false
      const 行们 = String(文本).split(/\r?\n/)
      for (let i = 0; i < 行们.length; i++) {
        const 行 = 行们[i].trim()
        if (!行) { if (收创意) 创意行们.push(''); continue }
        const 标题配 = 行.match(/^(?:【|\[)?\s*标题(?:】|\])?\s*[：:]\s*(.*)$/)
        const 创意配 = 行.match(/^(?:【|\[)?\s*(?:创意|一句话创意)(?:】|\])?\s*[：:]\s*(.*)$/)
        const 标签配 = 行.match(/^(?:【|\[)?\s*标签(?:】|\])?\s*[：:]\s*(.*)$/)
        if (标题配) { if (!标题) 标题 = 标题配[1].trim(); 收创意 = false }
        else if (创意配) { 创意行们.push(创意配[1].trim()); 收创意 = true }
        else if (标签配) {
          标签词们 = 标签配[1].split(/[、,，;；/|]/).map(function (词) { return 词.trim() })
            .filter(function (词) { return 词 && 词.length <= 6 })
          收创意 = false
        } else if (收创意) { 创意行们.push(行) }
      }
      const 新创意 = 创意行们.join('\n').replace(/\n+$/g, '').trim()
      if (新创意) { this.表单.创意 = 新创意.slice(0, 500); 写入数++ }
      if (标题) { this.表单.剧名 = 标题.slice(0, 30); 写入数++ }
      if (标签词们.length) {
        // 标签词要能对上标签库里的名字才选中，最多 2 个
        const 库名们 = this.题材选项.map(function (项) { return 项.名称 })
        const 命中们 = 标签词们.filter(function (词) { return 库名们.indexOf(词) >= 0 }).slice(0, 2)
        if (命中们.length) { this.表单.题材 = 命中们; 写入数++ }
      }
      return 写入数
    },
    // 选中/取消一个题材标签；最多 2 个（主 + 辅），超了挤掉最早的
    切换题材(项) {
      const 位置 = this.表单.题材.indexOf(项)
      if (位置 >= 0) {
        this.表单.题材.splice(位置, 1)
        return
      }
      if (this.表单.题材.length >= 2) {
        this.表单.题材.shift()
      }
      this.表单.题材.push(项)
    },
    // 题材标签从数据库读：所有新项目共用同一份标签库
    async 载入标签() {
      try {
        const 数据 = await 取('/api/标签')
        if (数据 && 数据.ok && 数据.列表 && 数据.列表.length) {
          this.题材选项 = 数据.列表
        }
      } catch (e) {
        /* 标签拉不到不阻塞页面，留空由用户手动添加 */
      }
    },
    // 手动添加标签：写进 题材标签 表，成功后进列表并自动选中
    async 添加标签() {
      const 名 = (this.新标签名 || '').trim()
      if (!名) {
        this.$message.warning('先填标签名')
        return
      }
      if (this.题材选项.some(function (项) { return 项.名称 === 名 })) {
        this.新标签名 = ''
        this.切换题材(名)
        return
      }
      this.加标签中 = true
      try {
        const 数据 = await 发('/api/标签/新增', { 名称: 名 })
        if (数据 && 数据.ok) {
          this.题材选项.push({ id: 数据.id, 名称: 数据.名称, 系统内置: false })
          this.切换题材(数据.名称)
          this.新标签名 = ''
        } else {
          this.$message.error((数据 && 数据.error) || '添加失败')
        }
      } catch (e) {
        this.$message.error((e && e.message) || '添加失败')
      } finally {
        this.加标签中 = false
      }
    },
    // AI 丰富梗概：免弹窗，点按钮直接用本页技能（剧本创作分类）生成。
    // 没配过技能就用列表第一个 + 本页默认规则；引入数据取表单实时值。
    // 没有标题时让 AI 一并生成标题；已有标题只丰富创意。
    async 丰富创意() {
      if (!this.扩写技能id && this.技能列表.length) {
        this.扩写技能id = 适配技能id(this.技能列表, this.页配置类型)
      }
      if (!this.扩写技能id) {
        this.$message.warning('「剧本创作」分类下还没有可用技能，先到技能管理页建一个')
        return
      }
      const 创意 = (this.表单.创意 || '').trim()
      if (!创意 && !this.表单.剧名.trim() && !this.表单.题材.length) {
        this.$message.warning('先写一句话创意，或选个题材标签，AI 才有下笔的地方')
        return
      }
      const 需求 = [
        this.表单.剧名.trim() ? '标题：' + this.表单.剧名.trim() : '标题：（无，请新起一个）',
        '题材标签：' + (this.表单.题材.join('、') || '未选择'),
        '当前一句话创意：' + (创意 || '（无，请按标题与题材新写）'),
        '要求：输出「标题：/创意：」两行；已有标题沿用原标题，已有创意在其基础上丰富。'
      ].join('\n')
      this.扩写中 = true
      try {
        // 统一走任务链路（/api/任务/提交 → 文本回复 → 轮询），测试台任务列表可查
        const 文本 = await 提交AI任务({
          正向: 需求,
          系统: this.技能引导 || this.页规则
        })
        const 结果 = String(文本 || '').trim()
        if (!结果) {
          this.$message.warning('AI 没有返回内容，可稍后重试')
          return
        }
        const 写入数 = this.解析丰富结果(结果)
        if (写入数) {
          this.$message.success('已丰富「一句话创意」' + (写入数 === 2 ? '并生成标题' : '') + '，可直接修改')
        } else {
          // 格式没认出来：整段当创意用，不硬塞标题
          this.表单.创意 = 结果
          this.$message.success('已丰富「一句话创意」（AI 原文格式略有出入，已整段回填）')
        }
      } catch (e) {
        this.扩写报错(e)
      } finally {
        this.扩写中 = false
      }
    },
    // 解析「标题：xxx / 创意：xxx」格式；创意允许多行（跟到下一个「标题：/创意：」行或文本末尾）。
    // 返回写入的字段数（0=没认出）。
    解析丰富结果(文本) {
      let 写入数 = 0
      let 标题 = ''
      const 创意行们 = []
      let 收创意 = false
      const 行们 = String(文本).split(/\r?\n/)
      for (let i = 0; i < 行们.length; i++) {
        const 行 = 行们[i].trim()
        if (!行) {
          if (收创意) 创意行们.push('')
          continue
        }
        const 标题配 = 行.match(/^(?:【|\[)?\s*标题(?:】|\])?\s*[：:]\s*(.*)$/)
        const 创意配 = 行.match(/^(?:【|\[)?\s*(?:创意|一句话创意)(?:】|\])?\s*[：:]\s*(.*)$/)
        if (标题配) {
          if (!标题) 标题 = 标题配[1].trim()
          收创意 = false
        } else if (创意配) {
          创意行们.push(创意配[1].trim())
          收创意 = true
        } else if (收创意) {
          创意行们.push(行)
        }
      }
      const 新创意 = 创意行们.join('\n').replace(/\n+$/g, '').trim()
      if (新创意) {
        this.表单.创意 = 新创意.slice(0, 500)
        写入数++
      }
      if (!this.表单.剧名.trim() && 标题) {
        this.表单.剧名 = 标题.slice(0, 30)
        写入数++
      }
      return 写入数
    },
    // 打开「技能 + 技能引导提示词 + 引入数据」配置弹窗
    打开技能弹窗() {
      this.技能弹窗显示 = true
    },
    // 进页面先把本页已存的配置带出来（没存过就保持空，等用户点「技能」去配）
    async 载入技能配置() {
      const 已存引导 = await 读引导(this.页配置类型)
      if (已存引导) {
        this.技能引导 = 已存引导
        this.技能已存过 = true
      }
      const 已存技能 = 读技能id(this.页配置类型)
      if (已存技能) this.扩写技能id = 已存技能
    },
    // 「开始制作」按钮：正式创建项目（不是草稿）→ 状态推到「创作中」→ 清本地草稿 → 进方案页。
    // 校验不过不放行；剧名重复时按同名续用不报错。
    async 开始创作() {
      if (!this.表单.剧名.trim()) {
        this.$message({ message: '请先填写剧名（可点「AI 丰富梗概」让 AI 起一个）', type: 'warning' })
        return
      }
      const 创意 = (this.表单.创意 || '').trim()
      if (创意.length < 20) {
        this.$message({ message: '一句话创意至少 20 个字才能开始制作（只想暂存就点「保存」）', type: 'warning' })
        return
      }
      const 集数 = parseInt(this.表单.集数, 10)
      if (!(集数 >= 2 && 集数 <= 100)) {
        this.$message({ message: '集数须在 2~100 之间', type: 'warning' })
        return
      }
      this.保存中 = true
      try {
        let 剧id = this.剧id
        if (!剧id) {
          剧id = await this.存剧库()
          if (!剧id) {
            this.$message.error('保存失败，请重试')
            return
          }
          this.剧id = 剧id
        }
        this.置创作中(剧id)
        try { localStorage.removeItem(草稿键) } catch (e) { /* 无所谓 */ }
        this.$router.push({
          path: '/script/plan',
          query: {
            id: 剧id,
            剧名: this.表单.剧名,
            集数: this.表单.集数,
            题材: this.表单.题材.join('、'),
            风格: this.表单.风格,
            // 一句话创意要一路带到方案详情，那边「引入数据」要用
            创意: this.表单.创意
          }
        })
      } catch (e) {
        this.扩写报错(e)
      } finally {
        this.保存中 = false
      }
    }
  }
}
</script>

<style scoped>
.chip组 { display: flex; flex-wrap: wrap; gap: 8px; }
.回显行 { display: flex; align-items: center; }
.回显名 { width: 72px; flex: 0 0 72px; font-size: 12px; color: var(--字弱); }
.回显值 { font-size: 14px; color: var(--字); }
.随机开头钮 {
  background: var(--主);
  color: #06210f;
  font-weight: 600;
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  user-select: none;
  transition: filter .15s, transform .15s;
}
.随机开头钮:hover { filter: brightness(1.12); }
.随机开头钮:active { transform: scale(.97); }
.随机开头钮.忙 { opacity: .65; pointer-events: none; }
</style>
