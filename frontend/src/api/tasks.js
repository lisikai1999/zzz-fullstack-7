import api from './index.js'

export const getTasks = (params) => api.get('/tasks', { params })
export const getTask = (id) => api.get(`/tasks/${id}`)
export const cancelTask = (id) => api.post(`/tasks/${id}/cancel`)
export const getTaskItems = (id, params) => api.get(`/tasks/${id}/items`, { params })
