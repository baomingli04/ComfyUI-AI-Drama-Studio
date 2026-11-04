<template>
  <div class="创作模块">
    <!-- 面包屑 -->
    <div class="面包屑条">
      <span class="可点" @click="$router.push('/script')">剧本创作</span>
      <span> / </span>
      <span class="可点" @click="去方案详情()">创作方案</span>
      <span> / </span>
      <span>分集剧本</span>
    </div>

    <!-- 四步进度条：和创作方案页同一位置（面包屑正下方、居中），点任意一步即跳到那一步。 -->
    <step-bar :步骤="步骤" :当前步="当前步" @切换="跳步骤($event)"></step-bar>

    <!-- 页头 -->
    <div class="页头">
      <div class="左">
        <h1 class="标题">{{ 剧名 }}</h1>
        <div class="副题">
          {{ 集数 }} 集 · {{ 题材 }} · 已采用 {{ 方案卡名 }} ·
          已生成 {{ 已生成数 }} 集 · 待复核 {{ 待复核数 }} 集
        </div>
      </div>
      <div class="右">
        <el-button @click="上一步()">上一步：分集目录</el-button>
        <el-button type="primary" @click="保存()">保存</el-button>
      </div>
    </div>

    <!-- 载入中 / 载入报错（真库载入门控） -->
    <div v-if="载入中" class="卡片 载入框">正在从数据库载入分集剧本…</div>
    <div v-else-if="载入报错" class="卡片 载入框 报错框">
      {{ 载入报错 }}
      <el-button size="mini" type="primary" plain style="margin-left:12px" @click="载入()">重试</el-button>
    </div>

    <!-- 首次进页：逐集自动生成进度遮罩 -->
    <div v-if="自动生成中" class="生成遮罩">
      <div class="生成框">
        <div class="生成标题">正在初始化本剧分集剧本</div>
        <div class="生成文案">{{ 自动文案 }}</div>
        <el-progress :percentage="自动进度" :stroke-width="10"></el-progress>
        <div class="生成注">每集用本页技能逐集生成，生成一集保存一集；中途失败不影响已完成集</div>
      </div>
    </div>

    <div v-if="!载入中 && !载入报错" class="卡片 提示卡">
      左边选集（可搜、可筛、可翻页），右边是这一集的完整剧本：正文按场次排，下面跟
      <b>能力档案 / 世界状态 / 关系网络 / 记忆回廊 / 行动推荐</b> 五块。
      点「按技能重写本集」让 AI 重出一版，出来先给你看解析结果，点写入才覆盖。
    </div>

    <!-- ============ 本页生成 ============ -->
    <div v-if="!载入中 && !载入报错" class="生成条">
      <div class="行间">
        <div class="行间">
          <div class="AI标">AI</div>
          <div>
            <div class="意见标题">生成第 {{ 当前集 }} 集剧本</div>
            <div class="意见价">0.2 积分/次 · 正文 + 5 个档案块</div>
          </div>
        </div>
        <div style="flex:1"></div>
        <div class="意见例如">例：台词更口语、开场三拍更快…</div>
        <el-button size="mini" icon="el-icon-setting" @click="打开技能()">技能</el-button>
        <el-button size="mini" type="primary" plain :loading="扩写中" @click="生成本集()">
          AI 生成第 {{ 当前集 }} 集
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
        placeholder="写一句要求，AI 按这句话重写本集（不写就按目录合同和人物列表直接产出一版）"></el-input>
    </div>

    <!-- ============ 生成结果预览 ============ -->
    <div v-if="!载入中 && !载入报错 && 预览" class="卡片 预览卡">
      <div class="卡头">
        <span class="卡名">生成结果 · 第 {{ 当前集 }} 集</span>
        <span class="卡注">解析完先给你看，点「写入」才覆盖现有剧本</span>
        <div style="flex:1"></div>
        <el-button type="text" size="mini" @click="看原文 = !看原文">{{ 看原文 ? '收起原文' : '看原文' }}</el-button>
        <el-button type="text" size="mini" @click="丢弃预览()">丢弃</el-button>
      </div>

      <div class="预览格">
        <div class="预览项">
          <div class="预览键">正文</div>
          <div class="预览值">{{ 预览.场们.length }} 场 · {{ 预览字数 }} 字<span class="旧">（原 {{ 当前检.场数 }} 场 · {{ 当前检.字数 }} 字）</span></div>
        </div>
        <div class="预览项">
          <div class="预览键">档案块</div>
          <div class="预览值">
            命中 {{ 预览.命中.length }}/6
            <span v-if="预览.缺.length" class="缺">缺：{{ 预览.缺.join('、') }}</span>
            <span v-else class="全">五块齐全</span>
          </div>
        </div>
        <div class="预览项">
          <div class="预览键">人物变化</div>
          <div class="预览值">
            <span v-if="!(预览.人物变化 || []).length" class="缺">本集人物字段无变化</span>
            <span v-else class="全">{{ 预览.人物变化.length }} 条 · 写入时同步进人物档案</span>
          </div>
        </div>
        <div class="预览项">
          <div class="预览键">解析提示</div>
          <div class="预览值">
            <span v-if="!预览.场们.length" class="缺">没认出「场次号 · 地点」开头的场次，正文会整段展示</span>
            <span v-else class="全">场次头认出来了，可以直接逐场编辑</span>
          </div>
        </div>
      </div>

      <pre v-if="看原文" class="原文">{{ 生成结果 }}</pre>

      <div class="行间 右" style="margin-top:12px">
        <el-button size="small" @click="丢弃预览()">取消</el-button>
        <el-button size="small" type="primary" @click="写入预览()">写入第 {{ 当前集 }} 集</el-button>
      </div>
    </div>

    <!-- 生成原文兜底（没有预览时也能看上一版原文） -->
    <div v-if="!载入中 && !载入报错 && 生成结果 && !预览" class="卡片 结果卡">
      <div class="行间" style="margin-bottom:10px">
        <div class="结果标题">生成原文 · 第 {{ 当前集 }} 集</div>
        <div style="flex:1"></div>
        <el-button type="text" size="mini" @click="重新解析()">重新解析</el-button>
        <el-button type="text" size="mini" @click="复制生成结果()">复制</el-button>
        <el-button type="text" size="mini" @click="生成结果 = ''">清空</el-button>
      </div>
      <pre class="原文">{{ 生成结果 }}</pre>
    </div>

    <!-- ============ 左：集数列表 / 右：本集剧本 ============ -->
    <div v-if="!载入中 && !载入报错" class="网格 二" style="grid-template-columns:300px 1fr">
      <!-- ---------- 侧栏：搜索 + 筛选 + 列表 + 分页 ---------- -->
      <div class="卡片 侧栏">
        <div class="侧题">
          <span class="侧名">集数列表</span>
          <span class="侧数">{{ 筛选后.length }}/{{ 目录表.length }}</span>
        </div>

        <el-input
          v-model="搜索"
          size="small"
          class="搜框"
          prefix-icon="el-icon-search"
          placeholder="搜集号 / 标题 / 梗概 / 人物"
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
            :class="{ 当前: 当前集 === 集.集 }"
            @click="切集(集.集)">
            <div class="集项头">
              <span class="集号">第 {{ 集.集 }} 集</span>
              <span class="集点" :class="集点类(集)"></span>
              <div style="flex:1"></div>
              <span class="集场">{{ 集场数(集.集) }} 场</span>
            </div>
            <div class="集名">{{ 集.标题 || '（未命名）' }}</div>
            <div class="集字">{{ 集.幕 || '未分幕' }} · {{ 集.字数 }} 字</div>
          </div>

          <div v-if="!分页集.length" class="列空">
            没有匹配「{{ 搜索 }}」的集
          </div>
        </div>

        <page-bar
          v-if="筛选后.length"
          :总数="筛选后.length"
          :每页="每页"
          :当前页="有效页"
          :每页选项="[10, 20, 50, 100]"
          单位="集"
          紧凑
          @换页="换页($event)"
          @换每页="换每页($event)"></page-bar>
      </div>

      <!-- ---------- 右侧：本集剧本 ---------- -->
      <div>
        <div class="本集导航">
          <el-button size="mini" :disabled="当前集 <= 1" @click="切集(当前集 - 1)">← 上一集</el-button>
          <span class="导航中">第 {{ 当前集 }} / {{ 目录表.length }} 集</span>
          <el-button size="mini" :disabled="当前集 >= 目录表.length" @click="切集(当前集 + 1)">下一集 →</el-button>
          <div style="flex:1"></div>
          <el-button size="mini" @click="保存并继续()">保存并进入下一集</el-button>
        </div>

        <script-card
          v-if="当前目录"
          :集="当前目录"
          :剧="当前剧"
          :前情="前情文本"
          :卖点="卖点文本"
          @重写="生成本集()"
          @复核="标记复核()"
          @全文="打开全文()"
          @新增场="新增一场()"
          @编辑场="打开编辑场"></script-card>

        <div v-else class="卡片 空场">这一集不在目录里，请回「分集目录」补齐。</div>
      </div>
    </div>

    <div class="行间 右" style="margin-top:20px">
      <el-button @click="上一步()">返回分集目录</el-button>
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
          <div class="弹窗副题">{{ 新增模式 ? '填完点「加入本集」，这一场会排到最后' : '改完点保存，直接写回这一场' }}</div>
        </div>
        <i class="el-icon-close 弹窗关闭" title="关闭" @click="编辑显示 = false"></i>
      </div>
      <div class="弹窗体">
        <el-form label-width="72px" size="small">
          <el-form-item label="场次号">
            <el-input v-model="草稿.场" maxlength="10" placeholder="例：1-3"></el-input>
          </el-form-item>
          <el-form-item label="地点">
            <el-input v-model="草稿.地点" maxlength="40" placeholder="例：内 · 忍校三班教室 · 日"></el-input>
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
        <el-button type="primary" @click="保存这一场()">{{ 新增模式 ? '加入本集' : '保存' }}</el-button>
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
          <div class="弹窗标题">第 {{ 当前集 }} 集全文</div>
          <div class="弹窗副题">正文 + 五个档案块，可直接整段复制走</div>
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

    <!-- 技能生成弹窗：技能 + 技能引导提示词 + 引入数据（人物列表 / 分集目录 / 上一集剧本 / 本集大纲）。
         in-DOM 模板只认 ASCII 标签名，必须用 skill-dialog 别名；
         事件处理器必须带括号，否则中文方法名不会被调用。 -->
    <skill-dialog
      :显示.sync="技能弹窗显示"
      :技能列表="技能列表"
      :技能id.sync="扩写技能id"
      :引导.sync="技能引导"
      :默认引导="默认引导"
      :配置类型="页配置类型"
      目标名="分集剧本"
      :引入数据="引入数据"
      @保存="技能已保存($event)"></skill-dialog>
  </div>
