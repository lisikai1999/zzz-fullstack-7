import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getSpiders, createSpider, updateSpider, deleteSpider, triggerRun } from '@/api/spiders.js'
import { ElMessage } from 'element-plus'

export const useSpiderStore = defineStore('spider', () => {
  const spiders = ref([])
  const loading = ref(false)

  async function fetchSpiders() {
    loading.value = true
    try {
      const { data } = await getSpiders()
      spiders.value = data
    } finally {
      loading.value = false
    }
  }

  async function addSpider(form) {
    const { data } = await createSpider(form)
    spiders.value.unshift(data)
    return data
  }

  async function editSpider(id, form) {
    const { data } = await updateSpider(id, form)
    const idx = spiders.value.findIndex(s => s.id === id)
    if (idx !== -1) spiders.value[idx] = data
    return data
  }

  async function removeSpider(id) {
    await deleteSpider(id)
    spiders.value = spiders.value.filter(s => s.id !== id)
    ElMessage.success('已删除')
  }

  async function runSpider(id) {
    return await triggerRun(id)
  }

  return { spiders, loading, fetchSpiders, addSpider, editSpider, removeSpider, runSpider }
})
