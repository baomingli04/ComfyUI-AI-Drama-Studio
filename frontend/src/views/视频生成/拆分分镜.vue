<template>
  <div class="创作模块">
    <div class="剧集布局">
      <ep-rail
        当前="拆分分镜"
        :剧名="剧名" :剧id="剧id" :集="集号" :标题="集标题" />

      <div class="剧集主体">
        <!-- 面包屑 -->
        <div class="面包屑条">
          <span class="可点" @click="$router.push('/video')">视频生成</span>
          <span> / </span>
          <span class="可点" @click="$router.push({ path: '/video/episode', query: $route.query })">{{ 剧名 }} 第 {{ 集号 }} 集</span>
          <span> / </span>
          <span style="color:var(--字次)">拆分分镜</span>
        </div>

        <!-- 载入 / 报错门控 -->
        <div v-if="载入中" class="卡片 空卡">
          <i class="el-icon-loading 空图标"></i>
          <div class="空题">正在读取本集分镜…</div>
        </div>
        <div v-else-if="载入报错" class="卡片 空卡">
          <i class="el-icon-warning-outline 空图标"></i>
          <div class="空题">{{ 载入报错 }}</div>
          <el-button size="small" @click="载入()">重试</el-button>
        </div>

        <template v-else>
        <!-- 页头 -->
        <div class="卡片 头卡">
          <div class="头行">
            <div>
              <div class="头题">拆分分镜</div>
              <div class="头副">用技能把本集剧本拆成镜头级分镜（场次 · 景别 · 运镜 · 画面 · 台词 · 时长），逐镜可编辑、可按技能重新生成</div>
            </div>
            <div style="flex:1"></div>
            <el-button size="small" icon="el-icon-setting" @click="打开技能()">技能</el-button>
            <el-button
              v-if="阶段 === '完成'"
              size="small" icon="el-icon-delete" @click="清空()">清空重拆</el-button>
            <el-button
              size="small" type="primary" icon="el-icon-scissors"
              :loading="阶段 === '拆分中'"
              @click="开始拆分()">{{ 阶段 === '拆分中' ? '拆分中…' : (阶段 === '完成' ? '重新拆分' : '开始拆分') }}</el-button>
            <el-button
              v-if="阶段 === '完成'"
              size="small" type="primary" plain icon="el-icon-video-camera"
              :loading="批量中"
              @click="连续生成()">{{ 批量中 ? '排队中…' : '连续生成未完成镜' }}</el-button>
          </div>
          <div v-if="当前技能" class="技能行">
            <span class="技能签">技能</span>
            <span class="技能名">{{ 当前技能.名称 }}</span>
            <span class="技能说">{{ 当前技能.简介 }}</span>
          </div>
        </div>

        <!-- ① 空态：本集尚未拆分 -->
        <div v-if="阶段 === '未拆分'" class="卡片 空卡">
          <i class="el-icon-film 空图标"></i>
          <div class="空题">本集尚未拆分分镜</div>
          <div class="空副">点「开始拆分」，AI 会通读本集剧本与资产，自动拆成镜头列表；每个镜头可单独编辑或按技能重新生成</div>
          <button class="大钮" :disabled="!本集正文" @click="开始拆分()"><i class="el-icon-scissors"></i> {{ 本集正文 ? '开始拆分' : '本集还没有剧本，先去剧本编辑生成' }}</button>
        </div>

        <!-- ② 拆分中：进度页 -->
        <div v-if="阶段 === '拆分中'" class="卡片 进卡">
          <div class="进头行">
            <div class="进块">
              <div class="进键">分集进度</div>
              <div class="进值">第 <b>{{ 集号 }}</b> 集</div>
            </div>
            <span class="灰签">第 {{ 集号 }} 集{{ 集标题 ? ' · ' + 集标题 : '' }}</span>
            <span class="做签">生成中</span>
            <div style="flex:1"></div>
            <span class="拆签">拆分中…</span>
          </div>

          <div class="工卡">
            <div class="工行">
              <div class="工题">工作集 · 第 {{ 集号 }} 集</div>
              <span class="做签">生成中</span>
              <span v-if="当前技能" class="工技能">技能 · {{ 当前技能.名称 }}</span>
              <div style="flex:1"></div>
            </div>
            <div class="工步">{{ 步文案 }}</div>
            <div class="工提示">
              <i class="el-icon-info"></i>
              AI 正在拆分分镜，完成后自动落库。请不要关闭页面 · 一般约 1-3 分钟
            </div>
          </div>
        </div>

        <!-- 单镜重写中 -->
        <div v-if="重写镜号" class="卡片 进卡">
          <div class="进头行">
            <span class="做签">生成中</span>
            <span class="灰签">重写 {{ 重写镜号 }}（{{ 重写率 }}%）</span>
            <div style="flex:1"></div>
            <span class="拆签">AI 正在按本集剧本与相邻镜头重写这个镜头…</span>
          </div>
        </div>

        <!-- ③ 完成态：分镜结果列表 -->
        <template v-if="阶段 === '完成'">
          <!-- 统计 + 场次筛选 -->
          <div class="卡片 筛卡">
            <div class="数行">
              <div class="数块"><div class="数值">{{ 分镜列表.length }}</div><div class="数键">镜头</div></div>
              <div class="数块"><div class="数值">{{ 场次数 }}</div><div class="数键">场次</div></div>
              <div class="数块"><div class="数值">{{ 总时长 }}<span class="单位">s</span></div><div class="数键">总时长 / 约 {{ 集时长 }}s</div></div>
              <div class="数块"><div class="数值 主">{{ 已生成视频 }}<span class="单位">/{{ 分镜列表.length }}</span></div><div class="数键">已生成视频</div></div>
              <div style="flex:1"></div>
              <div class="档签">时长档 · {{ 时长档 }}</div>
            </div>
            <div class="chips">
              <button
                v-for="场 in 场次组" :key="场.名"
                class="chip" :class="{ 选中: 场次筛选 === 场.名 }"
                @click="场次筛选 = 场.名">{{ 场.名 }} ({{ 场.数 }})</button>
            </div>
          </div>

          <!-- 分镜行列表：可编辑 / 可单镜按技能重写 -->
          <div class="卡片 无内距 镜表">
            <div class="行头">
              <span>镜号</span>
              <span>景别 · 运镜</span>
              <span>画面 / 台词</span>
              <span>时长</span>
              <span>视频</span>
              <span>操作</span>
            </div>
            <div
              v-for="镜 in 显示分镜" :key="镜.镜号"
              class="镜行">
              <span class="格镜号"><code>{{ 镜.镜号 }}</code></span>
              <span class="格镜中">
                <span class="景签" :class="景类(镜.景别)">{{ 镜.景别 || '—' }}</span>
                <span class="运镜">{{ 镜.运镜 || '—' }}</span>
              </span>
              <span class="格镜画">
                <span class="画" :title="镜.画面">{{ 镜.画面 }}</span>
                <span v-if="镜.台词 && 镜.台词 !== '（无）'" class="词">「{{ 镜.台词 }}」</span>
              </span>
              <span class="格时">{{ 镜.时长 || '—' }}</span>
              <span class="格态">
                <video v-if="镜版本(镜).选中版" class="镜视频"
                       :src="媒体地址(镜版本(镜).选中版.url)" muted
                       @click="视频预览 = 镜版本(镜).选中版.url; 预览显 = true"></video>
                <span v-else class="态签" :class="{ 生成中: 镜.视频状态 === '生成中' }">
                  {{ 镜.视频状态 === '已生成' ? '已生成' : (镜.视频状态 === '生成中' ? '生成中…' : '待生成') }}
                </span>
                <span class="推签" v-if="镜推荐(镜)" :title="'智能推荐生成方式：' + 镜推荐(镜)">推·{{ 镜推荐(镜) }}</span>
              </span>
              <span class="格操作">
                <el-button type="text" size="mini" @click="打开编辑(镜)">编辑</el-button>
                <el-button
                  type="text" size="mini" :disabled="!!重写镜号 || 阶段 !== '完成'"
                  @click="重写单镜(镜)">AI重写</el-button>
                <el-button type="primary" size="mini" plain :disabled="阶段 !== '完成'" @click="进单镜(镜)">生成视频</el-button>
                <el-button type="text" size="mini" class="删钮" @click="删镜(镜)">删</el-button>
              </span>
            </div>
          </div>
          <div class="提示行">「编辑」直接改画面/台词/景别等并即时落库 ·「AI重写」按本集剧本重新生成这一镜</div>

          <!-- 下游 -->
          <div class="卡片">
            <div class="行间" style="justify-content:space-between;flex-wrap:wrap;gap:12px">
              <div>
                <div style="font-size:14px;font-weight:600;color:var(--字)">全部镜头生成完？去合成</div>
                <div style="font-size:12px;color:var(--字弱);margin-top:4px">成片合成把已生成的镜头按顺序串上时间线，补音轨、加字幕、导出本集。</div>
              </div>
              <el-button size="small" type="primary" plain @click="进合成()">进入成片合成</el-button>
            </div>
          </div>
        </template>

        <!-- 底部 -->
        <div class="行间 右">
          <el-button @click="上一步()">上一步：美术资产</el-button>
          <el-button type="primary" @click="进合成()">下一步：成片合成<i class="el-icon-arrow-right"></i></el-button>
        </div>

        <!-- 编辑分镜弹窗：拆出为独立组件「拆分分镜编辑弹窗.vue」（表单/存编辑中/保存编辑已搬入子组件，
             in-DOM 约定用 ASCII 别名 edit-dialog；保存后经 @已保存 把新列表写回） -->
        <edit-dialog
          :显示.sync="编辑弹窗显示"
          :缓冲="编辑缓冲"
          :分镜列表="分镜列表"
          :存全库="存全库"
          @已保存="分镜列表 = $event"></edit-dialog>

        <!-- 视频预览弹窗：拆出为独立组件「拆分分镜预览弹窗.vue」（ASCII 别名 preview-dialog） -->
        <preview-dialog :显示.sync="预览显" :地址="视频预览"></preview-dialog>

        <!-- 技能生成弹窗：技能 + 技能引导提示词 + 引入数据（本集剧本 / 人物 / 资产 / 拆分要求）。
             in-DOM 模板只认 ASCII 标签名，必须用 skill-dialog 别名；事件处理器必须带括号。 -->
        <skill-dialog
          :显示.sync="技能弹窗显示"
          :技能列表="技能列表"
          :技能id.sync="扩写技能id"
          :引导.sync="技能引导"
          :默认引导="默认引导"
          :配置类型="页配置类型"
          目标名="分镜拆分"
          :引入数据="引入数据"
          @保存="技能已保存($event)"></skill-dialog>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import 剧集侧栏 from '@/共用/剧集侧栏/index.vue'