</template>

<script>
import 步骤条 from '@/共用/步骤条/index.vue'
import 剧本卡 from '@/共用/剧本卡/index.vue'
import 分页条 from '@/共用/分页条/index.vue'
import 技能生成弹窗 from '@/共用/技能生成弹窗/index.vue'
import 剧本页混入 from '@/共用/剧本页混入'
import { 读引导, 读技能id, 读引入, 存引入, 读创意, 存创意, 适配技能id } from '@/共用/技能生成配置'
import { 复制到剪贴板 } from '@/共用/复制文本'
import {
  解析生成结果, 数字数, 体检剧本, 拼正文, 拼全文, 档案块们
} from '@/共用/剧本档案'
import { 文本转值, 值文本 } from '@/共用/人物工具'
import { 取, 发 } from '@/接口/请求'
import { 提交AI任务 } from '@/共用/AI任务'

// 「引入数据」里来自方案详情的五块（真库 /api/方案/分区，键 = 库列名）
const 方案分区 = [
  { 键: '时空背景', 名: '时空背景', 库列: '时空背景', 型: '键值' },
  { 键: '故事线', 名: '故事线与核心冲突', 库列: '故事线', 型: '键值' },
  { 键: '爽点', 名: '爽点矩阵', 库列: '爽点矩阵', 型: '表格', 列: ['区间', '类型', '描述', '强度'] },
  { 键: '商业卖点', 名: '商业卖点', 库列: '商业卖点', 型: '嵌套' },
  { 键: '结局', 名: '结局设计', 库列: '结局设计', 型: '键值' }
]

// 「第1-5集：…；第6集起：…」之类分段文本按行拆开（库转集用，点位也用行格式）
function 解析点位(文本) {
  const 条们 = []
  String(文本 || '').split('\n').forEach(function (行) {
    const 净 = 行.trim()
    if (!净) return
    const 段 = 净.split('｜')
    if (段.length >= 3) {
      条们.push({ 类型: 段[0].trim(), 点: 段[1].trim(), 内容: 段.slice(2).join('｜').trim() })
    } else if (段.length === 2) {
      条们.push({ 类型: 段[0].trim(), 点: '', 内容: 段[1].trim() })
    }
  })
  return 条们
}

/* 五个档案块 ↔ 库列文本（键值块 =「键：值」行文本；列表块 =「N. 内容」行文本）。
   与 剧本档案.js 拼全文 的块内格式同构，往返无损。 */
function 剧档案转文本(档案) {
  const 出 = {}
  档案块们.forEach(function (块) {
    const 值 = (档案 || {})[块.键]
    if (块.型 === '列表') {
      出[块.键] = (值 || []).map(function (条, 序) { return (序 + 1) + '. ' + 条 }).join('\n')
      return
    }
    出[块.键] = (块.字段 || []).map(function (k) {
      const 文 = String((值 && 值[k]) || '').trim()
      return 文 ? k + '：' + 文 : ''
    }).filter(Boolean).join('\n')
  })
  return 出
}

function 文本转档案(文本们) {
  const 档案 = {}
  档案块们.forEach(function (块) {
    const 行们 = String(文本们 && 文本们[块.键] || '').replace(/\r\n?/g, '\n').split('\n')
    if (块.型 === '列表') {
      档案[块.键] = 行们.map(function (行) {
        return 行.trim().replace(/^\d+[.、）)]\s*/, '')
      }).filter(Boolean)
      return
    }
    const 键值 = {}
    ;(块.字段 || []).forEach(function (k) { 键值[k] = '' })
    行们.forEach(function (行) {
      const 净 = 行.trim()
      if (!净) return
      const 位 = 净.indexOf('：')
      if (位 < 0) return
      const 键 = 净.slice(0, 位).trim()
      if ((块.字段 || []).indexOf(键) >= 0) 键值[键] = 净.slice(位 + 1).trim()
    })
    档案[块.键] = 键值
  })
  return 档案
}

function 现在() {
  const d = new Date()
  const p = n => (n < 10 ? '0' + n : '' + n)
  return d.getFullYear() + '/' + p(d.getMonth() + 1) + '/' + p(d.getDate()) +
    ' ' + p(d.getHours()) + ':' + p(d.getMinutes())
}

