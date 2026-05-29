<template>
  <main class="app-shell">
    <TopBar
      :busy="busy"
      :can-report="!!selectedDate"
      @scan="handleScan"
      @report="handleReport(selectedDate)"
    />

    <section class="workspace">
      <aside class="sidebar">
        <StatusOverview :state="state" :selected-count="selectedPackages.length" />
        <ScanHistory :history="scanHistory" />
        <ScheduleControl
          v-model:schedule="schedule"
          v-model:interval="scheduleInterval"
          @start="handleStartSchedule"
          @stop="handleStopSchedule"
        />
        <DateList
          :dates="dates"
          :selected="selectedDate"
          :records="state.records"
          @update:selected="selectedDate = $event"
        />
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
            <input v-model.trim="query" type="search" placeholder="搜索包名..." aria-label="搜索包名" @keydown.escape="query = ''" />
          </div>
        </div>

        <PackageTable
          :packages="filteredPackages"
          :loaded="stateLoaded"
          :selected-date="selectedDate"
        />

        <LogPanel
          v-model:expanded="logExpanded"
          :entries="logEntries"
          @copy="copyLogs"
          @clear="clearLogs"
        />
      </section>
    </section>

    <footer class="status-bar" :class="{ active: busy, error: hasError }">
      <span class="status-message">{{ statusMessage }}</span>
      <span class="status-total" v-if="state.total_count">{{ state.total_count }} 个包</span>
    </footer>

    <ToastContainer :toasts="toasts" @dismiss="dismissToast" />
  </main>
</template>

<script setup>
import { computed, onMounted } from "vue";
import TopBar from "./components/TopBar.vue";
import StatusOverview from "./components/StatusOverview.vue";
import ScanHistory from "./components/ScanHistory.vue";
import ScheduleControl from "./components/ScheduleControl.vue";
import DateList from "./components/DateList.vue";
import PackageTable from "./components/PackageTable.vue";
import LogPanel from "./components/LogPanel.vue";
import ToastContainer from "./components/ToastContainer.vue";

import { useScan } from "./composables/useScan";
import { useSchedule } from "./composables/useSchedule";
import { useToast } from "./composables/useToast";

const { toasts, showToast, dismissToast } = useToast();

const {
  state,
  selectedDate,
  query,
  busy,
  statusMessage,
  logEntries,
  logExpanded,
  logContainer,
  stateLoaded,
  hasError,
  scanHistory,
  formatDate,
  handleScan,
  handleReport,
  copyLogs,
  clearLogs,
} = useScan({ showToast });

const {
  schedule,
  scheduleInterval,
  refreshSchedule,
  handleStartSchedule,
  handleStopSchedule,
} = useSchedule({ showToast, statusMessage });

const dates = computed(() => state.value.dates || []);
const selectedPackages = computed(() => {
  if (!selectedDate.value) return [];
  return state.value.records?.[selectedDate.value] || [];
});
const filteredPackages = computed(() => {
  const needle = query.value.toLowerCase();
  if (!needle) return selectedPackages.value;
  return selectedPackages.value.filter(
    (pkg) =>
      pkg.name.toLowerCase().includes(needle) ||
      pkg.manager.toLowerCase().includes(needle)
  );
});

onMounted(async () => {
  await refreshSchedule();
});
</script>

<style>
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
  min-width: 900px;
  min-height: 100vh;
}

button, input, select {
  font: inherit;
}

button {
  cursor: pointer;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}
</style>

<style scoped>
.app-shell {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.workspace {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.sidebar {
  width: 220px;
  background: var(--sf-sidebar);
  border-right: 1px solid var(--sf-gray-5);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--sf-bg);
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--sf-gray-5);
}

.header-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-info h2 {
  font-size: 15px;
  font-weight: 600;
  color: var(--sf-text);
}

.header-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  background: var(--sf-blue);
  color: white;
  font-size: 11px;
  font-weight: 600;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 10px;
  color: var(--sf-gray-2);
  pointer-events: none;
}

.search-box input {
  padding: 6px 10px 6px 30px;
  border: 1px solid var(--sf-gray-5);
  border-radius: 6px;
  font-size: 12px;
  width: 200px;
  transition: all 0.15s ease;
  background: var(--sf-gray-6);
}

.search-box input:focus {
  outline: none;
  border-color: var(--sf-blue);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.15);
  background: var(--sf-bg);
}

.table-container {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

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

.status-bar.error {
  background: rgba(255, 59, 48, 0.08);
}

.status-bar.error .status-message {
  color: var(--sf-red);
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
