import api from './index.js'

export const getSpiders = () => api.get('/spiders')
export const createSpider = (data) => api.post('/spiders', data)
export const updateSpider = (id, data) => api.put(`/spiders/${id}`, data)
export const deleteSpider = (id) => api.delete(`/spiders/${id}`)
export const triggerRun = (id) => api.post(`/spiders/${id}/run`)
export const resetBloom = (id) => api.post(`/spiders/${id}/reset-bloom`)
