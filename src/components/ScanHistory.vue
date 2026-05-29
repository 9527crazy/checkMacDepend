<template>
  <div v-if="history.length > 0" class="sidebar-section">
    <div class="sidebar-title">
      <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
        <path d="M8 1a7 7 0 100 14A7 7 0 008 1zm.5 3.5v5l-3 2 .5 1 3.5-2V4.5h-1z"/>
      </svg>
      最近扫描
    </div>
    <div class="history-list">
      <div v-for="(item, idx) in history" :key="idx" class="history-item">
        <span class="history-dot"></span>
        <span class="history-time">{{ item.time }}</span>
        <span class="history-count">{{ item.count }} 个包</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  history: { type: Array, default: () => [] },
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

.history-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--sf-text-sec);
  padding: 4px 0;
}

.history-item:first-child .history-time {
  font-weight: 600;
  color: var(--sf-text);
}

.history-item:first-child .history-dot {
  width: 8px;
  height: 8px;
  background: var(--sf-green);
  box-shadow: 0 0 4px rgba(52, 199, 89, 0.4);
}

.history-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--sf-gray-3);
  flex-shrink: 0;
}

.history-time {
  font-weight: 500;
  color: var(--sf-text);
  min-width: 70px;
}

.history-count {
  color: var(--sf-text-sec);
}
</style>
