<template>
  <div class="创作模块">
    <div class="剧集布局">
      <ep-rail
        当前="剧本编辑"
        :剧名="剧名" :剧id="剧id" :集="集号" :标题="集标题" />

      <div class="剧集主体">
        <!-- 面包屑 -->
        <div class="面包屑条">
          <span class="可点" @click="$router.push('/video')">视频生成</span>
          <span> / </span>
          <span class="可点" @click="$router.push({ path: '/video/episode', query: $route.query })">{{ 剧名 }} 第 {{ 集号 }} 集</span>
          <span> / </span>
          <span style="color:var(--字次)">剧本编辑</span>
        </div>

        <!-- 载入 / 报错门控 -->
        <div v-if="载入中" class="卡片 空场">
          <i class="el-icon-loading" style="font-size:40px;color:var(--字弱)"></i>
          <div class="空注">正在读取真库剧本…</div>
        </div>
        <div v-else-if="载入报错" class="卡片 空场">
          <div style="color:var(--警,#e6a23c)">{{ 载入报错 }}</div>
          <el-button size="small" style="margin-top:10px" @click="载入()">重试</el-button>
        </div>

        <template v-else>
        <!-- 页头 -->
        <div class="页头" style="margin-bottom:0">
          <div class="左">
            <h1 class="标题">剧本编辑</h1>
            <div class="副题">第 {{ 集号 }} 集{{ 集标题 ? ' · ' + 集标题 : '' }} · 已生成 {{ 已生成数 }}/{{ 本剧集.length }} 集 · 本集 {{ 当前场数 }} 场 {{ 当前字数 }} 字</div>
          </div>
          <div class="右">
            <el-button size="small" :loading="存库中" @click="保存()">保存</el-button>
            <el-button size="small" type="primary" @click="下一步()">下一步：资产清单<i class="el-icon-arrow-right"></i></el-button>
          </div>
        </div>

        <!-- ============ AI 生成条（真任务链路，生成完先预览再写入落库） ============ -->
        <div class="生成条">
          <div class="行间">
            <div class="行间">
              <div class="AI标">AI</div>
              <div>
                <div class="意见标题">生成第 {{ 集号 }} 集剧本</div>
                <div class="意见价">与分集剧本页同一套真库数据 · 生成完先看预览，点「写入」落库</div>
              </div>
            </div>
            <div style="flex:1"></div>
            <div class="意见例如">例：台词更口语、开场三拍更快…</div>
            <el-button size="mini" icon="el-icon-setting" @click="打开技能()">技能</el-button>
            <el-button size="mini" type="primary" plain :loading="扩写中" @click="生成本集()">
              AI 生成第 {{ 集号 }} 集
            </el-button>
          </div>
          <div class="意见快捷">
            <button
              v-for="句 in 快捷意见"
              :key="句"
              class="chip"
              :class="{ 选中: 扩写需求.indexOf(句) >= 0 }"
              @click="加意见(句)">{{ 句 }}</button>
          </div>
          <el-input
            v-model="扩写需求"
            type="textarea"
            :rows="2"
            class="意见输入"
            placeholder="写一句要求，AI 按这句话重写本集（不写就按本集剧情直接产出一版）"></el-input>
        </div>

        <!-- ============ 生成结果预览 ============ -->
        <div v-if="预览" class="卡片 预览卡">
          <div class="卡头">
            <span class="卡名">生成结果 · 第 {{ 集号 }} 集</span>
            <span class="卡注">解析完先给你看，点「写入」才落库覆盖</span>
            <div style="flex:1"></div>
            <el-button type="text" size="mini" @click="看原文 = !看原文">{{ 看原文 ? '收起原文' : '看原文' }}</el-button>
            <el-button type="text" size="mini" @click="丢弃预览()">丢弃</el-button>
          </div>

          <div class="预览格">
            <div class="预览项">
              <div class="预览键">正文</div>
              <div class="预览值">{{ 预览.场们.length }} 场 · {{ 预览字数 }} 字<span class="旧">（原 {{ 当前场数 }} 场 · {{ 当前字数 }} 字）</span></div>
            </div>
            <div class="预览项">
              <div class="预览键">状态</div>
              <div class="预览值">写入后标记为「待复核」</div>
            </div>
            <div class="预览项">
              <div class="预览键">解析提示</div>
              <div class="预览值">
                <span v-if="!预览.场们.length" class="缺">没认出「场次号 · 地点」开头的场次，正文会整段展示</span>
                <span v-else class="全">场次头认出来了，写入后可逐场编辑</span>
              </div>
            </div>
          </div>

          <pre v-if="看原文" class="原文">{{ 生成结果 }}</pre>

          <div class="行间 右" style="margin-top:12px">
            <el-button size="small" @click="丢弃预览()">取消</el-button>
            <el-button size="small" type="primary" :loading="存库中" @click="写入预览()">写入第 {{ 集号 }} 集</el-button>
          </div>
        </div>

        <!-- 生成原文兜底（没有预览时也能看上一版原文） -->
        <div v-if="生成结果 && !预览" class="卡片 结果卡">
          <div class="行间" style="margin-bottom:10px">
            <div class="结果标题">生成原文 · 第 {{ 集号 }} 集</div>
            <div style="flex:1"></div>
            <el-button type="text" size="mini" @click="重新解析()">重新解析</el-button>
            <el-button type="text" size="mini" @click="复制生成结果()">复制</el-button>
            <el-button type="text" size="mini" @click="生成结果 = ''">清空</el-button>
          </div>
          <pre class="原文">{{ 生成结果 }}</pre>
        </div>

        <!-- ============ 左：集数列表 / 右：本集剧本（真库） ============ -->
        <div class="集网格布局">
          <!-- ---------- 侧栏：搜索 + 筛选 + 列表 + 分页 ---------- -->
          <div class="卡片 集侧卡">
            <div class="侧题">
              <span class="侧名">集数列表</span>
              <span class="侧数">{{ 筛选后.length }}/{{ 本剧集.length }}</span>
            </div>

            <el-input
              v-model="搜索"
              size="small"
              class="搜框"
              prefix-icon="el-icon-search"
              placeholder="搜集号 / 标题"
              clearable></el-input>

            <div class="筛选">
              <button
                v-for="项 in 筛选项"
                :key="项.键"
                class="chip"
                :class="{ 选中: 状态筛 === 项.键 }"
                @click="切筛选(项.键)">{{ 项.名 }} {{ 项.数 }}</button>
            </div>

            <div class="集列">
              <div
                v-for="集 in 分页集"
                :key="'集' + 集.集"
                class="集项"
                :class="{ 当前: 集号 === 集.集 }"
                @click="切集(集.集)">
                <div class="集项头">
                  <span class="集号">第 {{ 集.集 }} 集</span>
                  <span class="集点" :class="集点类(集.集)"></span>
                  <div style="flex:1"></div>
                  <span class="集场">{{ 集场数(集.集) }} 场</span>
                </div>
                <div class="集名">{{ 集.标题 || '（未命名）' }}</div>
                <div class="集字">{{ 集状态(集.集) }} · {{ 集字数(集.集) }} 字</div>
              </div>

              <div v-if="!分页集.length" class="列空">
                没有匹配「{{ 搜索 }}」的集
              </div>
              <div v-if="!本剧集.length" class="列空">
                这部剧还没有分集与剧本，先去 分集剧本 页生成
              </div>
            </div>

            <page-bar
              v-if="总页数 > 1"
              style="margin-top:10px"
              紧凑
              单位="集"
              :总数="筛选后.length"
              :当前页="有效页"
              :每页="每页"
              @换页="换页"
              @换每页="换每页" />
          </div>

          <!-- ---------- 右侧：本集剧本 ---------- -->
          <div>
            <div class="本集导航">
              <el-button size="mini" :disabled="集号 <= 最小集" @click="切集(集号 - 1)">← 上一集</el-button>
              <span class="导航中">第 {{ 集号 }} / {{ 最大集 }} 集</span>
              <el-button size="mini" :disabled="集号 >= 最大集" @click="切集(集号 + 1)">下一集 →</el-button>
              <div style="flex:1"></div>
              <el-button size="mini" icon="el-icon-plus" @click="新增一场()">新增一场</el-button>
              <el-button size="mini" icon="el-icon-document" @click="打开全文()">全文</el-button>
            </div>

            <div v-if="当前剧 && 当前剧.场们 && 当前剧.场们.length" class="卡片 无内距">
              <div class="剧本头">
                <span class="剧本名">第 {{ 集号 }} 集正文</span>
                <span class="剧本注">{{ 当前剧.场们.length }} 场 · {{ 当前字数 }} 字 · {{ 当前剧.状态 }}</span>
                <div style="flex:1"></div>
                <span v-if="当前剧.更新时间" class="剧本注">库里更新于 {{ 当前剧.更新时间 }}</span>
              </div>

              <div class="场们列">
                <div v-for="(场, 序) in 当前剧.场们" :key="场.场 + 序" class="场块">
                  <div class="场头">
                    <span class="场号">{{ 场.场 }}</span>
                    <span class="场地">{{ 场.地点 }}</span>
                    <div style="flex:1"></div>
                    <el-button type="text" size="mini" @click="打开编辑场(场, 序)">编辑</el-button>
                  </div>
                  <div v-if="场.人物" class="场附">出场人物：{{ 场.人物 }}</div>
                  <div v-if="场.道具" class="场附">出场道具：{{ 场.道具 }}</div>
                  <div class="场文">
                    <p v-for="(行, 行序) in 场.正文" :key="行序" :class="{ 动作: 行.indexOf('△') === 0 }">{{ 行 }}</p>
                  </div>
                </div>
              </div>
            </div>

            <div v-else class="卡片 空场">
              <div class="空标题">第 {{ 集号 }} 集还没有剧本（真库里没有这一集）</div>
              <div class="空注">点上方「AI 生成第 {{ 集号 }} 集」先出一版预览，确认后写入落库。</div>
            </div>
          </div>
        </div>
        </template>
      </div>
    </div>

    <!-- ============ 场次编辑 / 新增弹窗 ============ -->
    <el-dialog
      :visible.sync="编辑显示"
      width="720px"
      top="6vh"
      custom-class="场次编辑弹窗"
      :show-close="false"
      :close-on-click-modal="false">
      <div class="弹窗头">
        <div>
          <div class="弹窗标题">{{ 新增模式 ? '新增一场' : '编辑 ' + 草稿.场 }}</div>
          <div class="弹窗副题">{{ 新增模式 ? '填完点「加入本集」，这一场会排到最后' : '改完点保存，直接写回真库这一场' }}</div>
        </div>
        <i class="el-icon-close 弹窗关闭" title="关闭" @click="编辑显示 = false"></i>
      </div>
      <div class="弹窗体">
        <el-form label-width="72px" size="small">
          <el-form-item label="场次号">
            <el-input v-model="草稿.场" maxlength="10" placeholder="例：1-1"></el-input>
          </el-form-item>
          <el-form-item label="地点">
            <el-input v-model="草稿.地点" maxlength="40" placeholder="例：内 · 高三教室 · 日"></el-input>
          </el-form-item>
          <el-form-item label="人物">
            <el-input v-model="草稿.人物" maxlength="80" placeholder="这一场出场的人，顿号分隔"></el-input>
          </el-form-item>
          <el-form-item label="道具">
            <el-input v-model="草稿.道具" maxlength="120" placeholder="这一场要用到的道具，顿号分隔"></el-input>
          </el-form-item>
          <el-form-item label="正文">
            <el-input
              v-model="草稿.正文"
              type="textarea"
              :rows="14"
              placeholder="一行一句。动作行以 △ 开头；台词写成「角色名（动作）：台词」"></el-input>
            <div class="字段注">一行一句，保存时按行拆开；动作行以 △ 开头，台词写「角色名（动作）：台词」</div>
          </el-form-item>
        </el-form>
      </div>
      <div class="弹窗底">
        <el-button v-if="!新增模式" type="text" class="删除钮" @click="删除这一场()">删除这一场</el-button>
        <div style="flex:1"></div>
        <el-button @click="编辑显示 = false">取消</el-button>
        <el-button type="primary" :loading="存库中" @click="保存这一场()">{{ 新增模式 ? '加入本集' : '保存' }}</el-button>
      </div>
    </el-dialog>

    <!-- ============ 全文弹窗 ============ -->
    <el-dialog
      :visible.sync="全文显示"
      width="820px"
      top="6vh"
      :show-close="false"
      :close-on-click-modal="false">
      <div class="弹窗头">
        <div>
          <div class="弹窗标题">第 {{ 集号 }} 集全文</div>
          <div class="弹窗副题">按场次排的完整正文，可直接整段复制走</div>
        </div>
        <i class="el-icon-close 弹窗关闭" title="关闭" @click="全文显示 = false"></i>
      </div>
      <div class="弹窗体">
        <pre class="原文 高">{{ 全文内容 }}</pre>
      </div>
      <div class="弹窗底">
        <div style="flex:1"></div>
        <el-button @click="全文显示 = false">关闭</el-button>
        <el-button type="primary" @click="复制全文()">复制全文</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import 剧集侧栏 from '@/共用/剧集侧栏/index.vue'
