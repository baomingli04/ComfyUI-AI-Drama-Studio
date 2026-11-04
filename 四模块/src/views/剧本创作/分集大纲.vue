<template>
  <div>
    <!-- 面包屑 -->
    <div class="面包屑条">
      <span class="可点" @click="$router.push('/script')">剧本创作</span>
      <span> / </span>
      <span class="可点" @click="$router.push('/script/plan')">创作方案</span>
      <span> / </span>
      <span>分集大纲</span>
    </div>

    <!-- 页头 -->
    <div class="页头">
      <div class="左">
        <h1 class="标题">{{ 剧名 }}</h1>
        <div class="副题">{{ 集数 }} 集 · {{ 题材 }} · 已采用 {{ 当前方案.标题 }}</div>
      </div>
      <div class="右">
        <el-button @click="$router.push('/script/plan')">返回方案</el-button>
        <el-button type="primary" @click="$message({ message: '已保存全部大纲内容', type: 'success' })">保存全部</el-button>
      </div>
    </div>

    <div class="卡片" style="margin-bottom:16px;font-size:13px;color:var(--字次)">
      分集目录与人物设定已按方案生成，如需调整请先返回创作方案页重置。
    </div>

    <el-tabs v-model="当前标签">
      <!-- 创作方案 -->
      <el-tab-pane label="创作方案" name="plan">
        <div class="卡片">
          <div class="行间">
            <div style="font-size:18px;font-weight:600">{{ 当前方案.标题 }}</div>
            <div style="flex:1"></div>
            <span class="小标签">已采用</span>
          </div>
          <div style="margin-top:10px;font-size:14px;color:var(--字次);line-height:1.8">
            {{ 当前方案.一句话 }}
          </div>
          <div class="网格 三" style="margin-top:16px">
            <div>
              <div style="font-size:12px;color:var(--字弱)">规划集数</div>
              <div style="font-size:16px;margin-top:4px">{{ 当前方案.集数 }} 集</div>
            </div>
            <div>
              <div style="font-size:12px;color:var(--字弱)">核心亮点</div>
              <div style="font-size:14px;margin-top:4px">{{ 当前方案.亮点.join(' / ') }}</div>
            </div>
            <div>
              <div style="font-size:12px;color:var(--字弱)">题材标签</div>
              <div style="margin-top:4px">
                <el-tag v-for="标 in 当前方案.标签" :key="标" size="mini" style="margin-right:6px">{{ 标 }}</el-tag>
              </div>
            </div>
          </div>
          <el-divider></el-divider>
          <div style="font-size:12px;color:var(--字弱);margin-bottom:6px">故事线与三幕结构</div>
          <div style="font-size:13px;color:var(--字次);line-height:1.8">
            第一幕（第 1-3 集）建置：林夜回到十年前讲台，当众演示禁术基础术式，插班生苏浅坐到最后一排。<br>
            第二幕（第 4-8 集）对抗：周正要求停课，林夜在资料室翻出十年前名单，校医叶青青说出禁术代价。<br>
            第三幕（第 9-24 集）高潮：陈默登场说出只有重生者才知道的话，林夜在黑板上落下第一枚棋子。
          </div>
        </div>
      </el-tab-pane>

      <!-- 人物设定 -->
      <el-tab-pane label="人物设定" name="character">
        <div class="网格 三">
          <div v-for="人 in 人物设定" :key="人.id" class="卡片">
            <div class="行间">
              <div class="占位图" :style="{ width:'56px', height:'56px', borderRadius:'999px', background: 人.色, flex:'0 0 56px' }">原图：{{ 人.名 }} 头像</div>
              <div style="flex:1">
                <div style="font-size:16px;font-weight:600">{{ 人.名 }}</div>
                <div style="font-size:12px;color:var(--字弱);margin-top:4px">
                  {{ 人.性别 }} · {{ 人.年龄 }} 岁 · {{ 人.身份 }}
                </div>
              </div>
            </div>
            <div style="margin-top:12px;font-size:13px;color:var(--字次);line-height:1.7">
              {{ 人.简介 }}
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 分集目录 -->
      <el-tab-pane label="分集目录" name="outline">
        <div class="卡片 无内距">
          <el-table :data="分集目录" style="width:100%">
            <el-table-column prop="集" label="集" width="70"></el-table-column>
            <el-table-column prop="标题" label="标题" width="180"></el-table-column>
            <el-table-column prop="梗概" label="梗概"></el-table-column>
            <el-table-column prop="字数" label="字数" width="100"></el-table-column>
            <el-table-column label="状态" width="120">
              <template slot-scope="域">
                <el-tag size="mini" :type="状态类型(域.row.状态)">{{ 域.row.状态 }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 分集剧本 -->
      <el-tab-pane label="分集剧本" name="script">
        <div class="网格 二" style="grid-template-columns:220px 1fr">
          <div class="卡片" style="align-self:start">
            <div style="font-size:12px;color:var(--字弱);margin-bottom:8px">集数列表</div>
            <div
              v-for="集 in 分集目录"
              :key="集.集"
              class="集项"
              :class="{ 当前: 当前集 === 集.集 }"
              @click="当前集 = 集.集">
              <div style="font-size:13px">第 {{ 集.集 }} 集 {{ 集.标题 }}</div>
              <div style="font-size:12px;color:var(--字弱);margin-top:2px">{{ 集.字数 }} 字</div>
            </div>
          </div>

          <div>
            <div class="卡片" style="margin-bottom:16px">
              <div class="行间">
                <div>
                  <div style="font-size:16px;font-weight:600">第 {{ 当前集 }} 集 {{ 当前目录.标题 }}</div>
                  <div style="font-size:12px;color:var(--字弱);margin-top:4px">{{ 当前目录.梗概 }}</div>
                </div>
                <div style="flex:1"></div>
                <div class="行间">
                  <el-button size="mini" @click="$message({ message: '已暂存本集', type: 'success' })">暂存</el-button>
                  <el-button size="mini" type="primary" @click="保存并继续()">保存并继续</el-button>
                </div>
              </div>
            </div>

            <div v-for="场 in 当前场次" :key="场.场" class="卡片" style="margin-bottom:16px">
              <div class="行间" style="padding-bottom:10px;border-bottom:1px solid var(--描边)">
                <div style="width:3px;height:16px;background:var(--主);border-radius:999px"></div>
                <div style="font-size:14px;color:var(--主)">{{ 场.场 }} · {{ 场.地点 }}</div>
                <div style="flex:1"></div>
                <div style="font-size:12px;color:var(--字弱)">{{ 场.人物 }}</div>
              </div>
              <div style="padding-top:10px;font-size:13px;color:var(--字次);line-height:1.9">
                <div v-for="(行, 序) in 场.正文" :key="序">{{ 行 }}</div>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 合规审查 -->
      <el-tab-pane label="合规审查" name="audit">
        <div class="卡片">
          <div class="行间" style="margin-bottom:12px">
            <div style="font-size:14px">共 {{ 审查项.length }} 项 · 通过 {{ 通过数 }} 项 · 待审 {{ 待审数 }} 项 · 不通过 {{ 不通过数 }} 项</div>
            <div style="flex:1"></div>
            <el-button size="mini" @click="重新审查()">重新审查</el-button>
          </div>
          <div class="卡片" v-for="项 in 审查项" :key="项.名" style="margin-bottom:12px;background:var(--卡片二)">
            <div class="行间">
              <div style="font-size:14px;font-weight:600">{{ 项.名 }}</div>
              <div style="flex:1"></div>
              <el-tag size="mini" :type="状态类型(项.状态)">{{ 项.状态 }}</el-tag>
            </div>
            <div style="margin-top:8px;font-size:13px;color:var(--字次);line-height:1.7">{{ 项.说明 }}</div>
            <div style="margin-top:8px;font-size:12px;color:var(--字弱)">涉及位置：{{ 项.位置 }}</div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <div class="行间 右" style="margin-top:20px">
      <el-button @click="$router.push('/script/plan')">返回方案</el-button>
    </div>
  </div>
</template>

<script>
import { 创作方案, 人物设定, 分集目录 } from '../../假数据'

export default {
  name: 'ScriptOutline',
  data() {
    return {
      方案列表: 创作方案,
      人物设定: 人物设定,
      分集目录: 分集目录,
      当前标签: 'plan',
      当前集: 1,
      审查项: [
        { 名: '敏感词审查', 状态: '通过', 说明: '全文 24 集逐集扫描，未命中政治敏感词与违禁词库，人物台词中的口语表达已做柔化处理。', 位置: '第 1-24 集 全部台词' },
        { 名: '暴力血腥审查', 状态: '通过', 说明: '禁术对抗以术式光效与动作呈现，无血腥特写；第 7 集「禁术的代价」改为心理压迫描写。', 位置: '第 2 集、第 7 集、第 10 集' },
        { 名: '版权风险审查', 状态: '待审', 说明: '第 5 集资料室名单出现真实校名，建议改为虚构校名后再送审；配乐素材待确认授权范围。', 位置: '第 5 集 场次 2' },
        { 名: '人物重名校验', 状态: '不通过', 说明: '角色「陈默」与资产库中已有角色重名，建议改为「陈墨」或合并人设，避免后续美术资产串用。', 位置: '人物设定 · 第 5 位' },
        { 名: '价值观合规', 状态: '通过', 说明: '师生关系严格保持职业边界，无暧昧化情感描写；校园霸凌情节以和解收束，未渲染细节。', 位置: '第 3 集、第 6 集、第 8 集' },
        { 名: '单集时长合规', 状态: '待审', 说明: '第 8 集字数 3500 超出 2 分钟承载上限，建议压缩至 3000 字以内或拆分为两集。', 位置: '第 8 集 期中考' }
      ],
      场次库: {
        1: [
          {
            场: '1-1', 地点: '内 · 教室 · 日', 人物: '林夜、赵小满、周正',
            正文: [
              '▲ 林夜在讲台前睁开眼，黑板右上角的日期是十年前。',
              '赵小满（起立）：老师，第一节是禁术概论，您要不要先点名？',
              '林夜（把粉笔放回笔槽）：点。从今天起，这门课我说了算。',
              '▲ 教室后门被推开，周正站在门口，手里拿着一份停课通知。'
            ]
          },
          {
            场: '1-2', 地点: '内 · 教室 · 日', 人物: '林夜、苏浅',
            正文: [
              '▲ 最后一排靠窗的位置，苏浅把帽檐压低，没有抬头。',
              '林夜（走过去，停在课桌旁）：禁术第一课，是把不敢开口的人叫起来。',
              '苏浅（没有动）：我不是这个班的学生。',
              '林夜：从今天起就是了。'
            ]
          }
        ],
        2: [
          {
            场: '2-1', 地点: '内 · 教室 · 日', 人物: '林夜、周正、赵小满',
            正文: [
              '▲ 林夜在黑板上写下被列为禁术的基础术式，粉笔断了三次。',
              '周正（拍桌子）：这门课去年就被停了，你凭什么重开？',
              '林夜（没回头）：凭去年停课时，签字的那个人是我。',
              '▲ 全班安静，赵小满低头在班级日志上写了一行字。'
            ]
          }
        ],
        3: [
          {
            场: '3-1', 地点: '内 · 教室 · 夜', 人物: '苏浅、林夜',
            正文: [
              '▲ 放学后，苏浅独自留在教室，指尖亮起微弱的光。',
              '苏浅（自语）：再来一次，就一次。',
              '▲ 门口的灯亮了，林夜站在那里，没有走进来。',
              '林夜：禁术的第一条规矩，是不许一个人练。'
            ]
          }
        ]
      }
    }
  },
  computed: {
    剧名() {
      return this.$route.query.剧名 || '重生之禁术教师'
    },
    集数() {
      return this.$route.query.集数 || '24'
    },
    题材() {
      return this.$route.query.题材 || '都市'
    },
    当前方案() {
      const 编号 = this.$route.query.方案 || 'A'
      for (let i = 0; i < this.方案列表.length; i++) {
        if (this.方案列表[i].id === 编号) return this.方案列表[i]
      }
      return this.方案列表[0]
    },
    当前目录() {
      for (let i = 0; i < this.分集目录.length; i++) {
        if (this.分集目录[i].集 === this.当前集) return this.分集目录[i]
      }
      return this.分集目录[0]
    },
    当前场次() {
      if (this.场次库[this.当前集]) return this.场次库[this.当前集]
      const 目录 = this.当前目录
      return [
        {
          场: this.当前集 + '-1', 地点: '内 · 教室 · 日', 人物: '林夜、苏浅、赵小满',
          正文: [
            '▲ ' + 目录.梗概,
            '赵小满：老师，今天的内容要不要记进班级日志？',
            '林夜（把教案合上）：记。从今天起，这门课的每一笔都要留档。'
          ]
        },
        {
          场: this.当前集 + '-2', 地点: '内 · 走廊 · 夜', 人物: '林夜、周正',
          正文: [
            '▲ 走廊尽头的灯只亮了一半，周正抱着一摞旧教案走过来。',
            '周正：你在资料室翻的那份名单，最好别让第三个人看见。',
            '林夜：已经有人看见了。'
          ]
        }
      ]
    },
    通过数() {
      return this.审查项.filter(function (项) { return 项.状态 === '通过' }).length
    },
    待审数() {
      return this.审查项.filter(function (项) { return 项.状态 === '待审' }).length
    },
    不通过数() {
      return this.审查项.filter(function (项) { return 项.状态 === '不通过' }).length
    }
  },
  methods: {
    状态类型(状态) {
      if (状态 === '通过' || 状态 === '已完成') return 'success'
      if (状态 === '待审' || 状态 === '进行中') return 'warning'
      return 'danger'
    },
    保存并继续() {
      const 下一集 = this.当前集 + 1
      if (下一集 <= this.分集目录.length) {
        this.当前集 = 下一集
        this.$message({ message: '第 ' + (下一集 - 1) + ' 集已保存，进入第 ' + 下一集 + ' 集', type: 'success' })
      } else {
        this.$message({ message: '全部集数已保存，可前往合规审查', type: 'success' })
        this.当前标签 = 'audit'
      }
    },
    重新审查() {
      this.$message({ message: '已提交重新审查，预计 1 分钟内返回结果', type: 'success' })
    }
  }
}
</script>

<style scoped>
.集项 {
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--描边);
  margin-bottom: 8px;
  cursor: pointer;
}
.集项:hover { border-color: var(--描边亮); }
.集项.当前 { border-color: var(--主); background: var(--主浅); }
</style>
