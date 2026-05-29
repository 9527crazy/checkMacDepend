import { ref } from "vue";

const STORAGE_KEY = "scan-history";
const MAX_ITEMS = 5;

export function useScanHistory() {
  const history = ref(load());

  function load() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    } catch {
      return [];
    }
  }

  function save(count) {
    const now = new Date();
    const timeStr = `${now.getMonth() + 1}/${now.getDate()} ${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}`;
    history.value.unshift({ time: timeStr, count });
    if (history.value.length > MAX_ITEMS) history.value.length = MAX_ITEMS;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history.value));
  }

  return { history, save };
}
