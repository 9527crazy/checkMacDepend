<template>
  <div class="table-container">
    <div v-if="!loaded" class="skeleton-table">
      <div class="skeleton-row" v-for="i in 5" :key="i">
        <div class="skeleton-cell skeleton-badge"></div>
        <div class="skeleton-cell skeleton-text" :class="'skeleton-w-' + i"></div>
        <div class="skeleton-cell skeleton-text" style="width: 20%"></div>
        <div class="skeleton-cell skeleton-text" style="width: 15%"></div>
      </div>
    </div>
    <div v-else-if="packages.length > 0" class="table-wrap" role="table" aria-describedby="table-desc">
      <table>
        <caption id="table-desc" class="sr-only">已安装包列表，包含管理器、包名、版本和时间信息</caption>
        <thead>
          <tr>
            <th class="th-manager">管理器</th>
            <th class="th-name">包名</th>
            <th class="th-version">版本</th>
            <th class="th-time">时间</th>
          </tr>
        </thead>
        <tbody style="transition: opacity 0.15s ease;">
          <tr v-for="pkg in packages" :key="`${pkg.manager}-${pkg.name}-${pkg.version}`">
            <td>
              <span class="manager-badge" :class="pkg.manager">{{ pkg.manager }}</span>
            </td>
            <td class="package-name">{{ pkg.name }}</td>
            <td class="version">
              <code>{{ pkg.version }}</code>
            </td>
            <td class="time">{{ pkg.time || "-" }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <EmptyState v-else :selected-date="selectedDate" />
  </div>
</template>

<script setup>
import EmptyState from "./EmptyState.vue";

defineProps({
  packages: { type: Array, default: () => [] },
  loaded: { type: Boolean, default: false },
  selectedDate: { type: String, default: "" },
});
</script>

<style scoped>
.table-container {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.table-wrap {
  flex: 1;
  overflow: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 10px 16px;
  text-align: left;
  border-bottom: 1px solid var(--sf-gray-5);
  font-size: 13px;
}

th {
  position: sticky;
  top: 0;
  background: var(--sf-bg);
  font-weight: 600;
  font-size: 11px;
  color: var(--sf-text-sec);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.manager-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  background: var(--sf-gray-6);
  color: var(--sf-text-sec);
}

.manager-badge.homebrew { background: #FFF3E0; color: #E65100; }
.manager-badge.pip { background: #E3F2FD; color: #1565C0; }
.manager-badge.npm { background: #FBE9E7; color: #BF360C; }
.manager-badge.cargo { background: #F3E5F5; color: #6A1B9A; }
.manager-badge.gem { background: #FFEBEE; color: #B71C1C; }
.manager-badge.go { background: #E8F5E9; color: #2E7D32; }

.package-name {
  font-weight: 500;
}

.version code {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--sf-gray-6);
  font-family: "SF Mono", "Menlo", monospace;
}

.time {
  color: var(--sf-text-sec);
  font-size: 12px;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.skeleton-table {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.skeleton-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.skeleton-cell {
  height: 16px;
  border-radius: 4px;
  background: linear-gradient(90deg, var(--sf-gray-5) 25%, var(--sf-gray-4) 50%, var(--sf-gray-5) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

.skeleton-badge {
  width: 60px;
  height: 20px;
  border-radius: 4px;
}

.skeleton-text {
  height: 14px;
}

.skeleton-w-1 { width: 55%; }
.skeleton-w-2 { width: 42%; }
.skeleton-w-3 { width: 63%; }
.skeleton-w-4 { width: 48%; }
.skeleton-w-5 { width: 58%; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
