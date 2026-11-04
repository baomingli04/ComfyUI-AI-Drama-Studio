<template>
  <div class="创作模块">
    <!-- 面包屑 -->
    <div class="面包屑条">
      <span class="可点" @click="$router.push('/script')">剧本创作</span>
      <span> / </span>
      <span class="可点" @click="去方案详情()">创作方案</span>
      <span> / </span>
      <span>分集目录</span>
    </div>

    <!-- 四步进度条：和创作方案页同一位置（面包屑正下方、居中），点任意一步即跳到那一步。
         本页是第 3 步「分集目录」，页面里不再有第二套步骤标签栏。 -->
    <step-bar :步骤="步骤" :当前步="当前步" @切换="跳步骤($event)"></step-bar>

    <!-- 页头 -->
    <div class="页头">
      <div class="左">
        <h1 class="标题">{{ 剧名 }}</h1>
        <div class="副题">
          {{ 集数 }} 集 · {{ 题材 }} · 已采用 {{ 已选方案名 }} ·
          关键 {{ 关键数 }} 集 · 卡点 {{ 卡点数 }} 集 · 未回收 {{ 未回收.length }}
        </div>
      </div>
      <div class="右">
        <el-button size="small" @click="体检显示 = true">
          体检 {{ 体检项.length }}
        </el-button>
        <el-button @click="上一步()">上一步：人物设定</el-button>
        <el-button @click="保存()">保存</el-button>
        <el-button type="primary" @click="下一步()">下一步：分集剧本</el-button>
      </div>
    </div>

    <!-- 载入中 / 载入报错 -->
    <div v-if="载入中" class="提示卡" style="text-align:center;padding:48px 0;color:var(--字弱)">
      <i class="el-icon-loading" style="font-size:26px;color:var(--主)"></i>
      <div style="margin-top:10px;font-size:13px">正在读取剧、方案、人物与分集目录…</div>
    </div>
    <div v-else-if="载入报错" class="提示卡" style="text-align:center;padding:40px 0">
      <div style="color:#ef4444;font-size:13px;margin-bottom:12px">{{ 载入报错 }}</div>
      <el-button size="mini" @click="载入目录()">重试</el-button>
    </div>

    <template v-else>
    <!-- 首次自动生成进度遮罩 -->
    <div v-if="自动生成中" class="生成遮罩">
      <div class="生成框">
        <div class="生成标题">首次生成分集目录</div>
        <el-progress :percentage="自动进度" :stroke-width="8"></el-progress>
        <div class="生成注">{{ 自动文案 }}</div>
      </div>
    </div>

    <div class="卡片 提示卡">
      分集目录按已选方案和人物设定产出。上面是这一版目录的节奏与钩子体检，下面是逐集卡；
      点「AI 生成分集目录」重出一版，会先进「差异预览」，你勾选后再写入，不会覆盖你手工改过的集。
    </div>

    <!-- ============ 节奏总览 ============ -->
    <div class="总览带">
      <div class="卡片 曲线卡">
        <div class="卡头">
          <span class="卡名">情绪波浪</span>
          <span class="卡注">纵轴 1–5 · 横轴集号 · 虚线：连续低谷警戒（≤2）</span>
        </div>
        <emotion-chart :集们="目录表" :高="180" @点集="定位到集"></emotion-chart>
      </div>

      <div class="侧列">
        <div class="卡片">
          <div class="卡头">
            <span class="卡名">黄金三集</span>
            <span class="卡注">ep1–3</span>
          </div>
          <div class="金集">
            <div
              v-for="集 in 黄金三集"
              :key="'金' + 集.集"
              class="金卡"
              @click="定位到集(集.集)">
              <div class="金头">EP{{ 集.集 }} · {{ 情绪档(集) }}</div>
              <div class="金题">{{ 集.标题 || '（未命名）' }}</div>
            </div>
          </div>
        </div>

        <div class="卡片">
          <div class="卡头">
            <span class="卡名">台账体检</span>
            <span class="卡注">由集卡点位派生</span>
          </div>
          <div class="体检">
            <div class="检"><div class="数 蓝">{{ 埋数 }}</div><div class="名">埋</div></div>
            <div class="检"><div class="数 绿">{{ 兑数 }}</div><div class="名">兑</div></div>
            <div class="检"><div class="数 青">{{ 回收数 }}</div><div class="名">回收</div></div>
            <div class="检"><div class="数 红">{{ 未回收.length }}</div><div class="名">未回收</div></div>
          </div>
          <div v-if="体检项.length" class="告警" @click="体检显示 = true">
            {{ 体检项[0].文 }}
            <span v-if="体检项.length > 1" class="告警多">还有 {{ 体检项.length - 1 }} 条</span>
          </div>
          <div v-else class="告警 好">这一版目录没查出结构问题</div>
        </div>
      </div>
    </div>

    <!-- ============ 本页生成 ============ -->
    <div class="生成条">
      <div class="行间">
        <div class="行间">
          <div class="AI标">AI</div>
          <div>
            <div class="意见标题">生成分集目录</div>
            <div class="意见价">0.2 积分/次</div>
          </div>
        </div>
        <div style="flex:1"></div>
        <div class="意见例如">例：第 3 集提前抛反转、每集结尾都留钩子…</div>
        <el-button size="mini" icon="el-icon-setting" @click="打开技能()">技能</el-button>
        <el-button size="mini" type="primary" plain :loading="扩写中" @click="生成目录()">
          AI 生成分集目录
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
        placeholder="写一句要求，AI 按这句话重排分集目录（不写就按方案直接产出一版）"></el-input>
    </div>

    <!-- 差异预览：AI 出的那一版不直接覆盖，逐集比对后勾选写入 -->
    <div v-if="差异表.length" class="卡片 差异卡">
      <div class="卡头">
        <span class="卡名">差异预览 · {{ 目录表.length }} 集 / {{ 差异改动数 }} 集有改动</span>
        <div style="flex:1"></div>
        <el-button type="text" size="mini" @click="全选差异(true)">全选</el-button>
        <el-button type="text" size="mini" @click="全选差异(false)">全不选</el-button>
        <el-button type="text" size="mini" @click="差异表 = []">关闭</el-button>
      </div>
      <div class="差列">
        <div v-for="(行, 序) in 差异表" :key="'差' + 序" class="差行">
          <el-checkbox v-model="行.勾选" :disabled="行.类型 === '未变'"></el-checkbox>
          <span class="差标" :class="行.类型">{{ 行.类型 }}</span>
          <span class="差集">EP{{ 行.集 }}</span>
          <span class="差文">{{ 行.标题 || '（无标题）' }}<span class="差注">{{ 行.说明 }}</span></span>
        </div>
      </div>
      <div class="行间 右" style="margin-top:12px">
        <el-button size="small" @click="差异表 = []">取消</el-button>
        <el-button size="small" type="primary" @click="写入差异()">
          写入勾选的 {{ 勾选数 }} 项
        </el-button>
      </div>
    </div>

    <!-- 生成结果：AI 返回的原文摊在这里，复制 / 清空 / 重新解析 -->
    <div v-if="生成结果" class="卡片 结果卡">
      <div class="行间" style="margin-bottom:10px">
        <div class="结果标题">生成结果 · 分集目录（原文）</div>
        <div style="flex:1"></div>
        <el-button type="text" size="mini" @click="重新解析()">重新解析</el-button>
        <el-button type="text" size="mini" @click="复制生成结果()">复制</el-button>
        <el-button type="text" size="mini" @click="生成结果 = ''">清空</el-button>
        <el-button type="text" size="mini" @click="保存()">保存本页</el-button>
      </div>
      <pre class="原文">{{ 生成结果 }}</pre>
    </div>

    <!-- ============ 视图切换 + 工具条 ============ -->
    <div class="列表工具">
      <div class="标签组">
        <button class="项" :class="{ 当前: 视图 === '目录' }" @click="视图 = '目录'">分集目录</button>
        <button class="项" :class="{ 当前: 视图 === '台账' }" @click="视图 = '台账'">钩子台账</button>
      </div>
      <div class="工具数">共 {{ 目录表.length }} 集 · 写完 {{ 完成数 }} 集 · 待创作 {{ 待创作数 }} 集</div>
      <div style="flex:1"></div>
      <template v-if="视图 === '目录'">
        <el-button size="mini" @click="切换全部展开()">{{ 全展开 ? '收起全部' : '展开全部' }}</el-button>
        <el-button size="mini" @click="切只看关键()">{{ 只看关键 ? '看全部集' : '只看关键集' }}</el-button>
        <el-button v-if="目录表.length < 目标集数" size="mini" @click="补齐集数()">
          补齐到 {{ 目标集数 }} 集
        </el-button>
        <el-button size="mini" icon="el-icon-plus" @click="新增一集()">新增一集</el-button>
      </template>
    </div>

    <!-- ============ 目录视图 ============ -->
    <div v-if="视图 === '目录'">
      <div v-for="幕 in 幕们" :key="'幕' + 幕.名" class="幕组">
        <div class="幕头">
          <span class="幕竖"></span>
          <span class="幕名">{{ 幕.名 }}</span>
          <span class="幕数">EP{{ 幕.全起 }}–EP{{ 幕.全止 }} · {{ 幕.全数 }} 集<span v-if="幕.全数 > 幕.集.length">（本页 {{ 幕.集.length }} 集）</span></span>
          <span class="幕线"></span>
        </div>
        <div v-for="集 in 幕.集" :key="'卡' + 集.集" :id="'ep-card-' + 集.集" class="卡位">
          <episode-card
            :集="集"
            :展开="是展开(集)"
            :未回收="未回收集号.indexOf(集.集) >= 0"
            @切换="切换展开(集)"
            @编辑="打开编辑(集)"
            @点位="打开点位(集)"></episode-card>
        </div>
      </div>

      <div v-if="!幕们.length" class="空态">
        <div class="大">还没有分集目录</div>
        点上方「AI 生成分集目录」，或右上「新增一集」
      </div>
    </div>

    <!-- ============ 台账视图 ============ -->
    <div v-else class="台账视图">
      <div v-if="总页数 > 1" class="台账提示">
        台账只画当前页的 {{ 分页集.length }} 集（第 {{ 分页集[0].集 }}–{{ 分页集[分页集.length - 1].集 }} 集）；
        跨页的埋与兑看下方「未回收」清单，那里是全量的。
      </div>
      <hook-ledger :集们="分页集" @点格="定位到集"></hook-ledger>
    </div>

    <!-- ============ 分页条：目录 / 台账共用一套页码 ============ -->
    <page-bar
      v-if="总集数"
      :总数="总集数"
      :每页="每页"
      :当前页="有效页"
      :每页选项="每页选项"
      单位="集"
      @换页="换页($event)"
      @换每页="换每页($event)"></page-bar>

    <div class="行间 右" style="margin-top:20px">
      <el-button @click="上一步()">返回人物设定</el-button>
    </div>
    </template>

    <!-- ============ 体检弹窗 ============ -->
    <el-dialog
      :visible.sync="体检显示"
      width="640px"
      top="8vh"
      :show-close="false"
      :close-on-click-modal="false">
      <div class="弹窗头">
        <div>
          <div class="弹窗标题">目录体检 · {{ 体检项.length }} 条</div>
          <div class="弹窗副题">全部是前端算出来的：情绪分、目标字数、点位、集数，没有一条靠 AI 猜</div>
        </div>
        <i class="el-icon-close 弹窗关闭" title="关闭" @click="体检显示 = false"></i>
      </div>
      <div class="弹窗体">
        <div v-if="!体检项.length" class="体检空">没查出问题：集数对得上、字数在目标 ±20% 内、没有连续低谷、钩子都兑了。</div>
        <div v-for="(项, 序) in 体检项" :key="'检' + 序" class="体检项">
          <span class="体检级" :class="项.级">{{ 项.级 === '红' ? '重' : '轻' }}</span>
          <div>
            <div class="体检类">{{ 项.类 }}</div>
            <div class="体检文">{{ 项.文 }}</div>
          </div>
        </div>
      </div>
      <div class="弹窗底">
        <div style="flex:1"></div>
        <el-button type="primary" @click="体检显示 = false">知道了</el-button>
      </div>
    </el-dialog>

    <!-- ============ 单集编辑 / 新增弹窗 ============ -->
    <el-dialog
      :visible.sync="编辑显示"
      width="680px"
      top="6vh"
      custom-class="集编辑弹窗"
      :show-close="false"
      :close-on-click-modal="false">
      <div class="弹窗头">
        <div>
          <div class="弹窗标题">{{ 新增模式 ? '新增一集' : '编辑第 ' + 草稿.集 + ' 集' }}</div>
          <div class="弹窗副题">{{ 新增模式 ? '填完点「加入目录」，这一集会排到最后' : '改完点保存，直接写回这一行' }}</div>
        </div>
        <i class="el-icon-close 弹窗关闭" title="关闭" @click="编辑显示 = false"></i>
      </div>
      <div class="弹窗体">
        <el-form label-width="80px" size="small">
          <div class="表单两列">
            <el-form-item label="集">
              <el-input-number v-model="草稿.集" :min="1" :max="999" controls-position="right"></el-input-number>
            </el-form-item>
            <el-form-item label="幕">
              <el-select v-model="草稿.幕" style="width:170px">
                <el-option label="第一幕 · 建置" value="第一幕 · 建置"></el-option>
                <el-option label="第二幕 · 对抗" value="第二幕 · 对抗"></el-option>
                <el-option label="第三幕 · 收束" value="第三幕 · 收束"></el-option>
              </el-select>
            </el-form-item>
          </div>
          <el-form-item label="标题">
            <el-input v-model="草稿.标题" maxlength="30" placeholder="这一集的看点，12 字内最好"></el-input>
          </el-form-item>
          <el-form-item label="梗概">
            <el-input v-model="草稿.梗概" type="textarea" :rows="4" placeholder="1~2 句：这一集发生什么、结尾卡在哪"></el-input>
          </el-form-item>
          <el-form-item label="出场">
            <el-input v-model="草稿.出场" maxlength="80" placeholder="顿号分隔，例如：李宝明、雏田、天天"></el-input>
          </el-form-item>
          <el-form-item label="开场钩子">
            <el-input v-model="草稿.钩子" maxlength="80" placeholder="开场三拍里最先抓住人的那个画面"></el-input>
          </el-form-item>
          <el-form-item label="尾钩">
            <el-input v-model="草稿.尾钩" maxlength="80" placeholder="这一集卡在哪，让观众必须看下一集"></el-input>
          </el-form-item>
          <el-form-item label="中心句">
            <el-input v-model="草稿.中心句" type="textarea" :rows="2" placeholder="一句话说清这一集的内核"></el-input>
          </el-form-item>
          <div class="表单两列">
            <el-form-item label="情绪分">
              <el-rate v-model="草稿.情绪分" :max="5" :colors="['#ef4444', '#f59e0b', '#22c55e']"></el-rate>
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="草稿.状态" style="width:140px">
                <el-option label="待创作" value="待创作"></el-option>
                <el-option label="进行中" value="进行中"></el-option>
                <el-option label="已完成" value="已完成"></el-option>
              </el-select>
            </el-form-item>
          </div>
          <div class="表单两列">
            <el-form-item label="字数">
              <el-input-number v-model="草稿.字数" :min="0" :max="20000" :step="100" controls-position="right"></el-input-number>
            </el-form-item>
            <el-form-item label="目标字数">
              <el-input-number v-model="草稿.目标" :min="0" :max="20000" :step="100" controls-position="right"></el-input-number>
            </el-form-item>
          </div>
          <div class="字段注">2 分钟短剧一般 2500~3000 字；偏离目标 20% 以上会在集卡上标红</div>
          <div class="表单两列 开关行">
            <el-form-item label="关键集">
              <el-switch v-model="草稿.关键"></el-switch>
            </el-form-item>
            <el-form-item label="付费卡点">
              <el-switch v-model="草稿.卡点"></el-switch>
            </el-form-item>
          </div>
        </el-form>
      </div>
      <div class="弹窗底">
        <el-button v-if="!新增模式" type="text" class="删除钮" @click="删除这一集()">删除这一集</el-button>
        <div style="flex:1"></div>
        <el-button @click="编辑显示 = false">取消</el-button>
        <el-button type="primary" @click="保存这一集()">{{ 新增模式 ? '加入目录' : '保存' }}</el-button>
      </div>
    </el-dialog>

    <!-- ============ 打点位弹窗 ============ -->
    <el-dialog
      :visible.sync="点位显示"
      width="560px"
      top="10vh"
      :show-close="false"
      :close-on-click-modal="false">
      <div class="弹窗头">
        <div>
          <div class="弹窗标题">EP{{ 点位对象 ? 点位对象.集 : '' }} · 钩子点位</div>
          <div class="弹窗副题">这里打一条，上面的台账和「未回收」立刻跟着变</div>
        </div>
        <i class="el-icon-close 弹窗关闭" title="关闭" @click="点位显示 = false"></i>
      </div>
      <div class="弹窗体">
        <div v-if="点位对象 && (点位对象.点位 || []).length" class="已有点">
          <div v-for="(点, 序) in 点位对象.点位" :key="'已' + 序" class="已有点行">
            <span class="点" :class="'点-' + 点.类型">{{ 点.类型 }} {{ 点.点 }}</span>
            <span class="已有点文">{{ 点.内容 }}</span>
            <el-button type="text" size="mini" class="删点" @click="删点位(序)">删除</el-button>
          </div>
        </div>
        <div v-else class="已有点 空">这一集还没有点位</div>

        <el-form label-width="64px" size="small" style="margin-top:14px">
          <div class="表单两列">
            <el-form-item label="动作">
              <el-select v-model="点位草稿.类型" style="width:130px">
                <el-option v-for="类 in 钩子类型们" :key="类" :label="类" :value="类"></el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="点位">
              <el-select v-model="点位草稿.点" style="width:110px">
                <el-option label="P01" value="P01"></el-option>
                <el-option label="P02" value="P02"></el-option>
                <el-option label="P03" value="P03"></el-option>
                <el-option label="P04" value="P04"></el-option>
                <el-option label="P05" value="P05"></el-option>
              </el-select>
            </el-form-item>
          </div>
          <el-form-item label="内容">
            <el-input v-model="点位草稿.内容" maxlength="40" placeholder="一句话，例如：宣布小组积分制"></el-input>
          </el-form-item>
        </el-form>
      </div>
      <div class="弹窗底">
        <div style="flex:1"></div>
        <el-button @click="点位显示 = false">关闭</el-button>
        <el-button type="primary" @click="保存点位()">加一条</el-button>
      </div>
    </el-dialog>

    <!-- 技能生成弹窗：技能 + 技能引导提示词 + 引入数据（本页一套，引入数据里带人物设定）。
         in-DOM 模板只认 ASCII 标签名，必须用 skill-dialog 别名（见 docs/09 第 8 节）；
         事件处理器必须带括号，否则中文方法名不会被调用（docs/09 第 1.6 节）。 -->
    <skill-dialog
      :显示.sync="技能弹窗显示"
      :技能列表="技能列表"
      :技能id.sync="扩写技能id"
      :引导.sync="技能引导"
      :默认引导="默认引导"
      :配置类型="页配置类型"
      目标名="分集目录"
      :引入数据="引入数据"
      @保存="技能已保存($event)"></skill-dialog>
  </div>
