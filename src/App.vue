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
import { generateReport, getAppState, scanPackages } from "./services";

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

onMounted(async () => {
  try {
    await refreshState();
  } catch (error) {
    statusMessage.value = `加载失败: ${error}`;
  }
});
</script>
