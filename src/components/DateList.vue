<template>
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
        :class="{ active: date === selected }"
        @click="$emit('update:selected', date)"
        @keydown.enter="$emit('update:selected', date)"
      >
        <span class="date-text">{{ formatDate(date) }}</span>
        <span class="date-count">{{ getDayCount(date) }}</span>
      </button>
      <div v-if="dates.length === 0" class="empty-state-mini">
        <p>暂无记录</p>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  dates: { type: Array, default: () => [] },
  selected: { type: String, default: "" },
  records: { type: Object, default: () => ({}) },
});

defineEmits(["update:selected"]);

function formatDate(dateStr) {
  const [, month, day] = dateStr.split("-");
  return `${month}月${day}日`;
}

function getDayCount(date) {
  return props.records?.[date]?.length || 0;
}
</script>

<style scoped>
.sidebar-section {
  padding: 12px;
  border-bottom: 1px solid var(--sf-gray-5);
}

.date-section {
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
  padding: 6px 10px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--sf-text);
  font-family: inherit;
}

.date-item:hover {
  background: var(--sf-gray-5);
}

.date-item.active {
  background: var(--sf-blue);
  color: white !important;
}

.date-text {
  font-size: 13px;
  font-weight: 500;
}

.date-count {
  font-size: 11px;
  opacity: 0.7;
}

.empty-state-mini {
  text-align: center;
  padding: 20px 0;
  color: var(--sf-text-sec);
  font-size: 12px;
}
</style>