</template>

<script>
import 步骤条 from '@/共用/步骤条/index.vue'
import 技能生成弹窗 from '@/共用/技能生成弹窗/index.vue'
import 剧本页混入 from '@/共用/剧本页混入'
import { 读引导, 读技能id, 读引入, 存引入, 读创意, 存创意, 适配技能id } from '@/共用/技能生成配置'
import { 复制到剪贴板 } from '@/共用/复制文本'
import 情绪折线 from '@/共用/情绪折线/index.vue'
import 钩子台账 from '@/共用/钩子台账/index.vue'
import 集卡 from '@/共用/集卡/index.vue'
import 分页条 from '@/共用/分页条/index.vue'
import { 钩子类型们, 建台账, 找未回收, 连续低谷, 估情绪分 } from '@/共用/节奏工具'
import { 取, 发 } from '@/接口/请求'
import { 提交AI任务 } from '@/共用/AI任务'

// 「引入数据」里来自方案详情的五块（真库 = 方案表分区列，见 this.方案分区值）
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
    if (段.length < 3) return
    条们.push({ 类型: 段[0].trim(), 点: 段[1].trim(), 内容: 段.slice(2).join('｜').trim() })
  })
  return 条们
}

// 本页默认技能引导提示词
const 默认引导文本 = [
  '1. 你要写的是短剧「分集目录」，不是视频/图片提示词：禁止输出 <Picture N>、<Video N>、<Audio N> 之类标签，也不要写镜头运动、光影、音效。',
  '2. 一集一行，格式固定为「集数｜标题｜梗概｜预估字数」，中间用全角竖线 ｜ 分隔，集数从第 1 集连续到最后。',
  '3. 梗概 1~2 句写清这一集发生什么、结尾卡在哪；单集预估字数按 2 分钟短剧 2500~3000 字。',
  '4. 角色只用参考数据里已有的人，不要新造；每集至少推进一条主线，结尾留钩子。',
  '5. 只输出这些行，不要表头、不要解释、不要前后缀。'
].join('\n')

