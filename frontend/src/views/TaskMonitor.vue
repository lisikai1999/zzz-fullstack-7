<template>
  <div>
    <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center">
      <h3 style="margin: 0">任务监控</h3>
      <div>
        <el-select v-model="filter.status" placeholder="状态筛选" clearable style="width: 140px; margin-right: 10px">
          <el-option label="运行中" value="running" />
          <el-option label="成功" value="success" />
          <el-option label="失败" value="failed" />
          <el-option label="等待中" value="pending" />
        </el-select>
        <el-tag type="info">自动刷新 5s</el-tag>
      </div>
    </div>

    <el-table :data="taskStore.tasks" v-loading="taskStore.loading" stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="spider_id" label="爬虫ID" width="80" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusColor(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="进度" width="200">
        <template #default="{ row }">
          <el-progress
            :percentage="row.urls_discovered ? Math.round(row.urls_scraped / row.urls_discovered * 100) : 0"
            :stroke-width="14"
            :text-inside="true"
          />
        </template>
      </el-table-column>
      <el-table-column prop="urls_discovered" label="发现" width="80" />
      <el-table-column prop="urls_scraped" label="已抓" width="80" />
      <el-table-column prop="urls_deduped" label="去重" width="80" />
      <el-table-column prop="items_extracted" label="提取" width="80" />
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'running'"
            size="small"
            type="danger"
            @click="taskStore.cancel(row.id)"
          >取消</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useTaskStore } from '@/stores/task.js'

const taskStore = useTaskStore()
const filter = ref({ status: null })

function statusColor(status) {
  const map = { running: 'primary', success: 'success', failed: 'danger', pending: 'info', cancelled: 'warning' }
  return map[status] || 'info'
}

onMounted(() => {
  taskStore.setFilter({})
  taskStore.startPolling()
})
onUnmounted(() => taskStore.stopPolling())

watch(() => filter.value.status, (val) => {
  taskStore.setFilter(val ? { status: val } : {})
})
</script>
