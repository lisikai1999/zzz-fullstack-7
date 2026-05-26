import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getTasks, cancelTask } from '@/api/tasks.js'
import { ElMessage } from 'element-plus'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref([])
  const loading = ref(false)
  let pollTimer = null
  let currentParams = {}

  async function fetchTasks() {
    loading.value = true
    try {
      const { data } = await getTasks(currentParams)
      tasks.value = data
    } finally {
      loading.value = false
    }
  }

  async function cancel(id) {
    await cancelTask(id)
    const task = tasks.value.find(t => t.id === id)
    if (task) task.status = 'cancelled'
    ElMessage.success('任务已取消')
  }

  function startPolling(interval = 5000) {
    stopPolling()
    fetchTasks()
    pollTimer = setInterval(fetchTasks, interval)
  }

  function setFilter(params) {
    const clean = {}
    for (const [k, v] of Object.entries(params)) {
      if (v != null && v !== '') clean[k] = v
    }
    currentParams = clean
    fetchTasks()
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  return { tasks, loading, fetchTasks, cancel, startPolling, setFilter, stopPolling }
})
