<template>
  <div>
    <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center">
      <h3 style="margin: 0">告警中心</h3>
      <div>
        <el-select v-model="filter.severity" placeholder="级别" clearable style="width: 120px; margin-right: 10px">
          <el-option label="critical" value="critical" />
          <el-option label="warning" value="warning" />
        </el-select>
        <el-select v-model="filter.alert_type" placeholder="类型" clearable style="width: 160px">
          <el-option label="选择器失效" value="selector_failure" />
          <el-option label="产出下降" value="yield_drop" />
          <el-option label="限流触发" value="rate_limit_hit" />
          <el-option label="任务错误" value="task_error" />
        </el-select>
      </div>
    </div>

    <el-table :data="alertStore.alerts" v-loading="alertStore.loading" stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="spider_id" label="爬虫ID" width="80" />
      <el-table-column label="类型" width="140">
        <template #default="{ row }">
          <el-tag size="small">{{ row.alert_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="级别" width="90">
        <template #default="{ row }">
          <el-tag :type="row.severity === 'critical' ? 'danger' : 'warning'" size="small">
            {{ row.severity }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="message" label="消息" show-overflow-tooltip />
      <el-table-column prop="created_at" label="时间" width="180" />
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button
            v-if="!row.acknowledged"
            size="small"
            type="primary"
            @click="alertStore.acknowledge(row.id)"
          >确认</el-button>
          <el-tag v-else type="success" size="small">已确认</el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useAlertStore } from '@/stores/alert.js'

const alertStore = useAlertStore()
const filter = ref({ severity: null, alert_type: null })

onMounted(() => alertStore.fetchAlerts())

watch(() => ({ ...filter.value }), (val) => {
  alertStore.fetchAlerts(val)
})
</script>
