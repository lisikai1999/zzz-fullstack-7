import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: () => import('@/views/Dashboard.vue') },
  { path: '/spiders', component: () => import('@/views/SpiderConfig.vue') },
  { path: '/tasks', component: () => import('@/views/TaskMonitor.vue') },
  { path: '/alerts', component: () => import('@/views/Alerts.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
