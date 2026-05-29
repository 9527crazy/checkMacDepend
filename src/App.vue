<template>
  <main class="app-shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">Package Monitor</p>
        <h1>包安装监控</h1>
      </div>
      <div class="actions">
        <button type="button" class="ghost-button" :disabled="!selectedDate || busy" @click="handleReport">
          生成报告
        </button>
        <button type="button" class="primary-button" :disabled="busy" @click="handleScan">
          {{ busy ? "扫描中..." : "立即扫描" }}
        </button>
      </div>
    </header>

    <section class="status-grid">
      <article>
        <span>新增安装记录</span>
        <strong>{{ state.total_count }}</strong>
      </article>
      <article>
        <span>当前日期记录</span>
        <strong>{{ selectedPackages.length }}</strong>
      </article>
      <article>
        <span>上次扫描</span>
        <strong class="small-value">{{ state.last_scan_at || "从未" }}</strong>
      </article>
      <article>
        <span>可用管理器</span>
        <strong class="small-value">{{ managerText }}</strong>
      </article>
    </section>

    <section class="schedule-section">
      <div class="schedule-header">
        <h3>定时扫描</h3>
        <div class="schedule-controls">
          <select 
            v-model="scheduleInterval" 
            :disabled="schedule.enabled"
            class="schedule-select"
          >
            <option :value="1">每 1 小时</option>
            <option :value="6">每 6 小时</option>
            <option :value="12">每 12 小时</option>
            <option :value="24">每 24 小时</option>
          </select>
          <button 
            v-if="!schedule.enabled" 
            type="button" 
            class="primary-button small"
            @click="handleStartSchedule"
          >
            启动定时扫描
          </button>
          <button 
            v-else 
            type="button" 
            class="danger-button small"
            @click="handleStopSchedule"
          >
            停止定时扫描
          </button>
        </div>
      </div>
      <div class="schedule-status">
        <span v-if="schedule.enabled" class="status-active">
          定时扫描运行中 - 每 {{ schedule.interval_hours }} 小时扫描一次
        </span>
        <span v-else class="status-inactive">定时扫描已停止</span>
      </div>
    </section>

    <section class="workspace">
      <aside class="date-panel" aria-label="日期列表">
        <div class="panel-title">日期</div>
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
      </aside>

      <section class="table-panel">
        <div class="table-toolbar">
          <div>
            <h2>{{ selectedDate || "今日" }}</h2>
            <p>{{ statusMessage }}</p>
          </div>
          <label class="search-box">
            <span>搜索</span>
            <input v-model.trim="query" type="search" placeholder="包名或管理器" />
          </label>
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
                <td><span class="manager-pill">{{ pkg.manager }}</span></td>
                <td class="package-name">{{ pkg.name }}</td>
                <td class="version">{{ pkg.version }}</td>
                <td>{{ pkg.time || "-" }}</td>
              </tr>
            </tbody>
          </table>
          <div v-if="filteredPackages.length === 0" class="empty-state">
            {{ selectedDate ? "当前日期没有匹配记录" : "还没有安装记录" }}
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
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background: #f5f7fa;
  color: #1f2937;
}

.app-shell {
  min-height: 100vh;
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.eyebrow {
  font-size: 12px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.topbar h1 {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.actions {
  display: flex;
  gap: 12px;
}

.primary-button {
  padding: 10px 20px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.primary-button:hover:not(:disabled) {
  background: #2563eb;
}

.primary-button:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.primary-button.small {
  padding: 8px 16px;
  font-size: 13px;
}

.ghost-button {
  padding: 10px 20px;
  background: transparent;
  color: #3b82f6;
  border: 1px solid #3b82f6;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.ghost-button:hover:not(:disabled) {
  background: #eff6ff;
}

.ghost-button:disabled {
  color: #94a3b8;
  border-color: #e2e8f0;
  cursor: not-allowed;
}

.danger-button {
  padding: 10px 20px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.danger-button:hover {
  background: #dc2626;
}

.danger-button.small {
  padding: 8px 16px;
  font-size: 13px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.status-grid article {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.status-grid span {
  display: block;
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
}

.status-grid strong {
  font-size: 28px;
  font-weight: 600;
  color: #1f2937;
}

.status-grid .small-value {
  font-size: 14px;
  font-weight: 500;
}

.schedule-section {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  margin-bottom: 24px;
}

.schedule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.schedule-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.schedule-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.schedule-select {
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
  color: #1f2937;
  background: white;
  cursor: pointer;
}

.schedule-select:disabled {
  background: #f1f5f9;
  cursor: not-allowed;
}

.schedule-status {
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.status-active {
  color: #16a34a;
  font-weight: 500;
}

.status-inactive {
  color: #64748b;
}

.workspace {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 20px;
}

.date-panel {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 16px;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 12px;
}

.date-item {
  display: block;
  width: 100%;
  padding: 10px 12px;
  background: transparent;
  border: none;
  border-radius: 6px;
  text-align: left;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
  transition: all 0.15s;
  margin-bottom: 4px;
}

.date-item:hover {
  background: #f1f5f9;
}

.date-item.active {
  background: #3b82f6;
  color: white;
}

.empty-note {
  font-size: 13px;
  color: #94a3b8;
  text-align: center;
  padding: 20px 0;
}

.table-panel {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 20px;
}

.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.table-toolbar h2 {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.table-toolbar p {
  font-size: 13px;
  color: #64748b;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-box span {
  font-size: 13px;
  color: #64748b;
}

.search-box input {
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
  width: 200px;
}

.search-box input:focus {
  outline: none;
  border-color: #3b82f6;
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}

th {
  background: #f8fafc;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

td {
  font-size: 14px;
  color: #374151;
}

.manager-pill {
  display: inline-block;
  padding: 4px 10px;
  background: #e0e7ff;
  color: #4338ca;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.package-name {
  font-weight: 500;
}

.version {
  color: #64748b;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #94a3b8;
  font-size: 14px;
}
</style>