import 分页条 from '@/共用/分页条/index.vue'
import { 取, 发 } from '@/接口/请求'
import { 提交AI任务 } from '@/共用/AI任务'
import { 解析生成结果, 数字数, 拼正文, 拼全文 } from '@/共用/剧本档案'
import { 复制到剪贴板 } from '@/共用/复制文本'
import { 取配置类型, 读引导, 读技能id, 适配技能id } from '@/共用/技能生成配置'

const 快捷意见 = ['台词更口语', '开场三拍更快', '压到 3 场', '加强师生张力', '结尾卡在悬念上']

/* 本页默认技能引导提示词：与 /script/episode 同口径的正文格式（只要求正文块） */
const 默认引导文本 = [
  '· 只输出一个【正文】块，按场次排；每场以「场次号 · 内/外 · 地点 · 日/夜」开头',
  '· 场头下两行：「出场人物：」顿号分隔、「出场道具：」顿号分隔（没有就写 出场道具：无）',
  '· 正文一行一句：动作行以 △ 开头写清可拍动作；台词写成「角色名（语气/动作）：台词」',
  '· 台词口语化、贴人物性格；单集 800~5000 字；结尾卡在分集目录给的「尾钩」上',
  '· 除【正文】块以外不要输出任何解释、前言、后记'
].join('\n')