// 输出格式规则：正文 + 5 个档案块。字段顺序必须和 剧本档案.js 里的一致，
// 否则解析器能认出块名却对不上字段，会显示成「档案缺 N 块」。
const 档案格式规则 = [
  '【输出格式（必须遵守）】',
  '· 只输出下面 7 个块，块名用【】包住，顺序固定，块内不要再出现别的块名：',
  '【正文】【能力档案】【世界状态】【关系网络】【记忆回廊】【行动推荐】【人物变化】',
  '· 【正文】按场次写：每场第一行写「场次号 · 内/外 · 地点 · 时间」（例：1-1 · 内 · 忍校三班教室 · 日）；第二行「出场人物：A、B」；第三行「出场道具：…」；之后一行一个动作或一句台词。动作行以 △ 开头；台词写成「角色名（动作）：台词」，台词要口语化、能直接念。',
  '· 【能力档案】固定 10 行，一行一个「键：值」：所属势力、声望影响、阶级、评级、拥有技能、当前体力、能量状态、健康状态、拥有物品、目前目标。',
  '· 【世界状态】固定 11 行：当前世界、当前日期、当前区域、当前环境、当前事件、区域布局、区域情报、区域角色、传闻、附近热议、附近动向。当前日期必填，没有就写「第1年春月初一」，或在上一集日期上推进一天。',
  '· 【世界状态】的「传闻」默认是尚未扩散的消息：除非本集正文明确演出「有人亲眼看到/亲耳听到并且传开了」，否则一律默认其他人都还不知道这件事——传闻措辞保持「据传/有人说」的未证实口径；「区域情报」「附近热议」「附近动向」同理，只写本集正文里已经公开发生、外人能看到听到的层面，暗中发生的事一律不进这三行。',
  '· 【关系网络】6 行：当前主线、预告1、预告2、蝴蝶效应、历史进程、角色记录。',
  '· 【记忆回廊】7 行：长期记忆、短期记忆1、短期记忆2、短期记忆3、短期记忆4、短期记忆5、短期记忆6。没有内容就留空冒号。记忆是全剧连贯性的命脉，必须逐条遵守：',
  '  - 长期记忆：只放从开篇到本集始终成立、决定主线走向的事实（真实身份、核心关系、总目标、世界观设定）。本集剧情没有改变它就原样保留上一集的写法；只有被剧情真实改变了才更新，更新后旧表述不再保留，全剧同一事实在长期记忆里只能有一个版本。',
  '  - 短期记忆1：本集正文里新发生的关键事件。必须能在本集正文里找到对应场面——正文没演到的事，一律不许写进任何一条记忆；反过来，正文里的关键转折（影响后续剧情的）也不许漏掉不记。',
  '  - 短期记忆2–6：由近到远存前几集的事，上一集的 1–5 顺延为 2–6；被挤出 6 的彻底丢弃，后面的集里不得再把它当新事写。',
  '  - 先去重再落笔：同一件事只占一条，相关细节并进同一条；每条一句话，写清「谁 + 干了什么 + 造成什么结果」，不写流水账、不写没有信息量的场面。',
  '  - 知情范围分清：只有当事角色知道的密谈/暗中操作可以进短期记忆（这是角色视角的记忆），但外界默认不知情——后面的剧情里，不知情的角色不得凭空对这些事做出反应，除非正文演出了他获知的过程。',
  '· 参考数据里给了「前情状态」时，五大档案必须在上一集档案的基础上推进，不许从零另起：【世界状态】的事件/日期/区域动向接续上一集并按本集剧情更新（日期往后推进）；【记忆回廊】短期记忆滚动——本集新事写进短期记忆1，上一集的记忆1–5 顺延为 2–6，挤出去的丢弃；【关系网络】的预告/蝴蝶效应/历史进程和【行动推荐】按本集剧情更新，不得原样照抄上一集。',
  '· 【行动推荐】3 行，编号 1. 2. 3.，每条一句可执行的动作。',
  '· 【人物变化】每行一条，格式「人物名｜字段｜第N集：内容」（N=本集集号；这段状态会持续到剧末就写「第N集起」）。只写本集因剧情确实发生了变化的人物字段：当前状态、内心想法、关系网、态度、情感情况、身份、技能、核心目标、精神情况、外貌、穿搭等。内容要接续该字段已有时间轴往下补新的一段（例：李宝明｜关系网｜第3-4集：与樱井桃在考核中建立信任，被千代宗公开针对），不要复述旧段；人物字段全程没有变化时，【人物变化】块里只写一个字：无。',
  '· 人物的「状态与心理」描写必须基于他的精神状态、情感状态、肉体状态和七情六欲推演，且一切变化都要有过程、有进度，绝不一步到位：【正文】写状态与心理时按这个幅度来，【人物变化】更新状态字段时也按这个幅度写。判断方法是：把事件对三条状态轴分别过一遍——肉体状态（身体受了什么、接触了什么）、精神状态（知道了什么、承受了什么压力）、情感状态（对谁的好感/敌意/愧疚动了多少），三条轴往往变化幅度完全不同。例：张三李四嘴唇意外碰了一下，只是巧合——肉体上初吻没了（事实记录），精神上只是有点尴尬，情感上毫无影响，不许写成脸红心跳、暗生情愫；再例：张三李四洞房了，不等于感情已经很好——情感进展要按好感进度走（陌生→戒备→缓和→信任→亲密→深爱），一次事件最多推进一到两档；再例：张三受严刑拷打，不是当场就屈服——要写清撑了多久、精神怎么一点点被磨、在哪条信息上先扛不住、屈服时肉体已经到了什么程度。事件发生在什么环境场景，就按那个场景产生对应的生理和心理反应（疼痛、恐惧、羞耻、戒备、兴奋各自不同），禁止跳过过程直接写结果状态。',
  '· 角色只用参考数据里已有的人，不要新造；本集结尾必须卡在目录给的「尾钩」上。',
  '· 除这 7 个块以外不要写任何解释、前言、后记。'
].join('\n')

// 老版自定义引导词（只有前 6 块）的补充规则：只讲【人物变化】，避免整份格式规则重复拼两遍
const 人物变化格式规则 = [
  '【输出块补充：人物变化】',
  '· 在原 6 个块之后追加第 7 块【人物变化】：每行一条，格式「人物名｜字段｜第N集：内容」（N=本集集号；持续到剧末写「第N集起」）。',
  '· 只写本集因剧情确实发生了变化的人物字段（当前状态、内心想法、关系网、态度、情感情况、身份、技能、核心目标、精神情况等），内容接续该字段已有时间轴往下补新的一段，不要复述旧段；没有变化就只写一个字：无。',
  '· 状态与心理的更新必须基于人物的精神状态、情感状态、肉体状态和七情六欲，分轴判断变化幅度：肉体、精神、情感三条轴的变化往往不同（例：意外碰到嘴唇只是肉体上初吻没了，精神只是尴尬，情感毫无影响），且一切情感与心理变化都要有过程有进度（好感按阶段逐步推进、受刑不会当场屈服），禁止一步到位写结果。'
].join('\n')

// 【人物变化】的字段名 → 人物表列名（字段名写别的就丢弃）
const 变化字段映射 = {
  '性格': '性格', '身份': '身份', '关系': '关系变化', '态度': '态度',
  '外貌': '外貌', '身材': '身材', '穿搭': '穿搭',
  '身体情况': '身体情况', '情感情况': '情感情况', '精神情况': '精神情况',
  '当前状态': '当前状态', '当前姿势': '当前姿势', '内心想法': '内心想法',
  '技能': '技能', '核心目标': '核心目标', '关系网': '关系网',
  '背景故事': '背景故事', '台词风格': '台词风格', '口头禅': '口头禅', '概括': '概括'
}

const 写作规则 = [
  '1. 你要写的是短剧「分集剧本」，不是视频/图片提示词：禁止输出 <Picture N>、<Video N>、<Audio N> 之类标签，也不要写镜头运动、光影参数。'
].join('\n')

// 本页默认技能引导提示词 = 写作规则 + 输出格式
const 默认引导文本 = 写作规则 + '\n' + 档案格式规则

const 快捷意见 = ['台词更口语', '开场三拍更快', '压到 3 场', '加强师徒张力', '结尾卡在尾钩上']

