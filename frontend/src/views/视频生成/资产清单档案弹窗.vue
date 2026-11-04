<template>
  <!-- 编辑人物档案弹窗（不跳人物设定页，就地编辑真库人物）。
       自 资产清单.vue 拆出：模板/样式/段编辑与保存逻辑整体搬入，业务逻辑不变。
       显隐控制字段（档案弹窗显示）与缓冲构造（打开档案编辑）留在父页面；
       保存写回的是 props 传入的同一份 人物们 数组，保存成功后 @保存成功 通知父页面重建人物文本。 -->
  <el-dialog
    :title="'编辑人物档案：' + ((缓冲 && 缓冲.名) || '')"
    :visible="visible" width="780px" top="6vh" append-to-body
    @update:visible="$emit('update:visible', $event)">
    <div v-if="缓冲" class="档案编辑">
      <div v-for="组 in 字段分组" :key="组.名" class="档组">
        <div class="档组名">{{ 组.名 }}</div>
        <div v-for="段名 in 组.字段" :key="段名" class="档行">
          <span class="档名">{{ 段名 }}</span>
          <!-- 会随剧情变的字段且已拆段：分段结构化编辑（同人物设定页：起/止集数 + 内容） -->
          <div v-if="是段字段(段名) && 段缓冲[档键(段名)]" class="段编辑列">
            <div v-for="(段, 序) in 段缓冲[档键(段名)]" :key="序" class="段编辑行">
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
                v-model="缓冲[档键(段名)]" size="small" />
              <el-input
                v-else
                v-model="缓冲[档键(段名)]" type="textarea"
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
      <el-button size="small" @click="$emit('update:visible', false)">取消</el-button>
      <el-button size="small" type="primary" :loading="存档案中" @click="保存档案()">保存</el-button>
    </div>
  </el-dialog>
</template>

<script>
import { 发 } from '@/接口/请求'
import { 字段分组, 可分段字段, 文本转值, 拆分段, 分段文本 } from '@/共用/人物工具'

/* 人物卡字段名 → 人物表列名（其余字段同名；关系=随剧情的关系变化，口径同人物设定页） */
const 卡字段映射 = { 姓名: '名', 年龄: '年龄档', 关系: '关系变化' }

/* 档案弹窗里单行输入的字段，其余用多行文本框 */
const 档案短字段 = ['姓名', '性别', '年龄', '身材', '当前姿势', '台词风格', '口头禅']

export default {
  name: 'AssetProfileDialog',
  props: {
    /* 显隐控制字段留在父组件（:visible.sync） */
    visible: { type: Boolean, default: false },
    /* 编辑缓冲：父组件 打开档案编辑 构造的浅拷贝（字段级 v-model 直接改对象内部属性） */
    缓冲: { type: Object, default: null },
    /* 分段编辑缓冲：键=人物表列名，值=段数组或 null（父组件 打开档案编辑 初始化） */
    段缓冲: { type: Object, required: true },
    /* 该人物在 人物们 里的下标（保存时按下标写回库内对象） */
    源序: { type: Number, default: -1 },
    /* 真库人物全量（保存时全量落库，后端事务内全量替换，必须传全部人物） */
    人物们: { type: Array, default: function () { return [] } },
    剧id: { type: Number, default: 0 },
    看集数: { type: Number, default: 0 }
  },
  data() {
    return {
      存档案中: false,
      档案短字段: 档案短字段
    }
  },
  methods: {
    /* 人物档案弹窗：字段名 → 编辑缓冲里的键（人物表列名） */
    档键(段名) {
      return 卡字段映射[段名] || 段名
    },
    是段字段(字段名) { return 可分段字段.indexOf(字段名) >= 0 },
    /* 段编辑：单值 → 拆段（原文里已经是「第1-5集：…；第6集起：…」就按原样拆开，否则包成 1..总集 一段） */
    拆此段(段名) {
      const 页 = this
      const 键 = 页.档键(段名)
      const 解析 = 文本转值(页.缓冲[键] || '', 页.看集数)
      页.$set(页.段缓冲, 键, Array.isArray(解析)
        ? 解析.map(function (段) { return Object.assign({}, 段) })
        : 拆分段(页.缓冲[键] || '', 页.看集数))
    },
    加段(键) {
      const 段们 = this.段缓冲[键] || []
      const 尾 = 段们.length ? 段们[段们.length - 1].止 : (this.看集数 || 1)
      段们.push({ 起: 尾, 止: this.看集数 || 尾, 值: '', 类型: '', 说明: '' })
    },
    删段(键, 序) {
      const 段们 = this.段缓冲[键] || []
      段们.splice(序, 1)
      if (!段们.length) this.段缓冲[键] = null
    },
    /* 合并成单值：取最后一段（口径同人物设定页「合并」） */
    并段(键) {
      const 段们 = this.段缓冲[键] || []
      this.缓冲[键] = 段们.length ? (段们[段们.length - 1].值 || '') : ''
      this.段缓冲[键] = null
    },
    async 保存档案() {
      const 页 = this
      const 缓冲 = 页.缓冲
      if (!缓冲) return
      if (!String(缓冲.名 || '').trim()) {
        页.$message.error('姓名不能为空')
        return
      }
      if (!页.人物们.length || !(页.源序 >= 0 && 页.源序 < 页.人物们.length)) {
        页.$message.error('人物数据未加载，无法保存')
        return
      }
      页.存档案中 = true
      try {
        /* 分段字段序列化回「第1-5集：…；第6集起：…」文本（与人物设定页 存库 口径一致） */
        for (const 键 in 页.段缓冲) {
          const 段们 = 页.段缓冲[键]
          if (Array.isArray(段们) && 段们.length) 缓冲[键] = 分段文本(段们, 页.看集数)
        }
        /* 写回库内对象，全量落库（后端事务内全量替换，必须传全部人物） */
        Object.assign(页.人物们[页.源序], 缓冲)
        await 发('/api/人物/保存', { 剧id: 页.剧id, 人物们: 页.人物们 })
        /* 通知父页面重建人物设定文本（原 重建人物文本） */
        页.$emit('保存成功')
        页.$message.success('人物档案已保存')
        页.$emit('update:visible', false)
      } catch (e) {
        页.$message.error('档案保存失败：' + ((e && e.message) || e))
      }
      页.存档案中 = false
    }
  }
}
</script>

<style scoped>
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
</style>
