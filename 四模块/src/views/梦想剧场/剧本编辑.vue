<template>
  <div>
    <!-- 面包屑 -->
    <div class="面包屑条">
      <span class="可点" @click="$router.push('/theater')">梦想剧场</span>
      <span> / </span>
      <span>{{ 剧名 }}</span>
      <span> / </span>
      <span style="color:var(--字次)">剧本编辑</span>
    </div>

    <div style="display:flex;gap:16px;align-items:flex-start">
      <!-- 左列 -->
      <aside style="width:340px;flex:0 0 340px;display:flex;flex-direction:column;gap:16px">
        <!-- 项目信息 -->
        <div class="卡片">
          <el-button type="text" icon="el-icon-arrow-left" style="padding:0;margin-bottom:8px" @click="$router.push('/theater')">
            返回项目
          </el-button>
          <div style="font-size:18px;font-weight:700;margin-bottom:8px;color:var(--字)">{{ 剧名 }}</div>
          <div class="行间">
            <span class="小标签 灰">第 {{ 当前集.序 }} 集</span>
            <span class="小标签">草稿</span>
            <span class="小标签 灰">{{ 当前集.时长 }}</span>
          </div>
          <el-divider style="margin:14px 0"></el-divider>
          <div style="font-size:12px;color:var(--字弱);line-height:1.8">
            <div>480p · 9:16 · {{ 剧集列表.length }}部在制</div>
            <div>风格：动漫漫画日系轻快风</div>
            <div>整体进度：<span style="color:var(--主)">风险 ✓</span> · 资产：<span style="color:var(--主)">12/25</span></div>
          </div>
          <el-divider style="margin:14px 0"></el-divider>
          <div style="font-size:12px;color:var(--字弱);margin-bottom:8px">切换集</div>
          <div style="display:flex;flex-direction:column;gap:6px">
            <div
              v-for="集 in 集列表"
              :key="集.id"
              class="chip"
              :class="{ 选中: 集.id === 当前集.id }"
              style="justify-content:space-between;width:100%"
              @click="当前集 = 集"
            >
              <span>{{ 集.名 }}</span>
              <span style="font-size:12px;opacity:.7">{{ 集.状态 }}</span>
            </div>
          </div>
        </div>

        <!-- AI 剧本助手 -->
        <div class="卡片" style="display:flex;flex-direction:column">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <span style="font-size:14px;font-weight:600;color:var(--字)">AI 剧本助手</span>
            <el-button type="text" size="mini" style="color:var(--字弱)">只读模式</el-button>
          </div>
          <div style="font-size:13px;line-height:1.8;color:var(--字次);min-height:96px">
            <template v-if="!助手记录.length">你好，我可以帮你改写、扩写或润色剧本。点击下方快捷指令体验 AI 生成功能。</template>
            <div v-for="(条, i) in 助手记录" :key="i" style="margin-bottom:8px">
              <div style="color:var(--主);font-size:12px;margin-bottom:2px">{{ 条.指令 }}</div>
              <div>{{ 条.结果 }}</div>
            </div>
          </div>
          <div class="行间" style="margin-top:12px;padding-top:12px;border-top:1px solid var(--描边)">
            <el-button size="mini" plain @click="助手('改写开场')">改写开场</el-button>
            <el-button size="mini" plain @click="助手('扩写对话')">扩写对话</el-button>
            <el-button size="mini" plain @click="助手('润色对白')">润色对白</el-button>
          </div>
        </div>

        <!-- 剧本版本 -->
        <div class="卡片">
          <div style="font-size:14px;font-weight:600;color:var(--字);margin-bottom:12px">剧本版本</div>
          <div style="background:var(--描边);border-radius:8px;padding:12px;display:flex;justify-content:space-between;align-items:center">
            <div>
              <div style="font-size:13px;color:var(--字)">初始版本 - V1</div>
              <div style="font-size:12px;color:var(--字弱);margin-top:4px">基于初始提示词生成的初稿 · 1 个修改</div>
            </div>
            <span style="font-size:12px;color:var(--主)">当前</span>
          </div>
        </div>
      </aside>

      <!-- 右列 -->
      <section style="flex:1;display:flex;flex-direction:column;gap:16px;min-width:0">
        <!-- 进度步骤 -->
        <div class="卡片">
          <div class="步骤条" style="margin:0">
            <div class="步 完成"><span class="圈">1</span><span class="字">剧本编辑</span></div>
            <span class="连"></span>
            <div class="步"><span class="圈">2</span><span class="字">分镜与美术资产</span></div>
            <span class="连"></span>
            <div class="步"><span class="圈">3</span><span class="字">导演台</span></div>
            <span class="连"></span>
            <div class="步"><span class="圈">4</span><span class="字">短片</span></div>
          </div>
        </div>

        <!-- 剧本内容 -->
        <div class="卡片 无内距" style="display:flex;flex-direction:column">
          <div style="padding:16px;background:var(--卡片二);border-bottom:1px solid var(--描边);font-size:13px">
            <div style="color:var(--字次);margin-bottom:4px">
              <span style="color:var(--字弱)">剧本：</span>在「{{ 剧名 }}」中，林夜重生回到十年前的讲台，用禁术棋局一步步收服问题学生。
            </div>
            <div style="color:var(--字次)">
              <span style="color:var(--字弱)">分镜：</span>完成剧本编辑后，进入「分镜与美术资产」提取角色与场景。
            </div>
          </div>

          <div style="padding:24px;max-height:520px;overflow-y:auto">
            <h2 style="font-size:18px;font-weight:700;margin:0 0 16px;color:var(--字)">剧本正文</h2>
            <div style="font-size:13px;line-height:1.9;color:var(--字次)">
              <p style="color:var(--字);font-weight:600;margin:0 0 6px">1-1 内·高三教室·日</p>
              <p style="margin:0 0 6px">出场人物：林夜、苏浅、周正、赵小满</p>
              <p style="margin:0 0 6px">出场服装：林夜-黑色教师外套、苏浅-校服、周正-灰色中山装、赵小满-校服</p>
              <p style="margin:0 0 6px">△ 教室后排的吊扇吱呀转着，黑板右上角写着十年前的日期。林夜猛地睁开眼，粉笔灰正落在他的袖口。</p>
              <p style="margin:0 0 6px">△ 他抬头，四十六张陌生又熟悉的脸正看着他。讲台上的教案翻在第一页，上面是他自己十年前的字迹。</p>
              <p style="margin:0 0 6px">林夜（低声）：……回来了。</p>
              <p style="margin:0 0 6px">△ 最后一排靠窗的位置，一个长发遮住半张脸的女孩始终低着头，笔尖在草稿纸上反复划同一道痕。</p>
              <p style="margin:0 0 6px">赵小满（举手）：老师，这节课还上吗？</p>
              <p style="margin:0 0 6px">△ 林夜把教案合上，转身在黑板上写下两个字——禁术。</p>
              <p style="margin:0 0 6px">林夜：上。从今天起，这门课改名字了。</p>
              <p style="margin:0 0 6px">△ 教室门被推开，周正站在门口，脸色沉下来。</p>
              <p style="margin:0 0 6px">周正：林老师，教务处没有批准。</p>
              <p style="margin:0 0 6px">林夜（没有回头）：批不批是你们的事。课我已经开了。</p>
              <p style="margin:0 0 6px">△ 最后一排的女孩终于抬起头，看了黑板一眼，又低下去。笔尖停住了。</p>
              <p style="margin:0 0 6px">【画外】：苏浅，插班生，入学三个月未交过一份作业。她的草稿纸上写满了同一个术式的名字。</p>
              <p style="margin:0 0 6px">△ 放学铃响，所有人陆续离开。苏浅最后一个起身，走到黑板前，用手掌擦掉了「禁术」两个字的一半。</p>
              <p style="margin:0 0 6px">苏浅（很轻）：老师，这个字，写错了。</p>
              <p style="margin:0 0 6px">△ 林夜看着被擦掉一半的字，忽然笑了。</p>
              <p style="margin:0">林夜：没错。是我故意的。</p>
            </div>
          </div>

          <div style="padding:16px;border-top:1px solid var(--描边);display:flex;justify-content:space-between;align-items:center">
            <span style="font-size:12px;color:var(--字弱)">已自动保存 · 最后编辑：演示模式已启用</span>
            <el-button type="primary" @click="下一步()">下一步：分镜与美术资产</el-button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import { 集列表, 剧集列表 } from '../../假数据'

export default {
  name: 'EpScript',
  data() {
    return {
      剧集列表,
      集列表,
      当前集: 集列表[0],
      助手记录: []
    }
  },
  computed: {
    剧名() {
      return this.$route.query.name || '火影之禁术教师'
    }
  },
  methods: {
    助手(指令) {
      const 结果 = {
        改写开场: '已重写开场：把「睁眼回到教室」改为「粉笔灰落在袖口」的特写入手，前 3 秒建立重生信号。',
        扩写对话: '已扩写林夜与周正的正面冲突：新增 4 轮对白，把周正的立场从「阻拦」改成「自保」，冲突更立体。',
        润色对白: '已润色全部对白：去掉书面语，改成短句；苏浅的台词控制在 8 字以内，保留她的沉默感。'
      }
      this.助手记录.push({ 指令, 结果: 结果[指令] })
    },
    下一步() {
      this.$router.push({ path: '/theater/assets', query: { ep: this.$route.query.ep, name: this.剧名 } })
    }
  }
}
</script>
