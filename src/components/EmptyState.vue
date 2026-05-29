<template>
  <div class="empty-state">
    <div class="empty-icon">
      <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
        <circle cx="32" cy="32" r="28" stroke="#E5E5EA" stroke-width="2" stroke-dasharray="4 4"/>
        <path d="M24 32h16M32 24v16" stroke="#C7C7CC" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </div>
    <p class="empty-title">{{ selectedDate ? "暂无安装记录" : "请先扫描或选择日期" }}</p>
    <p class="empty-hint">点击"立即扫描"开始检测已安装的包</p>
  </div>
</template>

<script setup>
defineProps({
  selectedDate: { type: String, default: "" },
});
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--sf-text);
  margin-bottom: 6px;
}

.empty-hint {
  font-size: 12px;
  color: var(--sf-text-sec);
}
</style>
