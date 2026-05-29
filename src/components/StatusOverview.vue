<template>
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
        <span class="stat-number">{{ selectedCount }}</span>
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
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  state: { type: Object, default: () => ({}) },
  selectedCount: { type: Number, default: 0 },
});

const managerText = computed(() => {
  const managers = props.state.available_managers || [];
  if (!managers.length) return "未检测";
  if (managers.length <= 2) return managers.join(", ");
  return managers.slice(0, 2).join(", ") + " +" + (managers.length - 2);
});

const managerList = computed(() => {
  const managers = props.state.available_managers || [];
  return managers.join(", ") || "未检测";
});
</script>

<style scoped>
.sidebar-section {
  padding: 12px;
  border-bottom: 1px solid var(--sf-gray-5);
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

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 10px;
}

.stat-card {
  background: var(--sf-bg);
  border: 1px solid var(--sf-gray-5);
  border-radius: 8px;
  padding: 10px;
  text-align: center;
}

.stat-number {
  display: block;
  font-size: 20px;
  font-weight: 600;
  color: var(--sf-blue);
}

.stat-label {
  font-size: 11px;
  color: var(--sf-text-sec);
}

.stat-info {
  background: var(--sf-bg);
  border: 1px solid var(--sf-gray-5);
  border-radius: 8px;
  padding: 8px 10px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 3px 0;
}

.stat-key {
  font-size: 12px;
  color: var(--sf-text-sec);
}

.stat-val {
  font-size: 12px;
  color: var(--sf-text);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