export default {
  name: 'EpScript',
  components: {
    'ep-rail': 剧集侧栏,
    'page-bar': 分页条
  },
  data() {
    return {
      载入中: true,
      载入报错: '',
      存库中: false,
      /* 真库剧本库：{ 集号: { 正文, 场们, 状态, 更新时间, 档案们:{能力档案,...} } } */
      剧本库: {},
      /* 真库分集（标题/梗概/目标/尾钩/中心句/出场，生成参考用） */
      分集们: [],
      /* 集列表侧栏：搜索 / 筛选 / 分页 */
      搜索: '',
      状态筛: '全部',
      当前页: 1,
      每页: 10,
      /* AI 生成 */
      技能列表: [],
      扩写技能id: '',
      技能引导: '',
      扩写需求: '',
      扩写中: false,
      生成结果: '',
      预览: null,
      看原文: false,
      快捷意见: 快捷意见,
      /* 场次编辑弹窗 */
      编辑显示: false,
      新增模式: false,
      编辑对象: null,
      编辑序: -1,
      草稿: { 场: '', 地点: '', 人物: '', 道具: '', 正文: '' },
      /* 全文弹窗 */
      全文显示: false
    }
  },
  computed: {
    剧名() {
      return this.$route.query.name || ''
    },
    剧id() {
      return parseInt(this.$route.query.ep) || 0
    },
    /* 当前集号：取 query.集；没传或库里没这集时回落到第一集 */
    集号() {
      const 号 = parseInt(this.$route.query.集) || 0
      if (号 && this.本剧集.some(function (x) { return x.集 === 号 })) return 号
      return this.最小集
    },
    /* 与 /script/episode 共用一套引导词/技能配置（用户指定直接用那页的） */
    页配置类型() {
      return 取配置类型('/script/episode')
    },
    默认引导() {
      return 默认引导文本
    },
    当前技能() {
      const id = String(this.扩写技能id)
      for (let i = 0; i < this.技能列表.length; i++) {
        if (String(this.技能列表[i].id) === id) return this.技能列表[i]
      }
      return null
    },
    /* 分集与剧本的并集：有目录按目录，没目录按已生成剧本 */
    本剧集() {
      const 页 = this
      const 集 = {}
      页.分集们.forEach(function (行) { 集[行.集号] = 行.标题 || '' })
      Object.keys(页.剧本库).forEach(function (号) {
        if (集[号] === undefined) 集[号] = ''
      })
      return Object.keys(集)
        .map(function (号) { return { 集: Number(号), 标题: 集[号] } })
        .sort(function (a, b) { return a.集 - b.集 })
    },
    集标题() {
      const 集 = this.本剧集.filter(function (x) { return x.集 === this.集号 }, this)[0]
      return 集 ? 集.标题 : ''
    },
    最小集() {
      return this.本剧集.length ? this.本剧集[0].集 : 1
    },
    最大集() {
      return this.本剧集.length ? this.本剧集[this.本剧集.length - 1].集 : 1
    },

    /* ---------- 列表 / 搜索 / 筛选 / 分页 ---------- */
    筛选项() {
      const 页 = this
      const 数 = function (键) {
        return 页.本剧集.filter(function (集) {
          return 页.集状态(集.集) === 键
        }).length
      }
      return [
        { 键: '全部', 名: '全部', 数: 数('全部') },
        { 键: '待复核', 名: '待复核', 数: 数('待复核') },
        { 键: '已复核', 名: '已复核', 数: 数('已复核') },
        { 键: '未生成', 名: '未生成', 数: 数('未生成') }
      ]
    },
    筛选后() {
      const 页 = this
      const 词 = this.搜索.trim()
      let 表 = this.本剧集
      if (this.状态筛 !== '全部') {
        表 = 表.filter(function (集) { return 页.集状态(集.集) === 页.状态筛 })
      }
      if (!词) return 表
      /* 纯数字按集号前缀匹配，其他按标题 */
      if (/^\d+$/.test(词)) {
        return 表.filter(function (集) { return String(集.集).indexOf(词) === 0 })
      }
      return 表.filter(function (集) {
        return String(集.标题 || '').indexOf(词) >= 0
      })
    },
    总页数() {
      const 页 = Math.ceil(this.筛选后.length / this.每页)
      return 页 > 0 ? 页 : 1
    },
    有效页() {
      const 页 = Number(this.当前页) || 1
      if (页 < 1) return 1
      if (页 > this.总页数) return this.总页数
      return 页
    },
    分页集() {
      const 起 = (this.有效页 - 1) * this.每页
      return this.筛选后.slice(起, 起 + this.每页)
    },

    /* ---------- 当前集剧本 ---------- */
    当前剧() {
      return this.剧本库[this.集号] || null
    },
    当前场数() {
      return this.当前剧 && this.当前剧.场们 ? this.当前剧.场们.length : 0
    },
    当前字数() {
      return this.当前剧 ? 数字数(this.当前剧.正文) : 0
    },
    预览字数() {
      return this.预览 ? 数字数(this.预览.正文) : 0
    },
    已生成数() {
      const 库 = this.剧本库
      return this.本剧集.filter(function (集) { return !!库[集.集] }).length
    },
    全文内容() {
      return 拼全文(this.当前剧)
    }
  },
  created() {
    this.载入()
    const 页 = this
    /* 与 /script/episode 共用的引导词/技能（按 页面×技能 存库） */
    读引导(this.页配置类型, this.扩写技能id).then(function (引导) { if (引导) 页.技能引导 = 引导 })
    const 技能 = 读技能id(this.页配置类型)
    if (技能) this.扩写技能id = 技能
  },
  watch: {
    /* 二级侧栏的上一集 / 下一集走的是同路由改 query，组件不会重建，得手动跟 */
    '$route.query.集'() {
      this.预览 = null
      this.看原文 = false
      this.滚到本集(this.集号)
    }
  },
  methods: {
    /* ---------------- 真库载入 / 保存 ---------------- */
    async 载入() {
      const 页 = this
      页.载入中 = true
      页.载入报错 = ''
      try {
        await 页.拉技能列表()
        const 数据 = await 取('/api/剧本/列表?剧id=' + 页.剧id)
        const 库 = {}
        ;((数据 && 数据.剧本们) || []).forEach(function (行) {
          库[行.集号] = {
            正文: 行.正文 || '',
            场们: 行.场次们 || [],
            状态: 行.状态 || '待复核',
            更新时间: (行.更新时间 || '').slice(0, 16).replace('T', ' '),
            档案们: {
              能力档案: 行.能力档案 || '', 世界状态: 行.世界状态 || '',
              关系网络: 行.关系网络 || '', 记忆回廊: 行.记忆回廊 || '',
              行动推荐: 行.行动推荐 || ''
            }
          }
        })
        页.剧本库 = 库
        try {
          const 分集数据 = await 取('/api/分集/列表?剧id=' + 页.剧id)
          页.分集们 = (分集数据 && 分集数据.分集们) || []
        } catch (e) { 页.分集们 = [] }
        页.滚到本集(页.集号)
      } catch (e) {
        页.载入报错 = '剧本读取失败：' + ((e && e.message) || e)
      }
      页.载入中 = false
    },
    async 拉技能列表() {
      try {
        const 数据 = await 取('/api/提示词/技能列表?分类=' + encodeURIComponent('剧本创作'))
        this.技能列表 = (数据 && 数据.列表) || []
        if (!this.扩写技能id && this.技能列表.length) {
          this.扩写技能id = 适配技能id(this.技能列表, this.页配置类型)
        }
      } catch (e) { /* 技能列表拉不到不阻塞页面 */ }
    },
    /* 全量落库：/api/剧本/保存 是「删除未传集」的全量替换语义，必须传全部集（保留各集档案块） */
    async 存全库() {
      const 页 = this
      const 集们 = 页.本剧集.map(function (集) {
        const 库行 = 页.剧本库[集.集]
        if (!库行) return null
        return {
          集号: 集.集,
          标题: 集.标题 || '',
          正文: 库行.正文 || '',
          能力档案: (库行.档案们 && 库行.档案们.能力档案) || '',
          世界状态: (库行.档案们 && 库行.档案们.世界状态) || '',
          关系网络: (库行.档案们 && 库行.档案们.关系网络) || '',
          记忆回廊: (库行.档案们 && 库行.档案们.记忆回廊) || '',
          行动推荐: (库行.档案们 && 库行.档案们.行动推荐) || '',
          状态: 库行.状态 || '待复核',
          场们: (库行.场们 || []).map(function (场) {
            return { 场: 场.场, 地点: 场.地点, 人物: 场.人物, 道具: 场.道具, 正文: 场.正文 }
          })
        }
      }).filter(Boolean)
      if (!集们.length) return
      await 发('/api/剧本/保存', { 剧id: 页.剧id, 集们: 集们 })
    },
    async 保存() {
      const 页 = this
      页.存库中 = true
      try {
        await 页.存全库()
        页.$message.success('全部剧本已落库')
      } catch (e) {
        页.$message.error('保存失败：' + ((e && e.message) || e))
      }
      页.存库中 = false
    },

    /* ---------------- AI 生成这一集（真任务链路） ---------------- */
    async 生成本集() {
      const 页 = this
      if (页.扩写中) return
      if (!页.扩写技能id) {
        页.$message.warning('请先点「技能」选择技能与引导提示词')
        页.打开技能()
        return
      }
      页.扩写中 = true
      try {
        /* 生成参考：本集分集目录信息 + 前一集正文尾段（滚动衔接） */
        const 目录行 = 页.分集们.filter(function (x) { return x.集号 === 页.集号 })[0] || {}
        const 前文 = 页.剧本库[页.集号 - 1]
        const 参考 = []
        参考.push('【本集信息】\n剧名：' + 页.剧名 + '\n第 ' + 页.集号 + ' 集' + (页.集标题 ? '《' + 页.集标题 + '》' : ''))
        if (目录行.梗概) 参考.push('本集梗概：' + 目录行.梗概)
        if (目录行.目标) 参考.push('本集目标：' + 目录行.目标)
        if (目录行.中心句) 参考.push('本集中心句：' + 目录行.中心句)
        if (目录行.尾钩) 参考.push('本集尾钩（结尾必须卡在这）：' + 目录行.尾钩)
        if (目录行.出场) 参考.push('本集出场人物：' + 目录行.出场)
        if (前文 && 前文.正文) {
          参考.push('【上一集结尾（接续写，不要重复）】\n' + 前文.正文.slice(-1000))
        }
        if (页.扩写需求.trim()) 参考.push('【用户要求】\n' + 页.扩写需求.trim())
        参考.push('【输出】只输出【正文】块：按场次排，每场以「场次号 · 内/外 · 地点 · 日/夜」开头，然后「出场人物：」「出场道具：」两行，正文一行一句（动作行以 △ 开头，台词写「角色名（语气）：台词」）。')

        const 规则 = 页.技能引导 || 页.默认引导
        const 文本 = String(await 提交AI任务({ 技能id: 页.扩写技能id, 系统: 规则, 正向: 参考.join('\n\n') }) || '').trim()
        if (!文本) {
          页.$message.warning('AI 没有返回内容，可稍后重试')
          return
        }
        页.生成结果 = 文本
        页.预览 = 解析生成结果(文本)
        页.看原文 = false
        页.$message.success('已生成第 ' + 页.集号 + ' 集，先看下面的解析结果')
      } catch (e) {
        页.$message.error('生成失败：' + ((e && e.message) || e))
      }
      页.扩写中 = false
    },
    打开技能() {
      this.$message.info('技能与引导词与「剧本创作 · 分集剧本」页共用同一套配置，在那页的技能弹窗里配置即可')
    },
    重新解析() {
      if (!this.生成结果) return
      this.预览 = 解析生成结果(this.生成结果)
    },
    丢弃预览() {
      this.预览 = null
      this.看原文 = false
    },
    async 写入预览() {
      const 页 = this
      if (!页.预览) return
      const 旧 = 页.剧本库[页.集号] || {}
      页.$set(页.剧本库, 页.集号, {
        正文: 页.预览.正文,
        场们: 页.预览.场们,
        状态: '待复核',
        更新时间: '',
        档案们: 旧.档案们 || { 能力档案: '', 世界状态: '', 关系网络: '', 记忆回廊: '', 行动推荐: '' }
      })
      页.存库中 = true
      try {
        await 页.存全库()
        页.预览 = null
        页.看原文 = false
        页.生成结果 = ''
        页.$message.success('已写入第 ' + 页.集号 + ' 集并落库，状态：待复核')
      } catch (e) {
        页.$message.error('落库失败：' + ((e && e.message) || e))
      }
      页.存库中 = false
    },
    加意见(句) {
      const 现 = this.扩写需求
      if (现.indexOf(句) >= 0) {
        this.扩写需求 = 现.replace(句, '').replace(/[，,]\s*[，,]/g, '，').replace(/^[，,\s]+|[，,\s]+$/g, '')
        return
      }
      this.扩写需求 = 现 ? 现.replace(/[，,\s]+$/, '') + '，' + 句 : 句
    },
    async 复制生成结果() {
      const 成功 = await 复制到剪贴板(this.生成结果)
      this.$message[成功 ? 'success' : 'error'](成功 ? '已复制到剪贴板' : '复制失败，请手动选择复制')
    },
    async 复制全文() {
      const 成功 = await 复制到剪贴板(this.全文内容)
      this.$message[成功 ? 'success' : 'error'](成功 ? '已复制全文' : '复制失败，请手动选择复制')
    },
    打开全文() {
      if (!this.当前剧 || !this.当前场数) {
        this.$message.warning('这一集还没有剧本')
        return
      }
      this.全文显示 = true
    },

    /* ---------------- 场次编辑 / 新增（即时落库） ---------------- */
    打开编辑场(场, 序) {
      if (!场) return
      this.新增模式 = false
      this.编辑对象 = 场
      this.编辑序 = 序
      this.草稿 = {
        场: 场.场,
        地点: 场.地点,
        人物: 场.人物,
        道具: 场.道具 || '',
        正文: (场.正文 || []).join('\n')
      }
      this.编辑显示 = true
    },
    新增一场() {
      if (!this.当前剧 || !this.当前剧.场们) {
        this.$message.warning('这一集还没有剧本，先让 AI 出一版再改')
        return
      }
      const 场们 = this.当前剧.场们 || []
      this.新增模式 = true
      this.编辑对象 = null
      this.编辑序 = -1
      this.草稿 = {
        场: '1-' + (场们.length + 1),
        地点: '内 · ',
        人物: '',
        道具: '',
        正文: ''
      }
      this.编辑显示 = true
    },
    async 保存这一场() {
      const 页 = this
      const 剧 = 页.当前剧
      if (!剧) return
      const 正文行 = String(页.草稿.正文 || '')
        .split(/\r?\n/)
        .map(function (s) { return s.trim() })
        .filter(function (s) { return s })
      const 条 = {
        场: (页.草稿.场 || '').trim(),
        地点: (页.草稿.地点 || '').trim(),
        人物: (页.草稿.人物 || '').trim(),
        道具: (页.草稿.道具 || '').trim(),
        正文: 正文行
      }
      if (!条.场) {
        页.$message.warning('先填场次号')
        return
      }
      const 场们 = (剧.场们 || []).slice()
      if (页.新增模式) {
        场们.push(条)
      } else {
        if (页.编辑序 < 0 || 页.编辑序 >= 场们.length) {
          页.编辑显示 = false
          return
        }
        场们[页.编辑序] = 条
      }
      页.$set(页.剧本库, 页.集号, Object.assign({}, 剧, {
        场们: 场们,
        正文: 拼正文(场们),
        状态: '待复核'
      }))
      页.存库中 = true
      try {
        await 页.存全库()
        页.编辑显示 = false
        页.$message.success(页.新增模式 ? '已加入第 ' + 页.集号 + ' 集（已落库）' : '已保存 ' + 条.场 + '（已落库）')
      } catch (e) {
        页.$message.error('落库失败：' + ((e && e.message) || e))
      }
      页.存库中 = false
    },
    删除这一场() {
      const 页 = this
      const 剧 = 页.当前剧
      const 序 = 页.编辑序
      if (!剧 || 序 < 0) return
      页.$confirm('确定删除 ' + 页.草稿.场 + '？', '删除这一场', {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async function () {
        const 场们 = (剧.场们 || []).slice()
        场们.splice(序, 1)
        页.$set(页.剧本库, 页.集号, Object.assign({}, 剧, {
          场们: 场们,
          正文: 拼正文(场们),
          状态: '待复核'
        }))
        页.存库中 = true
        try {
          await 页.存全库()
          页.编辑显示 = false
          页.$message.success('已删除 ' + 页.草稿.场 + '（已落库）')
        } catch (e) {
          页.$message.error('落库失败：' + ((e && e.message) || e))
        }
        页.存库中 = false
      }).catch(function () {})
    },

    /* ---------------- 列表交互 ---------------- */
    切集(号) {
      const 目标 = Number(号)
      if (!目标 || 目标 === this.集号) return
      const 目标集 = this.本剧集.filter(function (x) { return x.集 === 目标 })[0]
      if (!目标集) return
      this.$router.push({
        path: this.$route.path,
        query: Object.assign({}, this.$route.query, { 集: 目标集.集, 标题: 目标集.标题 })
      })
    },
    切筛选(键) {
      this.状态筛 = 键
      this.当前页 = 1
    },
    换页(页) {
      this.当前页 = 页
    },
    换每页(数) {
      const 首 = (this.有效页 - 1) * this.每页
      this.每页 = 数
      this.当前页 = Math.floor(首 / 数) + 1
    },
    /* 当前集不在当前页时，把它所在的页翻出来 */
    滚到本集(号) {
      const 页 = this
      const 位 = 页.筛选后.map(function (集) { return 集.集 }).indexOf(Number(号))
      if (位 < 0) {
        /* 被搜索或筛选挡住了：放开过滤，否则用户会以为切集失败 */
        页.搜索 = ''
        页.状态筛 = '全部'
        const 新位 = 页.本剧集.map(function (集) { return 集.集 }).indexOf(Number(号))
        页.当前页 = 新位 < 0 ? 1 : Math.floor(新位 / 页.每页) + 1
        return
      }
      页.当前页 = Math.floor(位 / 页.每页) + 1
    },
    集状态(集号) {
      const 剧 = this.剧本库[集号]
      return 剧 ? (剧.状态 || '待复核') : '未生成'
    },
    集点类(集号) {
      const 状态 = this.集状态(集号)
      if (状态 === '已复核') return '复核'
      if (状态 === '未生成') return '未'
      return '待'
    },
    集场数(集号) {
      const 剧 = this.剧本库[集号]
      return 剧 && 剧.场们 ? 剧.场们.length : 0
    },
    集字数(集号) {
      const 剧 = this.剧本库[集号]
      return 剧 ? 数字数(剧.正文) : 0
    },

    /* ---------------- 跳转 ---------------- */
    下一步() {
      this.$router.push({
        path: '/video/assets',
        query: Object.assign({}, this.$route.query)
      })
    }
  }
}
</script>

<style scoped>
/* ---- AI 生成条 ---- */
.生成条 {
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
.意见输入 { margin-top: 12px; }
.意见快捷 {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}
.chip {
  font-size: 12px;
  color: var(--字次);
  background: var(--卡片);
  border: 1px solid var(--描边);
  border-radius: 999px;
  padding: 3px 10px;
  cursor: pointer;
  transition: all .15s ease;
}
.chip:hover { border-color: var(--描边亮); color: var(--字); }
.chip.选中 { border-color: var(--主); color: var(--主); background: var(--主浅); }

/* ---- 预览卡 ---- */
.卡头 {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--描边);
}
.卡名 { font-size: 14px; font-weight: 600; color: var(--字); }
.卡注 { font-size: 12px; color: var(--字弱); }
.预览格 {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px 16px;
  padding: 12px 0;
}
.预览项 { display: flex; gap: 8px; font-size: 12px; line-height: 1.7; min-width: 0; }
.预览键 { flex: 0 0 56px; color: var(--字弱); }
.预览值 { flex: 1; min-width: 0; color: var(--字次); }
.预览值 .旧 { color: var(--字弱); margin-left: 6px; }
.预览值 .缺 { color: #f59e0b; margin-left: 6px; }
.预览值 .全 { color: var(--主); margin-left: 6px; }

/* ---- 生成原文 ---- */
.结果标题 { font-size: 14px; color: var(--字); font-weight: 600; }
.原文 {
  margin: 0;
  max-height: 320px;
  overflow: auto;
  padding: 12px;
  border-radius: 8px;
  background: var(--卡片二);
  font-family: inherit;
  font-size: 12px;
  line-height: 1.9;
  color: var(--字次);
  white-space: pre-wrap;
  word-break: break-word;
}
.原文.高 { max-height: 64vh; font-size: 13px; }

/* ---- 左集数列表 / 右本集剧本 ---- */
.集网格布局 {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 16px;
  align-items: start;
}
.集侧卡 { align-self: start; }
.侧题 {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.侧名 { font-size: 13px; font-weight: 600; color: var(--字); }
.侧数 { font-size: 11px; color: var(--字弱); }
.搜框 { margin-bottom: 10px; }
.筛选 {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}
.集列 { max-height: 560px; overflow-y: auto; padding-right: 2px; }
.集项 {
  padding: 9px 11px;
  border-radius: 8px;
  border: 1px solid var(--描边);
  margin-bottom: 8px;
  cursor: pointer;
  transition: all .15s ease;
}
.集项:hover { border-color: var(--描边亮); }
.集项.当前 { border-color: var(--主); background: var(--主浅); }
.集项头 { display: flex; align-items: center; gap: 6px; }
.集号 { font-size: 12px; color: var(--字弱); }
.集点 {
  width: 6px; height: 6px; border-radius: 999px;
  background: var(--描边亮);
}
.集点.待 { background: #f59e0b; }
.集点.复核 { background: var(--主); }
.集场 { font-size: 11px; color: var(--字弱); }
.集名 {
  font-size: 13px;
  color: var(--字);
  margin-top: 3px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.集字 { font-size: 11px; color: var(--字弱); margin-top: 2px; }
.列空 {
  padding: 24px 0;
  text-align: center;
  font-size: 12px;
  color: var(--字弱);
}

/* ---- 本集导航 + 剧本正文 ---- */
.本集导航 {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.导航中 { font-size: 12px; color: var(--字弱); }
.剧本头 {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 14px 16px;
  background: var(--卡片二);
  border-bottom: 1px solid var(--描边);
}
.剧本名 { font-size: 14px; font-weight: 600; color: var(--字); }
.剧本注 { font-size: 12px; color: var(--字弱); }
.场们列 { padding: 6px 16px 16px; }
.场块 {
  padding: 14px 0;
  border-bottom: 1px dashed var(--描边);
}
.场块:last-child { border-bottom: none; }
.场头 { display: flex; align-items: center; gap: 10px; }
.场号 { font-size: 13px; font-weight: 700; color: var(--主); }
.场地 { font-size: 13px; color: var(--字次); }
.场附 { margin-top: 4px; font-size: 12px; color: var(--字弱); }
.场文 { margin-top: 8px; }
.场文 p {
  margin: 0 0 6px;
  font-size: 13px;
  line-height: 1.9;
  color: var(--字次);
}
.场文 p.动作 { color: var(--字); }
.空场 {
  text-align: center;
  padding: 56px 0;
}
.空标题 { font-size: 14px; color: var(--字); font-weight: 600; }
.空注 { margin-top: 8px; font-size: 12px; color: var(--字弱); }

/* ---- 弹窗 ---- */
.弹窗头 {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding-bottom: 14px; border-bottom: 1px solid var(--描边);
}
.弹窗标题 { font-size: 16px; font-weight: 700; color: var(--字); }
.弹窗副题 { font-size: 12px; color: var(--字弱); margin-top: 4px; }
.弹窗关闭 { cursor: pointer; color: var(--字弱); font-size: 16px; }
.弹窗体 { padding: 16px 0 4px; max-height: 64vh; overflow-y: auto; }
.弹窗底 {
  display: flex; align-items: center; justify-content: flex-end; gap: 12px;
  padding-top: 14px; border-top: 1px solid var(--描边);
}
.删除钮 { color: #ef4444; }
.字段注 { margin-top: 6px; font-size: 12px; color: var(--字弱); line-height: 1.6; }

@media (max-width: 1200px) {
  .集网格布局 { grid-template-columns: 1fr; }
  .预览格 { grid-template-columns: minmax(0, 1fr); }
}
</style>