import 技能生成弹窗 from '@/共用/技能生成弹窗/index.vue'
import 拆分分镜编辑弹窗 from './拆分分镜编辑弹窗.vue'
import 拆分分镜预览弹窗 from './拆分分镜预览弹窗.vue'
import { 取, 发 } from '@/接口/请求'
import { 媒体地址 } from '@/接口/媒体'
import { 提交AI任务 } from '@/共用/AI任务'
import { 取配置类型, 读引导, 读技能id, 读引入, 存引入, 适配技能id } from '@/共用/技能生成配置'
import { 方式表, 拼任务参数, 校验方式, 匹配资产, 提示词草稿, 取镜秒, 对账生成中版本, 落对账结果, 推荐方式 } from '@/共用/分镜视频'

/* 本页默认技能引导提示词：拆分规则 + 输出格式 */
const 默认引导文本 = [
  '· 通读引入的本集剧本与资产，按动作节拍拆成镜头，逐镜输出，一行一镜，字段用「｜」分隔：镜号｜场次｜景别｜运镜｜画面｜台词｜时长',
  '· 场次用「场次 N · 地点」格式，与剧本场次对应；镜头按剧本顺序排列',
  '· 画面字段写清主体动作与可拍细节（谁在做什么、环境细节、可对上资产名），涉及人物/场景/道具时沿用资产名，保证连续性',
  '· 台词优先用剧本原句；无台词的镜头写「（无）」',
  '· 单镜时长遵守拆分要求里的时长档，全部镜头加起来接近本集目标时长',
  '· 每个场次拆 2-4 个镜头，先建立空间再进人物；除镜号行以外不要输出任何解释、前言、后记'
].join('\n')

