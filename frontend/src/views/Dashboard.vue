<template>
  <div>
    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="4" v-for="card in cards" :key="card.label">
        <el-card shadow="hover">
          <div style="text-align: center">
            <div style="font-size: 28px; font-weight: bold; color: #409eff">{{ card.value }}</div>
            <div style="color: #909399; margin-top: 8px">{{ card.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card header="域名限速状态">
          <el-table :data="rateLimits" size="small" stripe>
            <el-table-column prop="domain" label="域名" />
            <el-table-column prop="current_rate_rps" label="当前速率(req/s)" />
            <el-table-column prop="success_count" label="连续成功数" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card header="最近告警">
          <el-table :data="recentAlerts" size="small" stripe>
            <el-table-column prop="alert_type" label="类型" width="140" />
            <el-table-column prop="severity" label="级别" width="80">
              <template #default="{ row }">
                <el-tag :type="row.severity === 'critical' ? 'danger' : 'warning'" size="small">
                  {{ row.severity }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="消息" show-overflow-tooltip />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getDashboard, getRateLimits, getAlerts } from '@/api/alerts.js'

const stats = ref({})
const rateLimits = ref([])
const recentAlerts = ref([])

const cards = computed(() => [
  { label: '爬虫总数', value: stats.value.total_spiders || 0 },
  { label: '启用中', value: stats.value.enabled_spiders || 0 },
  { label: '今日任务', value: stats.value.tasks_today || 0 },
  { label: '运行中', value: stats.value.running_tasks || 0 },
  { label: '今日抓取', value: stats.value.items_today || 0 },
  { label: '未处理告警', value: stats.value.unacked_alerts || 0 },
])

onMounted(async () => {
  const [dashRes, rateRes, alertRes] = await Promise.all([
    getDashboard(),
    getRateLimits(),
    getAlerts({ limit: 5, acknowledged: false }),
  ])
  stats.value = dashRes.data
  rateLimits.value = rateRes.data
  recentAlerts.value = alertRes.data
})
</script>
