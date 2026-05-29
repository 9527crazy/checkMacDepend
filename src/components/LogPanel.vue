<template>
  <div class="log-panel" :class="{ collapsed: !expanded }">
    <div class="log-header" @click="$emit('update:expanded', !expanded)">
      <div class="log-header-left">
        <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
          <path d="M2 3h12v1H2V3zm0 3h12v1H2V6zm0 3h8v1H2V9zm0 3h6v1H2v-1z"/>
        </svg>
        <span>扫描日志</span>
        <span class="log-count" v-if="entries.length">{{ entries.length }}</span>
      </div>
      <div class="log-header-right" @click.stop>
        <button type="button" class="log-btn" @click="$emit('copy')" title="复制日志">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
            <path d="M4 2h8v2H4V2zm-1 2v8h8V4H3zm1 1h6v6H4V5z"/>
          </svg>
        </button>
        <button type="button" class="log-btn" @click="$emit('clear')" title="清空日志">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
            <path d="M5 2V1h6v1h3v1H2V2h3zm1 3v7h4V5H6zm-2 1v6h1V6H4zm4 0v6h1V6H8zm3 0v6h1V6h-1z"/>
          </svg>
        </button>
      </div>
    </div>
    <div v-show="expanded" ref="logContainer" class="log-body">
      <div
        v-for="(entry, idx) in entries"
        :key="idx"
        class="log-entry"
        :class="entry.level"
      >
        <span class="log-time">{{ entry.timestamp }}</span>
        <span class="log-level">[{{ entry.level }}]</span>
        <span class="log-msg">{{ entry.message }}</span>
      </div>
      <div v-if="entries.length === 0" class="log-empty">暂无日志</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  entries: { type: Array, default: () => [] },
  expanded: { type: Boolean, default: false },
});

defineEmits(["update:expanded", "copy", "clear"]);
</script>

<style scoped>
.log-panel {
  border-top: 1px solid var(--sf-gray-5);
  background: #1a1b26;
  transition: height 0.2s ease;
}

.log-panel.collapsed {
  height: 36px;
  overflow: hidden;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  cursor: pointer;
  user-select: none;
}

.log-header-left {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #7982a9;
  font-size: 12px;
  font-weight: 500;
}

.log-count {
  background: #3b4261;
  color: #7982a9;
  padding: 1px 6px;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 600;
}

.log-header-right {
  display: flex;
  gap: 4px;
}

.log-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  border-radius: 4px;
  color: #7982a9;
  cursor: pointer;
  transition: all 0.15s ease;
}

.log-btn:hover {
  background: #3b4261;
  color: #c0caf5;
}

.log-body {
  max-height: 200px;
  overflow-y: auto;
  padding: 0 16px 12px;
  font-family: "SF Mono", "Menlo", monospace;
  font-size: 11px;
}

.log-entry {
  display: flex;
  gap: 8px;
  padding: 3px 0;
  line-height: 1.5;
}

.log-time {
  color: #565f89;
  flex-shrink: 0;
}

.log-level {
  font-weight: 600;
  flex-shrink: 0;
}

.log-entry.info .log-level {
  color: #7aa2f7;
}

.log-entry.error .log-level {
  color: #F7768E;
}

.log-msg {
  color: #C0CAF5;
}

.log-entry.success .log-msg {
  color: #9ECE6A;
}

.log-entry.warning .log-msg {
  color: #E0AF68;
}

.log-empty {
  color: #565f89;
  text-align: center;
  padding: 20px 0;
}
</style>