export default {
  name: 'ShotSplit',
  components: { 'ep-rail': 剧集侧栏, 'skill-dialog': 技能生成弹窗, 'edit-dialog': 拆分分镜编辑弹窗, 'preview-dialog': 拆分分镜预览弹窗 },
  data() {
    return {
      /* 读库状态 */
      载入中: true,
      载入报错: '',
      /* 页面三态：未拆分 → 拆分中 → 完成 */
      阶段: '未拆分',
      分镜列表: [],
      场次筛选: '全部',
      时长档: '标准 ≤15秒',
      拆分率: 0,
      步序: 0,
      计时器: null,
      /* 本集剧本（真库） */
      本集正文: '',
      场次们: [],
      /* 引入库数据 */
      人物文本: '',
      资产文本: '',
      /* 单镜重写 */
      重写镜号: '',
      重写率: 0,
      重写计时器: null,
      /* 视频生成：版本们 / 美术资产（带图）/ 批量 / 预览 / 监控 */
      版本们: [],
      美术行们: [],
      批量中: false,
      视频预览: '',
      预览显: false,
      监控定时器: null,
      /* 行编辑（弹窗本体已拆出为 edit-dialog，显隐与缓冲留在父组件） */
      编辑弹窗显示: false,
      编辑缓冲: null,
      /* 技能生成（与剧本创作页同一套） */
      技能弹窗显示: false,
      技能列表: [],
      扩写技能id: '',
      技能引导: '',
      引入勾选: [],
      拆分要求: '1. 单镜时长不超过 15 秒\n2. 每个场次拆 2-4 个镜头\n3. 台词优先用剧本原句，无台词镜头写「（无）」'
    }
  },
  computed: {
    剧名() { return this.$route.query.name || '' },
    剧id() { return parseInt(this.$route.query.ep) || 0 },
    集号() { return parseInt(this.$route.query.集) || 1 },
    集标题() { return this.$route.query.标题 || '' },
    集时长() { return 60 },
    页配置类型() { return 取配置类型('/video/shot') },
    默认引导() { return 默认引导文本 },
    当前技能() {
      const id = String(this.扩写技能id)
      for (let i = 0; i < this.技能列表.length; i++) {
        if (String(this.技能列表[i].id) === id) return this.技能列表[i]
      }
      return null
    },
    /* 引入数据：真库剧本正文 + 真人物 + 真资产 + 可编辑的拆分要求 */
    引入数据() {
      const 页 = this
      const 本集剧本 = 页.本集正文
        ? ('第 ' + 页.集号 + ' 集' + (页.集标题 ? ' · ' + 页.集标题 : '') + '\n' + 页.本集正文)
        : '（本集还没有剧本）'
      const 场次文本 = 页.场次们.length
        ? 页.场次们.map(function (场) { return (场.场 || '') + ' · ' + (场.地点 || '') }).join('\n')
        : ''
      return [
        { 键: '剧本', 名: '本集剧本（真库）', 值: 本集剧本, 提示: '拆分的原始依据' },
        { 键: '场次', 名: '本集场次表', 值: 场次文本 || '（无场次数据）', 提示: '场次归属用' },
        { 键: '人物', 名: '人物资产（真库人物设定）', 值: 页.人物文本 || '（暂无人物数据）', 提示: '人物名与台词对齐用' },
        { 键: '场景道具', 名: '场景/道具/服装资产（真库）', 值: 页.资产文本 || '（暂无资产数据）', 提示: '画面细节连续性用' },
        { 键: '拆分要求', 名: '拆分要求（可编辑）', 值: 页.拆分要求, 可编辑: true, 占位: '例：单镜不超过15秒；每场次2-4个镜头…' }
      ].map(function (项) {
        return Object.assign({}, 项, { 勾选: 页.引入勾选.indexOf(项.键) !== -1 })
      })
    },
    步文案() {
      const 步们 = [
        '正在通读本集剧本，识别场次与动作节拍…',
        '正在按动作切镜头，标注景别与运镜…',
        '正在为每个镜头分配台词与时长…',
        '拆分结果落库中…'
      ]
      return 步们[Math.min(步们.length - 1, this.步序)]
    },
    场次组() {
      const 表 = {}
      this.分镜列表.forEach(function (x) { 表[x.场次] = (表[x.场次] || 0) + 1 })
      const 出 = [{ 名: '全部', 数: this.分镜列表.length }]
      Object.keys(表).forEach(function (名) { 出.push({ 名: 名, 数: 表[名] }) })
      return 出
    },
    场次数() {
      return Object.keys(this.分镜列表.reduce(function (表, x) { 表[x.场次] = 1; return 表 }, {})).length
    },
    显示分镜() {
      const 场 = this.场次筛选
      if (场 === '全部') return this.分镜列表
      return this.分镜列表.filter(function (x) { return x.场次 === 场 })
    },
    已生成视频() {
      return this.分镜列表.filter(function (x) { return x.视频状态 === '已生成' }).length
    },
    总时长() {
      return this.分镜列表.reduce(function (和, x) { return 和 + (parseInt(x.时长) || 0) }, 0)
    }
  },
  created() {
    this.载入()
    const 页 = this
    /* 带出已存配置：引导提示词（按 页面×技能）+ 技能 + 引入勾选 */
    读引导(this.页配置类型, this.扩写技能id).then(function (引导) { if (引导) 页.技能引导 = 引导 })
    const 技能 = 读技能id(this.页配置类型)
    if (技能) this.扩写技能id = 技能
    const 已存勾 = 读引入(this.页配置类型)
    this.引入勾选 = 已存勾 || ['剧本', '场次', '人物', '场景道具', '拆分要求']
    try {
      const 存的 = localStorage.getItem('技能生成:拆分要求:' + this.剧名)
      if (存的) this.拆分要求 = 存的
    } catch (e) { /* 忽略 */ }
  },
  beforeDestroy() {
    if (this.计时器) clearInterval(this.计时器)
    if (this.重写计时器) clearInterval(this.重写计时器)
    if (this.监控定时器) clearInterval(this.监控定时器)
  },
  methods: {
    媒体地址,
    /* ---------------- 视频生成 ---------------- */
    async 刷版本们() {
      try {
        const 据 = await 取('/api/分镜/视频?剧id=' + this.剧id + '&集号=' + this.集号)
        this.版本们 = (据 && 据.版本们) || []
      } catch (e) { this.版本们 = [] }
    },
    镜版本(镜) {
      const 号 = 镜.镜号
      const 本镜 = this.版本们.filter(function (v) { return v.镜号 === 号 })
      const 选 = 本镜.filter(function (v) { return v.选中 && v.状态 === '已生成' && v.url })[0]
      return { 选中版: 选 || null, 生成中: 本镜.some(function (v) { return v.状态 === '生成中' }) }
    },
    镜推荐(镜) {
      const 页 = this
      if (页.阶段 !== '完成') return ''
      const 本镜 = 页.镜版本(镜)
      if (本镜.生成中) return ''
      const 键 = 页.镜推荐键(镜, 本镜.选中版)
      return 键 && 方式表[键] ? 方式表[键].名 : ''
    },
    镜推荐键(镜, 有选中版) {
      /* 与导演台/连续生成共用同一套推荐规则（分镜视频.js 推荐方式），保证「标签=实际提交方式」 */
      const 命中数 = 匹配资产(镜.画面, this.美术行们).length
      return 推荐方式(镜, [], 命中数, !!有选中版)
    },
    /* 连续生成：未完成的镜按推荐方式排队提交现有任务 API（不等结果，出片由监控写回） */
    async 连续生成() {
      const 页 = this
      const 待生成 = 页.分镜列表.filter(function (x) { return x.视频状态 !== '已生成' && x.视频状态 !== '生成中' })
      if (!待生成.length) { 页.$message.success('没有待生成的镜'); return }
      页.批量中 = true
      let 排上 = 0
      for (let i = 0; i < 待生成.length; i++) {
        const 镜 = 待生成[i]
        try {
          const 键 = 页.镜推荐键(镜, null)
          const 参考们 = 匹配资产(镜.画面, 页.美术行们).map(function (行) {
            const 当前图 = (行.图们 || []).filter(function (g) { return g.状态 === '当前' })[0]
            return 当前图 ? 当前图.url : ''
          }).filter(function (u) { return u })
          /* 推荐方式缺素材就降级：要参考图没图 → 文生视频 */
          let 方式 = 键
          if (方式 !== '二采重绘' && 方式 !== '文生视频' && !参考们.length) 方式 = '文生视频'
          const 槽 = {
            首帧: '', 尾帧: '', 源视频: '',
            参考图们: 参考们,
            提示词: 镜.生成提示词 || 提示词草稿(镜),
            反向提示词: ''
          }
          const 错 = 校验方式(方式, 槽)
          if (错) continue
          const 参数 = 拼任务参数(方式, 槽, { 比例: '9:16', 一采MP: 0.4, 时长: 取镜秒(镜.时长, 5) })
          const 据 = await 发('/api/任务/提交', 参数)
          await 发('/api/分镜/视频保存', {
            剧id: 页.剧id, 集号: 页.集号, 镜号: 镜.镜号, 动作: '添加',
            方式: 方式, 提示词: 槽.提示词, 任务id: (据 && 据.id) || 0
          })
          镜.视频状态 = '生成中'
          镜.生成方式 = 方式
          镜.生成提示词 = 槽.提示词
          排上 += 1
        } catch (e) { /* 单镜失败不影响后面 */ }
      }
      if (排上) {
        try { await 页.存全库(页.分镜列表) } catch (e) { /* 忽略 */ }
        await 页.刷版本们()
        页.开监控()
      }
      页.批量中 = false
      页.$message.success('已排队 ' + 排上 + ' 镜，出片自动写回本列表')
    },
    开监控() {
      const 页 = this
      if (页.监控定时器) return
      页.监控定时器 = setInterval(function () {
        if (document.hidden) return
        页.对账一轮()
      }, 8000)
    },
    async 对账一轮() {
      const 页 = this
      if (!页.版本们.some(function (v) { return v.状态 === '生成中' })) {
        if (页.监控定时器) { clearInterval(页.监控定时器); 页.监控定时器 = null }
        return
      }
      try {
        const 结果们 = await 对账生成中版本(页.版本们)
        if (!结果们.length) return
        let 变了 = false
        for (let i = 0; i < 结果们.length; i++) {
          const 项 = 结果们[i]
          await 落对账结果(页.剧id, 页.集号, 项.镜号, 项)
          const 镜 = 页.分镜列表.filter(function (x) { return x.镜号 === 项.镜号 })[0]
          if (镜 && 项.状态 === '已生成') { 镜.视频状态 = '已生成'; 变了 = true }
          if (镜 && 项.状态 === '失败') { 镜.视频状态 = '待生成'; 变了 = true }
        }
        await 页.刷版本们()
        if (变了) {
          try { await 页.存全库(页.分镜列表) } catch (e) { /* 忽略 */ }
          页.$message.success('有镜出片了，已写回列表')
        }
      } catch (e) { /* 下一轮再试 */ }
    },
    /* ---------------- 读库 ---------------- */
    async 载入() {
      const 页 = this
      页.载入中 = true
      页.载入报错 = ''
      try {
        /* 技能池 + 默认适配 */
        await 页.拉技能列表()
        /* 本集分镜 */
        const 分镜数据 = await 取('/api/分镜/列表?剧id=' + 页.剧id + '&集号=' + 页.集号)
        页.分镜列表 = (分镜数据 && 分镜数据.分镜们) || []
        /* 本集剧本（含场次） */
        try {
          const 剧本数据 = await 取('/api/剧本/列表?剧id=' + 页.剧id)
          const 行 = ((剧本数据 && 剧本数据.剧本们) || []).filter(function (x) { return x.集号 === 页.集号 })[0]
          if (行) {
            页.本集正文 = 行.正文 || ''
            页.场次们 = 行.场次们 || []
          }
        } catch (e) { /* 剧本没生成不阻塞分镜页 */ }
        /* 人物（真库人物设定） */
        try {
          const 人物数据 = await 取('/api/人物/列表?剧id=' + 页.剧id)
          页.人物文本 = (人物数据.人物们 || []).map(function (人) {
            return [人.人物id || '', 人.名 || '', 人.性别 || '', 人.年龄档 || '', 人.身份 || '', 人.性格 || '', 人.台词风格 || ''].join('｜')
          }).join('\n')
        } catch (e) { 页.人物文本 = '' }
        /* 资产（真库，全集） */
        try {
          const 资产数据 = await 取('/api/资产/列表?剧id=' + 页.剧id)
          页.资产文本 = (资产数据.资产们 || []).map(function (项) {
            return [项.资产id || '', 项.类型 || '', 项.名称 || '', 项.级别 || '', 项.摘要 || ''].join('｜')
          }).join('\n')
        } catch (e) { 页.资产文本 = '' }
        /* 美术资产（带当前参考图，智能推荐/批量生成用） */
        try {
          const 美据 = await 取('/api/美术/列表?剧id=' + 页.剧id)
          页.美术行们 = ((美据 && 美据.行们) || []).filter(function (行) { return 行.图们 && 行.图们.length })
        } catch (e) { 页.美术行们 = [] }
        /* 分镜视频版本（选中版缩略/生成中监控） */
        await 页.刷版本们()

        页.阶段 = 页.分镜列表.length ? '完成' : '未拆分'
        /* 首次进入且本集已有剧本：自动拆分（生成完直接落库） */
        if (页.阶段 === '未拆分' && 页.本集正文) {
          页.跑拆分()
        }
        /* 有「生成中」版本就开监控（上一次排队的任务继续回写） */
        if (页.版本们.some(function (v) { return v.状态 === '生成中' })) 页.开监控()
      } catch (e) {
        页.载入报错 = '分镜读取失败：' + ((e && e.message) || e)
      }
      页.载入中 = false
    },
    /* ---------------- 技能配置（与剧本创作页同一套） ---------------- */
    async 拉技能列表() {
      try {
        const 数据 = await 取('/api/提示词/技能列表?分类=minimax')
        this.技能列表 = (数据 && 数据.列表) || []
        if (!this.扩写技能id && this.技能列表.length) {
          this.扩写技能id = 适配技能id(this.技能列表, this.页配置类型)
        }
      } catch (e) {
        /* 技能列表拉不到不阻塞页面 */
      }
    },
    打开技能() {
      this.技能引导 = this.技能引导 || this.默认引导
      this.技能弹窗显示 = true
    },
    技能已保存(值) {
      const 类型 = this.页配置类型
      const 引入 = (值 && 值.引入) || []
      const 勾 = []
      for (let i = 0; i < 引入.length; i++) {
        if (引入[i].键 === '拆分要求') {
          this.拆分要求 = 引入[i].值 || ''
          try { localStorage.setItem('技能生成:拆分要求:' + this.剧名, this.拆分要求) } catch (e) { /* 忽略 */ }
        }
        if (引入[i].勾选) 勾.push(引入[i].键)
      }
      this.引入勾选 = 勾
      存引入(类型, 勾)
      if (值 && 值.引导) this.技能引导 = 值.引导
    },

    景类(景别) {
      if (景别 === '特写' || 景别 === '近景') return '近'
      if (景别 === '全景') return '远'
      return '中'
    },
    /* ---------------- 拆分（真 AI 任务，完成即落库） ---------------- */
    开始拆分() {
      const 页 = this
      if (页.阶段 === '拆分中') return
      if (!页.扩写技能id) {
        页.$message.warning('请先点「技能」选择技能与引导提示词')
        页.打开技能()
        return
      }
      if (!页.本集正文) {
        页.$message.warning('本集还没有剧本，先去 剧本编辑 生成正文')
        return
      }
      if (页.阶段 === '完成') {
        页.$confirm('重新拆分会覆盖当前 ' + 页.分镜列表.length + ' 个分镜（重写落库），确定？', '重新拆分', {
          confirmButtonText: '重新拆分', cancelButtonText: '取消', type: 'warning'
        }).then(function () { 页.跑拆分() }).catch(function () {})
        return
      }
      页.跑拆分()
    },
    /* 组装提示词需求：勾选的引入数据 + 拆分要求 */
    组需求() {
      const 页 = this
      const 段们 = []
      for (let i = 0; i < 页.引入数据.length; i++) {
        const 项 = 页.引入数据[i]
        if (!项.勾选 || 项.键 === '拆分要求') continue
        段们.push('【' + 项.名 + '】\n' + (项.值 || ''))
      }
      段们.push('【拆分要求】\n' + 页.拆分要求)
      段们.push('【输出】只输出分镜行，一行一镜，格式：镜号｜场次｜景别｜运镜｜画面｜台词｜时长。镜号从 SH001 顺序编号。')
      return 段们.join('\n\n')
    },
    async 跑拆分() {
      const 页 = this
      if (页.阶段 === '拆分中') return
      页.阶段 = '拆分中'
      页.拆分率 = 0
      页.步序 = 0
      if (页.计时器) clearInterval(页.计时器)
      页.计时器 = setInterval(function () {
        页.步序 = Math.min(3, 页.步序 + 1)
        页.拆分率 = Math.min(95, 页.拆分率 + 25)
      }, 20000)
      try {
        const 规则 = 页.技能引导 || 页.默认引导
        const 文本 = String(await 提交AI任务({ 技能id: 页.扩写技能id, 系统: 规则, 正向: 页.组需求() }) || '').trim()
        if (!文本) throw new Error('AI 没有返回内容')
        const 镜们 = 页.解析分镜(文本)
        if (!镜们.length) throw new Error('AI 返回里没有可识别的分镜行')
        /* 旧镜号里不再出现于新列表的：其生成版本/资源图成为孤儿，一并清掉（同镜号保留历史版本） */
        await 页.清孤儿版本(Object.keys(镜们.reduce(function (表, 行) { 表[行.镜号] = 1; return 表 }, {})))
        await 发('/api/分镜/保存', { 剧id: 页.剧id, 集号: 页.集号, 镜们: 镜们 })
        页.分镜列表 = 镜们.map(function (行, 序) {
          return Object.assign({ id: 序 + 1 }, 行)
        })
        页.场次筛选 = '全部'
        页.阶段 = '完成'
        页.$message.success('拆分完成并已落库：' + 页.分镜列表.length + ' 个镜头 · ' + 页.场次数 + ' 个场次')
      } catch (e) {
        页.阶段 = 页.分镜列表.length ? '完成' : '未拆分'
        页.$message.error('拆分失败：' + ((e && e.message) || e))
      }
      if (页.计时器) { clearInterval(页.计时器); 页.计时器 = null }
    },
    /* 解析 AI 输出：镜号｜场次｜景别｜运镜｜画面｜台词｜时长 */
    解析分镜(文本) {
      const 行们 = String(文本).split('\n')
      const 出 = []
      for (let i = 0; i < 行们.length; i++) {
        const 行 = 行们[i].trim()
        if (!行 || 行.indexOf('｜') < 0) continue
        const 段 = 行.split('｜').map(function (s) { return s.trim() })
        if (段.length < 5) continue
        const 画面 = 段[4] || ''
        if (!画面) continue
        出.push({
          镜号: 段[0] || ('SH%03d'.replace('%03d', String(出.length + 1).padStart(3, '0'))),
          场次: 段[1] || '场次 1',
          景别: 段[2] || '中景',
          运镜: 段[3] || '固定',
          画面: 画面,
          台词: 段[5] || '（无）',
          时长: 段[6] || '3s',
          视频状态: '待生成'
        })
      }
      /* 镜号缺失或重复时兜底重编 */
      const 见过 = {}
      for (let i = 0; i < 出.length; i++) {
        if (!出[i].镜号 || 见过[出[i].镜号]) 出[i].镜号 = 'SH' + String(i + 1).padStart(3, '0')
        见过[出[i].镜号] = 1
      }
      return 出
    },
    清空() {
      const 页 = this
      页.$confirm('清空后删除库里本集全部分镜并回到「未拆分」状态，本集已生成的视频版本和资源图也会一并清掉，确定？', '清空重拆', {
        confirmButtonText: '清空', cancelButtonText: '取消', type: 'warning'
      }).then(async function () {
        try {
          /* 先记下旧镜号，落库清分镜后把这些镜号的版本/资源图一并清干净 */
          const 旧镜号们 = 页.分镜列表.map(function (行) { return 行.镜号 })
          await 发('/api/分镜/保存', { 剧id: 页.剧id, 集号: 页.集号, 镜们: [] })
          for (let i = 0; i < 旧镜号们.length; i++) {
            try {
              await 发('/api/分镜/视频保存', { 剧id: 页.剧id, 集号: 页.集号, 镜号: 旧镜号们[i], 动作: '清空' })
            } catch (e1) { /* 单镜清理失败不阻塞 */ }
            try {
              await 发('/api/分镜/图保存', { 剧id: 页.剧id, 集号: 页.集号, 镜号: 旧镜号们[i], 动作: '清空' })
            } catch (e2) { /* 忽略 */ }
          }
          页.分镜列表 = []
          页.阶段 = '未拆分'
          页.$message.info('已清空（该集分镜、视频版本与资源图均已删除）')
        } catch (e) {
          页.$message.error('清空失败：' + ((e && e.message) || e))
        }
      }).catch(function () {})
    },
    /* 重拆时清理孤儿：旧镜号不在新列表里的，其视频版本清掉（同镜号保留） */
    async 清孤儿版本(新镜号表) {
      const 页 = this
      const 旧镜号们 = 页.分镜列表.map(function (行) { return 行.镜号 })
      for (let i = 0; i < 旧镜号们.length; i++) {
        const 号 = 旧镜号们[i]
        if (新镜号表[号]) continue
        try {
          await 发('/api/分镜/视频保存', { 剧id: 页.剧id, 集号: 页.集号, 镜号: 号, 动作: '清空' })
        } catch (e1) { /* 忽略 */ }
        try {
          await 发('/api/分镜/图保存', { 剧id: 页.剧id, 集号: 页.集号, 镜号: 号, 动作: '清空' })
        } catch (e2) { /* 忽略 */ }
      }
    },
    /* ---------------- 行编辑（即时落库） ---------------- */
    打开编辑(镜) {
      this.编辑缓冲 = {
        镜号: 镜.镜号, 场次: 镜.场次, 景别: 镜.景别, 运镜: 镜.运镜,
        画面: 镜.画面, 台词: 镜.台词, 时长: 镜.时长
      }
      this.编辑弹窗显示 = true
    },
    /* 保存编辑已搬入子组件「拆分分镜编辑弹窗.vue」（保存后经 @已保存 写回 分镜列表） */
    /* 传完整列表（后端该集全量替换语义） */
    async 存全库(列表) {
      const 页 = this
      const 行们 = (列表 || 页.分镜列表).map(function (镜) {
        return {
          镜号: 镜.镜号, 场次: 镜.场次, 景别: 镜.景别, 运镜: 镜.运镜,
          画面: 镜.画面, 台词: 镜.台词, 时长: 镜.时长, 视频状态: 镜.视频状态 || '待生成',
          /* 全量替换语义：这两列是导演台写的，这里不带上就会把它们抹掉 */
          生成方式: 镜.生成方式 || null, 生成提示词: 镜.生成提示词 || null
        }
      })
      await 发('/api/分镜/保存', { 剧id: 页.剧id, 集号: 页.集号, 镜们: 行们 })
    },
    async 删镜(镜) {
      const 页 = this
      try {
        await 页.$confirm('删除镜头 ' + 镜.镜号 + '（落库删除），确定？', '删除镜头', {
          confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning'
        })
      } catch (e) { return }
      const 新列表 = 页.分镜列表.filter(function (行) { return 行.镜号 !== 镜.镜号 })
      try {
        await 页.存全库(新列表)
        页.分镜列表 = 新列表
        if (!新列表.length) 页.阶段 = '未拆分'
        页.$message.success('已删除 ' + 镜.镜号)
      } catch (e) {
        页.$message.error('删除失败：' + ((e && e.message) || e))
      }
    },
    /* 单镜按技能重写：给剧本 + 相邻镜头上下文，输出一行替换本镜 */
    async 重写单镜(镜) {
      const 页 = this
      if (页.重写镜号 || 阶段占位()) return
      function 阶段占位() { return 页.阶段 !== '完成' }
      if (!页.扩写技能id) {
        页.$message.warning('请先点「技能」选择技能与引导提示词')
        页.打开技能()
        return
      }
      const 序号 = 页.分镜列表.indexOf(镜)
      const 前镜 = 序号 > 0 ? 页.分镜列表[序号 - 1] : null
      const 后镜 = 序号 < 页.分镜列表.length - 1 ? 页.分镜列表[序号 + 1] : null
      页.重写镜号 = 镜.镜号
      页.重写率 = 0
      if (页.重写计时器) clearInterval(页.重写计时器)
      页.重写计时器 = setInterval(function () {
        页.重写率 = Math.min(95, 页.重写率 + 20)
      }, 8000)
      try {
        const 需求 = [
          '【本集剧本】\n' + 页.本集正文.slice(0, 6000),
          '【要重写的镜头】\n镜号：' + 镜.镜号 + '｜场次：' + 镜.场次 + '｜当前画面：' + 镜.画面 + '｜当前台词：' + (镜.台词 || '（无）'),
          '【前一镜】\n' + (前镜 ? 前镜.镜号 + '｜' + 前镜.画面 : '（无，本镜是开头）'),
          '【后一镜】\n' + (后镜 ? 后镜.镜号 + '｜' + 后镜.画面 : '（无，本镜是结尾）'),
          '【要求】重写这一镜：保持镜号 ' + 镜.镜号 + ' 与场次「' + 镜.场次 + '」不变，画面与台词要衔接前后镜、忠于剧本原意，画面写清可拍细节。',
          '【输出】只输出一行，格式：景别｜运镜｜画面｜台词｜时长'
        ].join('\n\n')
        const 规则 = (页.技能引导 || 页.默认引导) + '\n\n本次任务只重写一个镜头：只输出一行「景别｜运镜｜画面｜台词｜时长」，不要输出镜号、场次和其他任何内容。'
        const 文本 = String(await 提交AI任务({ 技能id: 页.扩写技能id, 系统: 规则, 正向: 需求 }) || '').trim()
        if (!文本) throw new Error('AI 没有返回内容')
        /* 取最后一条可解析行 */
        const 行们 = 文本.split('\n').map(function (s) { return s.trim() }).filter(function (s) { return s.indexOf('｜') >= 0 })
        if (!行们.length) throw new Error('AI 返回里没有可识别的行')
        const 段 = 行们[行们.length - 1].split('｜').map(function (s) { return s.trim() })
        const 新列表 = 页.分镜列表.map(function (行) {
          if (行.镜号 !== 镜.镜号) return 行
          return Object.assign({}, 行, {
            景别: 段[0] || 行.景别, 运镜: 段[1] || 行.运镜,
            画面: 段[2] || 行.画面, 台词: 段[3] || '（无）', 时长: 段[4] || 行.时长
          })
        })
        await 页.存全库(新列表)
        页.分镜列表 = 新列表
        页.$message.success(镜.镜号 + ' 已重写并落库')
      } catch (e) {
        页.$message.error('重写失败：' + ((e && e.message) || e))
      }
      if (页.重写计时器) { clearInterval(页.重写计时器); 页.重写计时器 = null }
      页.重写镜号 = ''
    },
    /* 生成视频在单镜生成页（/video/director）做，列表页只负责展示与进入 */
    进单镜(镜) {
      const 查询 = Object.assign({}, this.$route.query)
      if (镜) 查询.镜 = 镜.镜号
      this.$router.push({ path: '/video/director', query: 查询 })
    },
    进合成() {
      this.$router.push({ path: '/video/film', query: this.$route.query })
    },
    上一步() {
      this.$router.push({ path: '/video/art', query: this.$route.query })
    }
  }
}
</script>

