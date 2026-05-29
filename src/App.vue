<template>
  <main class="app-shell">
    <header class="topbar">
      <div class="topbar-left">
        <div class="app-icon">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="8" fill="#007AFF"/>
            <path d="M8 16h16M16 8v16M10 10l12 12M22 10L10 22" stroke="white" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <div>
          <h1>包安装监控</h1>
          <p class="subtitle">Package Monitor</p>
        </div>
      </div>
      <div class="actions">
        <button 
          type="button" 
          class="sf-button secondary" 
          :disabled="!selectedDate || busy" 
          @click="handleReport"
        >
          生成报告
        </button>
        <button 
          type="button" 
          class="sf-button primary" 
          :disabled="busy" 
          @click="handleScan"
        >
          {{ busy ? "扫描中..." : "立即扫描" }}
        </button>
      </div>
    </header>

    <section class="status-grid">
      <article class="status-card">
        <div class="status-icon blue">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 2a8 8 0 100 16 8 8 0 000-16zm1 11H9v-2h2v2zm0-4H9V5h2v4z"/>
          </svg>
        </div>
        <div class="status-content">
          <span>新增安装记录</span>
          <strong>{{ state.total_count }}</strong>
        </div>
      </article>
      <article class="status-card">
        <div class="status-icon green">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 2a8 8 0 100 16 8 8 0 000-16zm-1 11.5L5.5 10l1.4-1.4L9 10.7l4.1-4.1 1.4 1.4L9 13.5z"/>
          </svg>
        </div>
        <div class="status-content">
          <span>当前日期记录</span>
          <strong>{{ selectedPackages.length }}</strong>
        </div>
      </article>
      <article class="status-card">
        <div class="status-icon purple">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 2a8 8 0 100 16 8 8 0 000-16zm1 8.414l-3.707 3.707-1.414-1.414L8.586 10 4.879 6.293l1.414-1.414L10 7.586l3.707-3.707 1.414 1.414L11.414 10l3.707 3.707-1.414 1.414L10 10.414z"/>
          </svg>
        </div>
        <div class="status-content">
          <span>上次扫描</span>
          <strong class="text-sm">{{ state.last_scan_at || "从未" }}</strong>
        </div>
      </article>
      <article class="status-card">
        <div class="status-icon orange">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 2a8 8 0 100 16 8 8 0 000-16zM7 7h6v2H7V7zm0 4h6v2H7v-2z"/>
          </svg>
        </div>
        <div class="status-content">
          <span>可用管理器</span>
          <strong class="text-sm">{{ managerText }}</strong>
        </div>
      </article>
    </section>

    <section class="schedule-section">
      <div class="schedule-header">
        <h3>定时扫描</h3>
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
            启动定时扫描
          </button>
          <button 
            v-else 
            type="button" 
            class="sf-button danger small"
            @click="handleStopSchedule"
          >
            停止定时扫描
          </button>
        </div>
      </div>
      <div class="schedule-status">
        <span v-if="schedule.enabled" class="status-active">
          <span class="status-dot active"></span>
          定时扫描运行中 - 每 {{ schedule.interval_hours }} 小时扫描一次
        </span>
        <span v-else class="status-inactive">
          <span class="status-dot inactive"></span>
          定时扫描已停止
        </span>
      </div>
    </section>

    <section class="workspace">
      <aside class="date-panel" aria-label="日期列表">
        <div class="panel-header">
          <span class="panel-title">日期</span>
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
            {{ date }}
          </button>
          <p v-if="dates.length === 0" class="empty-note">暂无记录</p>
        </div>
      </aside>

      <section class="table-panel">
        <div class="table-toolbar">
          <div>
            <h2>{{ selectedDate || "今日" }}</h2>
            <p class="toolbar-subtitle">{{ statusMessage }}</p>
          </div>
          <div class="search-box">
            <svg class="search-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M11.742 10.344a6.5 6.5 0 10-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 001.415-1.414l-3.85-3.85a1.007 1.007 0 00-.115-.1zM12 6.5a5.5 5.5 0 11-11 0 5.5 5.5 0 0111 0z"/>
            </svg>
            <input v-model.trim="query" type="search" placeholder="搜索包名或管理器" />
          </div>
        </div>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>包管理器</th>
                <th>包名</th>
                <th>版本</th>
                <th>安装时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="pkg in filteredPackages" :key="`${pkg.manager}-${pkg.name}-${pkg.version}`">
                <td><span class="manager-badge" :class="pkg.manager">{{ pkg.manager }}</span></td>
                <td class="package-name">{{ pkg.name }}</td>
                <td class="version">{{ pkg.version }}</td>
                <td class="time">{{ pkg.time || "-" }}</td>
              </tr>
            </tbody>
          </table>
          <div v-if="filteredPackages.length === 0" class="empty-state">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
              <circle cx="24" cy="24" r="20" stroke="#C7C7CC" stroke-width="2"/>
              <path d="M16 24h16M24 16v16" stroke="#C7C7CC" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <p>{{ selectedDate ? "当前日期没有匹配记录" : "还没有安装记录" }}</p>
          </div>
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
  return managers.length ? managers.join(", ") : "未检测";
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
  statusMessage.value = "正在扫描已安装包...";
  try {
    const result = await scanPackages();
    await refreshState(result.scanned_at.slice(0, 10));
    statusMessage.value = result.is_initial_scan
      ? `首次扫描已建立基线，已扫描 ${result.scanned_count} 个包`
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
  statusMessage.value = "正在生成报告...";
  try {
    const path = await generateReport(selectedDate.value);
    statusMessage.value = `报告已生成: ${path}`;
  } catch (error) {
    statusMessage.value = `报告生成失败: ${error}`;
  } finally {
    busy.value = false;
  }
}

