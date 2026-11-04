<template>
  <div class="创作模块">
    <div class="剧集布局">
      <ep-rail
        当前="资产清单"
        :剧名="剧名" :剧id="剧id" :集="集号" :标题="集标题" />

      <div class="剧集主体">
        <!-- 面包屑 -->
        <div class="面包屑条">
          <span class="可点" @click="$router.push('/video')">视频生成</span>
          <span> / </span>
          <span class="可点" @click="$router.push({ path: '/video/episode', query: $route.query })">{{ 剧名 }} 第 {{ 集号 }} 集</span>
          <span> / </span>
          <span style="color:var(--字次)">资产清单</span>
        </div>

        <!-- 载入 / 报错门控 -->
        <div v-if="载入中" class="卡片 空态">
          <i class="el-icon-loading" style="font-size:40px;color:var(--字弱)"></i>
          <div style="margin-top:8px">正在读取本集资产…</div>
        </div>
        <div v-else-if="载入报错" class="卡片 空态">
          <i class="el-icon-warning-outline" style="font-size:40px;color:var(--警,#e6a23c)"></i>
          <div style="margin-top:8px">{{ 载入报错 }}</div>
          <el-button size="small" style="margin-top:10px" @click="载入()">重试</el-button>
        </div>

        <template v-else>
        <!-- 提取中进度 -->
        <div v-if="提取中" class="卡片 进度卡">
          <div class="进度行">
            <span class="做签">生成中</span>
            <span class="小标签">{{ 提取文案 }}</span>
            <div style="flex:1"></div>
            <div v-if="当前技能" class="技能行">
              <i class="el-icon-magic-stick" style="color:var(--主)"></i>
              <span class="技能名">{{ 当前技能.名称 }}</span>
            </div>
          </div>
          <div class="提取轨"><i :style="{ width: 提取率 + '%' }"></i></div>
        </div>

        <!-- 页头 -->
        <div class="页头" style="margin-bottom:0">
          <div class="左">
            <h1 class="标题">资产清单</h1>
            <div class="副题">从第 {{ 集号 }} 集剧本里提取的角色、场景、道具、服装，共 {{ 当前显示行们.length }} 项 · 每项可编辑、可按技能重新生成</div>
          </div>
          <div class="右" style="display:flex;align-items:center;gap:10px">
            <div v-if="当前技能 && !提取中" class="技能行">
              <i class="el-icon-magic-stick" style="color:var(--主)"></i>
              <span class="技能名">{{ 当前技能.名称 }}</span>
              <span class="技能说">{{ 当前技能.简介 }}</span>
            </div>
            <el-button size="small" icon="el-icon-magic-stick" @click="打开技能()">技能</el-button>
            <el-button
              size="small" type="primary" icon="el-icon-refresh"
              :loading="提取中" @click="全部重新提取()">全部重新提取</el-button>
          </div>
        </div>

        <!-- 分集进度 + 视图 + 筛选 -->
        <div class="卡片 进度卡">
          <div class="进度行">
            <div class="进度块">
              <div class="进度题">本集资产</div>
              <div class="进度值"><b>{{ 行们.length }}</b> 项</div>
            </div>
            <span class="小标签">第 {{ 集号 }} 集{{ 集标题 ? ' · ' + 集标题 : '' }}</span>
            <span class="小标签 灰">新增 {{ 新增数 }} · 引用 {{ 引用数 }}</span>
            <div style="flex:1"></div>
            <!-- 视图切换 -->
            <div class="视图切">
              <button
                v-for="视 in ['本集资产', '全剧资产']"
                :key="视"
                class="视图钮"
                :class="{ 选中: 视图 === 视 }"
                @click="切视图(视)">{{ 视 }}</button>
            </div>
          </div>

          <div class="筛选行">
            <button
              v-for="项 in 筛选项"
              :key="项.键"
              class="chip"
              :class="{ 选中: 类型筛选 === 项.键 }"
              @click="类型筛选 = 项.键">{{ 项.名 }} ({{ 项.数 }})</button>
          </div>
        </div>

        <!-- 分区表 -->
        <div v-for="区 in 显示区" :key="区.键" class="卡片 无内距 分区卡">
          <div class="区头">
            <span class="区名">{{ 区序(区) }}. {{ 区.标题 }}</span>
            <span class="区数">{{ 区.类型名 }} · {{ 区.行们.length }}</span>
            <span v-if="区.键 === '人物'" class="按集看">
              按集看
              <el-select v-model="卡看集" size="mini" style="width:96px">
                <el-option :value="0" label="全集（同人物设定页）"></el-option>
                <el-option v-for="n in 看集数" :key="'kj' + n" :value="n" :label="'第 ' + n + ' 集'"></el-option>
              </el-select>
            </span>
          </div>

          <!-- 人物分区：人物设定页同款档案卡（真库人物全字段，按本集取段） -->
          <div v-if="区.键 === '人物'" class="人物卡网">
            <div v-for="行 in 区.行们" :key="行.id" class="人物卡">
              <template v-if="人物匹配(行)">
                <div class="卡头">
                  <code>{{ 行.资产id }}</code>
                  <b class="卡名">{{ 人物匹配(行).名 }}</b>
                  <span class="卡签">{{ 人物匹配(行).性别 }}<template v-if="人物匹配(行).年龄档"> · {{ 人物匹配(行).年龄档 }}</template></span>
                  <span style="flex:1"></span>
                  <el-tag size="mini" :type="行.关系 === '新增' ? 'primary' : 'info'" effect="plain">{{ 行.关系 }}</el-tag>
                </div>
                <div v-for="组 in 字段分组" :key="组.名" class="卡组">
                  <div class="组名">{{ 组.名 }}</div>
                  <div v-for="段名 in 组.字段" :key="段名" class="组行">
                    <span class="组键">{{ 段名 }}</span>
                    <!-- 分段字段：同人物设定页，铺整条时间轴，按集看时高亮当前段 -->
                    <span v-if="卡段们(人物匹配(行), 段名).length" class="组值 分段">
                      <span v-for="(段, 序) in 卡段们(人物匹配(行), 段名)" :key="序" class="段行"
                            :class="{ 本集: 卡看集 > 0 && 段亮(段), 淡: 卡看集 > 0 && !段亮(段) }">
                        <span class="段标">{{ 集标(段) }}</span>
                        <span class="段文">{{ 段.值 || '—' }}</span>
                      </span>
                    </span>
                    <span v-else class="组值">{{ 卡静值(人物匹配(行), 段名) || '—' }}</span>
                  </div>
                </div>
                <div v-if="行.摘要" class="拍注">本集拍摄摘要（非档案）：{{ 行.摘要 }}</div>
                <div class="卡脚">
                  <template v-if="视图 === '本集资产'">
                    <el-button type="text" size="mini" @click="打开档案编辑(行)">编辑档案</el-button>
                    <el-button type="text" size="mini" :disabled="!!重写id" @click="重写一项(行)">AI重写摘要</el-button>
                    <el-button type="text" size="mini" class="删钮" @click="删一项(行)">删</el-button>
                  </template>
                  <el-button v-else type="text" size="mini" class="删钮" @click="删全剧(行)">全剧删除</el-button>
                </div>
              </template>
              <template v-else>
                <div class="卡头">
                  <code>{{ 行.资产id }}</code>
                  <b class="卡名">{{ 行.名称 }}</b>
                  <span style="flex:1"></span>
                  <el-tag size="mini" :type="行.关系 === '新增' ? 'primary' : 'info'" effect="plain">{{ 行.关系 }}</el-tag>
                </div>
                <div class="卡组">
                  <div class="组行"><span class="组键">级别</span><span class="组值">{{ 行.级别 || '—' }}</span></div>
                </div>
                <div class="空注 警注" style="padding:0 14px 6px;text-align:left">⚠ 未匹配到人物档案（{{ 行.资产id }}），请到 剧本创作-人物设定 建档后刷新本页</div>
                <div v-if="行.摘要" class="拍注">本集拍摄摘要（非档案）：{{ 行.摘要 }}</div>
                <div class="卡脚">
                  <template v-if="视图 === '本集资产'">
                    <el-button type="text" size="mini" :disabled="!!重写id" @click="重写一项(行)">AI重写摘要</el-button>
                    <el-button type="text" size="mini" class="删钮" @click="删一项(行)">删</el-button>
                  </template>
                  <el-button v-else type="text" size="mini" class="删钮" @click="删全剧(行)">全剧删除</el-button>
                </div>
              </template>
            </div>
          </div>

          <div v-else class="表">
            <div class="表头行">
              <span>资产 ID</span>
              <span>名称</span>
              <span>别名</span>
              <span>本集关系</span>
              <span>级别</span>
              <span>摘要</span>
              <span>操作</span>
            </div>

            <div v-for="行 in 区.行们" :key="行.id" class="表体">
              <div class="表行">
                <span class="格 格id"><code>{{ 行.资产id }}</code><span v-if="视图 === '全剧资产'" class="集签">E{{ 行.集号 }}</span></span>
                <span class="格 格名" :title="行.名称">{{ 行.名称 }}</span>
                <span class="格 格别名">
                  <template v-if="行.别名">{{ 行.别名 }}</template>
                  <template v-else>—</template>
                </span>
                <span class="格 格关系">
                  <el-tag size="mini" :type="行.关系 === '新增' ? 'primary' : 'info'" effect="plain">{{ 行.关系 }}</el-tag>
                </span>
                <span class="格 格级" :title="行.级别">{{ 行.级别 || '—' }}</span>
                <span class="格 格摘要">{{ 行.摘要 }}</span>
                <span class="格 格操作">
                  <template v-if="视图 === '本集资产'">
                    <el-button type="text" size="mini" @click="打开编辑(行)">编辑</el-button>
                    <el-button
                      type="text" size="mini"
                      :disabled="!!重写id" @click="重写一项(行)">AI重写</el-button>
                    <el-button
                      type="text" size="mini" class="删钮"
                      @click="删一项(行)">删</el-button>
                  </template>
                  <el-button v-else type="text" size="mini" class="删钮" @click="删全剧(行)">全剧删除</el-button>
                </span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="!显示区.length" class="卡片 空态">
          <template v-if="视图 === '本集资产' && !提取中">
            本集还没有资产
            <div style="margin-top:10px">
              <el-button size="small" type="primary" :disabled="!本集正文" @click="跑提取(false)">
                {{ 本集正文 ? '开始提取' : '本集还没有剧本，先去剧本编辑生成' }}
              </el-button>
            </div>
          </template>
          <template v-else-if="视图 !== '本集资产'">全剧还没有任何资产</template>
        </div>

        <!-- 编辑资产弹窗 -->
        <el-dialog title="编辑资产" :visible.sync="编辑弹窗显示" width="560px" append-to-body>
          <div v-if="编辑缓冲" class="编辑单">
            <label class="编项"><span class="编名">资产 ID</span><el-input :value="编辑缓冲.资产id" size="small" disabled /></label>
            <div class="编格">
              <label class="编项"><span class="编名">名称</span><el-input v-model="编辑缓冲.名称" size="small" /></label>
              <label class="编项"><span class="编名">级别</span><el-input v-model="编辑缓冲.级别" size="small" /></label>
            </div>
            <label class="编项"><span class="编名">别名（用 、 分隔）</span><el-input v-model="编辑缓冲.别名" size="small" /></label>
            <label class="编项"><span class="编名">本集关系</span>
              <el-radio-group v-model="编辑缓冲.关系" size="small">
                <el-radio label="新增">新增</el-radio>
                <el-radio label="引用">引用</el-radio>
              </el-radio-group>
            </label>
            <label class="编项"><span class="编名">摘要</span><el-input v-model="编辑缓冲.摘要" type="textarea" :rows="6" /></label>
          </div>
          <div slot="footer">
            <el-button size="small" @click="编辑弹窗显示 = false">取消</el-button>
            <el-button size="small" type="primary" :loading="存编辑中" @click="保存编辑()">保存</el-button>
          </div>
        </el-dialog>

        <!-- 编辑人物档案弹窗（不跳人物设定页，就地编辑真库人物） -->
        <el-dialog
          :title="'编辑人物档案：' + ((档案缓冲 && 档案缓冲.名) || '')"
          :visible.sync="档案弹窗显示" width="780px" top="6vh" append-to-body>
          <div v-if="档案缓冲" class="档案编辑">
            <div v-for="组 in 字段分组" :key="组.名" class="档组">
              <div class="档组名">{{ 组.名 }}</div>
              <div v-for="段名 in 组.字段" :key="段名" class="档行">
                <span class="档名">{{ 段名 }}</span>
                <!-- 会随剧情变的字段且已拆段：分段结构化编辑（同人物设定页：起/止集数 + 内容） -->
                <div v-if="是段字段(段名) && 档案段缓冲[档键(段名)]" class="段编辑列">
                  <div v-for="(段, 序) in 档案段缓冲[档键(段名)]" :key="序" class="段编辑行">
                    <span class="段编辑字">第</span>
                    <el-input-number v-model="段.起" :min="1" :max="看集数 || 99" :controls="false"
                                     size="mini" style="width:54px"></el-input-number>
                    <span class="段编辑字">–</span>
                    <el-input-number v-model="段.止" :min="1" :max="看集数 || 99" :controls="false"
                                     size="mini" style="width:54px"></el-input-number>
                    <span class="段编辑字">集</span>
                    <el-input v-model="段.值" type="textarea" :autosize="{ minRows: 1, maxRows: 3 }"
                              class="段编辑值"></el-input>
                    <i class="el-icon-close 段编辑删" title="删掉这一段" @click="删段(档键(段名), 序)"></i>
                  </div>
                  <div class="段编辑底">
                    <el-button type="text" size="mini" icon="el-icon-plus" @click="加段(档键(段名))">加一段</el-button>
                    <el-button type="text" size="mini" @click="并段(档键(段名))">合并成单值</el-button>
                  </div>
                </div>
                <!-- 单值模式 -->
                <template v-else>
                  <div class="档输入">
                    <el-input
                      v-if="档案短字段.indexOf(段名) >= 0"
                      v-model="档案缓冲[档键(段名)]" size="small" />
                    <el-input
                      v-else
                      v-model="档案缓冲[档键(段名)]" type="textarea"
                      :rows="段名 === '背景故事' || 段名 === '概括' ? 4 : 2" />
                    <el-button v-if="是段字段(段名)" type="text" size="mini" class="拆分钮"
                               @click="拆此段(段名)">按集拆分</el-button>
                  </div>
                </template>
              </div>
            </div>
            <div class="档提示">直接在文本框里改，保存后与 剧本创作-人物设定 同一份档案。只有某项会随剧情变化时（比如第5集换了身份/服装），才点该项的「按集拆分」，把它按集数拆成几段来写；写完想改回一句普通文本，点「合并成单值」。</div>
          </div>
          <div slot="footer">
            <el-button size="small" @click="档案弹窗显示 = false">取消</el-button>
            <el-button size="small" type="primary" :loading="存档案中" @click="保存档案()">保存</el-button>
          </div>
        </el-dialog>

        <!-- 底部导航 -->
        <div class="行间 右">
          <el-button @click="上一步()">上一步：剧本编辑</el-button>
          <el-button type="primary" @click="下一步()">下一步：美术资产<i class="el-icon-arrow-right"></i></el-button>
        </div>

        <!-- 技能生成弹窗：技能 + 技能引导提示词 + 引入数据（真库剧本/人物/既有资产 + 提取要求）。
             in-DOM 模板只认 ASCII 标签名，必须用 skill-dialog 别名；事件处理器必须带括号。 -->
        <skill-dialog
          :显示.sync="技能弹窗显示"
          :技能列表="技能列表"
          :技能id.sync="扩写技能id"
          :引导.sync="技能引导"
          :默认引导="默认引导"
          :配置类型="页配置类型"
          目标名="资产提取"
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
import { 取, 发 } from '@/接口/请求'
import { 提交AI任务 } from '@/共用/AI任务'
import { 取配置类型, 读引导, 读技能id, 读引入, 存引入, 适配技能id } from '@/共用/技能生成配置'
import { 字段分组, 值文本, 文本转值, 可分段字段, 集标签, 分段文本, 拆分段 } from '@/共用/人物工具'

