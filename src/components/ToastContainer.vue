<template>
  <Teleport to="body">
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="toast-item"
          :class="toast.type"
        >
          <svg v-if="toast.type === 'info'" width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 2.5a1.25 1.25 0 110 2.5 1.25 1.25 0 010-2.5zM6.5 7h3v5h-3V7z"/>
          </svg>
          <svg v-else-if="toast.type === 'success'" width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 1a7 7 0 100 14A7 7 0 008 1zm3.3-4.3L6.5 7.2 4.7 5.4 3.3 6.8l3.2 3.2 4.8-6.2z"/>
          </svg>
          <svg v-else width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 3a.75.75 0 01.75.75v4a.75.75 0 01-1.5 0v-4A.75.75 0 018 4zm0 8a1 1 0 100-2 1 1 0 000 2z"/>
          </svg>
          <span class="toast-msg">{{ toast.message }}</span>
          <button type="button" class="toast-close" @click="dismissToast(toast.id)">&times;</button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  toasts: { type: Array, default: () => [] },
});

const emit = defineEmits(["dismiss"]);

function dismissToast(id) {
  emit("dismiss", id);
}
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}

.toast-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 8px;
  background: var(--sf-bg);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  font-size: 13px;
  font-weight: 500;
  color: var(--sf-text);
  pointer-events: auto;
  max-width: 320px;
}

.toast-item.info {
  border-left: 3px solid var(--sf-blue);
}

.toast-item.info svg {
  color: var(--sf-blue);
  flex-shrink: 0;
}

.toast-item.success {
  border-left: 3px solid var(--sf-green);
}

.toast-item.success svg {
  color: var(--sf-green);
  flex-shrink: 0;
}

.toast-item.error {
  border-left: 3px solid var(--sf-red);
}

.toast-item.error svg {
  color: var(--sf-red);
  flex-shrink: 0;
}

.toast-msg {
  line-height: 1.3;
  flex: 1;
}

.toast-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  background: transparent;
  border-radius: 4px;
  color: var(--sf-gray-2);
  font-size: 16px;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s ease;
}

.toast-close:hover {
  background: var(--sf-gray-5);
  color: var(--sf-text);
}

.toast-enter-active {
  transition: all 0.25s ease;
}

.toast-leave-active {
  transition: all 0.2s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>