async function handleStartSchedule() {
  try {
    schedule.value = await startScheduledScan(scheduleInterval.value);
    statusMessage.value = `定时扫描已启动，每 ${schedule.value.interval_hours} 小时扫描一次`;
  } catch (error) {
    statusMessage.value = `启动定时扫描失败: ${error}`;
  }
}

async function handleStopSchedule() {
  try {
    schedule.value = await stopScheduledScan();
    statusMessage.value = "定时扫描已停止";
  } catch (error) {
    statusMessage.value = `停止定时扫描失败: ${error}`;
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
  --sf-blue-hover: #0056CC;
  --sf-green: #34C759;
  --sf-red: #FF3B30;
  --sf-orange: #FF9500;
  --sf-purple: #AF52DE;
  --sf-gray-1: #8E8E93;
  --sf-gray-2: #AEAEB2;
  --sf-gray-3: #C7C7CC;
  --sf-gray-4: #D1D1D6;
  --sf-gray-5: #E5E5EA;
  --sf-gray-6: #F2F2F7;
  --sf-bg: #FFFFFF;
  --sf-sidebar-bg: #F5F5F7;
  --sf-text: #1D1D1F;
  --sf-text-secondary: #86868B;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
  background: var(--sf-gray-6);
  color: var(--sf-text);
  -webkit-font-smoothing: antialiased;
}

.app-shell {
  min-height: 100vh;
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

/* Topbar */
.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px 20px;
  background: var(--sf-bg);
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.app-icon {
  width: 40px;
  height: 40px;
}

.app-icon svg {
  width: 100%;
  height: 100%;
}

.topbar h1 {
  font-size: 20px;
  font-weight: 600;
  color: var(--sf-text);
  letter-spacing: -0.3px;
}

.subtitle {
  font-size: 12px;
  color: var(--sf-text-secondary);
  margin-top: 2px;
}

.actions {
  display: flex;
  gap: 10px;
}

/* SF Buttons */
.sf-button {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.sf-button.primary {
  background: var(--sf-blue);
  color: white;
}

.sf-button.primary:hover:not(:disabled) {
  background: var(--sf-blue-hover);
}

.sf-button.primary:disabled {
  background: var(--sf-gray-4);
  cursor: not-allowed;
}

.sf-button.secondary {
  background: var(--sf-gray-6);
  color: var(--sf-text);
  border: 1px solid var(--sf-gray-4);
}

.sf-button.secondary:hover:not(:disabled) {
  background: var(--sf-gray-5);
}

.sf-button.secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sf-button.danger {
  background: var(--sf-red);
  color: white;
}

.sf-button.danger:hover {
  background: #E6392E;
}

.sf-button.small {
  padding: 6px 12px;
  font-size: 12px;
}

/* Status Grid */
.status-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.status-card {
  background: var(--sf-bg);
  padding: 16px;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-icon.blue {
  background: rgba(0, 122, 255, 0.12);
  color: var(--sf-blue);
}

.status-icon.green {
  background: rgba(52, 199, 89, 0.12);
  color: var(--sf-green);
}

.status-icon.purple {
  background: rgba(175, 82, 222, 0.12);
  color: var(--sf-purple);
}

.status-icon.orange {
  background: rgba(255, 149, 0, 0.12);
  color: var(--sf-orange);
}

.status-content span {
  display: block;
  font-size: 12px;
  color: var(--sf-text-secondary);
  margin-bottom: 4px;
}

.status-content strong {
  font-size: 22px;
  font-weight: 600;
  color: var(--sf-text);
}

.status-content .text-sm {
  font-size: 13px;
  font-weight: 500;
}

/* Schedule Section */
.schedule-section {
  background: var(--sf-bg);
  padding: 16px 20px;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  margin-bottom: 16px;
}

.schedule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.schedule-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--sf-text);
}

.schedule-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.sf-select {
  padding: 6px 24px 6px 10px;
  border: 1px solid var(--sf-gray-4);
  border-radius: 6px;
  font-size: 13px;
  color: var(--sf-text);
  background: var(--sf-bg);
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg width='10' height='6' viewBox='0 0 10 6' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1L5 5L9 1' stroke='%2386868B' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
}

.sf-select:disabled {
  background: var(--sf-gray-6);
  cursor: not-allowed;
}

.schedule-status {
  padding: 10px 12px;
  background: var(--sf-gray-6);
  border-radius: 6px;
  font-size: 12px;
}

.status-active {
  color: var(--sf-green);
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-inactive {
  color: var(--sf-text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-dot.active {
  background: var(--sf-green);
}

.status-dot.inactive {
  background: var(--sf-gray-3);
}

/* Workspace */
.workspace {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 16px;
}

/* Date Panel (macOS Sidebar Style) */
.date-panel {
  background: var(--sf-sidebar-bg);
  border-radius: 10px;
  overflow: hidden;
}

.panel-header {
  padding: 12px 16px 8px;
}

.panel-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--sf-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.date-list {
  padding: 0 8px 8px;
}

.date-item {
  display: block;
  width: 100%;
  padding: 8px 12px;
  background: transparent;
  border: none;
  border-radius: 6px;
  text-align: left;
  font-size: 13px;
  color: var(--sf-text);
  cursor: pointer;
  transition: background 0.1s ease;
}

.date-item:hover {
  background: rgba(0, 0, 0, 0.04);
}

.date-item.active {
  background: var(--sf-blue);
  color: white;
}

.empty-note {
  font-size: 12px;
  color: var(--sf-text-secondary);
  text-align: center;
  padding: 20px 0;
}

/* Table Panel */
.table-panel {
  background: var(--sf-bg);
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  padding: 16px 20px;
}

.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.table-toolbar h2 {
  font-size: 16px;
  font-weight: 600;
  color: var(--sf-text);
  margin-bottom: 2px;
}

.toolbar-subtitle {
  font-size: 12px;
  color: var(--sf-text-secondary);
}

.search-box {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: var(--sf-gray-6);
  border-radius: 6px;
  border: 1px solid transparent;
  transition: border-color 0.15s;
}

.search-box:focus-within {
  border-color: var(--sf-blue);
  background: var(--sf-bg);
}

.search-icon {
  color: var(--sf-gray-2);
}

.search-box input {
  border: none;
  background: transparent;
  font-size: 13px;
  color: var(--sf-text);
  width: 180px;
  outline: none;
  font-family: inherit;
}

.search-box input::placeholder {
  color: var(--sf-gray-2);
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid var(--sf-gray-5);
}

th {
  font-size: 11px;
  font-weight: 600;
  color: var(--sf-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

td {
  font-size: 13px;
  color: var(--sf-text);
}

.time {
  color: var(--sf-text-secondary);
}

/* Manager Badges */
.manager-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.manager-badge.homebrew {
  background: rgba(255, 149, 0, 0.12);
  color: #FF9500;
}

.manager-badge.pip {
  background: rgba(0, 122, 255, 0.12);
  color: #007AFF;
}

.manager-badge.npm {
  background: rgba(255, 59, 48, 0.12);
  color: #FF3B30;
}

.manager-badge.cargo {
  background: rgba(175, 82, 222, 0.12);
  color: #AF52DE;
}

.manager-badge.gem {
  background: rgba(255, 59, 48, 0.12);
  color: #FF3B30;
}

.manager-badge.go {
  background: rgba(0, 122, 255, 0.12);
  color: #007AFF;
}

.manager-badge.conda {
  background: rgba(52, 199, 89, 0.12);
  color: #34C759;
}

.package-name {
  font-weight: 500;
}

.version {
  color: var(--sf-text-secondary);
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--sf-text-secondary);
  font-size: 13px;
}

.empty-state svg {
  margin-bottom: 12px;
  opacity: 0.5;
}
</style>