/* 人物卡字段名 → 人物表列名（其余字段同名；关系=随剧情的关系变化，口径同人物设定页） */
const 卡字段映射 = { 姓名: '名', 年龄: '年龄档', 关系: '关系变化' }

/* 档案弹窗里单行输入的字段，其余用多行文本框 */
const 档案短字段 = ['姓名', '性别', '年龄', '身材', '当前姿势', '台词风格', '口头禅']

const 区定义 = [
  { 键: '人物', 类型名: '人物', 标题: '角色资产清单' },
  { 键: '场景', 类型名: '场景', 标题: '场景资产清单' },
  { 键: '道具', 类型名: '道具', 标题: '道具/物件资产清单' },
  { 键: '服装', 类型名: '服装', 标题: '服装/妆造状态资产清单' }
]

/* 本页默认技能引导提示词：提取规则 + 输出格式 */
const 默认引导文本 = [
  '· 基于引入的本集剧本提取可拍资产，逐项输出，一行一项，字段用「｜」分隔：资产ID｜类型｜名称｜别名｜关系｜级别｜摘要',
  '· 类型只能是 人物/场景/道具/服装；场景/道具/服装 资产ID 用 SCN_/PROP_/COST_ 前缀按类型顺序编号',
  '· 人物资产ID 必须沿用人物设定里的人物id（CHAR_xxx），名称用人物本名；人物摘要基于该人物档案里本集的外貌/穿搭/当前状态，写满可直接拍摄的细节（五官/发型/体型/服装/随身物/姿态）',
  '· 场景与道具摘要写可拍物件与状态',
  '· 与引入的既有资产对照判定「新增/引用」，引用项沿用既有资产ID与名称',
  '· 别名没有就写 —；除资产行以外不要输出任何解释、前言、后记'
].join('\n')

