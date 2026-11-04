<template>
  <div class="创作模块">
    <!-- 面包屑 -->
    <div class="面包屑条">
      <span class="可点" @click="$router.push('/script')">剧本创作</span>
      <span> / </span>
      <span class="可点" @click="去方案详情()">创作方案</span>
      <span> / </span>
      <span>人物设定</span>
    </div>

    <!-- 四步进度条：和创作方案页同一位置（面包屑正下方、居中），点任意一步即跳到那一步。
         本页是第 2 步「人物设定」，不再有第二套「创作方案/人物设定/…」标签栏。 -->
    <step-bar :步骤="步骤" :当前步="当前步" @切换="跳步骤($event)"></step-bar>

    <!-- 页头 -->
    <div class="页头">
      <div class="左">
        <h1 class="标题">{{ 剧名 }}</h1>
        <div class="副题">{{ 集数 }} 集 · {{ 题材 }} · 已采用 {{ 已选方案名 }}</div>
      </div>
      <div class="右">
        <el-button @click="上一步()">上一步：方案详情</el-button>
        <el-button @click="保存()">保存</el-button>
        <el-button type="primary" @click="下一步()">下一步：分集目录</el-button>
      </div>
    </div>

    <div class="卡片 提示卡">
      人物设定按已选方案产出。可点「技能」配本页技能与技能引导提示词，点「AI 生成人物设定」重出一版；也可以用「AI 新增人物」让 AI 补一个角色，或点角色卡上的「编辑」逐条改。
      首次进入（库里还没有人物）会自动生成全部角色与关系网并落库；再次进入直接读取数据库内容。
    </div>

    <!-- 载入中 / 载入报错 -->
    <div v-if="载入中" class="提示卡" style="text-align:center;padding:48px 0;color:var(--字弱)">
      <i class="el-icon-loading" style="font-size:26px;color:var(--主)"></i>
      <div style="margin-top:10px;font-size:13px">正在读取剧、方案与人物设定…</div>
    </div>
    <div v-else-if="载入报错" class="提示卡" style="text-align:center;padding:40px 0">
      <div style="color:#ef4444;font-size:13px;margin-bottom:12px">{{ 载入报错 }}</div>
      <el-button size="mini" @click="载入()">重试</el-button>
    </div>

    <template v-else>
    <!-- 首次自动生成进度遮罩 -->
    <div v-if="自动生成中" class="生成遮罩">
      <div class="生成框">
        <div class="生成标题">首次生成人物设定</div>
        <el-progress :percentage="自动进度" :stroke-width="8"></el-progress>
        <div class="生成注">{{ 自动文案 }}</div>
      </div>
    </div>

    <!-- 本页生成：⚙技能（弹窗里配 技能 + 技能引导提示词 + 引入数据）+ AI 生成人物设定 -->
    <div class="生成条">
      <div class="行间">
        <div class="行间">
          <div class="AI标">AI</div>
          <div>
            <div class="意见标题">生成人物设定</div>
            <div class="意见价">0.2 积分/次</div>
          </div>
        </div>
        <div style="flex:1"></div>
        <div class="意见例如">例：再加一个反派教务处主任、女主更主动…</div>
        <el-button size="mini" icon="el-icon-setting" @click="打开技能()">技能</el-button>
        <el-button size="mini" type="primary" plain :loading="扩写中" @click="生成人物设定()">
          AI 生成人物设定
        </el-button>
      </div>
      <el-input
        v-model="扩写需求"
        type="textarea"
        :rows="2"
        class="意见输入"
        placeholder="写一句要求，AI 按这句话重写人物设定（不写就按方案直接产出一版）"></el-input>
    </div>

    <!-- 生成结果：AI 返回的原文摊在这里，可解析入库 / 复制 / 清空 -->
    <div v-if="生成结果" class="卡片 结果卡">
      <div class="行间" style="margin-bottom:10px">
        <div class="结果标题">生成结果 · 人物设定</div>
        <div style="flex:1"></div>
        <el-button type="text" size="mini" @click="解析入表()">解析入角色表</el-button>
        <el-button type="text" size="mini" @click="复制生成结果()">复制</el-button>
        <el-button type="text" size="mini" @click="生成结果 = ''">清空</el-button>
        <el-button type="text" size="mini" @click="保存()">保存本页</el-button>
      </div>
      <pre class="原文">{{ 生成结果 }}</pre>
    </div>

    <!-- ============ 角色列表 / 关系网 ============ -->
    <!-- 列表工具条：两个视图（角色卡 / 关系网），工具按钮跟着视图换 -->
    <div class="列表工具">
      <div class="标签组">
        <button class="项" :class="{ 当前: 视图 === '角色卡' }" @click="视图 = '角色卡'">
          角色卡 {{ 角色数 }}
        </button>
        <button class="项" :class="{ 当前: 视图 === '关系网' }" @click="视图 = '关系网'">
          关系网 {{ 关系表.length }}
        </button>
      </div>
      <div class="工具数">
        {{ 视图 === '角色卡' ? '点卡片选中后可编辑，也可以让 AI 直接补一个' : '一条边 = 两个人之间的关系，可单独改、单独删' }}
      </div>
      <!-- 按集查看：会随剧情变的字段（身份/态度/情感…）按集数高亮，看「第 N 集时他是什么样」 -->
      <div class="集游标">
        <span class="集游标标">按集看</span>
        <el-select v-model="查看集" size="mini" style="width:108px">
          <el-option :value="0" label="全集"></el-option>
          <el-option v-for="n in 总集" :key="'看' + n" :value="n" :label="'第 ' + n + ' 集'"></el-option>
        </el-select>
      </div>
      <div style="flex:1"></div>
      <template v-if="视图 === '角色卡'">
        <el-button size="mini" icon="el-icon-edit" :disabled="!选中角色" @click="$refs.角色编辑弹窗.打开编辑(选中角色)">
          编辑选中
        </el-button>
        <el-button size="mini" icon="el-icon-plus" @click="$refs.角色编辑弹窗.打开新增()">手动新增</el-button>
        <el-button size="mini" type="primary" plain icon="el-icon-magic-stick" @click="$refs.AI新增人物弹窗.打开AI新增()">
          AI 新增人物
        </el-button>
      </template>
      <template v-else>
        <el-button size="mini" icon="el-icon-plus" @click="$refs.关系编辑弹窗.打开新增关系()">新增关系</el-button>
        <el-button size="mini" type="primary" plain icon="el-icon-magic-stick" :loading="关系中" @click="生成关系网()">
          AI 补关系网
        </el-button>
      </template>
    </div>

    <!-- ---------- 视图一：角色卡 ---------- -->
    <div v-if="视图 === '角色卡'">
      <div v-for="组 in 分组后" :key="组.名" class="角色组">
        <div class="组头">
          <span class="组名">{{ 组.名 }}</span>
          <span class="组数">· 共 {{ 组.数 }} 项</span>
        </div>
        <div class="网格 三">
          <div
            v-for="人 in 组.项"
            :key="人.id"
            class="角色卡"
            :class="{ 选中: 选中角色 && 选中角色.id === 人.id }"
            @click="选中角色 = 人">
            <div class="行间" style="margin-bottom:10px">
              <div class="头像" :style="{ background: 人.色 || '#334155' }">{{ 首字(人.名) }}</div>
              <div style="min-width:0">
                <div class="角色名">{{ 人.名 }}</div>
                <div class="角色副">{{ 人.性别 }} · {{ 人.年龄 }}</div>
              </div>
              <div style="flex:1"></div>
              <span class="小标签">{{ 人.关系 }}</span>
            </div>
            <div class="角色简介">{{ 人.简介 }}</div>
            <div class="行间" style="margin-top:12px">
              <span class="小标签 灰">{{ 人.资产ID }}</span>
              <span v-if="角色变化数(人)" class="小标签 变化标">随集变 {{ 角色变化数(人) }}</span>
              <span v-if="人.来源 === 'AI新增' || 人.来源 === '手动新增'" class="小标签 新增标">{{ 人.来源 }}</span>
              <div style="flex:1"></div>
              <el-button size="mini" icon="el-icon-edit" @click.stop="$refs.角色编辑弹窗.打开编辑(人)">编辑</el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ---------- 视图二：关系网 ---------- -->
    <div v-else>
      <!-- 按角色筛：点一个人，只看跟他有关的边 -->
      <div class="关系筛">
        <button
          v-for="名 in 关系角色们"
          :key="'筛' + 名"
          class="chip"
          :class="{ 选中: 关系筛选 === 名 }"
          @click="关系筛选 = 名">{{ 名 }}</button>
      </div>

      <!-- AI 补的关系网：先勾选，点写入才进列表 -->
      <div v-if="关系预览.length" class="卡片 关系预览">
        <div class="预览头">
          <span class="预览题">AI 补的关系网 · {{ 关系预览.length }} 条</span>
          <span class="预览注">勾上的才写进去；已有同一条边的自动跳过</span>
          <div style="flex:1"></div>
          <el-button type="text" size="mini" @click="关系预览 = []">关闭</el-button>
        </div>
        <div v-for="(条, 序) in 关系预览" :key="'预' + 序" class="预览行">
          <el-checkbox v-model="条.勾选" :disabled="条.重复"></el-checkbox>
          <span class="预览边">{{ 条.甲 }} ↔ {{ 条.乙 }}</span>
          <span
            class="关系类型"
            :style="{ color: 关系类型色(条.类型), borderColor: 关系类型色(条.类型) }">{{ 条.类型 }}</span>
          <span class="预览文">{{ 条.说明 }}<span v-if="条.阶段 && 条.阶段.length" class="预览重">按集拆成 {{ 条.阶段.length }} 段</span><span v-if="条.重复" class="预览重">已有同一条边，跳过</span></span>
        </div>
        <div class="行间 右" style="margin-top:10px">
          <el-button size="small" @click="关系预览 = []">取消</el-button>
          <el-button size="small" type="primary" @click="写入关系()">写入勾选的 {{ 关系勾选数 }} 条</el-button>
        </div>
      </div>

      <div v-if="关系筛选后.length" class="关系列">
        <div v-for="边 in 关系筛选后" :key="'边' + 边.id" class="卡片 关系卡">
          <div class="关系头">
            <span class="关系人">{{ 边.甲 }}</span>
            <span class="关系连">↔</span>
            <span class="关系人">{{ 边.乙 }}</span>
            <span
              class="关系类型"
              :style="{ color: 关系类型色(关系类型显示(边)), borderColor: 关系类型色(关系类型显示(边)) }">{{ 关系类型显示(边) }}</span>
            <span v-if="关系阶段(边).length > 1" class="小标签 变化标">
              随集变 {{ 关系阶段(边).length }} 段
            </span>
            <div style="flex:1"></div>
            <el-button size="mini" icon="el-icon-edit" @click="$refs.关系编辑弹窗.打开编辑关系(边)">编辑</el-button>
          </div>
          <div v-if="边.关键词 && 边.关键词.length" class="关系词">
            <span v-for="(词, 序) in 边.关键词" :key="'词' + 序" class="词">{{ 词 }}</span>
          </div>
          <!-- 关系会变：按集铺成时间轴，第几集从什么变成什么一目了然 -->
          <div v-if="关系阶段(边).length" class="阶段列">
            <div
              v-for="(段, 序) in 关系阶段(边)"
              :key="'阶' + 序"
              class="阶段行"
              :class="{ 本集: 段本集(段), 淡: 查看集 > 0 && !段本集(段) }">
              <span class="段标">{{ 集标(段) }}</span>
              <span
                v-if="段.类型"
                class="阶段类型"
                :style="{ color: 关系类型色(段.类型), borderColor: 关系类型色(段.类型) }">{{ 段.类型 }}</span>
              <span class="阶段说">{{ 段.说明 }}</span>
            </div>
          </div>
          <div v-else class="关系说">{{ 关系说明显示(边) }}</div>
        </div>
      </div>

      <div v-else class="空态">
        <div class="大">{{ 关系筛选 === '全部' ? '还没有人物关系' : 关系筛选 + ' 还没有关系记录' }}</div>
        点右上「新增关系」手写一条，或「AI 补关系网」让 AI 按现有角色补一遍
      </div>
    </div>

    <!-- ============ 角色详情：选中一张卡展开全部字段（按 字段分组 铺，缺的显示 —） ============
         会随集数变的字段不铺成一句话，而是铺成「第1-5集 / 第6-8集」的时间轴，
         上面再压一条「随集变化」摘要，一眼看到他在第几集变成了什么样。 -->
    <div v-if="选中角色" class="卡片 详情卡">
      <div class="行间" style="margin-bottom:12px">
        <div class="详情名">{{ 选中角色.名 }}</div>
        <span class="小标签">{{ 选中角色.关系 }}</span>
        <span class="小标签 灰">{{ 选中角色.资产ID }}</span>
        <div style="flex:1"></div>
        <el-button size="mini" icon="el-icon-edit" @click="$refs.角色编辑弹窗.打开编辑(选中角色)">编辑</el-button>
        <i class="el-icon-close 关闭钮" title="收起" @click="选中角色 = null"></i>
      </div>

      <!-- 变化摘要：哪些字段变过、在第几集变 -->
      <div v-if="变化概览.length" class="变化条">
        <span class="变化标题">随集变化</span>
        <span v-for="项 in 变化概览" :key="'变' + 项.键" class="变化项">
          {{ 项.键 }}
          <span class="变化集">第 {{ 项.点们.join('、') }} 集</span>
        </span>
        <div style="flex:1"></div>
        <span class="变化注">{{ 查看集 ? '正在看第 ' + 查看集 + ' 集' : '全 ' + 总集 + ' 集' }}</span>
      </div>

      <div v-for="组 in 字段分组" :key="'详' + 组.名" class="详情组">
        <div class="详情组名">
          {{ 组.名 }}
          <span v-if="查看集" class="组集注">第 {{ 查看集 }} 集</span>
        </div>
        <div class="详情格">
          <div
            v-for="键 in 组.字段"
            :key="键"
            class="详情项"
            :class="{ 跨列: 详段(键).length > 0 }">
            <div class="详情键">{{ 键 }}</div>
            <!-- 会变的字段：一条时间轴，当前集那一段亮着，其余压暗 -->
            <div v-if="详段(键).length" class="详情值 分段">
              <div
                v-for="(段, 序) in 详段(键)"
                :key="序"
                class="段行"
                :class="{ 本集: 段本集(段), 淡: 查看集 > 0 && !段本集(段) }">
                <span class="段标">{{ 集标(段) }}</span>
                <span class="段值">{{ 段.值 || '—' }}</span>
              </div>
            </div>
            <div v-else class="详情值" :class="{ 空: !详值(键) }">{{ 详值(键) || '—' }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="行间 右" style="margin-top:20px">
      <el-button @click="去方案详情()">返回方案详情</el-button>
    </div>
    </template>

    <!-- 角色表单弹窗（已拆分为独立组件） -->
    <juese-edit-dialog
      ref="角色编辑弹窗"
      :显示.sync="编辑显示"
      :总集="总集"
      :角色表="角色表"
      :关系表="关系表"
      :选中角色.sync="选中角色"
      :关系筛选.sync="关系筛选"
      @已保存="存本地()"
      @删除="删除角色($event)"></juese-edit-dialog>

    <!-- 关系编辑弹窗（已拆分为独立组件） -->
    <guanxi-edit-dialog
      ref="关系编辑弹窗"
      :显示.sync="关系编辑显示"
      :总集="总集"
      :角色名们="角色名们"
      :关系表="关系表"
      @已保存="存本地()"></guanxi-edit-dialog>

    <!-- AI 新增人物弹窗（已拆分为独立组件） -->
    <ai-xinzeng-dialog
      ref="AI新增人物弹窗"
      :显示.sync="AI新增显示"
      :技能列表="技能列表"
      :扩写技能id="扩写技能id"
      :剧名="剧名"
      :集数="集数"
      :题材="题材"
      :创意文本="创意文本"
      :已选方案名="已选方案名"
      :已选方案文本="已选方案文本()"
      :总集="总集"
      :角色表="角色表"
      @报错="扩写报错($event)"
      @生成成功="$refs.角色编辑弹窗.填入新角色($event)"></ai-xinzeng-dialog>

    <!-- 技能生成弹窗：技能 + 技能引导提示词 + 引入数据（本页一套）。
         in-DOM 模板只认 ASCII 标签名，必须用 skill-dialog 别名（见 docs/09 第 8 节）；
         事件处理器必须带括号，否则中文方法名不会被调用（docs/09 第 1.6 节）。 -->
    <skill-dialog
      :显示.sync="技能弹窗显示"
      :技能列表="技能列表"
      :技能id.sync="扩写技能id"
      :引导.sync="技能引导"
      :默认引导="默认引导"
      :配置类型="页配置类型"
      目标名="人物设定"
      :引入数据="引入数据"
      @保存="技能已保存($event)"></skill-dialog>
  </div>
</template>

<script>
import 步骤条 from '@/共用/步骤条/index.vue'
import 技能生成弹窗 from '@/共用/技能生成弹窗/index.vue'
import 剧本页混入 from '@/共用/剧本页混入'
import 角色编辑弹窗 from './角色编辑弹窗.vue'
import 关系编辑弹窗 from './关系编辑弹窗.vue'
import AI新增人物弹窗 from './AI新增人物弹窗.vue'
import { 读引导, 读技能id, 读引入, 存引入, 读创意, 存创意, 适配技能id } from '@/共用/技能生成配置'
import { 复制到剪贴板 } from '@/共用/复制文本'
import { 发, 取 } from '@/接口/请求'
import { 提交AI任务 } from '@/共用/AI任务'
import {
  字段分组, 关系类型们, 关系色, 可分段字段,
  空角色详, 规整详, 规整段, 是分段,
  文本转值, 集标签, 值文本, 变化点,
  关系类型, 关系说明, 关系一行, 解析关系阶段, 筛关系, 是同一条边
} from '@/共用/人物工具'

// 「引入数据」里来自方案详情的五块（真库 = 方案表五个分区列），按方案详情的数据形态取文本
const 方案分区 = [
  { 键: '时空背景', 名: '时空背景', 库列: '时空背景', 型: '键值' },
  { 键: '故事线', 名: '故事线与核心冲突', 库列: '故事线', 型: '键值' },
  { 键: '爽点', 名: '爽点矩阵', 库列: '爽点矩阵', 型: '表格', 列: ['区间', '类型', '描述', '强度'] },
  { 键: '商业卖点', 名: '商业卖点', 库列: '商业卖点', 型: '嵌套' },
  { 键: '结局', 名: '结局设计', 库列: '结局设计', 型: '键值' }
]

// 一行角色的字段顺序，必须和 共用/人物工具.js 的 角色字段 对齐（姓名/性别/年龄/简介已在前面单独占位）
const 行字段 = [
  '性格', '身份', '关系', '态度', '外貌', '身材', '穿搭',
  '身体情况', '情感情况', '精神情况', '当前状态', '当前姿势', '内心想法',
  '技能', '核心目标', '关系网', '背景故事', '台词风格', '口头禅', '概括'
]

const 行格式说明 = '「角色名｜本剧关系｜性别｜年龄｜一句话简介｜' + 行字段.join('｜') + '」'

// 本页默认技能引导提示词：库里没存过这一页的配置时用它兜底
const 默认引导文本 = [
  '1. 你要写的是短剧「人物设定」，不是视频/图片提示词：禁止输出 <Picture N>、<Video N>、<Audio N> 之类标签，也不要写镜头运动、光影、音效。',
  '2. 一个角色一段，格式固定为 ' + 行格式说明 + '，中间用全角竖线 ｜ 分隔，一段一行，一共 ' + (5 + 行字段.length) + ' 段。',
  '3. 每段都要写满，不许留空：性格写行为习惯不写形容词堆砌；身份写「在哪、是谁」；关系写他和主角是什么关系；态度写他现在站哪一边；外貌/身材/穿搭要能直接拿去画；身体情况/情感情况/精神情况是当前状态；当前状态写他此刻在干什么；当前姿势写一个能定格的画面；内心想法写一句他没说出口的话。',
  '4. 会随剧情变的字段，如果这一季里有变化，必须按集分段写：第1-5集：旧状态；第6-8集：新状态；第9集起：再往后。不变化就写一句话。会随剧情变的字段是：' + 可分段字段.join('、') + '。',
  '5. 关系网这一栏写「这个人和谁是什么关系」的概述，一句写完，点名到具体角色。',
  '6. 角色名、本剧关系必须和已选方案一致，不新增方案里没有的核心角色；补充角色要说明用途。',
  '7. 只输出这些行，不要表头、不要解释、不要前后缀。'
].join('\n')

// 「AI 补关系网」的默认技能引导提示词：一行一条边
const 关系默认引导文本 = [
  '1. 你要写的是短剧「人物关系网」，不是剧情、不是人物设定。',
  '2. 一行一条边，格式固定为「甲 ↔ 乙｜类型｜关键词1、关键词2｜说明」，中间用全角竖线 ｜ 分隔。',
  '3. 甲、乙必须都来自参考数据里的现有角色名，不许新造；同一条边只写一次。',
  '4. 类型只能从这几个里选：羁绊 / 协作 / 认可 / 对立 / 利用 / 亲情。',
  '5. 关系在第几集变了，说明就按集分段写：第1-5集 协作（这一段怎么处）；第6集起 羁绊（后来怎么处）。不变就写一句话。',
  '6. 说明要写清这段关系「从什么变成什么」，20–60 字，不要空话。',
  '7. 只输出这些行，不要表头、不要编号、不要解释。'
].join('\n')

// 新角色卡的配色盘（和假数据里的暗色系一致）
const 角色色盘 = ['#3b4a63', '#35435a', '#3f4652', '#4a3b57', '#524033', '#334a45', '#3a4a52', '#2f3a4a']

// 一行文本按 ｜ 拆成字段：先认全角竖线，再退到半角 |、再退到制表符
function 拆行(文本) {
  const 行 = String(文本 || '').split(/\r?\n/).map(s => s.trim()).filter(s => s)
  for (let i = 0; i < 行.length; i++) {
    let 段 = 行[i].split('｜')
    if (段.length < 3) 段 = 行[i].split('|')
    if (段.length < 3) 段 = 行[i].split('\t')
    if (段.length >= 3) return 段.map(s => s.trim())
  }
  return []
}

export default {
  name: 'ScriptCharacter',
  mixins: [剧本页混入],
  components: {
    'step-bar': 步骤条,
    'skill-dialog': 技能生成弹窗,
    'juese-edit-dialog': 角色编辑弹窗,
    'guanxi-edit-dialog': 关系编辑弹窗,
    'ai-xinzeng-dialog': AI新增人物弹窗
  },
  created() {
    // 从别处带过来的「一句话创意」：路由有就记住，没有就用上次补的
    const 路由创意 = (this.$route.query.创意 || '').trim()
    if (路由创意) {
      this.创意文本 = 路由创意
      存创意(this.剧名, 路由创意)
    } else {
      this.创意文本 = 读创意(this.剧名)
    }
    this.载入本页配置()
    this.载入()
  },
  data() {
    return {
      // 真库数据：进页从 /api/人物/列表 读；首次为空则自动生成
      角色表: [],
      选中角色: null,
      /* 视图：角色卡 / 关系网 */
      视图: '角色卡',
      /* 按集查看：0 = 全集（铺整条时间轴），N = 高亮第 N 集那一段 */
      查看集: 0,
      /* 关系网 */
      关系表: [],
      关系筛选: '全部',
      关系预览: [],
      关系中: false,
      /* 关系编辑弹窗（显隐留父，内容在 关系编辑弹窗.vue 里） */
      关系编辑显示: false,
      /* 真库载入状态 */
      载入中: false,
      载入报错: '',
      剧id: 0,
      剧行: null,
      方案卡: null,
      方案分区值: {},
      /* 首次自动生成进度 */
      自动生成中: false,
      自动文案: '',
      自动进度: 0,
      /* 字段口径（模板里要用） */
      字段分组: 字段分组,
      关系类型们: 关系类型们,
      /* 本页生成 */
      扩写需求: '',
      生成结果: '',
      创意文本: '',
      技能弹窗显示: false,
      技能引导: '',
      引入勾选: null,
      /* 角色表单弹窗（显隐留父，内容在 角色编辑弹窗.vue 里） */
      编辑显示: false,
      /* AI 新增人物弹窗（显隐留父，内容在 AI新增人物弹窗.vue 里） */
      AI新增显示: false
    }
  },
  computed: {
    剧名() {
      return this.$route.query.剧名 || (this.剧行 && this.剧行.剧名) || ''
    },
    集数() {
      return String(this.$route.query.集数 || (this.剧行 && this.剧行.集数) || '')
    },
    /* 总集数（数字）：分阶段的止集不能超过它，集游标也按它铺 */
    总集() {
      const 数 = parseInt(this.集数, 10)
      return 数 > 0 ? 数 : 0
    },
    /* 变化概览：选中角色里哪些字段变过、在第几集变，压在详情卡顶上 */
    变化概览() {
      if (!this.选中角色) return []
      const 详 = 规整详(this.选中角色.详)
      const 出 = []
      可分段字段.forEach(function (键) {
        const 点们 = 变化点(详[键])
        if (点们.length) 出.push({ 键: 键, 点们: 点们 })
      })
      return 出
    },
    题材() {
      return this.$route.query.题材 || (this.剧行 && this.剧行.题材) || ''
    },
    // 真库方案卡：地址栏 方案=方案行 id，找不到退回 是否选定 行，再退回第一行
    当前方案() {
      return this.方案卡
    },
    已选方案名() {
      const 卡 = this.方案卡
      if (!卡) return '未选定'
      return (卡.候选卡 && 卡.候选卡.标题) || 卡.版本号 || ('方案#' + 卡.id)
    },
    // 本页固定是第 2 步（0 起：0 创作方案 / 1 人物设定 / 2 分集目录 / 3 分集剧本）
    当前步() {
      return 1
    },
    /* 本页的配置 key：生成:/script/character */
    页配置类型() {
      return '生成:' + (this.$route.path || '')
    },
    默认引导() {
      return 默认引导文本
    },
    /* 引入数据：标题 + 一句话创意 + 已选方案 + 方案详情的七块 */
    引入数据() {
      return this.造引入数据(this.引入勾选)
    },
    // 现有关系网：补新角色 / 补关系网时都要看，别补出一个和谁都不连的人。
    // 有阶段的边写成「第1-5集 协作（…）；第6-8集 羁绊（…）」，和 AI 输出格式互逆
    关系网文本() {
      if (!this.关系表.length) return ''
      const 行们 = ['甲 ↔ 乙｜类型｜关键词｜说明（关系会变的写成：第1-5集 类型（说明）；第6集起 类型（说明））']
      const 总 = this.总集
      this.关系表.forEach(function (边) { 行们.push(关系一行(边, 总)) })
      return 行们.join('\n')
    },
    /* ---- 关系网 ---- */
    角色数() {
      return this.分组后.reduce(function (和, 组) { return 和 + 组.数 }, 0)
    },
    // 只取本剧角色（CHAR_）的名，关系网两端都从这里选
    角色名们() {
      const 出 = []
      this.角色表.forEach(function (人) {
        if (String(人.资产ID || '').indexOf('CHAR_') !== 0) return
        出.push(人.名)
      })
      return 出
    },
    关系角色们() {
      return ['全部'].concat(this.角色名们)
    },
    关系筛选后() {
      return 筛关系(this.关系表, this.关系筛选)
    },
    关系勾选数() {
      return this.关系预览.filter(function (条) { return 条.勾选 }).length
    },
    // 人物设定只放「角色」，场景/道具（SCR_/PROP_/CUSTOM_）归资产库，不在本页
    分组后() {
      const 分组 = {}
      this.角色表.forEach(人 => {
        if (String(人.资产ID || '').indexOf('CHAR_') !== 0) return
        const g = 人.分组 || '其他'
        if (!分组[g]) 分组[g] = []
        分组[g].push(人)
      })
      return Object.keys(分组).map(名 => ({ 名, 数: 分组[名].length, 项: 分组[名] }))
    }
  },
  methods: {
    /* ---------------- 引入数据 ---------------- */

    // 勾 = 勾上的数据键数组；null/空表示没配过，默认全选
    造引入数据(勾) {
      const 项们 = [
        { 键: '标题', 名: '标题（剧名）', 值: this.剧名 },
        {
          键: '创意', 名: '一句话创意', 值: this.创意文本, 可编辑: true,
          提示: '从新建剧本带过来的；没带过来就在这里补，会记住',
          占位: '例：重生教师带三个学生考过毕业考核，一边藏身份一边带她们成长'
        },
        { 键: '方案', 名: '已选方案（' + this.已选方案名 + '）', 值: this.已选方案文本() }
      ]
      方案分区.forEach(区 => {
        项们.push({ 键: 区.键, 名: 区.名, 值: this.方案分区文本(区) })
      })
      // 人物关系网：现有的人怎么连的，补新角色时别补出一个和谁都不连的人
      项们.push({
        键: '关系网', 名: '人物关系网（现有边）', 值: this.关系网文本,
        提示: '甲 ↔ 乙｜类型｜关键词｜说明，一行一条'
      })
      // null/undefined = 没配过，默认全选；[] = 用户点过「全不选」，要尊重
      for (let i = 0; i < 项们.length; i++) {
        项们[i].勾选 = 勾 == null ? true : 勾.indexOf(项们[i].键) >= 0
      }
      return 项们
    },
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
    // 方案详情某分区摊成文本（真库 = 方案表分区列，见 this.方案分区值）
    方案分区文本(区) {
      const 值 = this.方案分区值[区.库列 || 区.键]
      if (值 == null) return ''
      if (区.型 === '键值') {
        return (值 || []).map(条 => 条.键 + '：' + 条.值).join('\n')
      }
      if (区.型 === '分段') return (值 || []).join('\n\n')
      if (区.型 === '子卡片') {
        return (值 || []).map(条 => 条.标题 + '｜' + 条.正文).join('\n')
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
    // 生成时真正拼进需求的参考块：只取勾上且非空的
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

    /* ---------------- AI 生成人物设定 ---------------- */
    async 生成人物设定() {
      if (!this.扩写技能id) {
        this.$message.warning('请先在「技能」里选一个技能')
        return
      }
      const 参考 = this.参考块()
      const 需求 = (参考 ? [参考, ''] : []).concat([
        '剧名：' + this.剧名,
        '集数：' + this.集数 + ' 集',
        '题材：' + this.题材,
        '要生成的内容：人物设定',
        '要求：' + (this.扩写需求.trim() || '按已选方案直接产出一版')
      ]).join('\n')

      this.扩写中 = true
      try {
        const 文本 = String(await 提交AI任务({
          正向: 需求,
          系统: this.技能引导 || this.默认引导,
          技能id: this.扩写技能id
        }) || '').trim()
        if (!文本) {
          this.$message.warning('AI 没有返回内容，可稍后重试')
          return
        }
        this.生成结果 = 文本
        this.$message.success('已生成人物设定，见上方生成结果')
      } catch (e) {
        this.扩写报错(e)
      } finally {
        this.扩写中 = false
      }
    },
    async 复制生成结果() {
      const 成功 = await 复制到剪贴板(this.生成结果)
      this.$message[成功 ? 'success' : 'error'](成功 ? '已复制到剪贴板' : '复制失败，请手动选择复制')
    },
    // 把生成结果里的「名｜本剧关系｜性别｜年龄｜简介｜…」行解析成角色卡并入角色表，
    // 跳过与现有角色重名的行，CHAR 编号接着现有最大号往下排，落库走 存全库（人物+关系全量替换）。
    解析入表() {
      const 页 = this
      const 行们 = String(页.生成结果 || '').replace(/\r\n?/g, '\n').split('\n')
        .map(function (s) { return s.trim() })
        .filter(function (s) { return s })
      const 已有名 = {}
      let 最大号 = 0
      页.角色表.forEach(function (人) {
        if (人.名) 已有名[人.名] = 1
        const 配 = String(人.资产ID || '').match(/CHAR_(\d+)/)
        if (配) 最大号 = Math.max(最大号, parseInt(配[1], 10))
      })
      const 新们 = []
      行们.forEach(function (行) {
        const 段 = 拆行(行)
        if (段.length < 3) return
        const 人 = 页.行转角色(段, 0)
        if (!人.名 || 已有名[人.名]) return
        已有名[人.名] = 1
        新们.push(人)
      })
      if (!新们.length) {
        页.$message.warning('没认出可新增的角色行（格式：名｜本剧关系｜性别｜年龄｜简介｜…），或角色都已存在')
        return
      }
      新们.forEach(function (人) {
        最大号 += 1
        人.id = 最大号
        人.资产ID = 'CHAR_' + String(最大号).padStart(3, '0')
        人.色 = 角色色盘[(最大号 - 1) % 角色色盘.length]
        页.角色表.push(人)
      })
      页.选中角色 = 新们[0]
      页.存本地()
      页.生成结果 = ''
      页.$message.success('已解析并入库 ' + 新们.length + ' 个新角色')
    },

    /* ---------------- 角色编辑 / 新增 ---------------- */
    // 删除角色：弹窗里点「删除这个角色」后 $emit('删除', 编辑对象) 到这里。
    // 因删除要整体重赋值 关系表（filter 出新数组）并重置 选中角色/关系筛选，逻辑留在父组件。
    删除角色(人) {
      if (!人) return
      const 页 = this
      const 连边 = this.关系表.filter(function (边) { return 边.甲 === 人.名 || 边.乙 === 人.名 })
      const 提示 = '确定删除「' + 人.名 + '」？' +
        (连边.length ? '关系网里跟他有关的 ' + 连边.length + ' 条边也会一起删掉。' : '删掉后这张卡就不在列表里了。')
      this.$confirm(提示, '删除角色', {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(function () {
        const 序 = 页.角色表.indexOf(人)
        if (序 >= 0) 页.角色表.splice(序, 1)
        页.关系表 = 页.关系表.filter(function (边) { return 边.甲 !== 人.名 && 边.乙 !== 人.名 })
        if (页.选中角色 === 人) 页.选中角色 = null
        if (页.关系筛选 === 人.名) 页.关系筛选 = '全部'
        页.编辑显示 = false
        页.存本地()
        页.$message.success('已删除「' + 人.名 + '」' + (连边.length ? '，同时删掉 ' + 连边.length + ' 条关系' : ''))
      }).catch(function () {})
    },


    /* ---------------- 关系网 ---------------- */
    关系类型色(型) {
      return 关系色[型] || '#64748b'
    },
    /* ---- 详情卡取值：静态字段返回一句话，分段字段返回时间轴 ---- */
    // 这个角色有几项资料随集数变（角色卡上挂个「随集变 9」的标）
    角色变化数(人) {
      const 详 = 规整详(人 && 人.详)
      let 数 = 0
      可分段字段.forEach(function (键) {
        if (变化点(详[键]).length) 数++
      })
      return 数
    },
    // 静态值：按 角色字段 顺序补齐，缺的返回空串（模板显示 —）。
    // 分段值也走这里：看全集就铺整条时间轴，选了第 N 集就只返回那一段
    详值(键) {
      if (!this.选中角色) return ''
      const 值 = 规整详(this.选中角色.详)[键]
      if (是分段(值)) return 值文本(值, this.总集, this.查看集)
      return 值 || ''
    },
    // 分段值铺成时间轴用；不是分段就返回空数组，模板走单值分支
    详段(键) {
      if (!this.选中角色) return []
      const 值 = 规整详(this.选中角色.详)[键]
      return 是分段(值) ? 规整段(值, this.总集) : []
    },
    集标(段) {
      return 集标签(段.起, 段.止, this.总集)
    },
    // 这一段是不是「当前正在看的那一集」：没选集（全集）就都不算
    段本集(段) {
      return !!this.查看集 && this.查看集 >= 段.起 && this.查看集 <= 段.止
    },
    关系阶段(边) {
      return 是分段(边 && 边.阶段) ? 规整段(边.阶段, this.总集) : []
    },
    关系类型显示(边) {
      return 关系类型(边, this.总集, this.查看集)
    },
    关系说明显示(边) {
      return 关系说明(边, this.总集, this.查看集)
    },
    /* ---- AI 补关系网 ---- */
    async 生成关系网() {
      if (!this.扩写技能id) {
        this.$message.warning('请先在「技能」里选一个技能')
        return
      }
      const 参考 = this.参考块()
      const 需求 = (参考 ? [参考, ''] : []).concat([
        '剧名：' + this.剧名,
        '集数：' + this.集数 + ' 集',
        '题材：' + this.题材,
        '要生成的内容：这部剧的人物关系网，一行一条边',
        '要求：' + (this.扩写需求.trim() || '按现有角色和已选方案，把关键关系补全，别漏掉学生三人组内部的边')
      ]).join('\n')

      this.关系中 = true
      try {
        const 文本 = String(await 提交AI任务({
          正向: 需求,
          系统: 关系默认引导文本,
          技能id: this.扩写技能id
        }) || '').trim()
        if (!文本) {
          this.$message.warning('AI 没有返回内容，可稍后重试')
          return
        }
        const 条们 = this.解析关系(文本)
        if (!条们.length) {
          this.$message.warning('没认出「甲 ↔ 乙｜类型｜关键词｜说明」格式的边，可以点「新增关系」手写')
          return
        }
        this.关系预览 = 条们
        this.关系筛选 = '全部'
        this.$message.success('AI 补了 ' + 条们.length + ' 条关系，勾选后点写入')
      } catch (e) {
        this.扩写报错(e)
      } finally {
        this.关系中 = false
      }
    },
    // 把 AI 返回的文本拆成关系边。认不出人名的那一行直接丢掉，不硬塞。
    解析关系(文本) {
      const 行们 = String(文本 || '').replace(/\r\n?/g, '\n').split('\n')
      const 名们 = this.角色名们
      const 出 = []
      行们.forEach(原 => {
        let 行 = String(原 || '').trim()
        if (!行) return
        行 = 行.replace(/^[\s>*\-·]+/, '').replace(/^\d+\s*[.、)）]\s*/, '').trim()
        if (!行) return
        let 段 = 行.split('｜')
        if (段.length < 2) 段 = 行.split('|')
        if (段.length < 2) 段 = 行.split('\t')
        段 = 段.map(function (s) { return s.trim() }).filter(function (s) { return s !== '' })
        if (段.length < 2) return
        const 头 = 段[0].replace(/[（(].*$/, '').trim()
        const 拆 = 头.split(/\s*(?:↔|<->|—|－|-|→|vs)\s*/).filter(function (s) { return s })
        if (拆.length < 2) return
        const 甲 = 拆[0].trim()
        const 乙 = 拆[1].trim()
        if (甲 === 乙) return
        if (名们.indexOf(甲) < 0 || 名们.indexOf(乙) < 0) return

        let 类型 = '羁绊'
        let 词 = []
        let 说明 = ''
        if (段.length >= 3) {
          类型 = 关系类型们.indexOf(段[1]) >= 0 ? 段[1] : '羁绊'
          词 = 段[2].split(/[、,，]/).map(function (s) { return s.trim() }).filter(function (s) { return s })
          说明 = 段.slice(3).join('｜').trim()
        } else {
          说明 = 段[1]
        }
        // 说明里如果是「第1-5集 协作（…）；第6集起 羁绊（…）」，顺手拆成阶段
        let 阶段 = 解析关系阶段(说明, this.总集)
        if (阶段 && 阶段.length >= 2) {
          类型 = 阶段[阶段.length - 1].类型 || 类型
        } else {
          阶段 = []
        }
        const 重复 = this.关系表.some(function (边) { return 是同一条边(边, 甲, 乙) })
        出.push({
          甲: 甲, 乙: 乙, 类型: 类型, 关键词: 词, 说明: 说明, 阶段: 阶段,
          勾选: !重复, 重复: 重复
        })
      })
      return 出
    },
    写入关系() {
      const 加 = this.关系预览.filter(function (条) { return 条.勾选 && !条.重复 })
      if (!加.length) {
        this.$message.warning('没有勾选可写入的关系')
        return
      }
      let 最大 = 0
      this.关系表.forEach(function (边) { if (边.id > 最大) 最大 = 边.id })
      const 页 = this
      加.forEach(function (条) {
        最大++
        页.关系表.push({
          id: 最大, 甲: 条.甲, 乙: 条.乙,
          类型: 条.类型, 关键词: 条.关键词, 说明: 条.说明, 阶段: 条.阶段 || []
        })
      })
      this.关系预览 = []
      this.存本地()
      this.$message.success('已写入 ' + 加.length + ' 条关系')
    },

    /* ---------------- 载入 / 保存（真库） ---------------- */
    // 进页主流程：取剧+方案 → 读人物与关系 → 空则首次自动生成
    async 载入() {
      this.载入中 = true
      this.载入报错 = ''
      try {
        await this.取剧与方案()
        if (!this.剧id) {
          this.载入报错 = '找不到这部剧：请从「我的剧」或「新建剧本」进入本页'
          return
        }
        await this.取方案分区()
        const 数据 = await 取('/api/人物/列表?剧id=' + this.剧id)
        const 行们 = (数据 && 数据.人物们) || []
        const 边们 = (数据 && 数据.关系们) || []
        const 页 = this
        if (行们.length) {
          this.角色表 = 行们.map(function (行, 序) { return 页.库转角色(行, 序) })
          this.关系表 = 边们.map(function (行) { return 页.边从库(行) })
          this.选中角色 = this.角色表[0] || null
        } else {
          this.角色表 = []
          this.关系表 = []
          this.选中角色 = null
          this.载入中 = false
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
      } catch (e) {
        this.方案分区值 = {}
      }
    },
    // 一行「名｜本剧关系｜性别｜年龄｜简介｜20个字段」拆成角色卡（和 填入新角色 同一套对位）
    行转角色(段, 序) {
      const 详 = 空角色详()
      const 名 = (段[0] || '').trim()
      for (let i = 0; i < 行字段.length; i++) {
        const 值 = 段[5 + i]
        if (值) 详[行字段[i]] = 文本转值(值, this.总集)
      }
      详.姓名 = 名
      return {
        分组: '本剧角色',
        来源: 'AI生成',
        id: 序 + 1,
        资产ID: 'CHAR_' + String(序 + 1).padStart(3, '0'),
        关系: (段[1] || '').trim() || '功能性角色',
        名: 名,
        性别: 段[2] || '-',
        年龄: 段[3] || '-',
        简介: 段[4] || '',
        色: 角色色盘[序 % 角色色盘.length],
        详: 详
      }
    },
    // 角色卡 → 库行（可分段字段用 值文本 铺成「第1-5集：…；第6集起：…」文本）
    角色转库(人) {
      const 详 = 规整详(人.详 || {})
      const 总 = this.总集
      return {
        人物id: 人.资产ID || '',
        名: 人.名 || '',
        性别: 人.性别 || '',
        年龄档: 人.年龄 || '',
        性格: 值文本(详.性格, 总),
        关系: 人.关系 || '',
        简介: 人.简介 || '',
        分组: 人.分组 || '本剧角色',
        卡色: 人.色 || '',
        身份: 值文本(详.身份, 总),
        关系变化: 值文本(详.关系, 总),
        态度: 值文本(详.态度, 总),
        外貌: 值文本(详.外貌, 总),
        身材: 值文本(详.身材, 总),
        穿搭: 值文本(详.穿搭, 总),
        身体情况: 值文本(详.身体情况, 总),
        情感情况: 值文本(详.情感情况, 总),
        精神情况: 值文本(详.精神情况, 总),
        当前状态: 值文本(详.当前状态, 总),
        当前姿势: 值文本(详.当前姿势, 总),
        内心想法: 值文本(详.内心想法, 总),
        技能: 值文本(详.技能, 总),
        核心目标: 值文本(详.核心目标, 总),
        关系网: 值文本(详.关系网, 总),
        背景故事: 值文本(详.背景故事, 总),
        台词风格: 值文本(详.台词风格, 总),
        口头禅: 值文本(详.口头禅, 总),
        概括: 值文本(详.概括, 总)
      }
    },
    // 库行 → 角色卡（可分段字段用 文本转值 认回时间轴）
    库转角色(行, 序) {
      const 总 = this.总集
      const 详 = 空角色详()
      详.姓名 = 行.名 || ''
      详.性别 = 行.性别 || ''
      详.年龄 = 行.年龄档 || ''
      详.性格 = 文本转值(行.性格, 总)
      详.身份 = 文本转值(行.身份, 总)
      详.关系 = 文本转值(行.关系变化, 总)
      详.态度 = 文本转值(行.态度, 总)
      详.外貌 = 文本转值(行.外貌, 总)
      详.身材 = 文本转值(行.身材, 总)
      详.穿搭 = 文本转值(行.穿搭, 总)
      详.身体情况 = 文本转值(行.身体情况, 总)
      详.情感情况 = 文本转值(行.情感情况, 总)
      详.精神情况 = 文本转值(行.精神情况, 总)
      详.当前状态 = 文本转值(行.当前状态, 总)
      详.当前姿势 = 文本转值(行.当前姿势, 总)
      详.内心想法 = 文本转值(行.内心想法, 总)
      详.技能 = 文本转值(行.技能, 总)
      详.核心目标 = 文本转值(行.核心目标, 总)
      详.关系网 = 文本转值(行.关系网, 总)
      详.背景故事 = 文本转值(行.背景故事, 总)
      详.台词风格 = 文本转值(行.台词风格, 总)
      详.口头禅 = 文本转值(行.口头禅, 总)
      详.概括 = 文本转值(行.概括, 总)
      return {
        分组: 行.分组 || '本剧角色',
        来源: '库',
        id: 序 + 1,
        资产ID: 行.人物id || ('CHAR_' + String(序 + 1).padStart(3, '0')),
        关系: 行.关系 || '',
        名: 行.名 || '',
        性别: 行.性别 || '',
        年龄: 行.年龄档 || '',
        简介: 行.简介 || '',
        色: 行.卡色 || 角色色盘[序 % 角色色盘.length],
        详: 详
      }
    },
    // 关系边 → 库行（阶段铺回说明文本，与 关系一行 的第 4 列同格式）
    边转库(边, 序) {
      const 总 = this.总集
      let 说明 = String(边.说明 || '')
      const 阶段 = 是分段(边.阶段) ? 规整段(边.阶段, 总) : []
      if (阶段.length) {
        说明 = 阶段.map(function (段) {
          return 集标签(段.起, 段.止, 总) + ' ' + (段.类型 || '') + (段.说明 ? '（' + 段.说明 + '）' : '')
        }).join('；')
      }
      return {
        甲: 边.甲 || '',
        乙: 边.乙 || '',
        类型: 边.类型 || '',
        关键词: (边.关键词 || []).join('、'),
        说明: 说明,
        边序: 序
      }
    },
    // 库行 → 关系边（说明里认「第1-5集 协作（…）；…」阶段）
    边从库(行) {
      const 说明 = String(行.说明 || '')
      let 阶段 = 解析关系阶段(说明, this.总集)
      if (!阶段 || 阶段.length < 2) 阶段 = []
      return {
        id: 行.id,
        甲: 行.甲,
        乙: 行.乙,
        类型: 阶段.length ? (阶段[阶段.length - 1].类型 || 行.类型 || '羁绊') : (行.类型 || '羁绊'),
        关键词: String(行.关键词 || '').split(/[、,，]/).map(function (s) { return s.trim() }).filter(function (s) { return s }),
        说明: 说明,
        阶段: 阶段
      }
    },
    // 全量落库：人物 + 关系网一起发（后端事务内全量替换）
    async 存全库() {
      if (!this.剧id) throw new Error('没有剧 id，无法保存')
      const 页 = this
      const 人物们 = this.角色表
        .filter(function (人) { return String(人.资产ID || '').indexOf('CHAR_') === 0 })
        .map(function (人) { return 页.角色转库(人) })
      await 发('/api/人物/保存', { 剧id: this.剧id, 人物们: 人物们 })
      const 关系们 = this.关系表.map(function (边, 序) { return 页.边转库(边, 序) })
      await 发('/api/人物/关系保存', { 剧id: this.剧id, 关系们: 关系们 })
    },
    // 所有改动点共用的静默落库（编辑/新增/删除后调它），失败弹真实错误
    存本地() {
      const 页 = this
      this.存全库().catch(function (e) {
        页.$message.error('落库失败：' + ((e && e.message) || ''))
      })
      return true
    },
    // 首次进入（库里没人物）：AI 生成全部角色 → 逐个落库带进度 → 补关系网落库
    async 首次生成() {
      // 技能列表是 created 里异步拉的，可能还没回来；先等它就绪，否则只能裸跑不带技能规范
      if (!this.技能列表.length) await this.拉技能列表()
      this.扩写技能id = this.扩写技能id || 适配技能id(this.技能列表, this.页配置类型)
      this.自动生成中 = true
      this.自动进度 = 0
      const 页 = this
      try {
        // 第一步：一次生成全部角色行
        this.自动文案 = 'AI 正在为本剧生成人物设定…'
        const 参考 = this.参考块()
        const 需求 = (参考 ? [参考, ''] : []).concat([
          '剧名：' + this.剧名,
          '集数：' + this.集数 + ' 集',
          '题材：' + this.题材,
          '要生成的内容：人物设定',
          '要求：' + (this.扩写需求.trim() || '按已选方案直接产出一版')
        ]).join('\n')
        const 文本 = String(await 提交AI任务({
          正向: 需求,
          系统: this.技能引导 || this.默认引导,
          技能id: this.扩写技能id
        }) || '').trim()
        if (!文本) throw new Error('AI 没有返回人物设定内容')

        // 逐行解析成角色卡
        const 行们 = 文本.replace(/\r\n?/g, '\n').split('\n').map(function (s) { return s.trim() }).filter(function (s) { return s })
        const 新们 = []
        行们.forEach(function (行) {
          const 段 = 拆行(行)
          if (段.length < 3) return
          const 人 = 页.行转角色(段, 新们.length)
          if (人.名) 新们.push(人)
        })
        if (!新们.length) throw new Error('没认出「名｜本剧关系｜性别｜年龄｜简介｜…」格式的角色行')
        this.角色表 = 新们
        this.选中角色 = 新们[0]

        // 逐个落库（每落一个进度走一格；后端全量替换，累积发送）
        for (let i = 0; i < 新们.length; i++) {
          this.自动文案 = '正在落库「' + 新们[i].名 + '」（' + (i + 1) + '/' + 新们.length + '）…'
          this.自动进度 = Math.round((i / 新们.length) * 80)
          const 批 = 新们.slice(0, i + 1).map(function (人) { return 页.角色转库(人) })
          await 发('/api/人物/保存', { 剧id: this.剧id, 人物们: 批 })
        }

        // 第二步：补关系网（失败不挡人物）
        this.自动进度 = 85
        this.自动文案 = 'AI 正在补人物关系网…'
        try {
          const 参考2 = this.参考块()
          const 需求2 = (参考2 ? [参考2, ''] : []).concat([
            '剧名：' + this.剧名,
            '集数：' + this.集数 + ' 集',
            '题材：' + this.题材,
            '要生成的内容：这部剧的人物关系网，一行一条边',
            '要求：按现有角色和已选方案，把关键关系补全，别漏掉主角团内部的边'
          ]).join('\n')
          const 关系文本 = String(await 提交AI任务({
            正向: 需求2,
            系统: 关系默认引导文本,
            技能id: this.扩写技能id
          }) || '').trim()
          if (关系文本) {
            const 条们 = this.解析关系(关系文本).filter(function (条) { return 条.勾选 })
            条们.forEach(function (条, 序) {
              页.关系表.push({
                id: 序 + 1, 甲: 条.甲, 乙: 条.乙,
                类型: 条.类型, 关键词: 条.关键词, 说明: 条.说明, 阶段: 条.阶段 || []
              })
            })
            if (this.关系表.length) {
              const 边批 = this.关系表.map(function (边, 序) { return 页.边转库(边, 序) })
              await 发('/api/人物/关系保存', { 剧id: this.剧id, 关系们: 边批 })
            }
          }
        } catch (e) { /* 关系网失败不挡人物 */ }

        this.自动进度 = 100
        const 关系注 = this.关系表.length ? ('，关系网 ' + this.关系表.length + ' 条') : '（关系网没生成，可手动点「AI 补关系网」）'
        this.$message.success('人物设定已生成并落库：' + 新们.length + ' 个角色' + 关系注)
      } catch (e) {
        this.$message({
          message: '首次生成失败：' + ((e && e.message) || '') + '。已生成的角色不会丢，可重进本页续生成或手动新增。',
          type: 'error',
          duration: 8000
        })
      } finally {
        this.自动生成中 = false
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
      this.去方案详情()
    },
    async 下一步() {
      // 跳转前先全量落库，保证下次进来读得到
      try {
        await this.存全库()
      } catch (e) {
        this.$message.error('保存失败：' + ((e && e.message) || ''))
        return
      }
      this.$router.push({
        path: '/script/outline',
        query: Object.assign({}, this.$route.query)
      })
    },
    // 点四步进度条：四步各是一个独立页
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
    },
    async 保存() {
      try {
        await this.存全库()
        this.$message.success('已保存「人物设定」角色与关系网（数据库）')
      } catch (e) {
        this.$message.error('保存失败：' + ((e && e.message) || ''))
      }
    },
    首字(名) {
      return String(名 || '?').slice(0, 1)
    }
  }
}
</script>

<style scoped>
/* 首次生成进度遮罩（与方案详情页同一形态） */
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

/* 四步进度条居中（与创作方案页同一形态） */
.步骤条.居中 { max-width: 720px; margin: 0 auto 24px; }

.提示卡 { margin-bottom: 16px; font-size: 13px; color: var(--字次); }

/* ---- 本页生成条（和创作方案页的「修改意见」同一形态） ---- */
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

/* ---- 生成结果 ---- */
.结果卡 { margin-bottom: 16px; }
.结果标题 { font-size: 14px; color: var(--字); font-weight: 600; }
.结果卡 .原文 {
  margin: 0;
  max-height: 320px;
  overflow: auto;
  font-family: inherit;
  font-size: 12px;
  line-height: 1.8;
  color: var(--字次);
  white-space: pre-wrap;
  word-break: break-word;
}

/* ---- 角色卡 ---- */
/* 列表工具条：AI 新增人物 / 手动新增 / 编辑选中 */
.列表工具 {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  margin-bottom: 14px;
  background: var(--卡片二);
  border: 1px solid var(--描边);
  border-radius: 10px;
}
.工具数 { font-size: 12px; color: var(--字弱); }

.角色组 { margin-bottom: 20px; }
.组头 {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  margin-bottom: 12px;
  background: var(--卡片二);
  border: 1px solid var(--描边);
  border-radius: 10px;
  font-size: 13px;
}
.组头 .组名 { color: var(--字); font-weight: 600; }
.组头 .组数 { color: var(--字弱); }

.角色卡 {
  background: var(--卡片);
  border: 1px solid var(--描边);
  border-radius: 12px;
  padding: 14px;
  cursor: pointer;
  transition: border-color .15s, background .15s;
}
.角色卡:hover { border-color: var(--描边亮); }
.角色卡.选中 { border-color: var(--主); background: var(--主浅); }
.头像 {
  width: 36px; height: 36px; border-radius: 999px;
  flex: 0 0 36px;
  display: flex; align-items: center; justify-content: center;
  color: var(--字); font-size: 15px; font-weight: 700;
}
.角色名 { font-size: 14px; font-weight: 600; color: var(--字); }
.角色副 { font-size: 12px; color: var(--字弱); margin-top: 2px; }
.角色简介 {
  font-size: 12px; color: var(--字次); line-height: 1.7;
  min-height: 40px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ---- 角色详情 ---- */
.详情卡 { border-color: var(--主); }
.详情名 { font-size: 18px; font-weight: 700; color: var(--字); }
.关闭钮 { cursor: pointer; color: var(--字弱); }
.详情组 {
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px dashed var(--描边);
}
.详情组:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
.详情组名 {
  font-size: 12px;
  font-weight: 600;
  color: var(--主);
  margin-bottom: 8px;
  letter-spacing: .5px;
}
.详情格 {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px 24px;
}
.详情项 { display: flex; gap: 8px; font-size: 12px; line-height: 1.75; min-width: 0; }
/* 分段的字段要占满整行，时间轴才铺得开 */
.详情项.跨列 { grid-column: 1 / -1; }
.详情键 { flex: 0 0 60px; color: var(--字弱); }
.详情值 { flex: 1; min-width: 0; color: var(--字次); word-break: break-word; }
.详情值.空 { color: #475569; }

/* ---- 按集分阶段：字段时间轴 ---- */
.详情值.分段 { display: flex; flex-direction: column; gap: 3px; }
.段行 {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  padding: 3px 8px;
  border-left: 2px solid var(--描边);
  border-radius: 0 4px 4px 0;
}
.段行.本集 { border-left-color: var(--主); background: var(--主浅); }
.段行.淡 { opacity: .45; }
.段标 {
  flex: 0 0 auto;
  font-size: 11px;
  color: var(--字弱);
  white-space: nowrap;
  line-height: 1.75;
}
.段行.本集 .段标 { color: var(--主); font-weight: 600; }
.段值 { flex: 1; min-width: 0; }

/* 变化摘要条：压在详情卡顶上，一眼看到哪些字段在第几集变过 */
.变化条 {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 14px;
  padding: 9px 12px;
  margin-bottom: 14px;
  background: var(--卡片二);
  border: 1px dashed var(--描边亮);
  border-radius: 8px;
  font-size: 12px;
}
.变化标题 { color: var(--主); font-weight: 600; }
.变化项 { color: var(--字次); }
.变化集 { color: #f59e0b; margin-left: 2px; }
.变化注 { color: var(--字弱); }
.变化标 { color: #f59e0b; border-color: rgba(245, 158, 11, .35); background: rgba(245, 158, 11, .1); }
.组集注 { font-size: 11px; font-weight: 400; color: var(--字弱); margin-left: 6px; }

/* 「按集看」下拉：放在列表工具条右侧 */
.集游标 { display: flex; align-items: center; gap: 6px; }
.集游标标 { font-size: 12px; color: var(--字弱); white-space: nowrap; }

/* ---- 关系网 ---- */
.关系筛 {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}
.关系列 {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.关系卡 { padding: 14px; }
.关系头 { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.关系人 { font-size: 14px; font-weight: 600; color: var(--字); }
.关系连 { color: var(--字弱); }
.关系类型 {
  font-size: 11px;
  line-height: 18px;
  border: 1px solid var(--描边亮);
  border-radius: 999px;
  padding: 0 7px;
  white-space: nowrap;
}
.关系词 { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
.关系词 .词 {
  font-size: 11px;
  color: var(--主);
  background: var(--主浅);
  border: 1px solid rgba(34, 197, 94, .28);
  border-radius: 4px;
  padding: 1px 6px;
}
.关系说 { margin-top: 10px; font-size: 12px; line-height: 1.8; color: var(--字次); }

/* 关系会变：按集铺成时间轴 */
.阶段列 { margin-top: 10px; display: flex; flex-direction: column; gap: 4px; }
.阶段行 {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  padding: 4px 8px;
  border-left: 2px solid var(--描边);
  border-radius: 0 4px 4px 0;
  font-size: 12px;
}
.阶段行.本集 { border-left-color: var(--主); background: var(--主浅); }
.阶段行.淡 { opacity: .45; }
.阶段类型 {
  flex: 0 0 auto;
  font-size: 11px;
  line-height: 16px;
  border: 1px solid var(--描边亮);
  border-radius: 999px;
  padding: 0 6px;
  white-space: nowrap;
}
.阶段说 { flex: 1; min-width: 0; color: var(--字次); line-height: 1.75; }

/* AI 补的关系网：勾选预览 */
.关系预览 { margin-bottom: 14px; border-color: var(--主); }
.预览头 {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--描边);
}
.预览题 { font-size: 14px; font-weight: 600; color: var(--字); }
.预览注 { font-size: 12px; color: var(--字弱); }
.预览行 {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px dashed var(--描边);
  font-size: 12px;
}
.预览行:last-child { border-bottom: none; }
.预览边 { flex: 0 0 150px; color: var(--字); }
.预览文 { flex: 1; min-width: 0; color: var(--字次); line-height: 1.7; }
.预览重 { color: #f59e0b; margin-left: 6px; }

@media (max-width: 1200px) {
  .关系列 { grid-template-columns: minmax(0, 1fr); }
  .详情格 { grid-template-columns: minmax(0, 1fr); }
}

.新增标 { background: rgba(34, 197, 94, .12); border-color: rgba(34, 197, 94, .3); color: var(--主); }

</style>
