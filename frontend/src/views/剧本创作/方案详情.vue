<template>
  <div class="创作模块">
    <!-- 面包屑 -->
    <div class="行间 详情顶栏">
      <div class="面包屑条" style="margin:0">
        <span class="可点" @click="返回()">← 返回</span>
        <span> / </span>
        <span class="当前剧名">{{ 剧名 }}</span>
      </div>
    </div>

    <!-- 四步进度条：和创作方案页一样居中，点任意一步即跳到那一步 -->
    <step-bar :步骤="步骤" :当前步="当前序号" 修饰="竖向 居中" @切换="跳到步骤页($event)"></step-bar>

    <!-- 信息条 -->
    <div class="提示条">
      <span>{{ 详情.提示 }}</span>
      <el-button type="warning" size="small" @click="前往分集剧本()">{{ 详情.提示按钮 }}</el-button>
    </div>

    <!-- 上一/下一步（4 步进度自然衔接：创作方案 → 人物设定 → 分集目录 → 分集剧本） -->
    <div class="行间 右" style="margin-bottom:16px">
      <el-button @click="上一步()">上一步：选择方案</el-button>
      <el-button @click="保存()">保存</el-button>
      <el-button type="primary" @click="下一步()">下一步：人物设定</el-button>
    </div>

    <!-- Tabs：方案详情 / 创作方案 -->
    <div class="行间" style="justify-content:center;margin-bottom:16px">
      <div class="标签组">
        <button class="项" @click="切标签('plan')">创作方案</button>
        <button class="项 当前" @click="切标签('detail')">方案详情</button>
      </div>
    </div>

    <!-- 本页共 10 个分区，每个分区各有一套「技能 + 技能引导提示词」，
         所以这里是逐区配置、逐区生成、逐区编辑，互不影响。 -->
    <div class="分区提示">
      每个分区都有自己的「技能 + 技能引导提示词」，可以单独 AI 生成、单独编辑，互不影响。
      首次进入会按分区顺序逐区自动生成并落库；再次进入直接读取数据库内容。
    </div>

    <!-- 载入中 / 载入报错 -->
    <div v-if="载入中" class="分区提示" style="text-align:center;padding:48px 0;color:var(--字弱)">
      <i class="el-icon-loading" style="font-size:26px;color:var(--主)"></i>
      <div style="margin-top:10px;font-size:13px">正在读取剧、方案与分区内容…</div>
    </div>
    <div v-else-if="载入报错" class="分区提示" style="text-align:center;padding:40px 0">
      <div style="color:#ef4444;font-size:13px;margin-bottom:12px">{{ 载入报错 }}</div>
      <el-button size="mini" @click="载入()">重试</el-button>
    </div>

    <template v-else>
    <div v-for="区 in 分区表" :key="区.键" class="详情区">
      <div class="分区头">
        <div class="竖条"></div>
        <div class="分区名">{{ 区.名 }}</div>
        <div class="分区操作">
          <el-button size="mini" icon="el-icon-setting" @click="打开技能(区)">技能</el-button>
          <el-button size="mini" :loading="生成中键 === 区.键" @click="打开生成(区)">AI 生成</el-button>
          <el-button size="mini" icon="el-icon-edit" @click="打开编辑(区)">编辑</el-button>
        </div>
      </div>

      <div class="分区体">
        <!-- 键值（并列成行） -->
        <template v-if="区.型 === '键值并列'">
          <span v-for="条 in 详情[区.键]" :key="条.键" class="键值行 并列">
            <span class="键">{{ 条.键 }}：</span><span>{{ 条.值 }}</span>
          </span>
        </template>

        <!-- 键值（一条一段） -->
        <template v-if="区.型 === '键值段'">
          <div v-for="条 in 详情[区.键]" :key="条.键" class="键值行 段">
            <span class="键">{{ 条.键 }}：</span><span>{{ 条.值 }}</span>
          </div>
        </template>

        <!-- 分段正文 -->
        <template v-if="区.型 === '分段'">
          <div v-for="(段, 序) in 详情[区.键]" :key="区.键 + 序" class="段">{{ 段 }}</div>
        </template>

        <!-- 整段正文 -->
        <div v-if="区.型 === '整段'">{{ 详情[区.键] }}</div>

        <!-- 子卡片（三幕） -->
        <template v-if="区.型 === '子卡片'">
          <div class="网格 三">
            <div v-for="幕 in 详情[区.键]" :key="幕.标题" class="子卡片">
              <div class="子标题">{{ 幕.标题 }}</div>
              <div class="子正文">{{ 幕.正文 }}</div>
            </div>
          </div>
        </template>

        <!-- 表格 -->
        <template v-if="区.型 === '表格'">
          <table class="表格">
            <thead>
              <tr>
                <th v-for="列 in 区.列" :key="列.键" :style="{ width: 列.宽 || '' }">{{ 列.名 }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(行, 序) in 详情[区.键]" :key="序">
                <td v-for="列 in 区.列" :key="列.键" :class="{ 主: 列.主 }">{{ 行[列.键] }}</td>
              </tr>
            </tbody>
          </table>
        </template>

        <!-- 嵌套（商业卖点） -->
        <template v-if="区.型 === '嵌套'">
          <div class="子卡片" style="margin-bottom:16px">
            <div class="子标题">爽点兑现版本</div>
            <ul class="要点列">
              <li v-for="(条, 序) in 详情[区.键].爽点兑现" :key="'兑' + 序">{{ 条 }}</li>
            </ul>
          </div>

          <div class="子卡片">
            <div class="子标题">反派压力轨道</div>
            <ul class="要点列">
              <li v-for="(条, 序) in 详情[区.键].反派压力" :key="'反' + 序">{{ 条 }}</li>
            </ul>
          </div>
        </template>

        <!-- AI 原文兜底：格式没认出时原文摊在这里，不硬塞进本区 -->
        <div v-if="原文[区.键]" class="原始结果">
          <div class="行间" style="margin-bottom:8px">
            <div class="原文标题">AI 原文（格式未识别，没有写入本区）</div>
            <div style="flex:1"></div>
            <el-button type="text" size="mini" @click="收起原文(区.键)">收起</el-button>
          </div>
          <pre class="原文">{{ 原文[区.键] }}</pre>
        </div>

        <!-- 空区提示：还没生成过内容 -->
        <div v-if="区为空(区)" class="空区注">本区还没有内容：等首次自动生成，或点右上「AI 生成」手动生成</div>
      </div>
    </div>
    </template>

    <!-- 首次进页逐区生成进度遮罩：按分区顺序一个一个生成，全部结束后自动消失 -->
    <div v-if="自动生成中" class="生成遮罩">
      <div class="生成框">
        <div class="生成标题">首次生成分区内容</div>
        <el-progress :percentage="自动进度" :stroke-width="8"></el-progress>
        <div class="生成注">{{ 自动文案 }}</div>
      </div>
    </div>

    <!-- 技能生成弹窗：每个分区各配一套（技能 + 技能引导提示词 + 保存）。
         注意：in-DOM 模板只认 ASCII 标签名，必须用 skill-dialog 别名（见 docs/09 第 8 节）。 -->
    <skill-dialog
      :显示.sync="技能弹窗显示"
      :技能列表="技能列表"
      :技能id.sync="技能区技能id"
      :引导.sync="技能区引导"
      :默认引导="技能区默认规则"
      :配置类型="技能区配置类型"
      :目标名="技能区 ? 技能区.名 : '本区内容'"
      :引入数据="引入数据"
      @保存="技能已保存($event)"></skill-dialog>

    <!-- AI 生成弹窗：只生成当前这一区，结果写回这一区 -->
    <el-dialog
      :visible.sync="生成显示"
      width="620px"
      top="10vh"
      custom-class="详情生成弹窗"
      :show-close="false"
      :close-on-click-modal="false">
      <div class="弹窗头">
        <div>
          <div class="弹窗标题">AI 生成 · {{ 生成区.名 }}</div>
          <div class="弹窗副题">
            用「{{ 生成区技能名 }}」+ 本区技能引导提示词生成，结果只覆盖这一块。
          </div>
        </div>
        <i class="el-icon-close 弹窗关闭" title="关闭" @click="生成显示 = false"></i>
      </div>

      <div class="弹窗体">
        <el-input
          v-model="生成需求"
          type="textarea"
          :rows="6"
          placeholder="例：核心冲突再压一层，把反派换成教务处；只改这一块，其他不动"></el-input>
        <div class="段注">
          {{ 生成需求.length }} 字 ·
          <span class="可点 换技能" @click="从生成改技能()">改技能 / 技能引导提示词</span>
        </div>
      </div>

      <div class="弹窗底">
        <span class="底注">生成结果只覆盖「{{ 生成区.名 }}」，其他分区不动。</span>
        <el-button size="small" @click="生成显示 = false">取消</el-button>
        <el-button size="small" type="primary" :loading="生成中键 === 生成区.键" @click="执行生成()">
          生成
        </el-button>
      </div>
    </el-dialog>

    <!-- 分区编辑弹窗：按分区形态换表单（键值 / 分段 / 整段 / 子卡片 / 表格 / 嵌套） -->
    <el-dialog
      :visible.sync="编辑显示"
      width="760px"
      top="6vh"
      custom-class="详情编辑弹窗"
      :show-close="false"
      :close-on-click-modal="false">
      <div class="弹窗头">
        <div>
          <div class="弹窗标题">编辑 · {{ 编辑区.名 }}</div>
          <div class="弹窗副题">改完点保存，只覆盖这一块，其他分区不动</div>
        </div>
        <i class="el-icon-close 弹窗关闭" title="关闭" @click="编辑显示 = false"></i>
      </div>

      <div class="弹窗体">
        <!-- 键值：名称 + 内容 -->
        <div v-if="草稿.型 === '键值并列' || 草稿.型 === '键值段'">
          <div v-for="(行, 序) in 草稿.行" :key="序" class="编条">
            <el-input v-model="行.键" size="small" class="编键" placeholder="名称"></el-input>
            <el-input v-model="行.值" size="small" type="textarea" :rows="2" class="编值" placeholder="内容"></el-input>
            <el-button type="text" size="mini" class="编删" @click="草稿.行.splice(序, 1)">删除</el-button>
          </div>
          <el-button size="mini" icon="el-icon-plus" @click="草稿.行.push({ 键: '', 值: '' })">加一条</el-button>
        </div>

        <!-- 分段正文 -->
        <div v-if="草稿.型 === '分段'">
          <div v-for="(段, 序) in 草稿.段" :key="序" class="编条 竖">
            <div class="编条头">
              <span class="编序">第 {{ 序 + 1 }} 段</span>
              <el-button type="text" size="mini" @click="草稿.段.splice(序, 1)">删除</el-button>
            </div>
            <el-input v-model="段.文" type="textarea" :rows="4"></el-input>
          </div>
          <el-button size="mini" icon="el-icon-plus" @click="草稿.段.push({ 文: '' })">加一段</el-button>
        </div>

        <!-- 整段正文 -->
        <el-input
          v-if="草稿.型 === '整段'"
          v-model="草稿.文"
          type="textarea"
          :rows="14"
          placeholder="整段可演正文"></el-input>

        <!-- 子卡片 -->
        <div v-if="草稿.型 === '子卡片'">
          <div v-for="(条, 序) in 草稿.子" :key="序" class="编条 竖">
            <div class="编条头">
              <el-input v-model="条.标题" size="small" placeholder="幕名"></el-input>
              <el-button type="text" size="mini" @click="草稿.子.splice(序, 1)">删除</el-button>
            </div>
            <el-input v-model="条.正文" type="textarea" :rows="3"></el-input>
          </div>
          <el-button size="mini" icon="el-icon-plus" @click="草稿.子.push({ 标题: '', 正文: '' })">加一幕</el-button>
        </div>

        <!-- 表格 -->
        <div v-if="草稿.型 === '表格'">
          <div v-for="(行, 序) in 草稿.表" :key="序" class="编表行">
            <div v-for="列 in 编辑区.列" :key="列.键" class="编表格">
              <div class="编表名">{{ 列.名 }}</div>
              <el-input
                v-model="行[列.键]"
                size="small"
                :type="列.长 ? 'textarea' : 'text'"
                :rows="列.长 ? 3 : 1"></el-input>
            </div>
            <el-button type="text" size="mini" class="编删" @click="草稿.表.splice(序, 1)">删除</el-button>
          </div>
          <el-button size="mini" icon="el-icon-plus" @click="加表行()">加一行</el-button>
        </div>

        <!-- 嵌套（商业卖点） -->
        <div v-if="草稿.型 === '嵌套'">
          <div class="编块">
            <div class="编块名">爽点兑现（一行一条）</div>
            <el-input v-model="草稿.兑现" type="textarea" :rows="4"></el-input>
          </div>

          <div class="编块">
            <div class="编块名">反派压力（一行一条）</div>
            <el-input v-model="草稿.反派" type="textarea" :rows="4"></el-input>
          </div>
        </div>
      </div>

      <div class="弹窗底">
        <span class="底注">只改「{{ 编辑区.名 }}」，其他分区不动。</span>
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
import { 读引导, 读技能id, 读引入, 存引入, 读创意, 存创意 } from '@/共用/技能生成配置'
import { 取, 发 } from '@/接口/请求'
import { 提交AI任务 } from '@/共用/AI任务'

// 分区形态表：模板按 型 决定怎么渲染，编辑弹窗按 型 决定出什么表单，
// AI 生成按 型 决定怎么把文本解析回结构。加一个分区只改这里。
const 分区表 = [
  { 键: '时空背景', 名: '时空背景', 型: '键值段' },
  { 键: '故事线', 名: '故事线与核心冲突', 型: '键值段' },
  {
    键: '爽点', 名: '爽点矩阵', 型: '表格',
    列: [
      { 键: '区间', 名: '集数区间', 主: true },
      { 键: '类型', 名: '爽点类型', 主: true },
      { 键: '描述', 名: '爽点描述', 长: true },
      { 键: '强度', 名: '强度', 主: true, 宽: '70px' }
    ]
  },
  { 键: '商业卖点', 名: '商业卖点', 型: '嵌套' },
  { 键: '结局', 名: '结局设计', 型: '键值段' }
]

// 每个分区自己的默认技能引导提示词：库里没存过本区配置时用它。
// 输出格式是写死的——前端靠它把 AI 文本解析回结构（见 解析分区）。
const 通用头 = function (块名) {
  return [
    '1. 你要写的是短剧「方案详情 · ' + 块名 + '」文案，不是视频/图片提示词：禁止输出 <Picture N>、<Video N>、<Audio N> 之类标签，也不要写镜头、光影、音效。'
  ]
}

const 分区默认规则 = {
  时空背景: 通用头('时空背景').concat([
    '2. 严格按「名称：内容」一行一条输出，名称依次为：时空锚、硬规则 1~10、禁忌口径 1~9、场景库 · 各场景名、场景预算。',
    '3. 硬规则写可执行的禁制与代价；场景库每条写清「功能：…。视觉：…。预算档：低/中/高。」。',
    '4. 只输出正文，不要解释、不要前后缀、不要额外标题。'
  ]).join('\n'),

  故事线: 通用头('故事线与核心冲突').concat([
    '2. 严格按「名称：内容」一行一条输出，名称固定为这六个：一句话故事线、核心冲突、主题、副主题、节奏基调、开篇钩子。',
    '3. 核心冲突必须写清「谁要什么 → 谁挡着 → 代价是什么」，不要只堆抽象情绪。',
    '4. 只输出正文，不要解释、不要前后缀。'
  ]).join('\n'),

  爽点: 通用头('爽点矩阵').concat([
    '2. 一行一个爽点，格式固定为「集数区间｜爽点类型｜爽点描述｜强度」，用全角竖线 ｜ 分隔，强度只填 低/中/高。',
    '3. 3~5 行，覆盖前段/中段/末段，不要所有爽点都写「高」。',
    '4. 只输出这些行，不要表头、不要解释、不要前后缀。'
  ]).join('\n'),

  商业卖点: 通用头('商业卖点').concat([
    '2. 严格按下面结构输出，标题文字一个字都不能改：',
    '爽点兑现：',
    '- 一条一行',
    '反派压力：',
    '- 一条一行',
    '3. 「爽点兑现」「反派压力」每行以 - 开头，各 2~4 条。',
    '4. 只输出上面这些正文，不要解释、不要前后缀。'
  ]).join('\n'),

  结局: 通用头('结局设计').concat([
    '2. 严格按「结局类型：内容」一行一条输出，结局类型写 HE / BE / OE 加括号说明，例：大团圆（HE）：……',
    '3. 内容写清最后一场戏怎么收、哪几条线一起消解。',
    '4. 只输出正文，不要解释、不要前后缀。'
  ]).join('\n')
}

// 分区键 → 方案表列名（库列就是分区中文名；爽点/结局两键在卡上用简称）
const 分区列 = { 时空背景: '时空背景', 故事线: '故事线', 爽点: '爽点矩阵', 商业卖点: '商业卖点', 结局: '结局设计' }

// 分区空值结构：按 型 给出渲染层能直接消费的空值
function 空分区值(型) {
  if (型 === '嵌套') return { 爽点兑现: [], 反派压力: [] }
  if (型 === '整段') return ''
  return []
}

// 「名称：内容」→ [{键, 值}]，续行并入上一条
function 拆键值(文本) {
  const 行们 = String(文本).split('\n')
  const 结果 = []
  let 当前 = null
  for (let i = 0; i < 行们.length; i++) {
    const 行 = 行们[i].replace(/^\s*[-*·]\s*/, '').trim()
    if (!行) continue
    const 配 = 行.match(/^([^：:]{1,20})[：:]\s*(.*)$/)
    // 键名里不能带句末标点，否则一整句话会被误当成键
    if (配 && !/[。！？；]/.test(配[1])) {
      当前 = { 键: 配[1].trim(), 值: 配[2].trim() }
      结果.push(当前)
    } else if (当前) {
      当前.值 = (当前.值 ? 当前.值 + ' ' : '') + 行
    } else {
      结果.push({ 键: '要点' + (结果.length + 1), 值: 行 })
    }
  }
  return 结果
}

// 「a｜b｜c」→ [[a, b, c], ...]；只保留字段数够的行
function 拆竖线行(文本, 至少列) {
  const 行们 = String(文本).split('\n')
  const 结果 = []
  for (let i = 0; i < 行们.length; i++) {
    let 行 = 行们[i].replace(/^\s*[-*·]\s*/, '').trim()
    if (!行) continue
    if (!/[|｜\t]/.test(行)) continue
    行 = 行.replace(/^[|｜]/, '').replace(/[|｜]$/, '')
    const 格 = 行.split(/\s*[|｜\t]\s*/)
    if (格.length < 至少列) continue
    结果.push(格)
  }
  return 结果
}

// 商业卖点专用：认「爽点兑现 / 反派压力」两块
function 拆商业卖点(文本) {
  const 结果 = { 爽点兑现: [], 反派压力: [] }
  const 行们 = String(文本).split('\n')
  let 块 = ''
  for (let i = 0; i < 行们.length; i++) {
    let 行 = 行们[i].trim()
    if (!行) continue
    if (/^爽点兑现/.test(行)) { 块 = '兑现'; continue }
    if (/^反派压力/.test(行)) { 块 = '反派'; continue }
    const 净 = 行.replace(/^\s*[-*·]\s*/, '').trim()
    if (块 === '兑现') {
      结果.爽点兑现.push(净)
    } else if (块 === '反派') {
      结果.反派压力.push(净)
    }
  }
  const 空 = !结果.爽点兑现.length && !结果.反派压力.length
  return 空 ? null : 结果
}

export default {
  name: 'ScriptPlanDetail',
  mixins: [剧本页混入],
  components: { 'step-bar': 步骤条, 'skill-dialog': 技能生成弹窗 },
  created() {
    // 一句话创意：路由带过来就记住，没带就用上次在「引入数据」里补的
    const 路由创意 = (this.$route.query.创意 || '').trim()
    if (路由创意) {
      this.创意文本 = 路由创意
      存创意(this.剧名, 路由创意)
    } else {
      this.创意文本 = 读创意(this.剧名)
    }
    this.载入全部区配置()
    this.载入()
  },
  data() {
    // 分区初始为空结构，内容全部来自数据库（GET /api/方案/分区），首次进页自动生成后落库
    const 根 = {
      剧名: '',
      集数: '',
      提示: '选定方案在此展开成五个分区：逐区自动生成、逐区可改，内容全部落库，下次进来直接读取。',
      提示按钮: '前往分集剧本'
    }
    for (let i = 0; i < 分区表.length; i++) 根[分区表[i].键] = 空分区值(分区表[i].型)
    return {
      详情: 根,
      分区表: 分区表,
      // 载入状态
      载入中: false,
      载入报错: '',
      // 真 data：剧行 + 选中的方案行（数据库记录）
      剧行: null,
      剧id: 0,
      方案卡: null,
      // 首次进页逐区生成的进度遮罩
      自动生成中: false,
      自动进度: 0,
      自动文案: '',
      // 每区一份「技能 id + 技能引导提示词」，键 = 分区键
      区配置: {},
      // 每区一份「引入数据勾选」，键 = 分区键，值 = 勾上的数据键数组（null = 没配过，默认全选）
      引入勾选: {},
      // 一句话创意（引入数据里可改，按剧名记住）
      创意文本: '',
      // 解析失败时每区的 AI 原文兜底
      原文: {},
      // 技能弹窗（一次配一个区）
      技能弹窗显示: false,
      技能区: null,
      技能区技能id: '',
      技能区引导: '',
      // 生成弹窗
      生成显示: false,
      生成区: { 键: '', 名: '' },
      生成需求: '',
      生成中键: '',
      // 编辑弹窗
      编辑显示: false,
      编辑区: { 键: '', 名: '', 型: '' },
      草稿: { 型: '', 行: [], 段: [], 子: [], 表: [] }
    }
  },
  computed: {
    // 本页没有独立的剧名/集数/题材变量，优先用地址栏带过来的，没带就退回数据库里的剧
    剧名() {
      return this.$route.query.剧名 || (this.剧行 && this.剧行.剧名) || ''
    },
    集数() {
      return this.$route.query.集数 || String((this.剧行 && this.剧行.集数) || '')
    },
    题材() {
      return this.$route.query.题材 || (this.剧行 && this.剧行.题材) || '未分类'
    },
    // 选中的方案行（数据库记录；地址栏 方案=方案行 id，找不到就退回是否选定行）
    已选方案() {
      return this.方案卡
    },
    已选方案名() {
      return this.方案卡 ? (this.方案卡.版本号 || ('方案#' + this.方案卡.id)) : '未选定'
    },
    // 已选方案摊成多行文本，当「引入数据」的一项（来自真库候选卡）
    已选方案文本() {
      const 卡 = this.方案卡 && this.方案卡.候选卡
      if (!卡) return ''
      return [
        '方案标题：' + (卡.标题 || ''),
        '故事线：' + (卡.故事线 || ''),
        '推荐题材：' + (卡.题材 || ''),
        '基调：' + (卡.基调 || ''),
        '结局类型：' + (卡.结局 || ''),
        '核心驱动：' + (卡.驱动 || ''),
        '风险展示：' + (卡.风险 || '')
      ].join('\n')
    },
    // 传给技能弹窗的「引入数据」：跟着当前打开的那个区走（勾选按区各记一份）
    引入数据() {
      const 区 = this.技能区
      return this.造引入数据(区 ? this.引入勾选[区.键] : null)
    },
    技能区配置类型() {
      return this.技能区 ? this.区配置类型(this.技能区.键) : ''
    },
    技能区默认规则() {
      return this.技能区 ? (分区默认规则[this.技能区.键] || '') : ''
    },
    生成区技能名() {
      const 键 = this.生成区.键
      if (!键) return ''
      const id = String(this.区技能id(键))
      for (let i = 0; i < this.技能列表.length; i++) {
        if (String(this.技能列表[i].id) === id) return this.技能列表[i].名称
      }
      return '默认技能'
    }
  },
  methods: {
    返回() {
      this.$router.push('/script')
    },
    上一步() {
      this.$router.push({ path: '/script/plan', query: this.$route.query })
    },
    async 下一步() {
      // 方案详情属第 1 步「创作方案」，下一步落到第 2 步「人物设定」（独立页 /script/character）
      // 跳转前先把 5 个分区全量落库，保存失败就不跳，否则下次进来读不到
      const 好了 = await this.保存()
      if (!好了) return
      this.$router.push({
        path: '/script/character',
        query: Object.assign({}, this.$route.query)
      })
    },
    切标签(名) {
      if (名 === 'plan') {
        this.$router.push({ path: '/script/plan', query: this.$route.query })
      } else {
        this.$message({ message: '当前已在方案详情', type: 'info' })
      }
    },
    前往分集剧本() {
      this.$router.push({
        path: '/script/episode',
        query: Object.assign({}, this.$route.query)
      })
    },

    /* ---------------- 真数据：读库 / 落库 / 首次逐区生成 ---------------- */

    // 进页主流程：取剧+方案卡 → 读分区 → 有空区就按顺序逐区自动生成
    async 载入() {
      this.载入中 = true
      this.载入报错 = ''
      try {
        await this.取剧与方案()
        if (!this.剧id || !this.方案卡) {
          this.载入报错 = this.剧id
            ? '找不到选定的方案：请从「创作方案」页选定方案后进入本页'
            : '找不到这部剧：请从「我的剧」或「新建剧本」进入本页'
          return
        }
        await this.取分区()
        this.载入中 = false
        const 缺 = this.空区们()
        if (缺.length) await this.批量生成(缺)
      } catch (e) {
        this.载入报错 = (e && e.message) || '载入失败'
      } finally {
        this.载入中 = false
      }
    },
    // 取剧行 + 选中的方案行（地址栏 方案=方案行 id；找不到退回 是否选定 行，再退回第一行）
    async 取剧与方案() {
      const id = parseInt(this.$route.query.id, 10) || 0
      if (!id) return
      try {
        const 剧据 = await 取('/api/剧/详情?id=' + id)
        if (剧据 && 剧据.ok) {
          this.剧行 = 剧据.剧
          this.剧id = id
          if (!this.详情.剧名) this.详情.剧名 = this.剧行.剧名 || ''
          // 一句话创意没从路由/本地带来时，退回剧表的创意
          if (!this.创意文本 && this.剧行.创意) {
            this.创意文本 = this.剧行.创意
            存创意(this.剧名, this.创意文本)
          }
        }
      } catch (e) { /* 剧取不到时下面报错提示 */ }
      if (!this.剧id) return
      const 数据 = await 取('/api/方案列表?剧id=' + this.剧id)
      const 行们 = (数据 && 数据.列表) || []
      const 意id = parseInt(this.$route.query.方案, 10) || 0
      this.方案卡 = 行们.find(行 => 行.id === 意id)
        || 行们.find(行 => 行.是否选定)
        || 行们[0]
        || null
    },
    // 读该方案的五个分区，空值铺成对应型的空结构
    async 取分区() {
      const 数据 = await 取('/api/方案/分区?方案id=' + this.方案卡.id)
      const 分区 = (数据 && 数据.分区) || {}
      for (let i = 0; i < this.分区表.length; i++) {
        const 区 = this.分区表[i]
        let 值 = 分区[分区列[区.键]]
        if (值 == null) 值 = 空分区值(区.型)
        this.$set(this.详情, 区.键, 值)
      }
    },
    // 某区当前是否还没有内容（决定首次自动生成与空区提示）
    区为空(区) {
      const 值 = this.详情[区.键]
      if (值 == null) return true
      if (区.型 === '嵌套') return !(值.爽点兑现 || []).length && !(值.反派压力 || []).length
      if (区.型 === '整段') return !String(值).trim()
      return !(值 || []).length
    },
    空区们() {
      return this.分区表.filter(区 => this.区为空(区))
    },
    // 单区落库：只覆盖该区，其他分区不动（后端按键 PATCH）
    async 存分区(区键, 内容) {
      if (!this.方案卡) throw new Error('没有方案可保存')
      await 发('/api/方案/分区保存', {
        方案id: this.方案卡.id,
        分区们: (function () { const 表 = {}; 表[分区列[区键]] = 内容; return 表 })()
      })
    },
    // 顶部「保存」：五个分区全量落库；返回是否保存成功（下一步依赖它决定跳不跳）
    async 保存() {
      if (!this.方案卡) {
        this.$message.warning('还没有方案，无法保存')
        return false
      }
      const 分区们 = {}
      for (let i = 0; i < this.分区表.length; i++) {
        const 区 = this.分区表[i]
        分区们[分区列[区.键]] = this.详情[区.键]
      }
      try {
        await 发('/api/方案/分区保存', { 方案id: this.方案卡.id, 分区们: 分区们 })
        this.$message.success('方案详情已全部落库')
        return true
      } catch (e) {
        this.$message.error('保存失败：' + ((e && e.message) || ''))
        return false
      }
    },
    // 调 AI 生成本区文本：走统一任务链路（/test/t1-text 同款：任务提交 → 轮询到终态），
    // 每区用自己的技能（SKILL.md 规范由后端注入系统提示词）+ 本区引导词 + 勾选的引入数据
    async 生成区文本(区, 修改要求) {
      const 参考 = this.参考块(区.键)
      const 需求 = (参考 ? [参考, ''] : []).concat([
        '剧名：' + this.剧名,
        '集数：' + this.集数 + ' 集',
        '题材：' + this.题材,
        '要生成的区块：' + 区.名,
        '这一块的当前内容：',
        this.区块纯文本(区) || '（暂无）',
        修改要求 ? ('修改要求：' + 修改要求) : '首次生成本区：严格按系统提示词里的输出格式一次写全。'
      ].filter(Boolean)).join('\n')
      const 文本 = await 提交AI任务({
        正向: 需求,
        系统: this.区引导(区.键),
        技能id: this.区技能id(区.键)
      })
      return String(文本 || '').trim()
    },
    // 按分区表顺序串行生成；某区没技能就跳过标记待手动，失败不影响已完成区
    async 批量生成(区们) {
      // 技能列表是 created 里异步拉的，自动生成可能比它先跑完；先等它就绪，
      // 否则区技能id 全为空，五区会被整体当成「没有可用技能」跳过
      if (!this.技能列表.length) await this.拉技能列表()
      this.自动生成中 = true
      this.自动进度 = 0
      const 汇总 = { 成功: [], 失败: [], 跳过: [] }
      for (let i = 0; i < 区们.length; i++) {
        const 区 = 区们[i]
        this.自动文案 = '正在生成「' + 区.名 + '」（' + (i + 1) + '/' + 区们.length + '）…'
        if (!this.区技能id(区.键)) {
          汇总.跳过.push(区.名)
        } else {
          try {
            const 文本 = await this.生成区文本(区, '')
            const 新值 = this.解析分区(区, 文本)
            if (新值 === null) {
              this.$set(this.原文, 区.键, 文本)
              汇总.失败.push(区.名 + '（格式未识别）')
            } else {
              this.$set(this.详情, 区.键, 新值)
              this.$set(this.原文, 区.键, '')
              await this.存分区(区.键, 新值)
              汇总.成功.push(区.名)
            }
          } catch (e) {
            汇总.失败.push(区.名 + '：' + ((e && e.message) || '生成失败'))
          }
        }
        this.自动进度 = Math.round(((i + 1) / 区们.length) * 100)
      }
      this.自动生成中 = false
      let 消息 = '生成完成：成功 ' + 汇总.成功.length + ' 区'
      if (汇总.跳过.length) 消息 += '；「' + 汇总.跳过.join('、') + '」没有可用技能，待手动生成'
      if (汇总.失败.length) 消息 += '；失败：' + 汇总.失败.join('、')
      if (汇总.失败.length || 汇总.跳过.length) this.$message({ message: 消息, type: 'warning', duration: 6000 })
      else this.$message.success(消息)
    },

    /* ---------------- 引入数据（前面步骤产出的上下文） ---------------- */

    // 勾 = 勾上的数据键数组；null/空表示没配过，默认全选
    造引入数据(勾) {
      const 项们 = [
        { 键: '标题', 名: '标题（剧名）', 值: this.剧名 },
        {
          键: '创意', 名: '一句话创意', 值: this.创意文本, 可编辑: true,
          提示: '从新建剧本带过来的；没带过来就在这里补，会记住',
          占位: '例：重生教师带三个学生考过毕业考核，一边藏身份一边带她们成长'
        },
        { 键: '方案', 名: '已选方案（' + this.已选方案名 + '）', 值: this.已选方案文本 }
      ]
      // null/undefined = 没配过，默认全选；[] = 用户点过「全不选」，要尊重，不能再回退成全选
      for (let i = 0; i < 项们.length; i++) {
        项们[i].勾选 = 勾 == null ? true : 勾.indexOf(项们[i].键) >= 0
      }
      return 项们
    },
    // 生成时真正拼进需求的参考块：只取勾上且非空的
    参考块(区键) {
      const 项们 = this.造引入数据(this.引入勾选[区键])
      const 行们 = []
      for (let i = 0; i < 项们.length; i++) {
        const 项 = 项们[i]
        const 值 = String(项.值 || '').trim()
        if (!项.勾选 || !值) continue
        行们.push('【' + 项.名 + '】\n' + 值)
      }
      if (!行们.length) return ''
      return ['参考数据（前面步骤已经定下来的，必须遵守，不要改动）：'].concat(行们).join('\n')
    },

    /* ---------------- 技能配置（每区一份） ---------------- */

    // 后端存本区配置的 key：生成:/script/detail#故事线
    区配置类型(键) {
      return '生成:' + (this.$route.path || '') + '#' + 键
    },
    // 本区用的技能 id：配过用配的，没配过用本页默认（混入里默认选第一个）
    区技能id(键) {
      const 配 = this.区配置[键]
      return (配 && 配.技能id) || this.扩写技能id || ''
    },
    // 本区用的引导提示词：配过用配的，没配过用本区默认规则
    区引导(键) {
      const 配 = this.区配置[键]
      return (配 && 配.引导) || 分区默认规则[键] || ''
    },
    // 进页面把十个区的已存配置一次性带出来
    async 载入全部区配置() {
      const 任务 = 分区表.map(async (区) => {
        const 类型 = this.区配置类型(区.键)
        const 引导 = await 读引导(类型)
        this.$set(this.区配置, 区.键, {
          技能id: 读技能id(类型),
          引导: 引导 || ''
        })
        // null = 没配过，后面按默认全选处理
        this.$set(this.引入勾选, 区.键, 读引入(类型))
      })
      try {
        await Promise.all(任务)
      } catch (e) {
        /* 拉不到就用默认规则，不阻塞页面 */
      }
    },
    打开技能(区) {
      this.技能区 = 区
      this.技能区技能id = this.区技能id(区.键)
      this.技能区引导 = this.区引导(区.键)
      // 等 props 都换成本区的值再打开，弹窗的「载入」才会读对本区的配置
      this.$nextTick(() => {
        this.技能弹窗显示 = true
      })
    },
    技能已保存(值) {
      const 区 = this.技能区
      if (!区) return
      const 类型 = this.区配置类型(区.键)
      const 引入 = (值 && 值.引入) || []
      const 勾 = []
      for (let i = 0; i < 引入.length; i++) {
        // 一句话创意可能在这里被补过，按剧名记住
        if (引入[i].键 === '创意') {
          this.创意文本 = 引入[i].值 || ''
          存创意(this.剧名, this.创意文本)
        }
        if (引入[i].勾选) 勾.push(引入[i].键)
      }
      this.$set(this.引入勾选, 区.键, 勾)
      存引入(类型, 勾)
      this.$set(this.区配置, 区.键, {
        技能id: (值 && 值.技能id) || this.技能区技能id,
        引导: (值 && 值.引导) || this.技能区引导
      })
    },

    /* ---------------- AI 生成（只生成一个区） ---------------- */

    打开生成(区) {
      this.生成区 = 区
      this.生成需求 = ''
      this.生成显示 = true
    },
    从生成改技能() {
      const 区 = this.生成区
      this.生成显示 = false
      if (区 && 区.键) this.打开技能(区)
    },
    // 把本区当前内容摊成纯文本，当上下文喂给 AI
    区块纯文本(区) {
      const 值 = this.详情[区.键]
      if (值 == null) return ''
      if (区.型 === '键值并列' || 区.型 === '键值段') {
        return (值 || []).map(条 => 条.键 + '：' + 条.值).join('\n')
      }
      if (区.型 === '分段') return (值 || []).join('\n\n')
      if (区.型 === '整段') return String(值)
      if (区.型 === '子卡片') return (值 || []).map(条 => 条.标题 + '｜' + 条.正文).join('\n')
      if (区.型 === '表格') {
        return (值 || []).map(行 => 区.列.map(列 => 行[列.键] || '').join('｜')).join('\n')
      }
      if (区.型 === '嵌套') {
        const 卖 = 值 || {}
        const 段们 = ['爽点兑现：']
        ;(卖.爽点兑现 || []).forEach(条 => 段们.push('- ' + 条))
        段们.push('反派压力：')
        ;(卖.反派压力 || []).forEach(条 => 段们.push('- ' + 条))
        return 段们.join('\n')
      }
      return ''
    },
    async 执行生成() {
      const 区 = this.生成区
      if (!区 || !区.键) return
      if (!this.生成需求.trim()) {
        this.$message.warning('先写一句需求：这一区你想怎么改')
        return
      }
      const 技能id = this.区技能id(区.键)
      if (!技能id) {
        this.$message.warning('还没有可用技能，先在「技能」里选一个')
        return
      }

      this.生成中键 = 区.键
      try {
        const 文本 = await this.生成区文本(区, this.生成需求.trim())
        if (!文本) {
          this.$message.warning('AI 没有返回内容，可稍后重试')
          return
        }
        const 新值 = this.解析分区(区, 文本)
        if (新值 === null) {
          this.$set(this.原文, 区.键, 文本)
          this.$message.warning('AI 返回的格式没认出，原文放在「' + 区.名 + '」下面了')
        } else {
          this.$set(this.详情, 区.键, 新值)
          this.$set(this.原文, 区.键, '')
          try {
            await this.存分区(区.键, 新值)
            this.$message.success('已生成并保存「' + 区.名 + '」')
          } catch (错) {
            this.$message.warning('已生成「' + 区.名 + '」，但落库失败：' + ((错 && 错.message) || ''))
          }
        }
        this.生成显示 = false
      } catch (e) {
        this.扩写报错(e)
      } finally {
        this.生成中键 = ''
      }
    },
    // 按分区形态把 AI 文本解析回结构；认不出返回 null（走原文兜底）
    解析分区(区, 文本) {
      const 文 = String(文本 || '').trim()
      if (!文) return null
      if (区.型 === '键值并列' || 区.型 === '键值段') {
        const 行们 = 拆键值(文)
        return 行们.length ? 行们 : null
      }
      if (区.型 === '分段') {
        // 默认规则要求「一段一行」，所以按行切；只有一行时整段当一段
        const 行们 = 文.split('\n').map(条 => 条.trim()).filter(Boolean)
        return 行们.length > 1 ? 行们 : [文]
      }
      if (区.型 === '整段') {
        return 文.replace(/\n+/g, ' ').replace(/\s{2,}/g, ' ').trim()
      }
      if (区.型 === '子卡片') {
        const 行们 = 拆竖线行(文, 2)
        if (!行们.length) return null
        return 行们.map(格 => ({ 标题: 格[0], 正文: 格.slice(1).join('｜') }))
      }
      if (区.型 === '表格') {
        const 行们 = 拆竖线行(文, 区.列.length)
        if (!行们.length) return null
        return 行们.map(格 => {
          const 项 = {}
          for (let i = 0; i < 区.列.length; i++) 项[区.列[i].键] = 格[i] || ''
          return 项
        })
      }
      if (区.型 === '嵌套') return 拆商业卖点(文)
      return null
    },
    收起原文(键) {
      this.$set(this.原文, 键, '')
    },

    /* ---------------- 编辑（按分区形态出表单） ---------------- */

    打开编辑(区) {
      this.编辑区 = 区
      const 源 = this.详情[区.键]
      if (区.型 === '键值并列' || 区.型 === '键值段') {
        this.草稿 = {
          型: 区.型,
          行: (源 || []).map(条 => ({ 键: 条.键, 值: 条.值 })),
          段: [], 子: [], 表: []
        }
      } else if (区.型 === '分段') {
        this.草稿 = { 型: '分段', 行: [], 段: (源 || []).map(文 => ({ 文: 文 })), 子: [], 表: [] }
      } else if (区.型 === '整段') {
        this.草稿 = { 型: '整段', 行: [], 段: [], 子: [], 表: [], 文: 源 || '' }
      } else if (区.型 === '子卡片') {
        this.草稿 = {
          型: '子卡片', 行: [], 段: [], 表: [],
          子: (源 || []).map(条 => ({ 标题: 条.标题, 正文: 条.正文 }))
        }
      } else if (区.型 === '表格') {
        this.草稿 = {
          型: '表格', 行: [], 段: [], 子: [],
          表: (源 || []).map(行 => Object.assign({}, 行))
        }
      } else if (区.型 === '嵌套') {
        const 卖 = 源 || {}
        this.草稿 = {
          型: '嵌套', 行: [], 段: [], 子: [], 表: [],
          兑现: (卖.爽点兑现 || []).join('\n'),
          反派: (卖.反派压力 || []).join('\n')
        }
      }
      this.编辑显示 = true
    },
    加表行() {
      const 行 = {}
      const 列们 = this.编辑区.列 || []
      for (let i = 0; i < 列们.length; i++) 行[列们[i].键] = ''
      if (!this.草稿.表) this.$set(this.草稿, '表', [])
      this.草稿.表.push(行)
    },
    async 保存编辑() {
      const 区 = this.编辑区
      if (!区 || !区.键) {
        this.编辑显示 = false
        return
      }
      const 型 = this.草稿.型
      let 新值 = null

      if (型 === '键值并列' || 型 === '键值段') {
        新值 = this.草稿.行
          .map(条 => ({ 键: (条.键 || '').trim(), 值: (条.值 || '').trim() }))
          .filter(条 => 条.键 || 条.值)
        if (!新值.length) {
          this.$message.warning('这一块至少要留一条')
          return
        }
      } else if (型 === '分段') {
        新值 = this.草稿.段.map(条 => (条.文 || '').trim()).filter(Boolean)
        if (!新值.length) {
          this.$message.warning('这一块至少要留一段')
          return
        }
      } else if (型 === '整段') {
        新值 = (this.草稿.文 || '').trim()
        if (!新值) {
          this.$message.warning('正文不能为空')
          return
        }
      } else if (型 === '子卡片') {
        新值 = this.草稿.子
          .map(条 => ({ 标题: (条.标题 || '').trim(), 正文: (条.正文 || '').trim() }))
          .filter(条 => 条.标题 || 条.正文)
        if (!新值.length) {
          this.$message.warning('这一块至少要留一幕')
          return
        }
      } else if (型 === '表格') {
        const 列们 = 区.列 || []
        新值 = this.草稿.表.map(行 => {
          const 项 = {}
          for (let i = 0; i < 列们.length; i++) 项[列们[i].键] = (行[列们[i].键] || '').trim()
          return 项
        }).filter(行 => {
          for (let i = 0; i < 列们.length; i++) {
            if (行[列们[i].键]) return true
          }
          return false
        })
        if (!新值.length) {
          this.$message.warning('这一块至少要留一行')
          return
        }
      } else if (型 === '嵌套') {
        const 拆条 = function (文) {
          return String(文 || '').split('\n')
            .map(条 => 条.replace(/^\s*[-*·]\s*/, '').trim())
            .filter(Boolean)
        }
        新值 = {
          爽点兑现: 拆条(this.草稿.兑现),
          反派压力: 拆条(this.草稿.反派)
        }
        if (!新值.爽点兑现.length && !新值.反派压力.length) {
          this.$message.warning('这一块不能全空')
          return
        }
      }

      if (新值 === null) {
        this.$message.warning('这个分区暂不支持编辑')
        return
      }
      this.$set(this.详情, 区.键, 新值)
      this.编辑显示 = false
      try {
        await this.存分区(区.键, 新值)
        this.$message.success('已保存「' + 区.名 + '」')
      } catch (e) {
        this.$message.error('已保存到页面，但落库失败：' + ((e && e.message) || ''))
      }
    }
  }
}
</script>

<style scoped>
.详情顶栏 { justify-content: space-between; align-items: center; margin-bottom: 16px; }
/* 四步进度条居中（和创作方案页同一套写法：定宽 + margin auto） */
.步骤条.居中 { max-width: 720px; margin: 0 auto 24px; }
.当前剧名 { color: var(--字); font-weight: 500; }

.分区提示 {
  margin: -4px 0 12px;
  font-size: 12px;
  color: var(--字弱);
}

/* 分区头右侧的操作组：技能 / AI 生成 / 编辑 */
.分区操作 {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
}
.分区操作 .el-button { margin-left: 0; }
.分区操作 .el-button--mini { padding: 6px 10px; }

/* AI 原文兜底块 */
.原始结果 {
  margin-top: 14px;
  background: var(--卡片);
  border: 1px solid var(--描边亮);
  border-radius: 8px;
  padding: 12px 14px;
}
.原文标题 { font-size: 12px; color: #f59e0b; }
.原始结果 .原文 {
  margin: 0;
  max-height: 220px;
  overflow: auto;
  font-family: inherit;
  font-size: 12px;
  line-height: 1.8;
  color: var(--字次);
  white-space: pre-wrap;
  word-break: break-word;
}

/* ---- 弹窗内容（scoped 生效） ---- */
.弹窗头 {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--描边);
}
.弹窗标题 { font-size: 16px; font-weight: 700; color: var(--字); }
.弹窗副题 { margin-top: 4px; font-size: 12px; color: var(--字弱); line-height: 1.6; }
.弹窗关闭 { margin-left: auto; font-size: 18px; color: var(--字次); cursor: pointer; }
.弹窗关闭:hover { color: #ef4444; }
.弹窗体 { padding: 18px 20px 2px; max-height: 64vh; overflow-y: auto; }
.弹窗底 {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid var(--描边);
  background: var(--卡片二);
}
.弹窗底 .底注 { flex: 1; font-size: 12px; color: var(--字弱); }

.段注 { margin-top: 8px; font-size: 12px; color: var(--字弱); }
.换技能 { color: var(--主); }

/* ---- 编辑弹窗里的行 ---- */
.编条 {
  display: flex; align-items: flex-start; gap: 10px;
  margin-bottom: 12px;
}
.编条.竖 { flex-direction: column; align-items: stretch; gap: 8px; }
.编条头 { display: flex; align-items: center; gap: 10px; }
.编条头 .el-input { flex: 1; }
.编序 { font-size: 12px; color: var(--字弱); flex: 1; }
.编键 { width: 170px; flex: 0 0 170px; }
.编值 { flex: 1; }
.编删 { color: #ef4444; flex: 0 0 auto; }

.编表行 {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 10px 0;
  border-bottom: 1px dashed var(--描边);
}
.编表格 { flex: 1; min-width: 0; }
.编表格.窄 { flex: 0 0 90px; }
.编表名 { font-size: 12px; color: var(--字弱); margin-bottom: 6px; }

.编块 { margin-bottom: 18px; }
.编块名 { font-size: 13px; font-weight: 600; color: var(--字); margin-bottom: 8px; }
</style>

<style>
/* 弹窗外壳：el-dialog 根节点不在本组件模板里，scoped 选不中，单独一段 */
.详情生成弹窗,
.详情编辑弹窗 {
  background: #0d1424;
  border: 1px solid #1e293b;
  border-radius: 12px;
  box-shadow: 0 16px 56px rgba(0, 0, 0, 0.65);
  overflow: hidden;
}
.详情生成弹窗 .el-dialog__header,
.详情编辑弹窗 .el-dialog__header { display: none; }
.详情生成弹窗 .el-dialog__body,
.详情编辑弹窗 .el-dialog__body { padding: 0; }

/* 首次进页逐区生成进度遮罩（与创作方案页同一套深色写法） */
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

/* 空区提示 */
.空区注 {
  font-size: 12px;
  color: var(--字弱);
  padding: 14px 0 6px;
}
</style>