const 状态们 = ['待创作', '进行中', '已完成']

// 首次进页自动生成专用：要求 AI 按富格式一行一集，页面据此直接铺出完整目录卡。
// 手动「AI 生成分集目录」仍用本页配置的技能引导（默认引导的 4 列格式），走差异预览。
const 自动生成引导文本 = [
  '1. 你要写的是短剧「分集目录」初稿，不是视频/图片提示词：禁止输出 <Picture N>、<Video N>、<Audio N> 之类标签，也不要写镜头、光影、音效。',
  '2. 一集一行，一行 12 段，用全角竖线 ｜ 分隔，顺序固定：集数｜标题｜幕｜关键(是/否)｜卡点(是/否)｜情绪分(1-5)｜预估字数｜梗概｜出场人物(顿号分隔)｜开篇钩子｜尾钩｜中心句。',
  '3. 幕只能取：第一幕 · 建置 / 第二幕 · 对抗 / 第三幕 · 收束；集数从第 1 集连续到最后。',
  '4. 梗概 2~3 句写清这一集发生什么、结尾卡在哪；单集预估字数按 2 分钟短剧 2500~3000 字。',
  '5. 每集都要有开篇钩子和尾钩；关键集标「是」的不少于总集数的三分之一；按剧情节奏在付费墙上标卡点「是」。',
  '6. 角色只用参考数据里已有的人，不要新造；每集至少推进一条主线。',
  '7. 只输出这些行，不要表头、不要解释、不要前后缀。'
].join('\n')

// 修改意见的快捷句：点一下追加进需求框，省得手打
const 快捷意见 = [
  '补全关键集标记',
  '付费卡点提前',
  '第二幕加强反派压力',
  '前 3 集节奏加快',
  '拆掉 EP1 的多事件',
  '把连续低谷拉起来'
]

function 空草稿(集号) {
  return {
    集: 集号, 幕: '第一幕 · 建置', 标题: '', 关键: false, 卡点: false,
    梗概: '', 出场: '', 钩子: '', 尾钩: '', 中心句: '',
    情绪分: 3, 字数: 3000, 目标: 3000, 状态: '待创作'
  }
}