export default {
  name: 'AssetList',
  components: { 'ep-rail': 剧集侧栏, 'skill-dialog': 技能生成弹窗 },
  data() {
    return {
      /* 读库状态 */
      载入中: true,
      载入报错: '',
      /* 真库数据 */
      行们: [],
      全剧行们: [],
      本集正文: '',
      场次们: [],
      人物们: [],
      人物文本: '',
      /* 视图与筛选 */
      类型筛选: '全部',
      视图: '本集资产',
      /* 提取 */
      提取中: false,
      提取率: 0,
      提取文案: '',
      提取计时器: null,
      /* 单项重写 */
      重写id: null,
      /* 行编辑 */
      编辑弹窗显示: false,
      编辑缓冲: null,
      存编辑中: false,
      /* 人物档案弹窗编辑 */
      档案弹窗显示: false,
      档案缓冲: null,
      档案源序: -1,
      档案段缓冲: {},
      卡看集: 0,
      剧本总集: 0,
      存档案中: false,
      档案短字段: 档案短字段,
      /* 技能生成（与拆分分镜/单镜生成页同一套） */
      技能弹窗显示: false,
      技能列表: [],
      扩写技能id: '',
      技能引导: '',
      引入勾选: [],
      提取要求: '1. 只提取与剧情可拍相关的资产\n2. 人物摘要写满可拍外观与服装细节，场景/道具写可拍物件与状态\n3. 与既有资产对照判定「新增/引用」并沿用其资产ID'
    }
  },
  computed: {
    剧名() { return this.$route.query.name || '' },
    剧id() { return parseInt(this.$route.query.ep) || 0 },
    集号() { return parseInt(this.$route.query.集) || 1 },
    集标题() { return this.$route.query.标题 || '' },
    总集() { return parseInt(this.$route.query.集数) || 0 },
    /* 总集数兜底：地址栏没带 集数 时用剧本们最大集号（分段解析/集标签都按它钳制） */
    看集数() { return this.总集 || this.剧本总集 || 0 },
    页配置类型() { return 取配置类型('/video/assets') },
    默认引导() { return 默认引导文本 },
    当前技能() {
      const id = String(this.扩写技能id)
      for (let i = 0; i < this.技能列表.length; i++) {
        if (String(this.技能列表[i].id) === id) return this.技能列表[i]
      }
      return null
    },
    /* 引入数据 = 真库本集剧本 + 场次 + 人物 + 既有资产 + 可编辑的提取要求 */
    引入数据() {
      const 页 = this
      const 本集剧本 = 页.本集正文
        ? ('第 ' + 页.集号 + ' 集' + (页.集标题 ? ' · ' + 页.集标题 : '') + '\n' + 页.本集正文)
        : '（本集还没有剧本）'
      const 场次文本 = 页.场次们.length
        ? 页.场次们.map(function (场) { return (场.场 || '') + ' · ' + (场.地点 || '') + (场.人物 ? ' · 人物：' + 场.人物 : '') + (场.道具 ? ' · 道具：' + 场.道具 : '') }).join('\n')
        : ''
      return [
        { 键: '剧本', 名: '本集剧本（真库）', 值: 本集剧本, 提示: '提取资产的原始依据' },
        { 键: '场次', 名: '本集场次表', 值: 场次文本 || '（无场次数据）', 提示: '场景与道具识别用' },
        { 键: '人物', 名: '人物设定（真库）', 值: 页.人物文本 || '（暂无人物数据）', 提示: '角色资产与既有设定对齐用' },
        { 键: '既有资产', 名: '全剧既有资产（真库）', 值: 页.既有资产文本() || '（暂无，全部按新增提取）', 提示: '判定 新增/引用 与连续性用' },
        { 键: '要求', 名: '提取要求（可编辑）', 值: 页.提取要求, 可编辑: true, 占位: '例：人物摘要写满可拍外观细节…' }
      ].map(function (项) {
        return Object.assign({}, 项, { 勾选: 页.引入勾选.indexOf(项.键) !== -1 })
      })
    },
    新增数() { return this.行们.filter(function (x) { return x.关系 === '新增' }).length },
    引用数() { return this.行们.length - this.新增数 },
    当前显示行们() { return this.视图 === '本集资产' ? this.行们 : this.全剧行们 },
    筛选项() {
      const 页 = this
      const 数 = function (键) {
        return 键 === '全部' ? 页.当前显示行们.length : 页.当前显示行们.filter(function (x) { return x.类型 === 键 }).length
      }
      return [{ 键: '全部', 名: '全部' }].concat(区定义.map(function (区) {
        return { 键: 区.键, 名: 区.类型名 }
      })).map(function (项) {
        return { 键: 项.键, 名: 项.名, 数: 数(项.键) }
      })
    },
    区们() {
      const 页 = this
      return 区定义.map(function (区) {
        return Object.assign({}, 区, {
          行们: 页.当前显示行们.filter(function (行) { return 行.类型 === 区.键 })
        })
      }).filter(function (区) { return 区.行们.length })
    },
    /* 按筛选 chip 决定显示哪些分区 */
    显示区() {
      if (this.类型筛选 === '全部') return this.区们
      return this.区们.filter(function (区) { return 区.键 === this.类型筛选 }, this)
    }
  },
  created() {
    this.载入()
    const 页 = this
    /* 技能配置带出（按 页面×技能） */
    读引导(this.页配置类型, this.扩写技能id).then(function (引导) { if (引导) 页.技能引导 = 引导 })
    const 技能 = 读技能id(this.页配置类型)
    if (技能) this.扩写技能id = 技能
    const 已存勾 = 读引入(this.页配置类型)
    this.引入勾选 = 已存勾 || ['剧本', '场次', '人物', '既有资产', '要求']
    try {
      const 存要求 = localStorage.getItem('技能生成:提取要求:' + this.剧名)
      if (存要求) this.提取要求 = 存要求
    } catch (e) { /* 忽略 */ }
  },
  beforeDestroy() {
    if (this.提取计时器) clearInterval(this.提取计时器)
  },
  methods: {
    /* ---------------- 读库 ---------------- */
    async 载入() {
      const 页 = this
      页.载入中 = true
      页.载入报错 = ''
      try {
        await 页.拉技能列表()
        const 数据 = await 取('/api/资产/列表?剧id=' + 页.剧id + '&集号=' + 页.集号)
        页.行们 = (数据 && 数据.资产们) || []
        /* 本集剧本（提取依据） */
        try {
          const 剧本数据 = await 取('/api/剧本/列表?剧id=' + 页.剧id)
          const 剧本们 = (剧本数据 && 剧本数据.剧本们) || []
          页.剧本总集 = 剧本们.reduce(function (m, x) { return Math.max(m, x.集号 || 0) }, 0)
          const 行 = 剧本们.filter(function (x) { return x.集号 === 页.集号 })[0]
          if (行) {
            页.本集正文 = 行.正文 || ''
            页.场次们 = 行.场次们 || []
          }
        } catch (e) { /* 剧本没生成不阻塞资产页 */ }
        /* 人物（真库人物设定全量，人物分区档案卡 + 提取对齐用） */
        try {
          const 人物数据 = await 取('/api/人物/列表?剧id=' + 页.剧id)
          页.人物们 = (人物数据.人物们 || [])
          页.重建人物文本()
        } catch (e) { 页.人物们 = []; 页.人物文本 = '' }
        /* 首次进入且本集已有剧本：自动提取（生成完直接落库） */
        if (!页.行们.length && 页.本集正文 && !页.提取中) {
          页.跑提取(false)
        }
      } catch (e) {
        页.载入报错 = '资产读取失败：' + ((e && e.message) || e)
      }
      页.载入中 = false
    },
    既有资产文本() {
      return this.全剧行们.map(function (项) {
        return [项.资产id || '', 'E' + 项.集号, 项.类型 || '', 项.名称 || '', 项.级别 || '', 项.摘要 || ''].join('｜')
      }).join('\n')
    },
    /* ---------------- 人物档案卡（人物设定页同格式） ---------------- */
    /* 资产行 → 真库人物：先按 资产id==人物id 对，再按名称兜底 */
    人物匹配(行) {
      const 页 = this
      const 列 = 页.人物们
      for (let i = 0; i < 列.length; i++) {
        if (列[i].人物id && 列[i].人物id === 行.资产id) return 列[i]
      }
      for (let i = 0; i < 列.length; i++) {
        if ((列[i].名 || '') === (行.名称 || '')) return 列[i]
      }
      return null
    },
    /* 人物卡字段值：静态字段原样；随剧情分段字段（库里的「第1-5集：…；第6集起：…」文本）取本集那一段 */
    卡值(人, 字段名) {
      if (!人) return ''
      const 键 = 卡字段映射[字段名] || 字段名
      return 值文本(文本转值(人[键], this.看集数), this.看集数, this.集号) || ''
    },
    /* ---------------- 人物档案卡（与人物设定页同口径：全集时间轴 + 按集看） ---------------- */
    卡键(字段名) { return 卡字段映射[字段名] || 字段名 },
    是段字段(字段名) { return 可分段字段.indexOf(字段名) >= 0 },
    /* 分段字段：解析出段数组（无分段语法返回 []） */
    卡段们(人, 字段名) {
      if (!人 || !this.是段字段(字段名)) return []
      const 值 = 文本转值(人[this.卡键(字段名)], this.看集数)
      return Array.isArray(值) ? 值 : []
    },
    /* 静态值 / 无分段语法时的单值 */
    卡静值(人, 字段名) {
      if (!人) return ''
      const 键 = this.卡键(字段名)
      if (!this.是段字段(字段名)) return 人[键] || ''
      const 值 = 文本转值(人[键], this.看集数)
      return Array.isArray(值) ? '' : (值 || '')
    },
    /* 「按集看」选中集是否落在这段里 */
    段亮(段) {
      const 集 = this.卡看集
      return 集 > 0 && 集 >= 段.起 && 集 <= 段.止
    },
    集标(段) { return 集标签(段.起, 段.止, this.看集数) },
    /* 人物档案铺成文本（AI 重写人物摘要时作上下文） */
    人物卡文本(人) {
      const 页 = this
      const 行们 = []
      for (let i = 0; i < 字段分组.length; i++) {
        const 组 = 字段分组[i]
        for (let j = 0; j < 组.字段.length; j++) {
          const 名 = 组.字段[j]
          const 值 = 页.卡值(人, 名)
          if (值) 行们.push(名 + '：' + 值)
        }
      }
      return 行们.join('\n')
    },
    /* 人物档案弹窗：字段名 → 编辑缓冲里的键（人物表列名） */
    档键(段名) {
      return 卡字段映射[段名] || 段名
    },
    /* 人物卡「编辑档案」→ 就地弹窗编辑真库人物（不再跳人物设定页） */
    打开档案编辑(行) {
      const 人 = this.人物匹配(行)
      if (!人) {
        this.$message.warning('未匹配到人物设定档案，请先在剧本创作-人物设定里建档')
        return
      }
      if (!this.人物们.length) {
        this.$message.warning('人物数据未加载完成，请稍后重试')
        return
      }
      /* 浅拷贝做缓冲，取消不污染库内对象，保存时按索引写回 */
      const 页 = this
      let 源序 = -1
      for (let i = 0; i < 页.人物们.length; i++) {
        if (页.人物们[i] === 人) { 源序 = i; break }
      }
      if (源序 < 0) {
        页.$message.error('未在人物列表中定位到该人物')
        return
      }
      页.档案源序 = 源序
      页.档案缓冲 = Object.assign({}, 人)
      /* 分段字段默认按纯文本编辑（原文原样可见可改），点「按集拆分」才进入分段模式 */
      页.档案段缓冲 = {}
      字段分组.forEach(function (组) {
        组.字段.forEach(function (段名) {
          if (页.是段字段(段名)) 页.档案段缓冲[页.档键(段名)] = null
        })
      })
      页.档案弹窗显示 = true
    },
    /* 段编辑：单值 → 拆段（原文里已经是「第1-5集：…；第6集起：…」就按原样拆开，否则包成 1..总集 一段） */
    拆此段(段名) {
      const 页 = this
      const 键 = 页.档键(段名)
      const 解析 = 文本转值(页.档案缓冲[键] || '', 页.看集数)
      页.$set(页.档案段缓冲, 键, Array.isArray(解析)
        ? 解析.map(function (段) { return Object.assign({}, 段) })
        : 拆分段(页.档案缓冲[键] || '', 页.看集数))
    },
    加段(键) {
      const 段们 = this.档案段缓冲[键] || []
      const 尾 = 段们.length ? 段们[段们.length - 1].止 : (this.看集数 || 1)
      段们.push({ 起: 尾, 止: this.看集数 || 尾, 值: '', 类型: '', 说明: '' })
    },
    删段(键, 序) {
      const 段们 = this.档案段缓冲[键] || []
      段们.splice(序, 1)
      if (!段们.length) this.档案段缓冲[键] = null
    },
    /* 合并成单值：取最后一段（口径同人物设定页「合并」） */
    并段(键) {
      const 段们 = this.档案段缓冲[键] || []
      this.档案缓冲[键] = 段们.length ? (段们[段们.length - 1].值 || '') : ''
      this.档案段缓冲[键] = null
    },
    async 保存档案() {
      const 页 = this
      const 缓冲 = 页.档案缓冲
      if (!缓冲) return
      if (!String(缓冲.名 || '').trim()) {
        页.$message.error('姓名不能为空')
        return
      }
      if (!页.人物们.length || !(页.档案源序 >= 0 && 页.档案源序 < 页.人物们.length)) {
        页.$message.error('人物数据未加载，无法保存')
        return
      }
      页.存档案中 = true
      try {
        /* 分段字段序列化回「第1-5集：…；第6集起：…」文本（与人物设定页 存库 口径一致） */
        for (const 键 in 页.档案段缓冲) {
          const 段们 = 页.档案段缓冲[键]
          if (Array.isArray(段们) && 段们.length) 缓冲[键] = 分段文本(段们, 页.看集数)
        }
        /* 写回库内对象，全量落库（后端事务内全量替换，必须传全部人物） */
        Object.assign(页.人物们[页.档案源序], 缓冲)
        await 发('/api/人物/保存', { 剧id: 页.剧id, 人物们: 页.人物们 })
        页.重建人物文本()
        页.$message.success('人物档案已保存')
        页.档案弹窗显示 = false
      } catch (e) {
        页.$message.error('档案保存失败：' + ((e && e.message) || e))
      }
      页.存档案中 = false
    },
    /* 人物设定文本重建（载入与档案保存后共用） */
    重建人物文本() {
      const 页 = this
      页.人物文本 = 页.人物们.map(function (人) {
        return [人.人物id || '', 人.名 || '', 人.性别 || '', 人.年龄档 || '', 人.性格 || '',
          页.卡值(人, '身份'), 页.卡值(人, '态度'), 页.卡值(人, '外貌'), 页.卡值(人, '穿搭'),
          页.卡值(人, '当前状态'), 页.卡值(人, '技能'), 人.口头禅 || ''].join('｜')
      }).join('\n')
    },
    /* ---------------- 技能配置（与拆分分镜/单镜生成页同一套） ---------------- */
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
        if (引入[i].键 === '要求') {
          this.提取要求 = 引入[i].值 || ''
          try { localStorage.setItem('技能生成:提取要求:' + this.剧名, this.提取要求) } catch (e) { /* 忽略 */ }
        }
        if (引入[i].勾选) 勾.push(引入[i].键)
      }
      this.引入勾选 = 勾
      存引入(类型, 勾)
      if (值 && 值.引导) this.技能引导 = 值.引导
    },
    /* ---------------- 视图 ---------------- */
    async 切视图(视) {
      this.视图 = 视
      if (视 === '全剧资产' && !this.全剧行们.length) {
        try {
          const 数据 = await 取('/api/资产/列表?剧id=' + this.剧id)
          this.全剧行们 = (数据 && 数据.资产们) || []
        } catch (e) {
          this.$message.error('全剧资产读取失败：' + ((e && e.message) || e))
        }
      }
    },
    /* ---------------- 提取（真 AI 任务，完成即落库） ---------------- */
    组需求(单行要求) {
      const 页 = this
      const 段们 = []
      for (let i = 0; i < 页.引入数据.length; i++) {
        const 项 = 页.引入数据[i]
        if (!项.勾选 || 项.键 === '要求') continue
        段们.push('【' + 项.名 + '】\n' + (项.值 || ''))
      }
      段们.push('【提取要求】\n' + 页.提取要求)
      段们.push(单行要求 || '【输出】只输出资产行，一行一项，格式：资产ID｜类型｜名称｜别名｜关系｜级别｜摘要')
      return 段们.join('\n\n')
    },
    async 跑提取(是重提) {
      const 页 = this
      if (页.提取中) return
      if (!页.扩写技能id) {
        页.$message.warning('请先点「技能」选择技能与引导提示词')
        页.打开技能()
        return
      }
      if (!页.本集正文) {
        页.$message.warning('本集还没有剧本，先去 剧本编辑 生成正文')
        return
      }
      /* 重提前先把全剧既有资产拉齐（判定 新增/引用 用） */
      try {
        const 全数据 = await 取('/api/资产/列表?剧id=' + 页.剧id)
        页.全剧行们 = (全数据 && 全数据.资产们) || []
      } catch (e) { /* 拉不到就按无既有资产处理 */ }
      页.提取中 = true
      页.提取率 = 0
      页.提取文案 = '正在从本集剧本提取可拍资产…'
      if (页.提取计时器) clearInterval(页.提取计时器)
      页.提取计时器 = setInterval(function () {
        页.提取率 = Math.min(95, 页.提取率 + 15)
        页.提取文案 = 页.提取率 > 60 ? '正在解析资产明细并落库…' : '正在通读本集剧本与既有资产…'
      }, 15000)
      try {
        const 规则 = 页.技能引导 || 页.默认引导
        const 文本 = String(await 提交AI任务({ 技能id: 页.扩写技能id, 系统: 规则, 正向: 页.组需求() }) || '').trim()
        if (!文本) throw new Error('AI 没有返回内容')
        const 项们 = 页.解析资产(文本)
        if (!项们.length) throw new Error('AI 返回里没有可识别的资产行')
        await 发('/api/资产/保存', { 剧id: 页.剧id, 集号: 页.集号, 项们: 项们 })
        const 数据 = await 取('/api/资产/列表?剧id=' + 页.剧id + '&集号=' + 页.集号)
        页.行们 = (数据 && 数据.资产们) || []
        页.$message.success('提取完成并已落库：' + 页.行们.length + ' 项')
      } catch (e) {
        页.$message.error('提取失败：' + ((e && e.message) || e))
      }
      if (页.提取计时器) { clearInterval(页.提取计时器); 页.提取计时器 = null }
      页.提取中 = false
      页.提取率 = 0
    },
    全部重新提取() {
      const 页 = this
      if (!页.行们.length) { 页.跑提取(true); return }
      页.$confirm('重新提取会覆盖当前本集 ' + 页.行们.length + ' 项资产（重写落库），确定？', '重新提取', {
        confirmButtonText: '重新提取', cancelButtonText: '取消', type: 'warning'
      }).then(function () { 页.跑提取(true) }).catch(function () {})
    },
    /* 解析 AI 输出：资产ID｜类型｜名称｜别名｜关系｜级别｜摘要 */
    解析资产(文本) {
      const 行们 = String(文本).split('\n')
      const 出 = []
      for (let i = 0; i < 行们.length; i++) {
        const 行 = 行们[i].trim()
        if (!行 || 行.indexOf('｜') < 0) continue
        const 段 = 行.split('｜').map(function (s) { return s.trim() })
        if (段.length < 4) continue
        const 类型 = ['人物', '场景', '道具', '服装'].indexOf(段[1]) >= 0 ? 段[1] : '道具'
        const 名称 = 段[2] || ''
        const 摘要 = 段.slice(6).join('｜') || 段[5] || ''
        if (!名称 || !摘要) continue
        出.push({
          资产id: 段[0] || '',
          类型: 类型,
          名称: 名称,
          别名: (段[3] && 段[3] !== '—') ? 段[3] : '',
          关系: 段[4] === '引用' ? '引用' : '新增',
          级别: 段[5] || '',
          摘要: 摘要
        })
      }
      /* 资产id 缺失或重复时按类型前缀重编 */
      const 计数 = { CHAR: 0, SCN: 0, PROP: 0, COST: 0 }
      const 前缀表 = { 人物: 'CHAR', 场景: 'SCN', 道具: 'PROP', 服装: 'COST' }
      const 见过 = {}
      for (let i = 0; i < 出.length; i++) {
        const 项 = 出[i]
        if (!项.资产id || 见过[项.资产id]) {
          计数[前缀表[项.类型]]++
          项.资产id = 前缀表[项.类型] + '_' + String(计数[前缀表[项.类型]]).padStart(3, '0')
        }
        见过[项.资产id] = 1
      }
      return 出
    },
    /* ---------------- 行编辑（即时落库） ---------------- */
    async 存本集(列表) {
      const 页 = this
      const 项们 = (列表 || 页.行们).map(function (行) {
        return {
          资产id: 行.资产id, 类型: 行.类型, 名称: 行.名称, 别名: 行.别名 || '',
          关系: 行.关系, 级别: 行.级别 || '', 摘要: 行.摘要
        }
      })
      await 发('/api/资产/保存', { 剧id: 页.剧id, 集号: 页.集号, 项们: 项们 })
    },
    打开编辑(行) {
      this.编辑缓冲 = {
        资产id: 行.资产id, 名称: 行.名称, 级别: 行.级别 || '',
        别名: 行.别名 || '', 关系: 行.关系, 摘要: 行.摘要
      }
      this.编辑弹窗显示 = true
    },
    async 保存编辑() {
      const 页 = this
      const 缓 = 页.编辑缓冲
      if (!缓 || !缓.名称.trim()) {
        页.$message.warning('名称不能为空')
        return
      }
      页.存编辑中 = true
      try {
        const 新列表 = 页.行们.map(function (行) {
          if (行.资产id !== 缓.资产id) return 行
          return Object.assign({}, 行, {
            名称: 缓.名称, 级别: 缓.级别, 别名: 缓.别名, 关系: 缓.关系, 摘要: 缓.摘要
          })
        })
        await 页.存本集(新列表)
        页.行们 = 新列表
        页.编辑弹窗显示 = false
        页.$message.success('已保存 ' + 缓.资产id + '（已落库）')
      } catch (e) {
        页.$message.error('保存失败：' + ((e && e.message) || e))
      }
      页.存编辑中 = false
    },
    async 删一项(行) {
      const 页 = this
      try {
        await 页.$confirm('删除资产 ' + 行.资产id + ' ' + 行.名称 + '（落库删除），确定？', '删除资产', {
          confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning'
        })
      } catch (e) { return }
      const 新列表 = 页.行们.filter(function (项) { return 项.资产id !== 行.资产id })
      try {
        await 页.存本集(新列表)
        页.行们 = 新列表
        页.$message.success('已删除 ' + 行.资产id)
      } catch (e) {
        页.$message.error('删除失败：' + ((e && e.message) || e))
      }
    },
    /* 全剧视图删除：该资产 id 出现在几个集，就逐集全量替换落库删干净（保存接口是按集全量替换语义） */
    async 删全剧(行) {
      const 页 = this
      const 受影响 = {}
      页.全剧行们.forEach(function (项) {
        if (项.资产id === 行.资产id) 受影响[项.集号] = true
      })
      const 集们 = Object.keys(受影响).map(Number).sort(function (a, b) { return a - b })
      if (!集们.length) {
        页.$message.warning('没有找到该资产')
        return
      }
      try {
        await 页.$confirm('资产 ' + 行.资产id + ' ' + 行.名称 + ' 出现在 ' + 集们.length + ' 个集里，将从全剧所有集删除（落库删除），确定？', '全剧删除资产', {
          confirmButtonText: '全剧删除', cancelButtonText: '取消', type: 'warning'
        })
      } catch (e) { return }
      try {
        for (let i = 0; i < 集们.length; i++) {
          const 集 = 集们[i]
          const 项们 = 页.全剧行们
            .filter(function (项) { return 项.集号 === 集 && 项.资产id !== 行.资产id })
            .map(function (项) {
              return {
                资产id: 项.资产id, 类型: 项.类型, 名称: 项.名称, 别名: 项.别名 || '',
                关系: 项.关系, 级别: 项.级别 || '', 摘要: 项.摘要
              }
            })
          await 发('/api/资产/保存', { 剧id: 页.剧id, 集号: 集, 项们: 项们 })
        }
        页.全剧行们 = 页.全剧行们.filter(function (项) { return 项.资产id !== 行.资产id })
        if (受影响[页.集号]) {
          页.行们 = 页.行们.filter(function (项) { return 项.资产id !== 行.资产id })
        }
        页.$message.success('已从全剧 ' + 集们.length + ' 个集删除 ' + 行.资产id)
      } catch (e) {
        页.$message.error('删除失败：' + ((e && e.message) || e))
      }
    },
    /* 单项按技能重写：给剧本 + 同类型既有资产上下文，输出一行替换本项 */
    async 重写一项(行) {
      const 页 = this
      if (页.重写id || 页.提取中) return
      if (!页.扩写技能id) {
        页.$message.warning('请先点「技能」选择技能与引导提示词')
        页.打开技能()
        return
      }
      页.重写id = 行.资产id
      try {
        const 同类 = 页.行们.filter(function (项) { return 项.类型 === 行.类型 && 项.资产id !== 行.资产id })
          .map(function (项) { return 项.资产id + '｜' + 项.名称 + '｜' + 项.摘要 }).join('\n')
        const 段们 = [
          '【本集剧本】\n' + 页.本集正文.slice(0, 6000),
          '【要重写的资产】\n' + 行.资产id + '｜' + 行.类型 + '｜' + 行.名称 + '｜当前摘要：' + 行.摘要
        ]
        /* 人物资产带上人物设定档案（本集状态），摘要按档案写 */
        if (行.类型 === '人物') {
          const 人 = 页.人物匹配(行)
          段们.push(人
            ? '【该人物的人物设定档案（本集状态）】\n' + 页.人物卡文本(人)
            : '【该人物】还没有人物设定档案，摘要按本集剧本里该人物的言行与外观写')
        }
        段们.push(
          '【同类型其他资产（保持区分度）】\n' + (同类 || '（无）'),
          行.类型 === '人物'
            ? '【要求】结合本集剧本与人物档案重写这一项资产：保持资产ID ' + 行.资产id + ' 与类型「人物」不变，摘要基于档案里本集的外貌/穿搭/当前状态，写满可直接拍摄的细节（五官/发型/体型/服装/随身物/姿态），与同类型资产区分开。'
            : '【要求】结合本集剧本重写这一项资产：保持资产ID ' + 行.资产id + ' 与类型「' + 行.类型 + '」不变，摘要写满可直接拍摄的外观/物件/状态细节，与同类型资产区分开。',
          '【输出】只输出一行，格式：类型｜名称｜别名｜关系｜级别｜摘要'
        )
        const 需求 = 段们.join('\n\n')
        const 规则 = (页.技能引导 || 页.默认引导) + '\n\n本次任务只重写一项资产：只输出一行「类型｜名称｜别名｜关系｜级别｜摘要」，不要输出资产ID和其他任何内容。'
        const 文本 = String(await 提交AI任务({ 技能id: 页.扩写技能id, 系统: 规则, 正向: 需求 }) || '').trim()
        if (!文本) throw new Error('AI 没有返回内容')
        const 行们 = 文本.split('\n').map(function (s) { return s.trim() }).filter(function (s) { return s.indexOf('｜') >= 0 })
        if (!行们.length) throw new Error('AI 返回里没有可识别的行')
        const 段 = 行们[行们.length - 1].split('｜').map(function (s) { return s.trim() })
        const 新列表 = 页.行们.map(function (项) {
          if (项.资产id !== 行.资产id) return 项
          return Object.assign({}, 项, {
            类型: ['人物', '场景', '道具', '服装'].indexOf(段[0]) >= 0 ? 段[0] : 项.类型,
            名称: 段[1] || 项.名称,
            别名: (段[2] && 段[2] !== '—') ? 段[2] : 项.别名,
            关系: 段[3] === '引用' ? '引用' : (段[3] === '新增' ? '新增' : 项.关系),
            级别: 段[4] || 项.级别,
            摘要: 段[5] || 项.摘要
          })
        })
        await 页.存本集(新列表)
        页.行们 = 新列表
        页.$message.success(行.资产id + ' ' + 行.名称 + ' 已重写并落库')
      } catch (e) {
        页.$message.error('重写失败：' + ((e && e.message) || e))
      }
      页.重写id = null
    },
    /* 分区编号始终按 全部视图 的顺序排（1/2/3/4），筛选后不打乱 */
    区序(区) {
      return 区定义.findIndex(function (定) { return 定.键 === 区.键 }) + 1
    },
    上一步() { this.$router.push({ path: '/video/script', query: this.$route.query }) },
    下一步() { this.$router.push({ path: '/video/art', query: this.$route.query }) }
  }
}
</script>

