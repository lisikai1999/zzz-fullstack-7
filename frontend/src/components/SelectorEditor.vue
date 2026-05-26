<template>
  <div class="selector-editor">
    <div v-if="model.item_container" style="margin-bottom: 12px">
      <el-tag closable @close="model.item_container = null">
        容器: {{ model.item_container.expression }}
      </el-tag>
    </div>
    <el-button size="small" @click="addContainer" v-if="!model.item_container" style="margin-bottom: 12px">
      + 设置列表容器选择器
    </el-button>

    <div v-for="(field, fIdx) in model.fields" :key="fIdx" class="field-block">
      <div style="display: flex; align-items: center; margin-bottom: 8px">
        <el-input v-model="field.field_name" placeholder="字段名" style="width: 150px; margin-right: 10px" size="small" />
        <el-checkbox v-model="field.required" label="必填" size="small" />
        <span style="margin-left: 10px; font-size: 12px; color: #909399">
          最低产出率:
        </span>
        <el-input-number v-model="field.min_yield_pct" :min="0" :max="1" :step="0.1" size="small" style="width: 100px; margin-left: 5px" />
        <el-button size="small" type="danger" text @click="model.fields.splice(fIdx, 1)" style="margin-left: auto">
          删除字段
        </el-button>
      </div>

      <div v-for="(sel, sIdx) in field.selectors" :key="sIdx" style="display: flex; align-items: center; margin-bottom: 6px; padding-left: 20px">
        <el-tag size="small" type="info" style="margin-right: 8px">{{ sIdx === 0 ? '主' : '备' + sIdx }}</el-tag>
        <el-select v-model="sel.type" size="small" style="width: 80px; margin-right: 8px">
          <el-option label="CSS" value="css" />
          <el-option label="XPath" value="xpath" />
        </el-select>
        <el-input v-model="sel.expression" placeholder="选择器表达式" size="small" style="flex: 1; margin-right: 8px" />
        <el-input v-model="sel.attribute" placeholder="属性(留空取文本)" size="small" style="width: 120px; margin-right: 8px" />
        <el-button size="small" text type="danger" @click="field.selectors.splice(sIdx, 1)">×</el-button>
      </div>
      <el-button size="small" text @click="addSelector(field)" style="padding-left: 20px">+ 添加备用选择器</el-button>
    </div>

    <el-button size="small" type="primary" text @click="addField" style="margin-top: 12px">+ 添加字段</el-button>
  </div>
</template>

<script setup>
const model = defineModel({ type: Object, required: true })

function addField() {
  model.value.fields.push({
    field_name: '',
    required: true,
    min_yield_pct: 0.8,
    selectors: [{ type: 'css', expression: '', attribute: null }],
  })
}

function addSelector(field) {
  field.selectors.push({ type: 'css', expression: '', attribute: null })
}

function addContainer() {
  model.value.item_container = { type: 'css', expression: '' }
}
</script>

<style scoped>
.selector-editor { border: 1px solid #ebeef5; border-radius: 4px; padding: 12px; }
.field-block { border-bottom: 1px dashed #ebeef5; padding-bottom: 12px; margin-bottom: 12px; }
.field-block:last-of-type { border-bottom: none; }
</style>