export default {
  name: 'ScriptOutlineList',
  mixins: [剧本页混入],
  components: {
    'step-bar': 步骤条,
    'skill-dialog': 技能生成弹窗,
    'emotion-chart': 情绪折线,
    'hook-ledger': 钩子台账,
    'episode-card': 集卡,
    'page-bar': 分页条
  },
  created() {
    // 老地址 /script/outline?步=script|audit 以前是分集剧本/合规审查。
    // 合规审查已下线，两种老参数一律落到分集剧本页。
    const 步 = this.$route.query.步
    if (步 === 'script' || 步 === 'audit') {
      this.$router.replace({
        path: '/script/episode',
        query: Object.assign({}, this.$route.query, { 步: undefined })
      })
      return
    }
    const 路由创意 = (this.$route.query.创意 || '').trim()
    if (路由创意) {
      this.创意文本 = 路由创意
      存创意(this.剧名, 路由创意)
    } else {
      this.创意文本 = 读创意(this.剧名)
    }
    this.载入本页配置()
    this.载入目录()
  },
  watch: {
    // 同路径只改 ?步= 时组件不会重建，created 不会再跑，这里补一次跳转
    '$route.query.步'(值) {
      if (值 === 'script' || 值 === 'audit') {
        this.$router.replace({
          path: '/script/episode',
          query: Object.assign({}, this.$route.query, { 步: undefined })
        })
      }
    }
  },
  data() {
    return {
      /* 真库载入状态 */
      载入中: true,
      载入报错: '',
      剧id: 0,
      方案卡: null,
      方案分区值: {},
      人物行们: [],
      /* 首次自动生成进度 */
      自动生成中: false,
      自动文案: '',
      自动进度: 0,
      方案列表: [],
      // 页面逐集卡（真库回显 / 首次生成，不再用假数据）
      目录表: [],
      /* 视图 */
      视图: '目录',
      展开集: [],
      只看关键: false,
      体检显示: false,
      /* 分页：1000 集也只渲染当前页 */
      当前页: 1,
      每页: 20,
      每页选项: [10, 20, 50, 100],
      /* 本页生成 */
      扩写需求: '',
      生成结果: '',
      差异表: [],
      创意文本: '',
      技能弹窗显示: false,
      技能引导: '',
      引入勾选: null,
      快捷意见: 快捷意见,
      /* 单集编辑弹窗 */
      编辑显示: false,
      新增模式: false,
      编辑对象: null,
      草稿: 空草稿(1),
      /* 打点位弹窗 */
      点位显示: false,
      点位对象: null,
      点位草稿: { 类型: '埋', 点: 'P01', 内容: '' },
      钩子类型们: 钩子类型们
    }
  },
  computed: {
    剧名() {
      return this.$route.query.剧名 || ''
    },
    集数() {
      return this.$route.query.集数 || '24'
    },
    题材() {
      return this.$route.query.题材 || '都市'
    },
    目标集数() {
      const 值 = parseInt(this.集数, 10)
      return isNaN(值) ? 0 : 值
    },
    当前方案() {
      return this.方案卡
    },
    已选方案名() {
      const 卡 = this.方案卡
      if (!卡) return '未选定'
      return (卡.候选卡 && 卡.候选卡.标题) || 卡.版本号 || ('方案#' + 卡.id)
    },
    // 第 3 步（0 起：0 创作方案 / 1 人物设定 / 2 分集目录 / 3 分集剧本）
    当前步() {
      return 2
    },
    /* 本页配置 key：生成:/script/outline */
    页配置类型() {
      return '生成:' + (this.$route.path || '')
    },
    默认引导() {
      return 默认引导文本
    },
    完成数() {
      return this.目录表.filter(function (集) { return 集.状态 === '已完成' }).length
    },
    待创作数() {
      return this.目录表.filter(function (集) { return 集.状态 === '待创作' }).length
    },
    关键数() {
      return this.目录表.filter(function (集) { return 集.关键 }).length
    },
    卡点数() {
      return this.目录表.filter(function (集) { return 集.卡点 }).length
    },

    /* ---------- 节奏 / 钩子（全部派生，不存） ---------- */
    台账() {
      return 建台账(this.目录表)
    },
    未回收() {
      return 找未回收(this.目录表)
    },
    未回收集号() {
      return this.未回收.map(function (条) { return 条.集 })
    },
    埋数() {
      return this.数类型('埋')
    },
    兑数() {
      return this.数类型('兑')
    },
    回收数() {
      return this.数类型('回收')
    },
    低谷段() {
      return 连续低谷(this.目录表)
    },
    黄金三集() {
      const 表 = this.目录表.slice().sort(function (a, b) { return a.集 - b.集 })
      return 表.slice(0, 3)
    },

    /* ---------- 体检 ---------- */
    体检项() {
      const 项 = []
      const 目标 = this.目标集数
      if (目标 && this.目录表.length !== 目标) {
        项.push({
          类: '集数缺口', 级: '黄',
          文: '页头写 ' + 目标 + ' 集，目录里只有 ' + this.目录表.length + ' 集'
        })
      }
      const 偏 = this.目录表.filter(function (集) {
        const 字数 = Number(集.字数) || 0
        const 目 = Number(集.目标) || 0
        if (!目 || !字数) return false
        return Math.abs(字数 - 目) / 目 > 0.2
      })
      if (偏.length) {
        项.push({
          类: '字数偏差', 级: '黄',
          文: '第 ' + 偏.map(function (集) { return 集.集 }).join('、') + ' 集偏离目标字数 20% 以上'
        })
      }
      if (this.低谷段.length) {
        项.push({
          类: '连续低谷', 级: '红',
          文: '第 ' + this.低谷段.map(function (段) {
            return 段.起 === 段.止 ? 段.起 : 段.起 + '–' + 段.止
          }).join('、') + ' 集情绪分连续 ≤2，观众容易掉线'
        })
      }
      if (this.未回收.length) {
        const 前几 = this.未回收.slice(0, 3).map(function (条) {
          return 'EP' + 条.集 + ' ' + 条.点 + '「' + 条.内容 + '」'
        }).join('；')
        项.push({
          类: '未回收钩子', 级: '红',
          文: this.未回收.length + ' 条埋点全剧没有兑或回收：' + 前几 + (this.未回收.length > 3 ? ' …' : '')
        })
      }
      const 缺尾钩 = this.目录表.filter(function (集) { return !集.尾钩 })
      if (缺尾钩.length) {
        项.push({
          类: '缺尾钩', 级: '黄',
          文: '第 ' + 缺尾钩.map(function (集) { return 集.集 }).join('、') + ' 集没有尾钩，结尾会松'
        })
      }
      return 项
    },

    /* ---------- 列表 / 分页 ---------- */
    // 排序后的全量目录（不动原数组）
    排序表() {
      return this.目录表.slice().sort(function (a, b) { return a.集 - b.集 })
    },
    // 过滤（只看关键集）之后、分页之前的那一份
    显示表() {
      if (!this.只看关键) return this.排序表
      return this.排序表.filter(function (集) { return 集.关键 || 集.卡点 })
    },
    总集数() {
      return this.显示表.length
    },
    总页数() {
      const 页 = Math.ceil(this.总集数 / this.每页)
      return 页 > 0 ? 页 : 1
    },
    // 当前页夹在 1..总页数 之间：删集、切过滤之后不会停在空页上
    有效页() {
      const 页 = Number(this.当前页) || 1
      if (页 < 1) return 1
      if (页 > this.总页数) return this.总页数
      return 页
    },
    // 只渲染这一页，1000 集也只有 20 张卡进 DOM
    分页集() {
      const 起 = (this.有效页 - 1) * this.每页
      return this.显示表.slice(起, 起 + this.每页)
    },
    幕们() {
      const 出 = []
      this.分页集.forEach(function (集) {
        const 名 = 集.幕 || '未分幕'
        let 组 = null
        for (let i = 0; i < 出.length; i++) {
          if (出[i].名 === 名) { 组 = 出[i]; break }
        }
        if (!组) { 组 = { 名: 名, 集: [] }; 出.push(组) }
        组.集.push(集)
      })
      // 幕头要显示这个幕在全剧的起止，不是本页的起止（分页会把一个幕切开）
      const 全 = this.排序表
      出.forEach(function (组) {
        const 全组 = 全.filter(function (集) { return (集.幕 || '未分幕') === 组.名 })
        组.全起 = 全组.length ? 全组[0].集 : 组.集[0].集
        组.全止 = 全组.length ? 全组[全组.length - 1].集 : 组.集[组.集.length - 1].集
        组.全数 = 全组.length
      })
      return 出
    },
    全展开() {
      if (!this.分页集.length) return false
      const 页 = this
      return this.分页集.every(function (集) { return 页.展开集.indexOf(集.集) >= 0 })
    },
    差异改动数() {
      return this.差异表.filter(function (行) { return 行.类型 !== '未变' }).length
    },
    勾选数() {
      return this.差异表.filter(function (行) { return 行.勾选 }).length
    },

    /* 引入数据：标题 + 一句话创意 + 已选方案 + 方案七块 + 角色信息 */
    引入数据() {
      return this.造引入数据(this.引入勾选)
    }
  },
  methods: {
    /* ---------------- 载入 / 保存（真库） ---------------- */
    async 载入目录() {
      this.载入中 = true
      this.载入报错 = ''
      try {
        await this.取剧与方案()
        if (!this.剧id) {
          this.载入报错 = '找不到这部剧：请从「我的剧」或「新建剧本」进入本页'
          return
        }
        await this.取方案分区()
        await this.取人物清单()
        const 数据 = await 取('/api/分集/列表?剧id=' + this.剧id)
        const 行们 = (数据 && 数据.分集们) || []
        if (行们.length) {
          this.目录表 = 行们.map(行 => this.库转集(行))
        } else {
          this.目录表 = []
          this.载入中 = false
          await this.首次生成()
        }
        // 默认只展开关键集和卡点集，其余折叠成一行摘要
        this.展开集 = this.目录表.filter(function (集) { return 集.关键 || 集.卡点 })
          .map(function (集) { return 集.集 })
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
      } catch (e) { /* 分区取不到就让引入数据里这几块为空 */ }
    },
    // 读人物设定真库清单（引入数据用，只留 CHAR_ 人）
    async 取人物清单() {
      this.人物行们 = []
      try {
        const 数据 = await 取('/api/人物/列表?剧id=' + this.剧id)
        this.人物行们 = (数据 && 数据.人物们) || []
      } catch (e) { /* 人物取不到就让角色信息块为空 */ }
    },
    // 库行 → 页面集卡（点位行文本解析回数组，出场按顿号拆开）
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
    // 页面集卡 → 库行（出场并成顿号文本，点位并成行文本）
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
    // 全量落库（后端按剧全量替换）
    async 存全库() {
      const 批 = this.排序表.map(集 => this.集转库(集))
      await 发('/api/分集/保存', { 剧id: this.剧id, 分集们: 批 })
    },
    // 首次进页（库里没有分集）：AI 按富格式一次产出一版，逐段落库带进度
    async 首次生成() {
      if (!this.扩写技能id && this.技能列表.length) this.扩写技能id = 适配技能id(this.技能列表, this.页配置类型)
      if (!this.扩写技能id) {
        this.$message.warning('还没有可用技能（剧本创作分类为空），先去「技能」里建一个再进本页')
        return
      }
      this.自动生成中 = true
      this.自动进度 = 10
      const 页 = this
      try {
        this.自动文案 = 'AI 正在为本剧生成分集目录…'
        const 参考 = this.参考块()
        const 需求 = (参考 ? [参考, ''] : []).concat([
          '剧名：' + this.剧名,
          '集数：' + this.集数 + ' 集',
          '题材：' + this.题材,
          '要生成的内容：全剧分集目录（共 ' + this.集数 + ' 集，一集一行）'
        ]).join('\n')
        const 文本 = String(await 提交AI任务({
          正向: 需求,
          系统: 自动生成引导文本,
          技能id: this.扩写技能id
        }) || '').trim()
        if (!文本) throw new Error('AI 没有返回分集目录内容')

        this.自动进度 = 55
        this.自动文案 = '正在解析 AI 返回的目录…'
        const 新们 = this.解析富行(文本)
        if (!新们.length) throw new Error('没认出「集数｜标题｜…」格式的目录行')
        // 补缺的幕与情绪分，铺齐集号
        新们.forEach(function (集) {
          if (!集.幕) 集.幕 = 页.按比例分幕(集.集, 页.目标集数 || 新们.length)
          if (!集.情绪分) 集.情绪分 = 估情绪分(集) || 3
        })
        this.目录表 = 新们.sort(function (a, b) { return a.集 - b.集 })

        this.自动进度 = 75
        this.自动文案 = '正在保存分集目录…'
        await this.存全库()
        this.自动进度 = 100
        this.$message.success('已生成本剧 ' + 新们.length + ' 集分集目录并保存')
      } catch (e) {
        this.$message.error((e && e.message) || '首次生成失败，可点「AI 生成分集目录」重试')
      } finally {
        this.自动生成中 = false
      }
    },
    // 解析首次生成的富格式行（12 段），兼容退回 4 段简格式（集数｜标题｜梗概｜字数）
    解析富行(文本) {
      const 页 = this
      const 出 = []
      String(文本 || '').replace(/\r\n?/g, '\n').split('\n').forEach(function (行) {
        const 净 = 行.trim()
        if (!净) return
        const 段 = 净.split('｜').map(function (片) { return 片.trim() })
        const 号 = parseInt(String(段[0]).replace(/[^0-9]/g, ''), 10)
        if (!号 || isNaN(号)) return
        if (段.length >= 12) {
          出.push({
            集: 号, 标题: 段[1] || '', 幕: 段[2] || '',
            关键: 段[3] === '是', 卡点: 段[4] === '是',
            情绪分: Math.min(5, Math.max(1, parseInt(段[5], 10) || 3)),
            字数: parseInt(String(段[6]).replace(/[^0-9]/g, ''), 10) || 3000,
            目标: parseInt(String(段[6]).replace(/[^0-9]/g, ''), 10) || 3000,
            状态: '待创作',
            梗概: 段[7] || '',
            出场: String(段[8] || '').split(/[、,，]/).map(function (s) { return s.trim() }).filter(Boolean),
            钩子: 段[9] || '', 尾钩: 段[10] || '', 中心句: 段[11] || '',
            点位: []
          })
          return
        }
        // 退回简格式：集数｜标题｜梗概｜字数（只认 3~4 段；5~11 段是富格式被截断的残行，
        // 按简格式解析会把幕名当梗概，宁可丢弃等「补齐集数」兜底）
        if (段.length === 3 || 段.length === 4) {
          const 字数 = parseInt(String(段[3] || '').replace(/[^0-9]/g, ''), 10) || 3000
          出.push({
            集: 号, 标题: 段[1] || '', 幕: 页.按比例分幕(号, 页.目标集数 || 0),
            关键: false, 卡点: false, 情绪分: 3, 字数: 字数, 目标: 3000,
            状态: '待创作', 梗概: 段[2] || '', 出场: [], 钩子: '', 尾钩: '', 中心句: '', 点位: []
          })
        }
      })
      return 出
    },
    保存() {
      const 页 = this
      this.存全库().then(function () {
        页.$message({ message: '已保存「分集目录」当前内容（数据库）', type: 'success' })
      }).catch(function (e) {
        页.$message.error('保存失败：' + ((e && e.message) || '数据库不可用'))
      })
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
        { 键: '方案', 名: '已选方案（' + this.已选方案名 + '）', 值: this.已选方案文本() }
      ]
      方案分区.forEach(区 => {
        项们.push({ 键: 区.键, 名: 区.名, 值: this.方案分区文本(区) })
      })
      // 角色信息：人物设定库里定下来的角色，分集目录必须照这些人写
      项们.push({ 键: '角色信息', 名: '角色信息（来自人物设定）', 值: this.角色清单文本() })
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
    // 人物设定真库角色清单：只留 CHAR_ 人，字段铺全（关系/性格/目标/背景/台词风格…）
    角色清单文本() {
      const 行们 = []
      this.人物行们.forEach(人 => {
        if (String(人.人物id || '').indexOf('CHAR_') !== 0) return
        const 段们 = []
        const 字段们 = [
          ['本剧关系', 人.关系], ['性别', 人.性别], ['年龄档', 人.年龄档], ['性格', 人.性格],
          ['简介', 人.简介], ['身份', 人.身份], ['态度', 人.态度], ['核心目标', 人.核心目标],
          ['背景故事', 人.背景故事], ['台词风格', 人.台词风格], ['口头禅', 人.口头禅], ['概括', 人.概括]
        ]
        字段们.forEach(function (对) {
          const 值 = String(对[1] || '').trim()
          if (值) 段们.push(对[0] + '：' + 值)
        })
        if (!段们.length) return
        行们.push('【' + (人.名 || '未命名') + '】\n' + 段们.join('\n'))
      })
      return 行们.join('\n\n')
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

    /* ---------------- 修改意见快捷句 ---------------- */
    加意见(句) {
      const 现 = this.扩写需求 || ''
      if (现.indexOf(句) >= 0) {
        this.扩写需求 = 现.replace(句, '').replace(/；；/g, '；').replace(/^；|；$/g, '').trim()
        return
      }
      this.扩写需求 = 现.trim() ? 现.trim() + '；' + 句 : 句
    },

    /* ---------------- AI 生成分集目录 ---------------- */
    async 生成目录() {
      if (!this.扩写技能id) {
        this.$message.warning('请先在「技能」里选一个技能')
        return
      }
      const 参考 = this.参考块()
      const 需求 = (参考 ? [参考, ''] : []).concat([
        '剧名：' + this.剧名,
        '集数：' + this.集数 + ' 集',
        '题材：' + this.题材,
        '要生成的内容：分集目录',
        '要求：' + (this.扩写需求.trim() || '按已选方案和人物设定直接产出一版')
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
        const 数 = this.解析差异()
        if (数) {
          this.$message.success('已生成，下方有 ' + 数 + ' 集差异待你勾选写入')
        } else {
          this.$message.success('已生成，和现有目录没有差异')
        }
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

    /* ---------------- 差异预览 / 写入 ---------------- */
    // 按「集数｜标题｜梗概｜字数」解析 AI 原文，逐集和现有目录比对
    解析差异() {
      const 文本 = String(this.生成结果 || '')
      const 行们 = 文本.split(/\r?\n/)
      const 解析出 = []
      行们.forEach(function (行) {
        const 净 = 行.trim()
        if (!净) return
        const 段 = 净.split(/[｜|]/).map(function (片) { return 片.trim() })
        if (段.length < 3) return
        const 号 = parseInt(String(段[0]).replace(/[^0-9]/g, ''), 10)
        if (!号 || isNaN(号)) return
        const 字数 = parseInt(String(段[3] || '').replace(/[^0-9]/g, ''), 10) || 0
        解析出.push({ 集: 号, 标题: 段[1] || '', 梗概: 段[2] || '', 字数: 字数 })
      })
      if (!解析出.length) {
        this.差异表 = []
        return 0
      }
      const 页 = this
      this.差异表 = 解析出.map(function (行) {
        let 现有 = null
        for (let i = 0; i < 页.目录表.length; i++) {
          if (页.目录表[i].集 === 行.集) { 现有 = 页.目录表[i]; break }
        }
        if (!现有) {
          return {
            集: 行.集, 标题: 行.标题, 梗概: 行.梗概, 字数: 行.字数,
            类型: '新增', 勾选: true, 说明: '目录里还没有这一集'
          }
        }
        const 变题 = 行.标题 && 行.标题 !== 现有.标题
        const 变概 = 行.梗概 && 行.梗概 !== 现有.梗概
        const 变字 = 行.字数 && 行.字数 !== 现有.字数
        if (!变题 && !变概 && !变字) {
          return {
            集: 行.集, 标题: 行.标题, 梗概: 行.梗概, 字数: 行.字数,
            类型: '未变', 勾选: false, 说明: '和现有内容一致'
          }
        }
        const 说明 = []
        if (变题) 说明.push('标题改动')
        if (变概) {
          说明.push('梗概重写（' + String(现有.梗概 || '').length + ' 字 → ' + String(行.梗概).length + ' 字）')
        }
        if (变字) 说明.push('字数 ' + 现有.字数 + ' → ' + 行.字数)
        return {
          集: 行.集, 标题: 行.标题, 梗概: 行.梗概, 字数: 行.字数,
          类型: '改动', 勾选: true, 说明: 说明.join('，')
        }
      })
      return this.差异改动数
    },
    重新解析() {
      const 数 = this.解析差异()
      this.$message[数 ? 'success' : 'info'](数 ? '解析出 ' + 数 + ' 集差异' : '没解析出「集数｜标题｜梗概｜字数」格式的行')
    },
    全选差异(值) {
      this.差异表.forEach(function (行) {
        if (行.类型 !== '未变') 行.勾选 = 值
      })
    },
    写入差异() {
      const 页 = this
      let 写 = 0
      this.差异表.forEach(function (行) {
        if (!行.勾选) return
        let 现有 = null
        for (let i = 0; i < 页.目录表.length; i++) {
          if (页.目录表[i].集 === 行.集) { 现有 = 页.目录表[i]; break }
        }
        if (现有) {
          if (行.标题) 现有.标题 = 行.标题
          if (行.梗概) 现有.梗概 = 行.梗概
          if (行.字数) 现有.字数 = 行.字数
        } else {
          页.目录表.push({
            集: 行.集,
            幕: 页.按比例分幕(行.集, 页.目标集数 || 页.目录表.length + 1),
            标题: 行.标题,
            关键: false,
            卡点: false,
            情绪分: 估情绪分(行),
            字数: 行.字数 || 3000,
            目标: 3000,
            状态: '待创作',
            梗概: 行.梗概,
            出场: [],
            钩子: '',
            尾钩: '',
            中心句: '',
            点位: []
          })
        }
        写++
      })
      this.目录表.sort(function (a, b) { return a.集 - b.集 })
      this.差异表 = []
      const 页2 = this
      this.存全库().then(function () {
        页2.$message.success('已写入 ' + 写 + ' 项并保存')
      }).catch(function (e) {
        页2.$message.warning('已写入页面，但落库失败：' + ((e && e.message) || ''))
      })
    },

    /* ---------------- 展开 / 定位 ---------------- */
    是展开(集) {
      return this.展开集.indexOf(集.集) >= 0
    },
    切换展开(集) {
      const 序 = this.展开集.indexOf(集.集)
      if (序 >= 0) this.展开集.splice(序, 1)
      else this.展开集.push(集.集)
    },
    切换全部展开() {
      const 页 = this
      if (this.全展开) {
        this.分页集.forEach(function (集) {
          const 序 = 页.展开集.indexOf(集.集)
          if (序 >= 0) 页.展开集.splice(序, 1)
        })
        return
      }
      this.分页集.forEach(function (集) {
        if (页.展开集.indexOf(集.集) < 0) 页.展开集.push(集.集)
      })
    },
    换页(页) {
      this.当前页 = 页
    },
    换每页(数) {
      this.每页 = 数
      this.当前页 = 1
    },
    切只看关键() {
      this.只看关键 = !this.只看关键
      this.当前页 = 1
    },
    // 把某一集所在的页翻出来（不滚动）。找不到就不动，返回 false
    翻到集(集号) {
      const 表 = this.显示表
      for (let i = 0; i < 表.length; i++) {
        if (表[i].集 === 集号) {
          this.当前页 = Math.floor(i / this.每页) + 1
          return true
        }
      }
      return false
    },
    // 点折线 / 点台账格子：先翻到它所在的页，再滚过去闪一下
    定位到集(集号) {
      this.视图 = '目录'
      let 找到 = this.翻到集(集号)
      // 只看关键集时目标可能被过滤掉了，临时放开再看一次
      if (!找到 && this.只看关键) {
        this.只看关键 = false
        找到 = this.翻到集(集号)
      }
      if (!找到) return
      const 页 = this
      this.$nextTick(function () {
        const 元 = document.getElementById('ep-card-' + 集号)
        if (!元) return
        元.scrollIntoView({ behavior: 'smooth', block: 'center' })
        const 卡 = 元.querySelector('.集卡')
        if (!卡) return
        卡.classList.add('闪')
        setTimeout(function () { 卡.classList.remove('闪') }, 1600)
      })
    },
    情绪档(集) {
      if (集.情绪分 <= 2) return '低谷'
      if (集.情绪分 >= 4) return '强钩'
      return '推进'
    },
    数类型(类) {
      const 行 = this.台账[类] || {}
      let 数 = 0
      Object.keys(行).forEach(function (集号) { 数 += 行[集号].length })
      return 数
    },

    /* ---------------- 单集编辑 / 新增 ---------------- */
    打开编辑(集) {
      if (!集) return
      this.新增模式 = false
      this.编辑对象 = 集
      this.草稿 = {
        集: 集.集,
        幕: 集.幕 || '第一幕 · 建置',
        标题: 集.标题 || '',
        关键: !!集.关键,
        卡点: !!集.卡点,
        梗概: 集.梗概 || '',
        出场: (集.出场 || []).join('、'),
        钩子: 集.钩子 || '',
        尾钩: 集.尾钩 || '',
        中心句: 集.中心句 || '',
        情绪分: 集.情绪分 || 3,
        字数: 集.字数 || 0,
        目标: 集.目标 || 3000,
        状态: 集.状态 || '待创作'
      }
      this.编辑显示 = true
    },
    新增一集() {
      let 最大 = 0
      this.目录表.forEach(function (集) { if (集.集 > 最大) 最大 = 集.集 })
      this.新增模式 = true
      this.编辑对象 = null
      this.草稿 = 空草稿(最大 + 1)
      this.草稿.幕 = this.按比例分幕(最大 + 1, this.目标集数 || 最大 + 1)
      this.编辑显示 = true
    },
    草稿转集(草稿) {
      return {
        集: 草稿.集,
        幕: 草稿.幕,
        标题: 草稿.标题,
        关键: !!草稿.关键,
        卡点: !!草稿.卡点,
        梗概: 草稿.梗概,
        出场: String(草稿.出场 || '').split(/[、,，\s]+/).filter(function (人) { return !!人 }),
        钩子: 草稿.钩子,
        尾钩: 草稿.尾钩,
        中心句: 草稿.中心句,
        情绪分: 草稿.情绪分 || 3,
        字数: 草稿.字数,
        目标: 草稿.目标,
        状态: 草稿.状态
      }
    },
    保存这一集() {
      if (this.新增模式) {
        if (!String(this.草稿.标题 || '').trim()) {
          this.$message.warning('先给这一集起个标题')
          return
        }
        const 新集 = this.草稿转集(this.草稿)
        新集.点位 = []
        this.目录表.push(新集)
        this.目录表.sort(function (a, b) { return a.集 - b.集 })
        this.只看关键 = false
        this.翻到集(新集.集)
        this.编辑显示 = false
        const 页2 = this
        this.存全库().then(function () {
          页2.$message.success('已加入第 ' + 新集.集 + ' 集并保存')
        }).catch(function (e) {
          页2.$message.warning('已加入页面，但落库失败：' + ((e && e.message) || ''))
        })
        return
      }
      const 集 = this.编辑对象
      if (!集) {
        this.编辑显示 = false
        return
      }
      const 改后 = this.草稿转集(this.草稿)
      // 整条替换而不是逐字段赋值：老数据可能没有 幕/关键/卡点/情绪分 这些新键，
      // 直接赋新键 Vue 2 不认（不是响应式），卡片不会刷新。
      const 序 = this.目录表.indexOf(集)
      const 新集 = Object.assign({}, 集, 改后)
      if (序 >= 0) this.$set(this.目录表, 序, 新集)
      this.目录表.sort(function (a, b) { return a.集 - b.集 })
      this.编辑显示 = false
      const 页2 = this
      this.存全库().then(function () {
        页2.$message.success('已保存第 ' + 新集.集 + ' 集并落库')
      }).catch(function (e) {
        页2.$message.warning('已保存到页面，但落库失败：' + ((e && e.message) || ''))
      })
    },
    删除这一集() {
      const 集 = this.编辑对象
      if (!集) return
      const 页 = this
      this.$confirm('确定删除第 ' + 集.集 + ' 集「' + 集.标题 + '」？', '删除这一集', {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(function () {
        const 序 = 页.目录表.indexOf(集)
        if (序 >= 0) 页.目录表.splice(序, 1)
        页.编辑显示 = false
        页.存全库().then(function () {
          页.$message.success('已删除第 ' + 集.集 + ' 集并落库')
        }).catch(function (e) {
          页.$message.warning('已从页面删除，但落库失败：' + ((e && e.message) || ''))
        })
      }).catch(function () {})
    },
    状态类型(状态) {
      if (状态 === '已完成') return 'success'
      if (状态 === '进行中') return 'warning'
      return 'info'
    },

    /* ---------------- 钩子点位 ---------------- */
    打开点位(集) {
      if (!集) return
      this.点位对象 = 集
      this.点位草稿 = { 类型: '埋', 点: 'P01', 内容: '' }
      this.点位显示 = true
    },
    保存点位() {
      const 集 = this.点位对象
      if (!集) return
      const 文 = String(this.点位草稿.内容 || '').trim()
      if (!文) {
        this.$message.warning('写一句这个点位是什么')
        return
      }
      if (!集.点位) this.$set(集, '点位', [])
      集.点位.push({ 类型: this.点位草稿.类型, 点: this.点位草稿.点, 内容: 文 })
      this.点位草稿.内容 = ''
      const 页2 = this
      this.存全库().then(function () {
        页2.$message.success('已加到 EP' + 集.集 + ' 并落库')
      }).catch(function (e) {
        页2.$message.warning('已加到页面，但落库失败：' + ((e && e.message) || ''))
      })
    },
    删点位(序) {
      const 页2 = this
      const 集 = this.点位对象
      if (!集 || !集.点位) return
      集.点位.splice(序, 1)
      页2.存全库().catch(function (e) {
        页2.$message.warning('点位已删，但落库失败：' + ((e && e.message) || ''))
      })
    },

    /* ---------------- 补齐集数 ---------------- */
    按比例分幕(集号, 总数) {
      const 总 = Number(总数) || 0
      if (!总) return '第一幕 · 建置'
      const 比 = 集号 / 总
      if (比 <= 0.25) return '第一幕 · 建置'
      if (比 <= 0.75) return '第二幕 · 对抗'
      return '第三幕 · 收束'
    },
    补齐集数() {
      const 目标 = this.目标集数
      if (!目标) return
      let 最大 = 0
      this.目录表.forEach(function (集) { if (集.集 > 最大) 最大 = 集.集 })
      if (最大 >= 目标) return
      for (let 号 = 最大 + 1; 号 <= 目标; 号++) {
        const 空 = 空草稿(号)
        this.目录表.push({
          集: 号,
          幕: this.按比例分幕(号, 目标),
          标题: '',
          关键: false,
          卡点: false,
          梗概: '',
          出场: [],
          钩子: '',
          尾钩: '',
          中心句: '',
          情绪分: 空.情绪分,
          字数: 0,
          目标: 3000,
          状态: '待创作',
          点位: []
        })
      }
      this.只看关键 = false
      this.当前页 = Math.ceil(this.显示表.length / this.每页)
      const 页2 = this
      this.存全库().then(function () {
        页2.$message.success('已补齐到 ' + 目标 + ' 集，空卡待填（已落库）')
      }).catch(function (e) {
        页2.$message.warning('已补齐页面，但落库失败：' + ((e && e.message) || ''))
      })
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
        path: '/script/character',
        query: Object.assign({}, this.$route.query)
      })
    },
    async 下一步() {
      try {
        await this.存全库()
      } catch (e) {
        this.$message.warning('落库失败，已取消跳转：' + ((e && e.message) || ''))
        return
      }
      this.$router.push({
        path: '/script/episode',
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
    }
  }
}
</script>

<style scoped>
/* 首次自动生成进度遮罩（与人物设定页同一形态） */
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

/* ---------- 节奏总览带 ---------- */
.总览带 {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 14px;
  margin-bottom: 16px;
}
.曲线卡 { min-width: 0; }
.侧列 { display: flex; flex-direction: column; gap: 14px; min-width: 0; }

.卡头 {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.卡名 { font-size: 13px; font-weight: 700; color: var(--字); }
.卡注 { font-size: 11px; color: var(--字弱); }

.金集 { display: flex; gap: 8px; }
.金卡 {
  flex: 1;
  min-width: 0;
  background: var(--卡片二);
  border: 1px solid var(--描边);
  border-radius: 8px;
  padding: 8px 9px;
  cursor: pointer;
  transition: border-color 0.15s ease;
}
.金卡:hover { border-color: var(--主); }
.金头 { font-size: 10.5px; font-weight: 700; color: var(--主); }
.金题 {
  margin-top: 2px;
  font-size: 11.5px;
  line-height: 1.45;
  color: var(--字次);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.体检 { display: flex; gap: 8px; }
.检 {
  flex: 1;
  text-align: center;
  background: var(--卡片二);
  border: 1px solid var(--描边);
  border-radius: 8px;
  padding: 7px 4px;
}
.检 .数 { font-size: 17px; font-weight: 800; line-height: 1.2; }
.检 .数.蓝 { color: #60a5fa; }
.检 .数.绿 { color: var(--主); }
.检 .数.青 { color: #2dd4bf; }
.检 .数.红 { color: #ef4444; }
.检 .名 { font-size: 10px; color: var(--字弱); }

.告警 {
  margin-top: 10px;
  font-size: 11.5px;
  line-height: 1.6;
  color: #fca5a5;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 7px;
  padding: 6px 9px;
  cursor: pointer;
}
.告警.好 {
  color: var(--主);
  background: var(--主浅);
  border-color: rgba(34, 197, 94, 0.3);
  cursor: default;
}
.告警多 { color: var(--字弱); margin-left: 4px; }

/* ---------- 本页生成条（和创作方案页的「修改意见」同一形态） ---------- */
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
.意见快捷 { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 12px; }
.意见输入 { margin-top: 10px; }

/* ---------- 差异预览 ---------- */
.差异卡 { margin-bottom: 16px; }
.差列 { max-height: 320px; overflow-y: auto; }
.差行 {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 0;
  font-size: 12.5px;
  color: var(--字次);
  border-bottom: 1px dashed rgba(30, 41, 59, 0.9);
}
.差行:last-of-type { border-bottom: 0; }
.差标 {
  flex: 0 0 auto;
  font-size: 10.5px;
  border-radius: 4px;
  padding: 0 6px;
  font-weight: 700;
}
.差标.新增 { color: var(--主); background: var(--主浅); }
.差标.改动 { color: #fcd34d; background: rgba(245, 158, 11, 0.14); }
.差标.未变 { color: var(--字弱); background: var(--描边); }
.差集 { color: var(--字); font-weight: 600; }
.差文 { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.差注 { color: var(--字弱); margin-left: 8px; }

/* ---------- 生成结果 ---------- */
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

/* ---------- 列表工具条 ---------- */
.列表工具 {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  margin-bottom: 12px;
  background: var(--卡片二);
  border: 1px solid var(--描边);
  border-radius: 10px;
  flex-wrap: wrap;
}
.工具数 { font-size: 12px; color: var(--字弱); }

/* ---------- 幕分组 ---------- */
.幕组 { margin-bottom: 6px; }
.幕头 {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 14px 0 8px;
}
.幕竖 { width: 3px; height: 14px; background: var(--主); border-radius: 2px; }
.幕名 { font-size: 12.5px; font-weight: 700; color: var(--字); }
.幕数 { font-size: 11px; color: var(--字弱); }
.幕线 { flex: 1; height: 1px; background: var(--描边); }
.卡位 { scroll-margin-top: 80px; }

/* ---------- 台账视图 ---------- */
.台账视图 { margin-bottom: 8px; }
.台账提示 {
  margin-bottom: 8px;
  font-size: 11.5px;
  line-height: 1.6;
  color: var(--字弱);
}

/* ---------- 弹窗 ---------- */
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
.字段注 { font-size: 12px; color: var(--字弱); margin: -4px 0 14px 80px; }

.表单两列 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 16px;
}
.开关行 { margin-top: 4px; }

/* ---------- 体检弹窗 ---------- */
.体检空 { padding: 24px 0; text-align: center; font-size: 13px; color: var(--字弱); }
.体检项 {
  display: flex;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px dashed var(--描边);
}
.体检项:last-child { border-bottom: 0; }
.体检级 {
  flex: 0 0 auto;
  height: 20px;
  line-height: 18px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 11px;
  border: 1px solid;
}
.体检级.红 { color: #fca5a5; border-color: rgba(239, 68, 68, 0.45); background: rgba(239, 68, 68, 0.12); }
.体检级.黄 { color: #fcd34d; border-color: rgba(245, 158, 11, 0.45); background: rgba(245, 158, 11, 0.12); }
.体检类 { font-size: 13px; font-weight: 650; color: var(--字); }
.体检文 { font-size: 12.5px; line-height: 1.7; color: var(--字次); }

/* ---------- 点位弹窗 ---------- */
.已有点 {
  background: var(--卡片二);
  border: 1px solid var(--描边);
  border-radius: 8px;
  padding: 8px 10px;
}
.已有点.空 { font-size: 12px; color: var(--字弱); text-align: center; padding: 14px 10px; }
.已有点行 { display: flex; align-items: center; gap: 8px; padding: 3px 0; }
.已有点文 { flex: 1; min-width: 0; font-size: 12px; color: var(--字次); }
.删点 { color: #ef4444 !important; }
.已有点行 .点 {
  font-size: 10px;
  line-height: 16px;
  border-radius: 4px;
  padding: 0 6px;
  border: 1px solid;
  font-family: Consolas, 'Courier New', monospace;
}
.已有点行 .点-埋 { color: #93c5fd; border-color: rgba(96, 165, 250, 0.4); background: rgba(96, 165, 250, 0.12); }
.已有点行 .点-露 { color: #a5b4fc; border-color: rgba(129, 140, 248, 0.4); background: rgba(129, 140, 248, 0.12); }
.已有点行 .点-压 { color: #fca5a5; border-color: rgba(239, 68, 68, 0.4); background: rgba(239, 68, 68, 0.12); }
.已有点行 .点-兑 { color: #86efac; border-color: rgba(34, 197, 94, 0.4); background: rgba(34, 197, 94, 0.12); }
.已有点行 .点-假兑 { color: #fcd34d; border-color: rgba(245, 158, 11, 0.45); background: rgba(245, 158, 11, 0.12); }
.已有点行 .点-回收 { color: #5eead4; border-color: rgba(45, 212, 191, 0.4); background: rgba(45, 212, 191, 0.12); }
.已有点行 .点-转 { color: #d8b4fe; border-color: rgba(192, 132, 252, 0.4); background: rgba(192, 132, 252, 0.12); }

@media (max-width: 1100px) {
  .总览带 { grid-template-columns: 1fr; }
  .表单两列 { grid-template-columns: 1fr; }
}
</style>