<style scoped>
/* ---- 分集进度 + 视图 + 筛选 ---- */
.进度卡 { padding: 14px 16px; }
.进度行 { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.进度题 { font-size: 12px; color: var(--字弱); }
.进度值 { font-size: 14px; color: var(--字); }
.进度值 b { color: var(--主); }
.小标签 {
  font-size: 12px; color: var(--字次);
  background: var(--卡片二); border: 1px solid var(--描边);
  border-radius: 6px; padding: 3px 10px;
}
.小标签.灰 { color: var(--字弱); }
.做签 {
  font-size: 12px; color: var(--警, #e6a23c);
  background: rgba(230,162,60,.1); border-radius: 6px; padding: 3px 10px;
}
.视图切 { display: flex; gap: 4px; background: var(--描边); border-radius: 8px; padding: 3px; }
.视图钮 {
  border: 0; background: transparent; cursor: pointer;
  font-size: 12px; color: var(--字次);
  padding: 4px 12px; border-radius: 6px;
  transition: all .15s ease;
}
.视图钮.选中 { background: var(--卡片); color: var(--字); font-weight: 600; }
.筛选行 { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
.chip {
  font-size: 12px; color: var(--字次);
  background: var(--卡片二); border: 1px solid var(--描边);
  border-radius: 999px; padding: 3px 12px; cursor: pointer;
  transition: all .15s ease;
}
.chip:hover { border-color: var(--描边亮); color: var(--字); }
.chip.选中 { border-color: var(--主); color: var(--主); background: var(--主浅); }
.提取轨 {
  margin-top: 12px; height: 4px; border-radius: 999px;
  background: var(--描边); overflow: hidden;
}
.提取轨 i { display: block; height: 100%; background: var(--主); transition: width .2s; }

/* ---- 技能行 ---- */
.技能行 {
  display: flex;
  align-items: center;
  gap: 6px;
  max-width: 280px;
  padding: 3px 10px;
  border: 1px solid var(--描边);
  border-radius: 999px;
  background: var(--卡片二);
}
.技能名 { flex: 0 0 auto; color: var(--字); font-weight: 600; font-size: 12px; }
.技能说 {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  color: var(--字弱);
}

/* ---- 人物档案卡（人物设定页同格式） ---- */
.人物卡网 {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(430px, 1fr));
  gap: 12px;
  padding: 14px 16px;
}
.人物卡 {
  border: 1px solid var(--描边);
  border-radius: 10px;
  background: var(--卡片二);
  overflow: hidden;
}
.卡头 {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--描边);
  background: var(--卡片);
}
.卡名 { font-size: 14px; color: var(--字); }
.卡签 { font-size: 12px; color: var(--字弱); }
.卡组 { padding: 8px 14px 2px; }
.组名 {
  font-size: 11px; font-weight: 700; color: var(--主);
  margin: 6px 0 4px;
}
.组行 {
  display: grid; grid-template-columns: 70px 1fr; gap: 8px;
  font-size: 12px; line-height: 1.7; padding: 1px 0;
}
.组键 { color: var(--字弱); }
.组值 { color: var(--字次); min-width: 0; word-break: break-all; }
.卡脚 {
  display: flex; justify-content: flex-end; gap: 2px;
  padding: 6px 10px 8px;
  border-top: 1px dashed var(--描边);
  margin-top: 8px;
}
.卡脚 .删钮 { color: var(--败, #f56c6c); }

/* ---- 编辑弹窗 ---- */
.编辑单 { display: flex; flex-direction: column; gap: 12px; }
.编项 { display: flex; flex-direction: column; gap: 4px; }
.编名 { font-size: 12px; color: var(--字弱); }
.编格 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

/* ---- 人物档案编辑弹窗 ---- */
.档案编辑 { max-height: 62vh; overflow-y: auto; padding-right: 4px; }
.档组 { margin-bottom: 10px; }
.档组名 {
  font-size: 12px; font-weight: 700; color: var(--主);
  border-left: 3px solid var(--主);
  padding-left: 8px; margin: 4px 0 8px;
}
/* 分段结构化编辑（同人物设定页） */
.档输入 { display: flex; flex-direction: column; gap: 2px; }
.拆分钮 { align-self: flex-start; padding: 0; }
.段编辑列 { display: flex; flex-direction: column; gap: 6px; }
.段编辑行 { display: flex; align-items: flex-start; gap: 4px; }
.段编辑字 { font-size: 12px; color: var(--字次); line-height: 28px; flex: none; }
.段编辑值 { flex: 1; min-width: 0; }
.段编辑删 { cursor: pointer; color: var(--字弱); line-height: 28px; margin-left: 4px; flex: none; }
.段编辑删:hover { color: var(--败, #f56c6c); }
.段编辑底 { display: flex; gap: 10px; }
.档行 {
  display: grid; grid-template-columns: 70px 1fr; gap: 8px;
  align-items: start; margin-bottom: 6px;
}
.档名 { font-size: 12px; color: var(--字弱); line-height: 1.7; padding-top: 6px; }
.档提示 {
  font-size: 11px; color: var(--字弱);
  border-top: 1px dashed var(--描边);
  padding-top: 8px; margin-top: 2px;
}

/* ---- 分区表 ---- */
.分区卡 { margin-bottom: 2px; }
.区头 {
  display: flex; align-items: baseline; gap: 10px;
  padding: 14px 16px 10px; border-bottom: 1px solid var(--描边);
}
.区名 { font-size: 14px; font-weight: 700; color: var(--字); }
.区数 { font-size: 12px; color: var(--字弱); }
.按集看 { margin-left: auto; display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: var(--字次); }
/* 人物卡时间轴（与人物设定页详情卡同口径） */
.组值.分段 { display: flex; flex-direction: column; gap: 3px; }
.段行 { display: flex; gap: 6px; align-items: baseline; }
.段行.本集 .段文 { color: var(--主); font-weight: 600; }
.段行.淡 { opacity: .45; }
.段标 { flex: none; font-size: 11px; color: var(--字弱); white-space: nowrap; }
.段文 { min-width: 0; word-break: break-all; }
/* 本集拍摄摘要小字（非档案） */
.拍注 { margin: 0 14px 10px; padding-top: 8px; border-top: 1px dashed var(--描边); font-size: 11px; color: var(--字弱); line-height: 1.6; }
.警注 { color: var(--警, #e6a23c); }

.表 { font-size: 12px; }
.表头行, .表行 {
  display: grid;
  grid-template-columns: 130px 150px 150px 80px 100px 1fr 180px;
  gap: 10px;
  align-items: start;
  padding: 9px 16px;
}
.表头行 {
  color: var(--字弱); font-size: 11px;
  border-bottom: 1px solid var(--描边);
  background: var(--卡片二);
}
.表体 { border-bottom: 1px solid var(--描边); }
.表体:last-child { border-bottom: none; }
.表行 { transition: background .15s; }
.表行:hover { background: var(--卡片二); }
.格 { min-width: 0; line-height: 1.7; color: var(--字次); }
.格id code {
  font-family: Consolas, monospace; font-size: 11px;
  color: var(--字弱); background: var(--描边);
  border-radius: 4px; padding: 1px 6px;
}
.集签 {
  font-size: 10px; color: var(--主); margin-left: 4px;
  background: var(--主浅, rgba(64,158,255,.12));
  border-radius: 4px; padding: 0 5px;
}
.格名 { color: var(--字); font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.格别名 { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.格级 { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.格摘要 { line-height: 1.7; }
.格操作 { text-align: right; white-space: nowrap; }
.格操作 .删钮 { color: var(--败, #f56c6c); }

.空态 { text-align: center; padding: 48px 0; color: var(--字弱); font-size: 13px; }

@media (max-width: 1400px) {
  .表头行, .表行 { grid-template-columns: 120px 120px 130px 70px 90px 1fr 170px; }
}
@media (max-width: 1100px) {
  .表头行 { display: none; }
  .表行 { grid-template-columns: 1fr 1fr; }
}
</style>
