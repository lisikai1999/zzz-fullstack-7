import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getAlerts, ackAlert, getAlertSummary } from '@/api/alerts.js'
import { ElMessage } from 'element-plus'

export const useAlertStore = defineStore('alert', () => {
  const alerts = ref([])
  const unackedCount = ref(0)
  const loading = ref(false)

  async function fetchAlerts(params = {}) {
    loading.value = true
    try {
      const clean = {}
      for (const [k, v] of Object.entries(params)) {
        if (v != null && v !== '') clean[k] = v
      }
      const { data } = await getAlerts(clean)
      alerts.value = data
    } finally {
      loading.value = false
    }
  }

  async function acknowledge(id) {
    await ackAlert(id)
    const alert = alerts.value.find(a => a.id === id)
    if (alert) alert.acknowledged = true
    unackedCount.value = Math.max(0, unackedCount.value - 1)
    ElMessage.success('告警已确认')
  }

  async function fetchSummary() {
    try {
      const { data } = await getAlertSummary()
      unackedCount.value = data.total_unacked
    } catch {}
  }

  return { alerts, unackedCount, loading, fetchAlerts, acknowledge, fetchSummary }
})
