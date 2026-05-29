<template>
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
        :disabled="!canReport || busy"
        aria-label="生成报告"
        tabindex="0"
        @click="$emit('report')"
        @keydown.enter="$emit('report')"
      >
        <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
          <path d="M2 2h12v12H2V2zm1 1v10h10V3H3zm2 2h6v1H5V5zm0 3h6v1H5V8zm0 3h4v1H5v-1z"/>
        </svg>
        生成报告
      </button>
      <button
        type="button"
        class="sf-button"
        :class="busy ? 'scanning' : 'primary'"
        :disabled="busy"
        aria-label="立即扫描"
        tabindex="0"
        @click="$emit('scan')"
        @keydown.enter="$emit('scan')"
      >
        <span v-if="busy" class="spinner"></span>
        <svg v-else width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
          <path d="M8 2a6 6 0 100 12A6 6 0 008 2zm0 1v4l3 2"/>
        </svg>
        {{ busy ? "扫描中..." : "立即扫描" }}
      </button>
    </div>
  </header>
</template>

<script setup>
defineProps({
  busy: { type: Boolean, default: false },
  canReport: { type: Boolean, default: false },
});

defineEmits(["scan", "report"]);
</script>

<style scoped>
.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background: var(--sf-sidebar);
  border-bottom: 1px solid var(--sf-gray-5);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.topbar-title h1 {
  font-size: 16px;
  font-weight: 600;
  color: var(--sf-text);
}

.topbar-subtitle {
  font-size: 11px;
  color: var(--sf-text-sec);
}

.actions {
  display: flex;
  gap: 8px;
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

.sf-button.primary:hover {
  background: linear-gradient(180deg, #6BB3FF 0%, #3395FF 100%);
}

.sf-button.secondary {
  background: var(--sf-gray-6);
  color: var(--sf-text);
  border: 1px solid var(--sf-gray-5);
}

.sf-button.secondary:hover {
  background: var(--sf-gray-5);
}

.sf-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

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

.sf-button.scanning {
  background: linear-gradient(180deg, #FF6B6B 0%, var(--sf-red) 100%);
  color: white;
  box-shadow: 0 1px 3px rgba(255, 59, 48, 0.3);
  cursor: wait;
}
</style>
