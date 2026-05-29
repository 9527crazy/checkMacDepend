<template>
  <main class="app-shell">
    <header class="topbar">
      <div class="topbar-left">
        <div class="app-icon">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="7" fill="url(#gradient)"/>
            <defs>
              <linearGradient id="gradient" x1="0" y1="0" x2="32" y2="32">
                <stop offset="0%" stop-color="#007AFF"/>
                <stop offset="100%" stop-color="#5856D6"/>
              </linearGradient>
            </defs>
            <path d="M10 16h12M16 10v12" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
            <circle cx="16" cy="16" r="4" stroke="white" stroke-width="2" fill="none"/>
          </svg>
        </div>
        <div class="topbar-title">
          <h1>Package Monitor</h1>
          <span class="topbar-subtitle">包安装监控</span>
        </div>
      </div>
      <div class="actions">
        <button 
          type="button" 
          class="sf-button secondary" 
          :disabled="!selectedDate || busy" 
          @click="handleReport"
        >
          <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
            <path d="M2 2h12v12H2V2zm1 1v10h10V3H3zm2 2h6v1H5V5zm0 3h6v1H5V8zm0 3h4v1H5v-1z"/>
          </svg>
          生成报告
        </button>
        <button 
          type="button" 
          class="sf-button primary" 
          :class="{ loading: busy }" 
          :disabled="busy" 
          @click="handleScan"
        >
          <span v-if="busy" class="spinner"></span>
          <svg v-else width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 2a6 6 0 100 12A6 6 0 008 2zm0 1v4l3 2"/>
          </svg>
          {{ busy ? "扫描中..." : "立即扫描" }}
        </button>
      </div>
    </header>

    <section class="workspace">
      <aside class="sidebar">
        <!-- Status Section -->
        <div class="sidebar-section">
          <div class="sidebar-title">
            <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 2.5a1.25 1.25 0 110 2.5 1.25 1.25 0 010-2.5zM6.5 7h3v5h-3V7z"/>
            </svg>
            状态概览
          </div>
          <div class="stats-grid">
            <div class="stat-card">
              <span class="stat-number">{{ state.total_count }}</span>
              <span class="stat-label">新增记录</span>
            </div>
            <div class="stat-card">
              <span class="stat-number">{{ selectedPackages.length }}</span>
              <span class="stat-label">今日记录</span>
            </div>
          </div>
          <div class="stat-info">
            <div class="stat-row">
              <span class="stat-key">上次扫描</span>
              <span class="stat-val">{{ state.last_scan_at || "从未" }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-key">管理器</span>
              <span class="stat-val managers" :title="managerList">{{ managerText }}</span>
            </div>
          </div>
        </div>

        <!-- Schedule Section -->
        <div class="sidebar-section">
          <div class="sidebar-title">
            <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 1a7 7 0 100 14A7 7 0 008 1zm.5 3.5v5l-3 2 .5 1 3.5-2V4.5h-1z"/>
            </svg>
            定时扫描
          </div>
          <div class="schedule-controls">
            <select 
              v-model="scheduleInterval" 
              :disabled="schedule.enabled"
              class="sf-select"
            >
              <option :value="1">每 1 小时</option>
              <option :value="6">每 6 小时</option>
              <option :value="12">每 12 小时</option>
              <option :value="24">每 24 小时</option>
            </select>
            <button 
              v-if="!schedule.enabled" 
              type="button" 
              class="sf-button primary small"
              @click="handleStartSchedule"
            >
              启动
            </button>
            <button 
              v-else 
              type="button" 
              class="sf-button danger small"
              @click="handleStopSchedule"
            >
              停止
            </button>
          </div>
          <div class="schedule-status" :class="{ active: schedule.enabled }">
            <span class="status-indicator"></span>
            <span v-if="schedule.enabled">
              运行中 · 每 {{ schedule.interval_hours }} 小时
            </span>
            <span v-else>已停止</span>
          </div>
        </div>

        <!-- Date Section -->
        <div class="sidebar-section date-section">
          <div class="sidebar-title">
            <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
              <path d="M4 0h1v2H4V0zm7 0h1v2h-1V0zM1 2h14v1H1V2zm0 1v11h14V3H1zm1 1v10h12V4H2zm2 2h8v1H4V6zm0 3h6v1H4V9zm0 3h4v1H4v-1z"/>
            </svg>
            日期
          </div>
          <div class="date-list">
            <button
              v-for="date in dates"
              :key="date"
              type="button"
              class="date-item"
              :class="{ active: date === selectedDate }"
              @click="selectedDate = date"
            >
              <span class="date-text">{{ formatDate(date) }}</span>
              <span class="date-count">{{ getDayCount(date) }}</span>
            </button>
            <div v-if="dates.length === 0" class="empty-state-mini">
              <p>暂无记录</p>
            </div>
          </div>
        </div>
      </aside>

      <section class="content">
        <div class="content-header">
          <div class="header-info">
            <h2>{{ selectedDate ? formatDate(selectedDate) : "选择日期查看记录" }}</h2>
            <span class="header-badge" v-if="selectedPackages.length">
              {{ selectedPackages.length }} 个包
            </span>
          </div>
          <div class="search-box">
            <svg class="search-icon" width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
              <path d="M11.742 10.344a6.5 6.5 0 10-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 001.415-1.414l-3.85-3.85a1.007 1.007 0 00-.115-.1zM12 6.5a5.5 5.5 0 11-11 0 5.5 5.5 0 0111 0z"/>
            </svg>
            <input v-model.trim="query" type="search" placeholder="搜索包名..." />
          </div>
        </div>

        <div class="table-container">
          <div class="table-wrap" v-if="filteredPackages.length > 0">
            <table>
              <thead>
                <tr>
                  <th class="th-manager">管理器</th>
                  <th class="th-name">包名</th>
                  <th class="th-version">版本</th>
                  <th class="th-time">时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="pkg in filteredPackages" :key="`${pkg.manager}-${pkg.name}-${pkg.version}`">
                  <td>
                    <span class="manager-badge" :class="pkg.manager">{{ pkg.manager }}</span>
                  </td>
                  <td class="package-name">{{ pkg.name }}</td>
                  <td class="version">
                    <code>{{ pkg.version }}</code>
                  </td>
                  <td class="time">{{ pkg.time || "-" }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="empty-state">
            <div class="empty-icon">
              <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                <circle cx="32" cy="32" r="28" stroke="#E5E5EA" stroke-width="2" stroke-dasharray="4 4"/>
                <path d="M24 32h16M32 24v16" stroke="#C7C7CC" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <p class="empty-title">{{ selectedDate ? "暂无安装记录" : "请先扫描或选择日期" }}</p>
            <p class="empty-hint">点击"立即扫描"开始检测已安装的包</p>
          </div>
        </div>

        <!-- Status Bar -->
        <div class="status-bar" :class="{ active: busy }">
          <span class="status-message">{{ statusMessage }}</span>
          <span class="status-total" v-if="state.total_count">
            共 {{ state.total_count }} 个包
          </span>
        </div>
      </section>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { 
  generateReport, 
  getAppState, 
  scanPackages,
  getScanSchedule,
  startScheduledScan,
  stopScheduledScan
} from "./services";

const state = ref({
  dates: [],
  records: {},
  total_count: 0,
  last_scan_at: null,
  available_managers: [],
});
const selectedDate = ref("");
const query = ref("");
const busy = ref(false);
const statusMessage = ref("就绪");
const schedule = ref({
  enabled: false,
  interval_hours: 24,
  last_scan_at: null,
});
const scheduleInterval = ref(24);

const dates = computed(() => state.value.dates || []);
const managerText = computed(() => {
  const managers = state.value.available_managers || [];
  if (!managers.length) return "未检测";
  if (managers.length <= 2) return managers.join(", ");
  return managers.slice(0, 2).join(", ") + " +" + (managers.length - 2);
});

const managerList = computed(() => {
  const managers = state.value.available_managers || [];
  return managers.join(", ") || "未检测";
});
const selectedPackages = computed(() => {
  if (!selectedDate.value) return [];
  return state.value.records?.[selectedDate.value] || [];
});
const filteredPackages = computed(() => {
  const needle = query.value.toLowerCase();
  if (!needle) return selectedPackages.value;
  return selectedPackages.value.filter((pkg) => {
    return pkg.name.toLowerCase().includes(needle) || pkg.manager.toLowerCase().includes(needle);
  });
});

function formatDate(dateStr) {
  const [year, month, day] = dateStr.split("-");
  return `${month}月${day}日`;
}

function getDayCount(date) {
  return state.value.records?.[date]?.length || 0;
}

async function refreshState(preferredDate) {
  state.value = await getAppState();
  const nextDates = state.value.dates || [];
  selectedDate.value = preferredDate && nextDates.includes(preferredDate) ? preferredDate : nextDates[0] || "";
}

async function refreshSchedule() {
  try {
    schedule.value = await getScanSchedule();
    scheduleInterval.value = schedule.value.interval_hours;
  } catch (error) {
    console.error("Failed to load schedule:", error);
  }
}

async function handleScan() {
  busy.value = true;
  statusMessage.value = "扫描中...";
  try {
    const result = await scanPackages();
    await refreshState(result.scanned_at.slice(0, 10));
    statusMessage.value = result.is_initial_scan
      ? `首次扫描完成，${result.scanned_count} 个包`
      : `扫描完成，新增 ${result.new_count} 个包`;
  } catch (error) {
    statusMessage.value = `扫描失败: ${error}`;
  } finally {
    busy.value = false;
  }
}

async function handleReport() {
  if (!selectedDate.value) return;
  busy.value = true;
  statusMessage.value = "生成报告...";
  try {
    await generateReport(selectedDate.value);
    statusMessage.value = "报告已生成并打开";
  } catch (error) {
    statusMessage.value = `报告生成失败: ${error}`;
  } finally {
    busy.value = false;
  }
}

async function handleStartSchedule() {
  try {
    schedule.value = await startScheduledScan(scheduleInterval.value);
    statusMessage.value = "定时扫描已启动";
  } catch (error) {
    statusMessage.value = `启动失败: ${error}`;
  }
}

async function handleStopSchedule() {
  try {
    schedule.value = await stopScheduledScan();
    statusMessage.value = "定时扫描已停止";
  } catch (error) {
    statusMessage.value = `停止失败: ${error}`;
  }
}

onMounted(async () => {
  try {
    await refreshState();
    await refreshSchedule();
  } catch (error) {
    statusMessage.value = `加载失败: ${error}`;
  }
});
</script>

<style>
:root {
  --sf-blue: #007AFF;
  --sf-blue-light: #409CFF;
  --sf-blue-dark: #0051D5;
  --sf-purple: #5856D6;
  --sf-green: #34C759;
  --sf-red: #FF3B30;
  --sf-orange: #FF9500;
  --sf-gray-1: #8E8E93;
  --sf-gray-2: #AEAEB2;
  --sf-gray-3: #C7C7CC;
  --sf-gray-4: #D1D1D6;
  --sf-gray-5: #E5E5EA;
  --sf-gray-6: #F2F2F7;
  --sf-bg: #FFFFFF;
  --sf-sidebar: #F5F5F7;
  --sf-text: #1D1D1F;
  --sf-text-sec: #6E6E73;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", system-ui, sans-serif;
  background: var(--sf-gray-6);
  color: var(--sf-text);
  -webkit-font-smoothing: antialiased;
}

.app-shell {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Topbar */
.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: var(--sf-bg);
  border-bottom: 1px solid var(--sf-gray-5);
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.app-icon {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
}

.app-icon svg {
  width: 100%;
  height: 100%;
  filter: drop-shadow(0 1px 2px rgba(0,0,0,0.1));
}

.topbar-title h1 {
  font-size: 14px;
  font-weight: 600;
  color: var(--sf-text);
  line-height: 1.2;
}

.topbar-subtitle {
  font-size: 11px;
  color: var(--sf-text-sec);
}

.actions {
  display: flex;
  gap: 8px;
}

/* SF Buttons */
.sf-button {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.sf-button svg {
  flex-shrink: 0;
}

.sf-button.primary {
  background: linear-gradient(180deg, var(--sf-blue-light) 0%, var(--sf-blue) 100%);
  color: white;
  box-shadow: 0 1px 3px rgba(0, 122, 255, 0.3);
}

.sf-button.primary:hover:not(:disabled) {
  background: linear-gradient(180deg, var(--sf-blue) 0%, var(--sf-blue-dark) 100%);
  box-shadow: 0 2px 6px rgba(0, 122, 255, 0.4);
  transform: translateY(-1px);
}

.sf-button.primary:active:not(:disabled) {
  transform: translateY(0);
}

.sf-button.primary:disabled {
  background: var(--sf-gray-4);
  box-shadow: none;
  cursor: not-allowed;
}

.sf-button.secondary {
  background: var(--sf-gray-6);
  color: var(--sf-text);
  border: 1px solid var(--sf-gray-4);
}

.sf-button.secondary:hover:not(:disabled) {
  background: var(--sf-gray-5);
  border-color: var(--sf-gray-3);
}

.sf-button.secondary:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.sf-button.danger {
  background: linear-gradient(180deg, #FF6B6B 0%, var(--sf-red) 100%);
  color: white;
  box-shadow: 0 1px 3px rgba(255, 59, 48, 0.3);
}

.sf-button.danger:hover {
  box-shadow: 0 2px 6px rgba(255, 59, 48, 0.4);
  transform: translateY(-1px);
}

.sf-button.small {
  padding: 5px 10px;
  font-size: 11px;
}

/* Workspace */
.workspace {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Sidebar */
.sidebar {
  width: 220px;
  background: var(--sf-sidebar);
  border-right: 1px solid var(--sf-gray-5);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-section {
  padding: 14px 12px;
  border-bottom: 1px solid var(--sf-gray-5);
}

.sidebar-section.date-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-title {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 600;
  color: var(--sf-text-sec);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}

.sidebar-title svg {
  opacity: 0.7;
}

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 10px;
}

.stat-card {
  background: var(--sf-bg);
  padding: 10px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}

.stat-number {
  display: block;
  font-size: 20px;
  font-weight: 600;
  color: var(--sf-blue);
  line-height: 1.2;
}

.stat-card .stat-label {
  font-size: 10px;
  color: var(--sf-text-sec);
  margin-top: 2px;
}

.stat-info {
  background: var(--sf-bg);
  border-radius: 8px;
  padding: 8px 10px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}

.stat-row + .stat-row {
  border-top: 1px solid var(--sf-gray-6);
}

.stat-key {
  font-size: 11px;
  color: var(--sf-text-sec);
}

.stat-val {
  font-size: 11px;
  font-weight: 500;
  color: var(--sf-text);
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stat-val.managers {
  max-width: 90px;
  font-size: 10px;
}

/* Schedule */
.schedule-controls {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
}

.sf-select {
  flex: 1;
  padding: 5px 20px 5px 8px;
  border: 1px solid var(--sf-gray-4);
  border-radius: 5px;
  font-size: 11px;
  color: var(--sf-text);
  background: var(--sf-bg);
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg width='8' height='5' viewBox='0 0 8 5' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1L4 4L7 1' stroke='%2386868B' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 6px center;
}

.sf-select:disabled {
  background: var(--sf-gray-6);
  cursor: not-allowed;
}

.schedule-status {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  color: var(--sf-text-sec);
  padding: 6px 8px;
  background: var(--sf-bg);
  border-radius: 5px;
}

.schedule-status.active {
  color: var(--sf-green);
}

.status-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--sf-gray-3);
}

.schedule-status.active .status-indicator {
  background: var(--sf-green);
  box-shadow: 0 0 6px var(--sf-green);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Date List */
.date-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.date-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.date-item:hover {
  background: rgba(0, 0, 0, 0.04);
}

.date-item.active {
  background: var(--sf-blue);
}

.date-text {
  font-size: 12px;
  font-weight: 500;
  color: var(--sf-text);
}

.date-item.active .date-text {
  color: white;
}

.date-count {
  font-size: 10px;
  color: var(--sf-text-sec);
  background: var(--sf-gray-5);
  padding: 1px 6px;
  border-radius: 10px;
}

.date-item.active .date-count {
  background: rgba(255,255,255,0.25);
  color: white;
}

.empty-state-mini {
  padding: 20px;
  text-align: center;
}

.empty-state-mini p {
  font-size: 11px;
  color: var(--sf-text-sec);
}

/* Content */
.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: var(--sf-bg);
  border-bottom: 1px solid var(--sf-gray-5);
}

.header-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.content-header h2 {
  font-size: 15px;
  font-weight: 600;
  color: var(--sf-text);
}

.header-badge {
  font-size: 10px;
  font-weight: 500;
  color: var(--sf-blue);
  background: rgba(0, 122, 255, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  background: var(--sf-gray-6);
  border-radius: 6px;
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.search-box:focus-within {
  border-color: var(--sf-blue);
  background: var(--sf-bg);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
}

.search-icon {
  color: var(--sf-gray-2);
  flex-shrink: 0;
}

.search-box input {
  border: none;
  background: transparent;
  font-size: 12px;
  color: var(--sf-text);
  width: 140px;
  outline: none;
  font-family: inherit;
}

.search-box input::placeholder {
  color: var(--sf-gray-2);
}

/* Table */
.table-container {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.table-wrap {
  flex: 1;
  overflow: auto;
  padding: 0 20px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  position: sticky;
  top: 0;
  background: var(--sf-bg);
  padding: 10px 12px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  color: var(--sf-text-sec);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid var(--sf-gray-5);
  z-index: 1;
}

td {
  padding: 10px 12px;
  font-size: 12px;
  color: var(--sf-text);
  border-bottom: 1px solid var(--sf-gray-6);
}

tr:hover td {
  background: var(--sf-gray-6);
}

.time {
  color: var(--sf-text-sec);
  font-size: 11px;
}

/* Manager Badges */
.manager-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.manager-badge.homebrew {
  background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
  color: #E65100;
}

.manager-badge.pip {
  background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
  color: #1565C0;
}

.manager-badge.npm {
  background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
  color: #C62828;
}

.manager-badge.cargo {
  background: linear-gradient(135deg, #F3E5F5 0%, #E1BEE7 100%);
  color: #6A1B9A;
}

.manager-badge.gem {
  background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
  color: #C62828;
}

.manager-badge.go {
  background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
  color: #2E7D32;
}

.manager-badge.conda {
  background: linear-gradient(135deg, #E8F5E9 0%, #A5D6A7 100%);
  color: #1B5E20;
}

.package-name {
  font-weight: 500;
}

.version code {
  font-family: "SF Mono", Menlo, monospace;
  font-size: 11px;
  background: var(--sf-gray-6);
  padding: 2px 6px;
  border-radius: 4px;
  color: var(--sf-text-sec);
}

/* Empty State */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.empty-icon {
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--sf-text);
  margin-bottom: 4px;
}

.empty-hint {
  font-size: 12px;
  color: var(--sf-text-sec);
}


/* Spinner */
.spinner {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.sf-button.loading {
  opacity: 0.8;
  cursor: wait;
}

/* Status Bar */
.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 20px;
  background: var(--sf-sidebar);
  border-top: 1px solid var(--sf-gray-5);
  font-size: 11px;
  transition: background 0.2s ease;
}

.status-bar.active {
  background: rgba(0, 122, 255, 0.05);
}

.status-bar.active .status-message {
  color: var(--sf-blue);
  font-weight: 500;
}

.status-message {
  color: var(--sf-text-sec);
}

.status-total {
  color: var(--sf-blue);
  font-weight: 500;
}
</style>
