<template>
  <el-container style="height: 100vh">
    <el-aside width="200px" style="background: #304156">
      <div style="padding: 20px; color: #fff; font-size: 16px; font-weight: bold; text-align: center">
        抓取管理平台
      </div>
      <el-menu
        :default-active="$route.path"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/spiders">
          <el-icon><Setting /></el-icon>
          <span>爬虫配置</span>
        </el-menu-item>
        <el-menu-item index="/tasks">
          <el-icon><List /></el-icon>
          <span>任务监控</span>
        </el-menu-item>
        <el-menu-item index="/alerts">
          <el-icon><Bell /></el-icon>
          <el-badge :value="alertStore.unackedCount" :hidden="!alertStore.unackedCount" class="nav-badge">
            <span>告警中心</span>
          </el-badge>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-main style="padding: 20px; background: #f0f2f5">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAlertStore } from './stores/alert.js'

const alertStore = useAlertStore()

onMounted(() => {
  alertStore.fetchSummary()
  setInterval(() => alertStore.fetchSummary(), 30000)
})
</script>

<style>
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
.nav-badge .el-badge__content { top: 5px; }
</style>
