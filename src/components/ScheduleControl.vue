<template>
  <div class="sidebar-section">
    <div class="sidebar-title">
      <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
        <path d="M8 1a7 7 0 100 14A7 7 0 008 1zm.5 3.5v5l-3 2 .5 1 3.5-2V4.5h-1z"/>
      </svg>
      定时扫描
    </div>
    <div class="schedule-controls">
      <select
        :value="interval"
        :disabled="schedule.enabled"
        class="sf-select"
        @change="$emit('update:interval', Number($event.target.value))"
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
        @click="$emit('start')"
      >
        启动
      </button>
      <button
        v-else
        type="button"
        class="sf-button danger small"
        @click="$emit('stop')"
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
</template>

<script setup>
defineProps({
  schedule: { type: Object, default: () => ({}) },
  interval: { type: Number, default: 24 },
});

defineEmits(["update:interval", "start", "stop"]);
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

.schedule-controls {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
}

.sf-select {
  padding: 4px 8px;
  border: 1px solid var(--sf-gray-5);
  border-radius: 6px;
  font-size: 11px;
  background: var(--sf-bg);
  color: var(--sf-text);
  font-family: inherit;
}

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

.sf-button.primary {
  background: linear-gradient(180deg, #409CFF 0%, var(--sf-blue) 100%);
  color: white;
  box-shadow: 0 1px 3px rgba(0, 122, 255, 0.3);
}

.sf-button.danger {
  background: var(--sf-red);
  color: white;
}

.sf-button.small {
  padding: 4px 10px;
  font-size: 11px;
}

.schedule-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--sf-text-sec);
}

.status-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--sf-gray-3);
}

.schedule-status.active .status-indicator {
  background: var(--sf-green);
  box-shadow: 0 0 4px rgba(52, 199, 89, 0.5);
}
</style>