<style scoped>
/* ---- 页头 ---- */
.头卡 { padding: 16px 18px; margin-bottom: 14px; }
.头行 { display: flex; align-items: flex-start; gap: 12px; }
.头题 { font-size: 15px; font-weight: 700; color: var(--字); }
.头副 { margin-top: 4px; font-size: 12px; color: var(--字弱); }

.技能行 {
  margin-top: 12px; padding-top: 10px;
  border-top: 1px dashed var(--描边);
  display: flex; align-items: center; gap: 8px;
  font-size: 12px; min-width: 0;
}
.技能签 {
  flex: 0 0 auto; font-size: 11px; color: var(--主);
  background: var(--主浅, rgba(64,158,255,.12));
  border-radius: 4px; padding: 1px 7px;
}
.技能名 { flex: 0 0 auto; color: var(--字); font-weight: 600; }
.技能说 {
  color: var(--字弱); overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap;
}

/* ---- ① 空态 ---- */
.空卡 {
  padding: 64px 24px; text-align: center;
  display: flex; flex-direction: column; align-items: center; gap: 10px;
}
.空图标 { font-size: 46px; color: var(--字弱); }
.空题 { font-size: 16px; font-weight: 700; color: var(--字); }
.空副 { font-size: 12px; color: var(--字弱); max-width: 460px; line-height: 1.8; }
.大钮 {
  margin-top: 14px; cursor: pointer;
  font-size: 14px; font-weight: 600; color: #fff;
  background: var(--主); border: 0; border-radius: 8px;
  padding: 10px 28px;
  transition: opacity .15s;
}
.大钮:disabled { opacity: .5; cursor: not-allowed; }
.大钮:hover:not(:disabled) { opacity: .88; }

