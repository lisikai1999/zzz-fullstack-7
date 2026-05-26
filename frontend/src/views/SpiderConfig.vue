<template>
  <div>
    <div style="margin-bottom: 16px; display: flex; justify-content: space-between">
      <h3 style="margin: 0">爬虫配置</h3>
      <el-button type="primary" @click="openCreate">新建爬虫</el-button>
    </div>

    <el-table :data="spiderStore.spiders" v-loading="spiderStore.loading" stripe>
      <el-table-column prop="name" label="名称" width="160" />
      <el-table-column prop="domain" label="域名" width="200" />
      <el-table-column prop="schedule_cron" label="调度" width="120" />
      <el-table-column label="Playwright" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.use_playwright" size="small">是</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-switch v-model="row.enabled" @change="toggleEnabled(row)" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240">
        <template #default="{ row }">
          <el-button size="small" type="success" @click="runNow(row)">执行</el-button>
          <el-button size="small" @click="editRow(row)">编辑</el-button>
          <el-popconfirm title="确认删除?" @confirm="spiderStore.removeSpider(row.id)">
            <template #reference>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showForm" :title="editingId ? '编辑爬虫' : '新建爬虫'" width="700px" destroy-on-close>
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="域名">
          <el-input v-model="form.domain" placeholder="example.com" />
        </el-form-item>
        <el-form-item label="起始URL">
          <el-input v-model="form.start_urls_str" type="textarea" :rows="3" placeholder="每行一个URL" />
        </el-form-item>
        <el-form-item label="Cron调度">
          <el-input v-model="form.schedule_cron" placeholder="留空为手动触发, 如: 0 */6 * * *" />
        </el-form-item>
        <el-form-item label="最大深度">
          <el-input-number v-model="form.max_depth" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="Playwright">
          <el-switch v-model="form.use_playwright" />
        </el-form-item>
        <el-form-item label="选择器配置">
          <SelectorEditor v-model="form.selectors" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showForm = false">取消</el-button>
        <el-button type="primary" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useSpiderStore } from '@/stores/spider.js'
import SelectorEditor from '@/components/SelectorEditor.vue'

const spiderStore = useSpiderStore()
const showForm = ref(false)
const editingId = ref(null)

const defaultForm = () => ({
  name: '',
  domain: '',
  start_urls_str: '',
  schedule_cron: '',
  max_depth: 3,
  use_playwright: false,
  selectors: { fields: [], pagination: null, item_container: null },
})

const form = ref(defaultForm())

onMounted(() => spiderStore.fetchSpiders())

function editRow(row) {
  editingId.value = row.id
  form.value = {
    ...row,
    start_urls_str: row.start_urls.join('\n'),
  }
  showForm.value = true
}

async function toggleEnabled(row) {
  try {
    await spiderStore.editSpider(row.id, { enabled: row.enabled })
  } catch {
    row.enabled = !row.enabled
  }
}

function openCreate() {
  editingId.value = null
  form.value = defaultForm()
  showForm.value = true
}

async function runNow(row) {
  try {
    const { data } = await spiderStore.runSpider(row.id)
    ElMessage.success(`任务已派发, task_id=${data.task_id}`)
  } catch {}
}

async function submitForm() {
  const payload = {
    ...form.value,
    start_urls: form.value.start_urls_str.split('\n').filter(u => u.trim()),
  }
  delete payload.start_urls_str
  if (!payload.schedule_cron) payload.schedule_cron = null

  try {
    if (editingId.value) {
      await spiderStore.editSpider(editingId.value, payload)
    } else {
      await spiderStore.addSpider(payload)
    }
    showForm.value = false
    editingId.value = null
    form.value = defaultForm()
    ElMessage.success('保存成功')
  } catch {}
}
</script>