export default {
  name: 'ScriptEpisode',
  mixins: [剧本页混入],
  components: {
    'step-bar': 步骤条,
    'script-card': 剧本卡,
    'page-bar': 分页条,
    'skill-dialog': 技能生成弹窗
  },
  created() {
    const 路由创意 = (this.$route.query.创意 || '').trim()
    if (路由创意) {
      this.创意文本 = 路由创意
      存创意(this.剧名, 路由创意)
    } else {
      this.创意文本 = 读创意(this.剧名)
    }
    this.载入()
  },
  watch: {
    // 换集时把这一集翻到当前页，并清掉上一集的生成态
    当前集(值) {
      this.滚到本集(值)
      this.预览 = null
      this.看原文 = false
    }
  },
  data() {
    return {
      /* 真库数据 */
      剧id: 0,
      方案卡: null,
      方案分区值: {},
      人物行们: [],
      角色们: [],
      // 目录表：来自 /api/分集/列表（库转集），结构与分集目录页一致
      目录表: [],
      // 剧本库：{ 集号: { 正文, 场们, 档案, 余文, 命中, 缺, 状态, 时间 } }
      剧本库: {},
      /* 载入态 */
      载入中: true,
      载入报错: '',
      /* 首次自动逐集生成 */
      自动生成中: false,
      自动进度: 0,
      自动文案: '',
      当前集: 1,
      /* 侧栏：搜索 / 筛选 / 分页 */
      搜索: '',
      状态筛: '全部',
      当前页: 1,
      每页: 20,
      /* 本页生成 */
      扩写需求: '',
      生成结果: '',
      预览: null,
      看原文: false,
      创意文本: '',
      技能弹窗显示: false,
      技能引导: '',
      引入勾选: null,
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
      return this.$route.query.剧名 || ''
    },
    集数() {
      return this.$route.query.集数 || '24'
    },
    // 总集数（数字）：人物状态分段时用来判断「第13集起」这类写法铺到哪
    总集() {
      const 数 = parseInt(this.集数, 10)
      return 数 > 0 ? 数 : 24
    },
    题材() {
      return this.$route.query.题材 || '都市'
    },
    // 已选方案卡（进页时按地址栏 方案=方案行 id 从 /api/方案列表 精确取）
    方案卡名() {
      return this.方案卡 ? (this.方案卡.标题 || ('方案 ' + this.方案卡.id)) : '（未选定方案）'
    },
    // 第 4 步（0 起：0 创作方案 / 1 人物设定 / 2 分集目录 / 3 分集剧本）
    当前步() {
      return 3
    },
    /* 本页配置 key：生成:/script/episode */
    页配置类型() {
      return '生成:' + (this.$route.path || '')
    },
    默认引导() {
      return 默认引导文本
    },

    /* ---------- 列表 / 搜索 / 分页 ---------- */
    排序表() {
      return this.目录表.slice().sort(function (a, b) { return a.集 - b.集 })
    },
    筛选项() {
      const 页 = this
      const 数 = function (键) {
        return 页.排序表.filter(function (集) {
          const 剧 = 页.剧本库[集.集]
          if (键 === '已生成') return !!剧
          if (键 === '待复核') return !!剧 && 剧.状态 === '待复核'
          if (键 === '未生成') return !剧
          return true
        }).length
      }
      return [
        { 键: '全部', 名: '全部', 数: 数('全部') },
        { 键: '已生成', 名: '已生成', 数: 数('已生成') },
        { 键: '待复核', 名: '待复核', 数: 数('待复核') },
        { 键: '未生成', 名: '未生成', 数: 数('未生成') }
      ]
    },
    筛选后() {
      const 页 = this
      const 词 = this.搜索.trim()
      let 表 = this.排序表
      if (this.状态筛 === '已生成') 表 = 表.filter(集 => !!页.剧本库[集.集])
      else if (this.状态筛 === '待复核') 表 = 表.filter(集 => 页.剧本库[集.集] && 页.剧本库[集.集].状态 === '待复核')
      else if (this.状态筛 === '未生成') 表 = 表.filter(集 => !页.剧本库[集.集])
      if (!词) return 表
      // 纯数字按集号前缀匹配，其他按标题 / 梗概 / 出场人物
      if (/^\d+$/.test(词)) {
        return 表.filter(function (集) { return String(集.集).indexOf(词) === 0 })
      }
      return 表.filter(function (集) {
        const 串 = [集.标题, 集.梗概, (集.出场 || []).join(''), 集.幕 || ''].join(' ')
        return 串.indexOf(词) >= 0
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

    /* ---------- 当前集 ---------- */
    当前目录() {
      for (let i = 0; i < this.目录表.length; i++) {
        if (this.目录表[i].集 === this.当前集) return this.目录表[i]
      }
      return this.目录表[0] || null
    },
    当前剧() {
      return this.剧本库[this.当前集] || null
    },
    当前检() {
      return 体检剧本(this.当前剧)
    },
    预览字数() {
      return this.预览 ? 数字数(this.预览.正文) : 0
    },
    已生成数() {
      const 页 = this
      return this.排序表.filter(function (集) { return !!页.剧本库[集.集] }).length
    },
    待复核数() {
      const 页 = this
      return this.排序表.filter(function (集) {
        const 剧 = 页.剧本库[集.集]
        return !!剧 && 剧.状态 === '待复核'
      }).length
    },
    前情文本() {
      if (this.当前集 <= 1) return '无（首集）'
      const 前 = this.排序表.filter(集 => 集.集 === this.当前集 - 1)[0]
      if (!前) return '无（上一集不在目录里）'
      const 文 = String(前.尾钩 || 前.梗概 || '')
      return '第 ' + 前.集 + ' 集「' + (前.标题 || '') + '」结尾：' + (文.length > 70 ? 文.slice(0, 70) + '…' : 文)
    },
    卖点文本() {
      // 商业卖分区结构是 {爽点兑现:[], 反派压力:[]}（同方案详情页 拆商业卖点 的口径）
      const 卖 = this.方案分区值['商业卖点'] || {}
      const 首条 = String((卖.爽点兑现 || [])[0] || '').trim()
      if (首条) return 首条.length > 90 ? 首条.slice(0, 90) + '…' : 首条
      return this.方案卡名
    },
    全文内容() {
      return 拼全文(this.当前剧)
    },
    /* 引入数据：标题 + 创意 + 方案 + 方案七块 + 人物列表 + 场景道具 + 分集目录 + 上一集 + 本集大纲 */
    引入数据() {
      return this.造引入数据(this.引入勾选)
    }
  },
  methods: {
    /* ---------------- 主载入（真库） ---------------- */
    async 载入() {
      this.载入中 = true
      this.载入报错 = ''
      try {
        await this.载入本页配置()
        await this.取剧与方案()
        await this.取方案分区()
        await this.取人物清单()
        await this.取目录()
        await this.取剧本()
        // 库里一集剧本都没有且目录已有：首次进页，AI 逐集生成
        const 有剧本 = Object.keys(this.剧本库).length > 0
        if (!有剧本 && this.目录表.length) {
          await this.首次生成()
        }
      } catch (e) {
        this.载入报错 = (e && e.message) || '载入失败'
      } finally {
        this.载入中 = false
      }
    },
    // 取剧行（补一句话创意）+ 选中的方案行（地址栏 方案=方案行 id）
    async 取剧与方案() {
      const id = parseInt(this.$route.query.id, 10) || 0
      this.剧id = id
      if (!id) return
      try {
        const 剧据 = await 取('/api/剧/详情?id=' + id)
        if (剧据 && 剧据.ok && 剧据.剧 && 剧据.剧.创意 && !this.创意文本) {
          this.创意文本 = 剧据.剧.创意
          存创意(this.剧名, this.创意文本)
        }
      } catch (e) { /* 取不到创意就用地址栏/本地记住的 */ }
      const 数据 = await 取('/api/方案列表?剧id=' + id)
      const 行们 = (数据 && 数据.列表) || []
      const 意id = parseInt(this.$route.query.方案, 10) || 0
      this.方案卡 = 行们.find(function (行) { return 行.id === 意id })
        || 行们.find(function (行) { return 行.是否选定 })
        || 行们[0]
        || null
    },
    // 读方案详情五分区真库内容（引入数据用）
    async 取方案分区() {
      this.方案分区值 = {}
      if (!this.方案卡) return
      try {
        const 数据 = await 取('/api/方案/分区?方案id=' + this.方案卡.id)
        this.方案分区值 = (数据 && 数据.分区) || {}
      } catch (e) { /* 取不到就让方案块为空 */ }
    },
    // 人物设定真库清单 + 库转角色（可分段字段认回时间轴，人物状态按本集取值）
    async 取人物清单() {
      this.人物行们 = []
      this.角色们 = []
      if (!this.剧id) return
      try {
        const 数据 = await 取('/api/人物/列表?剧id=' + this.剧id)
        this.人物行们 = (数据 && 数据.人物们) || []
      } catch (e) { /* 人物取不到就让人物块为空 */ }
      const 页 = this
      this.角色们 = this.人物行们.map(function (行, 序) { return 页.库转角色(行, 序) })
    },
    // 库行 → 角色卡（同人物设定页口径：可分段字段用 文本转值 认回时间轴）
    库转角色(行, 序) {
      const 总 = this.总集
      const 详 = {}
      const 可分段 = {
        性格: 行.性格, 身份: 行.身份, 关系: 行.关系变化, 态度: 行.态度,
        外貌: 行.外貌, 身材: 行.身材, 穿搭: 行.穿搭, 身体情况: 行.身体情况,
        情感情况: 行.情感情况, 精神情况: 行.精神情况, 当前状态: 行.当前状态,
        当前姿势: 行.当前姿势, 内心想法: 行.内心想法, 技能: 行.技能,
        核心目标: 行.核心目标, 关系网: 行.关系网, 背景故事: 行.背景故事,
        台词风格: 行.台词风格, 口头禅: 行.口头禅, 概括: 行.概括
      }
      Object.keys(可分段).forEach(function (键) { 详[键] = 文本转值(可分段[键], 总) })
      return {
        资产ID: 行.人物id || ('CHAR_' + String(序 + 1).padStart(3, '0')),
        关系: 行.关系 || '',
        名: 行.名 || '',
        性别: 行.性别 || '',
        年龄: 行.年龄档 || '',
        简介: 行.简介 || '',
        详: 详
      }
    },
    // 分集目录真库行 → 页面集卡（同分集目录页口径）
    async 取目录() {
      this.目录表 = []
      if (!this.剧id) return
      try {
        const 数据 = await 取('/api/分集/列表?剧id=' + this.剧id)
        const 行们 = (数据 && 数据.分集们) || []
        this.目录表 = 行们.map(行 => this.库转集(行))
      } catch (e) { /* 目录取不到就空表，本集大纲块会显示缺 */ }
    },
    库转集(行) {
      return {
        集: 行.集号,
        幕: 行.幕 || '第一幕 · 建置',
        标题: 行.标题 || '',
        关键: !!行.关键,
        卡点: !!行.卡点,
        情绪分: Number(行.情绪分) || 3,
        字数: Number(行.字数) || 0,
        目标: Number(行.目标) || 3000,
        状态: 行.状态 || '待创作',
        梗概: 行.梗概 || '',
        出场: String(行.出场 || '').split(/[、,，]/).map(function (s) { return s.trim() }).filter(Boolean),
        钩子: 行.钩子 || '',
        尾钩: 行.尾钩 || '',
        中心句: 行.中心句 || '',
        点位: 解析点位(行.点位)
      }
    },
    // 页面集卡 → 库行（出场并成顿号文本，点位并成行文本；同步目录落分集表用）
    集转库(集) {
      return {
        集号: 集.集,
        标题: 集.标题 || '',
        梗概: 集.梗概 || '',
        钩子: 集.钩子 || '',
        状态: 集.状态 || '待创作',
        幕: 集.幕 || '',
        关键: !!集.关键,
        卡点: !!集.卡点,
        情绪分: Number(集.情绪分) || 3,
        字数: Number(集.字数) || 0,
        目标: Number(集.目标) || 3000,
        尾钩: 集.尾钩 || '',
        中心句: 集.中心句 || '',
        出场: (集.出场 || []).join('、'),
        点位: (集.点位 || []).map(function (条) {
          return [条.类型, 条.点, 条.内容].join('｜')
        }).join('\n')
      }
    },
    // 剧本真库行 → 剧本库（正文/场们/档案/状态；命中缺按档案是否有值重算）
    async 取剧本() {
      this.剧本库 = {}
      if (!this.剧id) return
      const 数据 = await 取('/api/剧本/列表?剧id=' + this.剧id)
      const 行们 = (数据 && 数据.剧本们) || []
      const 库 = {}
      行们.forEach(function (行) {
        const 档案 = 文本转档案({
          能力档案: 行.能力档案, 世界状态: 行.世界状态,
          关系网络: 行.关系网络, 记忆回廊: 行.记忆回廊, 行动推荐: 行.行动推荐
        })
        const 命中 = []
        const 缺 = []
        档案块们.forEach(function (块) {
          const 值 = 档案[块.键]
          const 有值 = 块.型 === '列表'
            ? !!(值 || []).length
            : Object.keys(值 || {}).some(function (k) { return String(值[k] || '').trim() })
          ;(有值 ? 命中 : 缺).push(块.键)
        })
        库[行.集号] = {
          正文: 行.正文 || '',
          场们: (行.场次们 || []).map(function (场) {
            return { 场: 场.场, 地点: 场.地点, 人物: 场.人物, 道具: 场.道具, 正文: 场.正文 || [] }
          }),
          档案: 档案,
          余文: {},
          命中: 命中,
          缺: 缺,
          状态: 行.状态 || '待复核',
          时间: 行.更新时间 || ''
        }
      })
      this.剧本库 = 库
    },
    // 页面一集剧本 → 库行（档案铺回键值/列表行文本，场次并成行）
    集转剧本行(集号) {
      const 剧 = this.剧本库[集号]
      if (!剧) return null
      const 档 = 剧档案转文本(剧.档案)
      const 集 = this.目录表.filter(function (项) { return 项.集 === 集号 })[0]
      return {
        集号: 集号,
        标题: (集 && 集.标题) || '',
        正文: 剧.正文 || '',
        能力档案: 档['能力档案'],
        世界状态: 档['世界状态'],
        关系网络: 档['关系网络'],
        记忆回廊: 档['记忆回廊'],
        行动推荐: 档['行动推荐'],
        状态: 剧.状态 || '待复核',
        场们: (剧.场们 || []).map(function (场) {
          return { 场: 场.场, 地点: 场.地点, 人物: 场.人物, 道具: 场.道具, 正文: 场.正文 || [] }
        })
      }
    },
    // 单集落库（写入预览/编辑场次/删除场次/标记复核后即时调）。
    // 注意后端 /api/剧本/保存 是「删除本次未传集」的全量替换语义：只传一集会把其他集整行删掉，
    // 所以这里必须走 存全库() 把全部已生成集一起传。返回是否落库成功，调用方据此决定提示与计数。
    async 存本集(集号) {
      const 行 = this.集转剧本行(集号)
      if (!行) return false
      try {
        await this.存全库()
        return true
      } catch (e) {
        this.$message.error('第 ' + 集号 + ' 集落库失败：' + ((e && e.message) || e))
        return false
      }
    },
    // 全量落库（顶部保存 / 保存并继续）
    async 存全库() {
      const 页 = this
      const 集们 = this.排序表
        .map(function (集) { return 页.集转剧本行(集.集) })
        .filter(Boolean)
      if (!集们.length) return
      await 发('/api/剧本/保存', { 剧id: this.剧id, 集们: 集们 })
    },
    // 【人物变化】→ 追加进人物档案的时间轴分段（库文本层直接补「第N集：内容」），全量落库
    // /api/人物/保存。返回应用的条数；落库失败只提示，不影响本集剧本。
    async 落人物变化(集号, 变化们) {
      const 行们 = this.人物行们
      if (!行们.length || !变化们 || !变化们.length) return 0
      let 应用了 = 0
      const 页 = this
      变化们.forEach(function (条) {
        const 名 = String(条.名 || '').trim()
        const 列 = 变化字段映射[String(条.字段 || '').trim()]
        let 文 = String(条.内容 || '').trim()
        if (!名 || !列 || !文 || 文 === '无') return
        const 行 = 行们.filter(function (r) { return String(r.名 || '').trim() === 名 })[0]
        if (!行) return
        // 内容没带集数头（「第N集/第N-M集/第N集起」，含不带「第」的写法）就自动补上本集的
        if (/^第\s*\d/.test(文)) { /* 已带「第N」头 */ } else if (/^\d+\s*(?:[-–—~～至到]\s*\d+\s*)?集/.test(文)) { 文 = '第' + 文 } else { 文 = '第' + 集号 + '集：' + 文 }
        const 旧 = String(行[列] || '').trim()
        行[列] = 旧 ? 旧 + '；' + 文 : 文
        应用了++
      })
      if (!应用了) return 0
      try {
        await 发('/api/人物/保存', { 剧id: 页.剧id, 人物们: 页.人物行们 })
        // 重建 角色们：下一集引入的人物状态（按集取段）拿到的就是刚写进去的新段
        页.角色们 = 页.人物行们.map(function (行, 序) { return 页.库转角色(行, 序) })
        return 应用了
      } catch (e) {
        页.$message.warning('人物档案更新失败（不影响本集剧本）：' + ((e && e.message) || e))
        return 0
      }
    },
    // 写完一集，把字数 / 状态回写到分集目录（内存 + 落分集表），两个页面不会各说一套
    async 同步目录(集号) {
      const 集 = this.目录表.filter(function (项) { return 项.集 === 集号 })[0]
      if (!集) return
      const 剧 = this.剧本库[集号]
      if (剧) {
        集.字数 = 数字数(剧.正文)
        集.状态 = '已完成'
      }
      try {
        await 发('/api/分集/保存', { 剧id: this.剧id, 分集们: this.排序表.map(集 => this.集转库(集)) })
      } catch (e) {
        /* 目录回写失败不影响本页，下次同步会再写 */
      }
    },

    /* ---------------- 首次进页：逐集自动生成 ---------------- */
    // 库里一集剧本都没有且目录已有：按目录逐集串行生成，每集生成完立即落库
    async 首次生成() {
      if (!this.扩写技能id && this.技能列表.length) this.扩写技能id = 适配技能id(this.技能列表, this.页配置类型)
      if (!this.扩写技能id) {
        this.$message.warning('还没有可用技能（剧本创作分类为空），先去「技能」里建一个再进本页')
        return
      }
      this.自动生成中 = true
      const 集序 = this.排序表
      const 总数 = 集序.length
      let 成功 = 0
      const 失败们 = []
      try {
        // 用户改过引导提示词但没带档案格式时自动补（同 生成本集 的口径）
        let 规则 = this.技能引导 || this.默认引导
        if (规则.indexOf('【能力档案】') < 0) 规则 = 规则 + '\n\n' + 档案格式规则
        else if (规则.indexOf('【人物变化】') < 0) 规则 = 规则 + '\n\n' + 人物变化格式规则
        for (let i = 0; i < 集序.length; i++) {
          const 目标 = 集序[i].集
          // 参考块（人物状态/上一集/本集大纲）都按本集取值，先把当前集切过去
          this.当前集 = 目标
          this.自动进度 = Math.round((i / 总数) * 90)
          this.自动文案 = '正在生成第 ' + 目标 + ' 集剧本（' + (i + 1) + '/' + 总数 + '）…'
          try {
            const 参考 = this.参考块()
            const 需求 = (参考 ? [参考, ''] : []).concat([
              '剧名：' + this.剧名,
              '集数：' + this.集数 + ' 集',
              '题材：' + this.题材,
              '要生成的内容：第 ' + 目标 + ' 集「' + (this.当前目录 ? this.当前目录.标题 : '') + '」的分集剧本',
              '要求：按本集大纲和人物列表直接产出一版'
            ]).join('\n')
            const 文本 = await 提交AI任务({ 技能id: this.扩写技能id, 系统: 规则, 正向: 需求 })
            const 果 = 解析生成结果(文本)
            if (!果.正文) throw new Error('没认出【正文】块')
            果.状态 = '待复核'
            果.时间 = 现在()
            this.$set(this.剧本库, 目标, 果)
            if (await this.存本集(目标)) {
              await this.落人物变化(目标, 果.人物变化 || [])
              await this.同步目录(目标)
              成功++
            } else {
              失败们.push('第 ' + 目标 + ' 集：落库失败')
            }
          } catch (e) {
            失败们.push('第 ' + 目标 + ' 集：' + ((e && e.message) || e))
          }
        }
        this.自动进度 = 100
        if (失败们.length) {
          this.$message.warning('生成完成：成功 ' + 成功 + ' 集，失败 ' + 失败们.length + ' 集（' + 失败们.join('；') + '）')
        } else {
          this.$message.success('已生成全剧 ' + 成功 + ' 集剧本并保存')
        }
      } finally {
        this.自动生成中 = false
      }
    },

    /* ---------------- 引入数据 ---------------- */
    造引入数据(勾) {
      const 项们 = [
        { 键: '标题', 名: '标题（剧名）', 值: this.剧名 },
        {
          键: '创意', 名: '一句话创意', 值: this.创意文本, 可编辑: true,
          提示: '从新建剧本带过来的；没带过来就在这里补，会记住',
          占位: '例：重生教师带三个学生考过毕业考核，一边藏身份一边带她们成长'
        },
        { 键: '方案', 名: '已选方案（' + this.方案卡名 + '）', 值: this.已选方案文本() }
      ]
      方案分区.forEach(区 => {
        项们.push({ 键: 区.键, 名: 区.名, 值: this.方案分区文本(区) })
      })
      // 人物列表 + 场景道具：写台词和场次头时的唯一人名 / 地名来源。
      // 人物状态按「本集」取：写第 9 集就用第 9 集的身份/态度/情感，不会拿第 1 集的人来写
      项们.push({
        键: '人物列表',
        名: '人物列表（来自人物设定 · 第 ' + this.当前集 + ' 集时的状态）',
        值: this.人物列表文本(this.当前集, this.总集),
        提示: '竖线分隔：角色名｜关系｜性别｜年龄｜简介｜身份｜性格｜态度｜外貌｜穿搭｜身体情况｜情感情况｜精神情况｜当前状态｜内心想法｜技能｜核心目标｜关系网｜台词风格｜口头禅；会随剧情变的字段已经是本集的取值'
      })
      项们.push({
        键: '场景道具', 名: '场景与道具（来自人物设定）', 值: this.场景道具文本(),
        提示: '场次头的「地点」和「出场道具」优先从这里取'
      })
      // 分集目录：全剧结构 + 本集前后几集的完整梗概
      项们.push({
        键: '分集目录', 名: '分集目录（全剧结构 + 本集前后）', 值: this.分集目录文本(),
        提示: '保证前后集接得上；集数多时只展开本集前后 3 集'
      })
      项们.push({
        键: '前情档案', 名: '前情状态（上一集档案 · 逐集滚动）', 值: this.前情档案文本(),
        提示: '只带上 1~2 集：上一集完整五大档案 + 上二集记忆回廊；新集的世界状态/记忆/预告都照它推进'
      })
      项们.push({
        键: '上一集', 名: '上一集剧本（第 ' + (this.当前集 - 1) + ' 集）', 值: this.上一集文本(),
        提示: '写「前情提要」和「记忆回廊」用'
      })
      项们.push({ 键: '本集大纲', 名: '本集大纲（第 ' + this.当前集 + ' 集）', 值: this.本集大纲文本() })
      // null/undefined = 没配过，默认全选；[] = 用户点过「全不选」，要尊重
      for (let i = 0; i < 项们.length; i++) {
        项们[i].勾选 = 勾 == null ? true : 勾.indexOf(项们[i].键) >= 0
      }
      // 前情状态是逐集滚动生成的命脉：强制引入，旧配置里没这个键也不会被漏掉
      项们.forEach(function (项) { if (项.键 === '前情档案') 项.勾选 = true })
      return 项们
    },
    已选方案文本() {
      const 方案 = this.方案卡
      if (!方案) return ''
      return [
        '方案标题：' + (方案.标题 || ''),
        '故事线：' + (方案.故事线 || ''),
        '推荐题材：' + (方案.题材 || ''),
        '基调：' + (方案.基调 || ''),
        '结局类型：' + (方案.结局 || ''),
        '核心驱动：' + (方案.驱动 || ''),
        '风险展示：' + (方案.风险 || '')
      ].join('\n')
    },
    // 方案详情五分区真库内容 → 文本（同分集目录页口径）
    方案分区文本(区) {
      const 值 = this.方案分区值[区.库列 || 区.键]
      if (值 == null) return ''
      if (区.型 === '键值') {
        return (值 || []).map(条 => 条.键 + '：' + 条.值).join('\n')
      }
      if (区.型 === '表格') {
        return (值 || []).map(行 => (区.列 || []).map(k => 行[k] || '').join('｜')).join('\n')
      }
      if (区.型 === '嵌套') {
        const 卖 = 值 || {}
        const 行们 = ['爽点兑现：']
        ;(卖.爽点兑现 || []).forEach(条 => 行们.push('- ' + 条))
        行们.push('反派压力：')
        ;(卖.反派压力 || []).forEach(条 => 行们.push('- ' + 条))
        return 行们.join('\n')
      }
      return ''
    },
    // 人物设定真库角色列表：带本集的分段状态（写第 9 集就给第 9 集的身份/态度/情感）
    人物列表文本(集, 总集) {
      const 列 = ['身份', '性格', '态度', '外貌', '穿搭', '身体情况', '情感情况', '精神情况', '当前状态', '内心想法', '技能', '核心目标', '关系网', '台词风格', '口头禅']
      const 头 = 集 ? '角色名（第' + 集 + '集时的状态）' : '角色名'
      const 行们 = [[头, '关系', '性别', '年龄', '一句话简介'].concat(列).join('｜')]
      this.角色们.forEach(人 => {
        if (String(人.资产ID || '').indexOf('CHAR_') !== 0) return
        行们.push([人.名, 人.关系, 人.性别, 人.年龄, 人.简介]
          .concat(列.map(function (键) { return 值文本(人.详[键], 总集, 集) || '' }))
          .join('｜'))
      })
      return 行们.join('\n')
    },
    // 场景与道具：写场次时「地点」「出场道具」两个字段直接从这里取
    场景道具文本() {
      const 场 = []
      const 道 = []
      this.角色们.forEach(项 => {
        const 号 = String(项.资产ID || '')
        if (号.indexOf('SCR_') === 0) 场.push(项.名 + '｜' + (项.简介 || ''))
        if (号.indexOf('PROP_') === 0) 道.push(项.名 + '｜' + (项.简介 || ''))
      })
      return ['【场景】'].concat(场, ['【道具】'], 道).join('\n')
    },
    分集目录文本() {
      const 表 = this.排序表
      if (!表.length) return ''
      const 行们 = ['全剧结构：']
      const 幕序 = []
      const 幕表 = {}
      表.forEach(function (集) {
        const 名 = 集.幕 || '未分幕'
        if (!幕表[名]) { 幕表[名] = []; 幕序.push(名) }
        幕表[名].push(集)
      })
      幕序.forEach(function (名) {
        const 组 = 幕表[名]
        行们.push('· ' + 名 + '：EP' + 组[0].集 + '–EP' + 组[组.length - 1].集 + '（' + 组.length + ' 集）')
      })
      // 集数多的时候只展开本集前后 3 集，不然 1000 集会撑爆提示词
      const 起 = Math.max(1, this.当前集 - 3)
      const 止 = Math.min(表[表.length - 1].集, this.当前集 + 3)
      const 邻 = 表.filter(function (集) { return 集.集 >= 起 && 集.集 <= 止 })
      行们.push('', 'EP' + 起 + '–EP' + 止 + ' 的分集大纲：')
      邻.forEach(function (集) {
        const 标 = []
        if (集.关键) 标.push('关键')
        if (集.卡点) 标.push('付费卡点')
        行们.push('EP' + 集.集 + '｜' + (集.幕 || '') + '｜' + (集.标题 || '') + (标.length ? '｜' + 标.join('/') : ''))
        行们.push('  梗概：' + (集.梗概 || '—'))
        行们.push('  开场钩子：' + (集.钩子 || '—'))
        行们.push('  尾钩：' + (集.尾钩 || '—'))
      })
      return 行们.join('\n')
    },
    上一集文本() {
      const 号 = this.当前集 - 1
      if (号 < 1) return '（首集，无前情）'
      const 剧 = this.剧本库[号]
      if (!剧 || !剧.正文) return '（第 ' + 号 + ' 集还没有剧本，本集按目录大纲独立写）'
      const 文 = String(剧.正文)
      return '第 ' + 号 + ' 集正文' + (文.length > 1500 ? '（节选前 1500 字）' : '') + '：\n' +
        (文.length > 1500 ? 文.slice(0, 1500) : 文)
    },
    // 前情状态：滚动窗口只带上 1~2 集，绝不把前面所有集都塞进提示词（100 集也会撑爆）。
    // 上一集带完整五大档案（新集的状态面板就照着它推进），上二集只带【记忆回廊】帮短期记忆滚动。
    // 首次逐集生成时上一集刚落库就在 剧本库 里，所以第 2 集起每集都能拿到真前情。
    前情档案文本() {
      const 号 = this.当前集 - 1
      if (号 < 1) return '（首集，无前情状态；五大档案按本集剧情从零建立）'
      const 上集 = this.剧本库[号]
      if (!上集 || !上集.档案) return '（第 ' + 号 + ' 集还没有剧本档案，本集档案按本集剧情从零建立）'
      const 文本 = 剧档案转文本(上集.档案)
      const 有货 = 档案块们.some(function (块) { return String(文本[块.键] || '').trim() })
      if (!有货) return '（第 ' + 号 + ' 集剧本档案为空，本集档案按本集剧情从零建立）'
      const 行们 = [
        '第 ' + 号 + ' 集结束时的状态（本集五大档案必须在它的基础上推进，不许从零另起）：',
        '【能力档案】', 文本['能力档案'] || '（空）',
        '【世界状态】', 文本['世界状态'] || '（空）',
        '【关系网络】', 文本['关系网络'] || '（空）',
        '【记忆回廊】', 文本['记忆回廊'] || '（空）',
        '【行动推荐】', 文本['行动推荐'] || '（空）'
      ]
      const 上二集 = this.剧本库[号 - 1]
      if (上二集 && 上二集.档案) {
        const 回廊 = String(剧档案转文本(上二集.档案)['记忆回廊'] || '').trim()
        if (回廊) 行们.push('【上二集（第 ' + (号 - 1) + ' 集）记忆回廊 · 供短期记忆滚动参考】', 回廊)
      }
      return 行们.join('\n')
    },
    本集大纲文本() {
      const 集 = this.当前目录
      if (!集) return ''
      const 行们 = [
        '第 ' + 集.集 + ' 集：' + (集.标题 || ''),
        '幕：' + (集.幕 || '未分幕'),
        '梗概：' + (集.梗概 || ''),
        '出场人物：' + ((集.出场 || []).join('、') || '—'),
        '开场钩子：' + (集.钩子 || '—'),
        '尾钩（本集必须卡在这里）：' + (集.尾钩 || '—'),
        '中心句：' + (集.中心句 || '—'),
        '目标字数：' + (集.目标 || 集.字数 || '—') + ' 字',
        '情绪分：' + (集.情绪分 || '—') + '/5'
      ]
      const 点位 = 集.点位 || []
      if (点位.length) {
        行们.push('本集钩子点位：')
        点位.forEach(function (点) {
          行们.push('· ' + 点.类型 + ' ' + 点.点 + '：' + 点.内容)
        })
      }
      return 行们.join('\n')
    },
    参考块() {
      const 项们 = this.造引入数据(this.引入勾选)
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

    /* ---------------- 技能配置（本页一份） ---------------- */
    async 载入本页配置() {
      const 类型 = this.页配置类型
      this.技能引导 = ''
      this.引入勾选 = null
      this.扩写技能id = 适配技能id(this.技能列表, this.页配置类型)
      try {
        const 引导 = await 读引导(类型)
        if (引导) this.技能引导 = 引导
        const 技能 = 读技能id(类型)
        if (技能) this.扩写技能id = 技能
        this.引入勾选 = 读引入(类型)
      } catch (e) {
        /* 拉不到就用默认规则 */
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
        if (引入[i].键 === '创意') {
          this.创意文本 = 引入[i].值 || ''
          存创意(this.剧名, this.创意文本)
        }
        if (引入[i].勾选) 勾.push(引入[i].键)
      }
      this.引入勾选 = 勾
      存引入(类型, 勾)
      if (值 && 值.引导) this.技能引导 = 值.引导
    },

    /* ---------------- AI 生成这一集 ---------------- */
    async 生成本集() {
      if (this.扩写中) return
      if (!this.扩写技能id) {
        this.$message.warning('请先在「技能」里选一个技能')
        return
      }
      const 参考 = this.参考块()
      const 需求 = (参考 ? [参考, ''] : []).concat([
        '剧名：' + this.剧名,
        '集数：' + this.集数 + ' 集',
        '题材：' + this.题材,
        '要生成的内容：第 ' + this.当前集 + ' 集「' + (this.当前目录 ? this.当前目录.标题 : '') + '」的分集剧本',
        '要求：' + (this.扩写需求.trim() || '按本集大纲和人物列表直接产出一版')
      ]).join('\n')

      this.扩写中 = true
      try {
        // 用户在「技能」里改过引导提示词时，只要那份里没有【能力档案】，
        // 就自动把格式要求补在后面，否则 AI 只出正文，5 个档案块永远空着。
        let 规则 = this.技能引导 || this.默认引导
        if (规则.indexOf('【能力档案】') < 0) 规则 = 规则 + '\n\n' + 档案格式规则
        else if (规则.indexOf('【人物变化】') < 0) 规则 = 规则 + '\n\n' + 人物变化格式规则
        // 统一任务链路（T1 文本回复）：任务落 task 表，测试台任务列表可见
        const 文本 = String(await 提交AI任务({ 技能id: this.扩写技能id, 系统: 规则, 正向: 需求 }) || '').trim()
        if (!文本) {
          this.$message.warning('AI 没有返回内容，可稍后重试')
          return
        }
        this.生成结果 = 文本
        this.预览 = 解析生成结果(文本)
        this.看原文 = false
        // 先停在预览态，由用户点「写入」才落库覆盖（与页面文案一致）
        this.$message.success('已生成第 ' + this.当前集 + ' 集解析结果，确认无误后点「写入第 ' + this.当前集 + ' 集」落库')
      } catch (e) {
        this.扩写报错(e)
      } finally {
        this.扩写中 = false
      }
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
      if (!this.预览) return
      const 集号 = this.当前集
      const 变化们 = this.预览.人物变化 || []
      const 剧 = {
        正文: this.预览.正文,
        场们: this.预览.场们,
        档案: this.预览.档案,
        余文: this.预览.余文 || {},
        命中: this.预览.命中,
        缺: this.预览.缺,
        状态: '待复核',
        时间: 现在()
      }
      this.$set(this.剧本库, 集号, 剧)
      this.预览 = null
      this.看原文 = false
      this.生成结果 = ''
      if (!(await this.存本集(集号))) return
      const 变条 = await this.落人物变化(集号, 变化们)
      await this.同步目录(集号)
      this.$message.success('已写入第 ' + 集号 + ' 集（已落库），状态：待复核' +
        (变条 ? '；人物档案已更新 ' + 变条 + ' 条' : ''))
    },
    async 保存() {
      try {
        await this.存全库()
        this.$message({ message: '已保存「分集剧本」到数据库', type: 'success' })
      } catch (e) {
        this.$message.error('保存失败：' + ((e && e.message) || e))
      }
    },
    async 标记复核() {
      const 剧 = this.当前剧
      if (!剧) return
      this.$set(this.剧本库, this.当前集, Object.assign({}, 剧, { 状态: '已复核' }))
      if (!(await this.存本集(this.当前集))) return
      this.$message.success('第 ' + this.当前集 + ' 集已标记为已复核')
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
      if (!this.当前剧) {
        this.$message.warning('这一集还没生成剧本')
        return
      }
      this.全文显示 = true
    },
    加意见(句) {
      const 现 = this.扩写需求
      if (现.indexOf(句) >= 0) {
        this.扩写需求 = 现.replace(句, '').replace(/[，,]\s*[，,]/g, '，').replace(/^[，,\s]+|[，,\s]+$/g, '')
        return
      }
      this.扩写需求 = 现 ? 现.replace(/[，,\s]+$/, '') + '，' + 句 : 句
    },

    /* ---------------- 场次编辑 / 新增 ---------------- */
    打开编辑场(场, 序) {
      if (!场) return
      this.新增模式 = false
      this.编辑对象 = 场
      this.编辑序 = 序
      this.草稿 = {
        场: 场.场, 地点: 场.地点, 人物: 场.人物,
        道具: 场.道具 || '',
        正文: (场.正文 || []).join('\n')
      }
      this.编辑显示 = true
    },
    新增一场() {
      if (!this.当前剧) {
        this.$message.warning('这一集还没生成剧本，先让 AI 出一版再改')
        return
      }
      const 场们 = this.当前剧.场们 || []
      this.新增模式 = true
      this.编辑对象 = null
      this.编辑序 = -1
      this.草稿 = {
        场: this.当前集 + '-' + (场们.length + 1),
        地点: '内 · ',
        人物: '',
        道具: '',
        正文: ''
      }
      this.编辑显示 = true
    },
    async 保存这一场() {
      const 剧 = this.当前剧
      if (!剧) return
      const 正文行 = String(this.草稿.正文 || '')
        .split(/\r?\n/)
        .map(s => s.trim())
        .filter(s => s)
      const 条 = {
        场: (this.草稿.场 || '').trim(),
        地点: (this.草稿.地点 || '').trim(),
        人物: (this.草稿.人物 || '').trim(),
        道具: (this.草稿.道具 || '').trim(),
        正文: 正文行
      }
      if (!条.场) {
        this.$message.warning('先填场次号')
        return
      }
      const 场们 = (剧.场们 || []).slice()
      if (this.新增模式) {
        场们.push(条)
      } else {
        const 位 = 场们.indexOf(this.编辑对象)
        if (位 < 0) {
          this.编辑显示 = false
          return
        }
        场们[位] = 条
      }
      this.$set(this.剧本库, this.当前集, Object.assign({}, 剧, {
        场们: 场们,
        正文: 拼正文(场们),
        状态: '待复核'
      }))
      this.编辑显示 = false
      if (!(await this.存本集(this.当前集))) return
      await this.同步目录(this.当前集)
      this.$message.success(this.新增模式 ? '已加入第 ' + this.当前集 + ' 集' : '已保存 ' + 条.场)
    },
    删除这一场() {
      const 剧 = this.当前剧
      const 场 = this.编辑对象
      if (!剧 || !场) return
      const 页 = this
      this.$confirm('确定删除 ' + 场.场 + '？', '删除这一场', {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async function () {
        const 场们 = (剧.场们 || []).filter(function (项) { return 项 !== 场 })
        页.$set(页.剧本库, 页.当前集, Object.assign({}, 剧, {
          场们: 场们,
          正文: 拼正文(场们),
          状态: '待复核'
        }))
        页.编辑显示 = false
        if (!(await 页.存本集(页.当前集))) return
        await 页.同步目录(页.当前集)
        页.$message.success('已删除 ' + 场.场)
      }).catch(function () {})
    },

    /* ---------------- 列表交互 ---------------- */
    切集(号) {
      const 目标 = Number(号)
      if (!目标 || 目标 === this.当前集) return
      const 存在 = this.排序表.some(function (集) { return 集.集 === 目标 })
      if (!存在) return
      this.当前集 = 目标
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
    // 当前集不在当前页时，把它所在的页翻出来
    滚到本集(号) {
      const 位 = this.筛选后.map(function (集) { return 集.集 }).indexOf(号)
      if (位 < 0) {
        // 被搜索或筛选挡住了：放开过滤，否则用户会以为切集失败
        this.搜索 = ''
        this.状态筛 = '全部'
        const 新位 = this.排序表.map(function (集) { return 集.集 }).indexOf(号)
        this.当前页 = 新位 < 0 ? 1 : Math.floor(新位 / this.每页) + 1
        return
      }
      this.当前页 = Math.floor(位 / this.每页) + 1
    },
    集点类(集) {
      const 剧 = this.剧本库[集.集]
      if (!剧) return '未'
      return 剧.状态 === '已复核' ? '复核' : '待'
    },
    集场数(集号) {
      const 剧 = this.剧本库[集号]
      return 剧 && 剧.场们 ? 剧.场们.length : 0
    },
    async 保存并继续() {
      try {
        await this.存全库()
      } catch (e) {
        this.$message.error('保存失败：' + ((e && e.message) || e))
        return
      }
      const 下 = this.排序表.filter(集 => 集.集 > this.当前集)[0]
      if (下) {
        this.切集(下.集)
        this.$message.success('已保存，进入第 ' + 下.集 + ' 集')
      } else {
        this.$message.success('已经是最后一集，全部保存完毕')
      }
    },

    /* ---------------- 步骤跳转 ---------------- */
    去方案详情() {
      this.$router.push({
        path: '/script/detail',
        query: Object.assign({}, this.$route.query)
      })
    },
    上一步() {
      this.$router.push({
        path: '/script/outline',
        query: Object.assign({}, this.$route.query)
      })
    },
    // 点四步进度条：每一步都是独立页
    跳步骤(序) {
      if (序 < 0 || 序 >= this.步骤.length) return
      if (序 === this.当前步) {
        this.$message({ message: '当前已在「' + this.步骤[序] + '」', type: 'info' })
        return
      }
      const 路 = ['/script/plan', '/script/character', '/script/outline', '/script/episode'][序]
      this.$router.push({
        path: 路,
        query: Object.assign({}, this.$route.query, { 步: undefined })
      })
    }
  }
}
</script>

<style scoped>
/* ---- 载入态 / 首次生成遮罩 ---- */
.载入框 { text-align: center; padding: 28px 0; color: var(--字次); font-size: 13px; }
.报错框 { color: #f56c6c; }
.生成遮罩 {
  position: fixed; inset: 0; z-index: 2000;
  background: rgba(6, 14, 10, .72);
  display: flex; align-items: center; justify-content: center;
}
.生成框 {
  width: 460px; max-width: 90vw;
  background: var(--卡片); border: 1px solid var(--描边亮);
  border-radius: 12px; padding: 26px 28px 20px;
}
.生成标题 { font-size: 15px; font-weight: 600; color: var(--字); margin-bottom: 8px; }
.生成文案 { font-size: 13px; color: var(--字次); margin-bottom: 14px; }
.生成注 { font-size: 12px; color: var(--字弱); margin-top: 10px; line-height: 1.7; }

/* 四步进度条居中（与创作方案页同一形态） */
.步骤条.居中 { max-width: 720px; margin: 0 auto 24px; }

.提示卡 { margin-bottom: 16px; font-size: 13px; color: var(--字次); line-height: 1.8; }
.提示卡 b { color: var(--主); font-weight: 600; }

/* ---- 本页生成条 ---- */
.生成条 {
  background: var(--卡片二);
  border: 1px solid var(--描边);
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 16px;
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
.预览卡 { margin-bottom: 16px; }
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
.结果卡 { margin-bottom: 16px; }
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

/* ---- 左侧集数列表 ---- */
.侧栏 { align-self: start; }
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
.集列 { max-height: 620px; overflow-y: auto; padding-right: 2px; }
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

/* ---- 本集导航 ---- */
.本集导航 {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.导航中 { font-size: 12px; color: var(--字弱); }

.空场 { text-align: center; padding: 40px 0; color: var(--字弱); font-size: 13px; }

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
  .预览格 { grid-template-columns: minmax(0, 1fr); }
}
</style>