/* ---- ② 拆分中 ---- */
.进卡 { padding: 16px 18px; margin-bottom: 14px; }
.进头行 { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.进键 { font-size: 11px; color: var(--字弱); }
.进值 { font-size: 14px; color: var(--字); margin-top: 2px; }
.进值 b { color: var(--主); }
.灰签 {
  font-size: 12px; color: var(--字次);
  background: var(--卡片二); border: 1px solid var(--描边);
  border-radius: 6px; padding: 3px 10px;
}
.做签 {
  font-size: 12px; color: var(--警, #e6a23c);
  background: rgba(230,162,60,.1); border-radius: 6px; padding: 3px 10px;
}
.拆签 { font-size: 13px; color: var(--警, #e6a23c); font-weight: 600; }

.工卡 {
  margin-top: 14px; border: 1px solid var(--描边);
  border-radius: 10px; padding: 16px 18px;
  background: var(--卡片二);
}
.工行 { display: flex; align-items: center; gap: 10px; }
.工题 { font-size: 14px; font-weight: 600; color: var(--字); }
.工技能 {
  font-size: 11px; color: var(--主);
  background: var(--主浅, rgba(64,158,255,.12));
  border-radius: 4px; padding: 1px 7px;
}
.工步 { margin-top: 10px; font-size: 12px; color: var(--字次); }
.工提示 {
  margin-top: 12px; font-size: 12px; color: var(--字弱);
  display: flex; align-items: center; gap: 6px;
}

/* ---- ③ 完成态 ---- */
.筛卡 { padding: 14px 16px; margin-bottom: 14px; }
.数行 { display: flex; align-items: flex-end; gap: 28px; flex-wrap: wrap; }
.数块 { min-width: 64px; }
.数值 { font-size: 20px; font-weight: 700; color: var(--字); line-height: 1.2; }
.数值.主 { color: var(--主); }
.单位 { font-size: 12px; font-weight: 400; color: var(--字弱); margin-left: 2px; }
.数键 { font-size: 11px; color: var(--字弱); margin-top: 2px; }
.档签 {
  font-size: 12px; color: var(--字次);
  background: var(--卡片二); border: 1px solid var(--描边);
  border-radius: 6px; padding: 3px 10px; margin-bottom: 2px;
}
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
.chip {
  font-size: 12px; color: var(--字次); cursor: pointer;
  background: var(--卡片二); border: 1px solid var(--描边);
  border-radius: 999px; padding: 3px 12px;
  transition: all .15s ease;
}
.chip:hover { border-color: var(--描边亮, var(--描边)); color: var(--字); }
.chip.选中 { border-color: var(--主); color: var(--主); background: var(--主浅, transparent); }

/* ---- 分镜行列表 ---- */
.镜表 { margin-bottom: 10px; font-size: 12px; }
.行头, .镜行 {
  display: grid;
  grid-template-columns: 76px 110px 1fr 56px 120px 250px;
  gap: 10px;
  align-items: center;
  padding: 10px 16px;
}
.行头 {
  color: var(--字弱); font-size: 11px;
  border-bottom: 1px solid var(--描边);
  background: var(--卡片二);
}
.镜行 {
  border-bottom: 1px solid var(--描边);
  transition: background .15s;
}
.镜行:last-child { border-bottom: none; }
.镜行:hover { background: var(--卡片二); }
.格镜号 code {
  font-family: Consolas, monospace; font-size: 11px;
  color: var(--字弱); background: var(--描边);
  border-radius: 4px; padding: 1px 6px;
}
.格镜中 { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.景签 { font-size: 11px; border-radius: 4px; padding: 1px 7px; }
.景签.近 { color: var(--主); background: var(--主浅, rgba(64,158,255,.12)); }
.景签.中 { color: var(--字次); background: var(--卡片二); border: 1px solid var(--描边); }
.景签.远 { color: #9a88c8; background: rgba(154,136,200,.14); }
.运镜 { font-size: 11px; color: var(--字弱); }
.格镜画 { min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.格镜画 .画 {
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  color: var(--字次); line-height: 1.6;
}
.格镜画 .词 { font-size: 12px; color: var(--字); }
.格时 { color: var(--字次); font-variant-numeric: tabular-nums; }
.态签 { font-size: 11px; color: var(--成, #67c23a); }
.态签.生成中 { color: var(--警, #e6a23c); }
.镜视频 {
  display: block; width: 100%; height: 46px; object-fit: cover;
  border-radius: 6px; background: #000; cursor: pointer;
}
.推签 {
  display: inline-block; margin-top: 4px; font-size: 10px; padding: 0 6px;
  border-radius: 999px; background: var(--主弱, rgba(64,158,255,.12)); color: var(--主);
}
.格操作 { text-align: right; white-space: nowrap; }
.格操作 .删钮 { color: var(--败, #f56c6c); }
.提示行 { font-size: 12px; color: var(--字弱); text-align: center; padding: 4px 0 14px; }

/* ---- 编辑弹窗样式已随弹窗搬入「拆分分镜编辑弹窗.vue」 ---- */

@media (max-width: 1100px) {
  .行头 { display: none; }
  .镜行 { grid-template-columns: 76px 1fr 150px; grid-auto-rows: auto; row-gap: 6px; }
  .格镜中, .格时, .格态 { display: none; }
}
</style>
