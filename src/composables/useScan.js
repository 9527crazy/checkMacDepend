import { ref, nextTick, onMounted, onUnmounted } from "vue";
import { listen } from "@tauri-apps/api/event";
import { getAppState, scanPackages, generateReport } from "../services";
import { useScanHistory } from "./useStorage";

export function useScan({ showToast }) {
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
  const logEntries = ref([]);
  const logExpanded = ref(false);
  const logContainer = ref(null);
  const stateLoaded = ref(false);
  const scanCount = ref(0);
  const hasError = ref(false);
  const { history: scanHistory, save: saveScanHistory } = useScanHistory();

  let unlisten = null;
  let unlistenLog = null;

  function formatDate(dateStr) {
    const [, month, day] = dateStr.split("-");
    return `${month}月${day}日`;
  }

  async function refreshState(preferredDate) {
    state.value = await getAppState();
    const nextDates = state.value.dates || [];
    selectedDate.value =
      preferredDate && nextDates.includes(preferredDate)
        ? preferredDate
        : nextDates[0] || "";
  }

  async function handleScan() {
    busy.value = true;
    hasError.value = false;
    logExpanded.value = true;
    scanCount.value = 0;
    statusMessage.value = "扫描中...";
    showToast("正在启动扫描...", "info");
    try {
      const result = await scanPackages();
      await refreshState(result.scanned_at.slice(0, 10));
      const msg = result.is_initial_scan
        ? `首次扫描完成，${result.scanned_count} 个包`
        : `扫描完成，新增 ${result.new_count} 个包`;
      statusMessage.value = msg;
      showToast(msg, "success");
      saveScanHistory(result.scanned_count);
      stateLoaded.value = true;
    } catch (error) {
      hasError.value = true;
      statusMessage.value = `扫描失败: ${error}`;
      showToast(`扫描失败: ${error}`, "error");
    } finally {
      busy.value = false;
    }
  }

  async function handleReport(date) {
    if (!date) return;
    busy.value = true;
    hasError.value = false;
    statusMessage.value = "生成报告...";
    try {
      await generateReport(date);
      statusMessage.value = "报告已生成并打开";
      showToast("报告已生成并打开", "success");
    } catch (error) {
      hasError.value = true;
      statusMessage.value = `报告生成失败: ${error}`;
      showToast(`报告生成失败: ${error}`, "error");
    } finally {
      busy.value = false;
    }
  }

  function copyLogs() {
    const text = logEntries.value
      .map((e) => `${e.timestamp}  [${e.level}]  ${e.message}`)
      .join("\n");
    navigator.clipboard.writeText(text);
  }

  function clearLogs() {
    logEntries.value = [];
  }

  onMounted(async () => {
    unlisten = await listen("request-scan", () => {
      handleScan();
    });

    unlistenLog = await listen("scan-log", (event) => {
      logEntries.value.push(event.payload);
      if (event.payload.level === "info" && busy.value) {
        scanCount.value++;
        statusMessage.value = `扫描中... 已发现 ${scanCount.value} 个包`;
      }
      nextTick(() => {
        if (logContainer.value) {
          logContainer.value.scrollTop = logContainer.value.scrollHeight;
        }
      });
    });

    try {
      await refreshState();
      stateLoaded.value = true;
    } catch (error) {
      hasError.value = true;
      statusMessage.value = `加载失败: ${error}`;
      showToast(`加载失败: ${error}`, "error");
    }
  });

  onUnmounted(() => {
    if (unlisten) unlisten();
    if (unlistenLog) unlistenLog();
  });

  return {
    state,
    selectedDate,
    query,
    busy,
    statusMessage,
    logEntries,
    logExpanded,
    logContainer,
    stateLoaded,
    scanCount,
    hasError,
    scanHistory,
    formatDate,
    refreshState,
    handleScan,
    handleReport,
    copyLogs,
    clearLogs,
  };
}
