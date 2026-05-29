import { createApp } from "vue";
import { invoke } from "@tauri-apps/api/core";
import App from "./App.vue";

// Dev mode: Cmd+Shift+I opens WebKit devtools
document.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === "I") {
    e.preventDefault();
    invoke("toggle_devtools");
  }
});

createApp(App).mount("#app");
