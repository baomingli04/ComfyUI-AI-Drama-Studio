<template>
  <el-dialog title="上传技能包（确认分类）" :visible="显示" width="480px" @close="$emit('关闭')">
    <el-form label-width="80px">
      <el-form-item label="分类">
        <el-select v-model="分类id" placeholder="选择技能包所属分类" style="width: 100%">
          <el-option v-for="分类 in 分类列表" :key="分类.id" :label="分类.名称" :value="分类.id"></el-option>
        </el-select>
      </el-form-item>
      <el-form-item label="技能包">
        <el-upload
          drag
          :action="上传地址"
          :headers="上传头"
          name="文件"
          :show-file-list="false"
          :on-success="上传成功"
          :on-error="上传失败"
          accept=".zip"
        >
          <i class="el-icon-upload"></i>
          <div class="el-upload__text">把 zip 压缩包拖到这里，或<em>点击选择</em></div>
        </el-upload>
        <div class="上传提示">上传成功后会自动解压登记；同名技能包会拒绝。</div>
      </el-form-item>
    </el-form>
    <div slot="footer">
      <el-button @click="$emit('关闭')">关 闭</el-button>
    </div>
  </el-dialog>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
