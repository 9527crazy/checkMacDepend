import { ref } from "vue";
import { getScanSchedule, startScheduledScan, stopScheduledScan } from "../services";

export function useSchedule({ showToast, statusMessage }) {
  const schedule = ref({
    enabled: false,
    interval_hours: 24,
    last_scan_at: null,
  });
  const scheduleInterval = ref(24);

  async function refreshSchedule() {
    try {
      schedule.value = await getScanSchedule();
      scheduleInterval.value = schedule.value.interval_hours;
    } catch (error) {
      console.error("Failed to load schedule:", error);
    }
  }

  async function handleStartSchedule() {
    try {
      schedule.value = await startScheduledScan(scheduleInterval.value);
      statusMessage.value = "定时扫描已启动";
      showToast("定时扫描已启动", "success");
    } catch (error) {
      statusMessage.value = `启动失败: ${error}`;
      showToast(`启动失败: ${error}`, "error");
    }
  }

  async function handleStopSchedule() {
    try {
      schedule.value = await stopScheduledScan();
      statusMessage.value = "定时扫描已停止";
      showToast("定时扫描已停止", "success");
    } catch (error) {
      statusMessage.value = `停止失败: ${error}`;
      showToast(`停止失败: ${error}`, "error");
    }
  }

  return {
    schedule,
    scheduleInterval,
    refreshSchedule,
    handleStartSchedule,
    handleStopSchedule,
  };
}
