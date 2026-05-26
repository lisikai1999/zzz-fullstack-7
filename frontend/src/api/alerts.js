import api from './index.js'

export const getAlerts = (params) => api.get('/alerts', { params })
export const ackAlert = (id) => api.put(`/alerts/${id}/ack`)
export const getAlertSummary = () => api.get('/alerts/summary')
export const getDashboard = () => api.get('/stats/dashboard')
export const getRateLimits = () => api.get('/stats/rate-limits')
