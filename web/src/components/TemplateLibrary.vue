<template>
  <Teleport to="body">
    <div v-if="visible" class="library-overlay" @click.self="$emit('close')">
      <div class="library-modal">
        <div class="library-header">
          <h2>模板库</h2>
          <button class="btn-close" @click="$emit('close')">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
        <div class="library-grid">
          <div v-for="t in templates" :key="t.key" class="library-card">
            <div class="color-bar" :style="gradientStyle(t)" />
            <div class="card-body">
              <div class="card-name">{{ t.name }}</div>
              <div class="card-desc">{{ t.description }}</div>
              <div class="palette">
                <span
                  v-for="(hex, name) in (t.colors || {})"
                  :key="name"
                  class="swatch"
                  :style="{ background: hex }"
                  :title="String(name)"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import client from "../api/client";

defineProps<{ visible: boolean }>();
defineEmits<{ (e: "close"): void }>();

interface TemplateData {
  key: string;
  name: string;
  description: string;
  colors?: Record<string, string>;
}

const templates = ref<TemplateData[]>([]);

onMounted(async () => {
  try {
    const { data } = await client.get("/templates");
    templates.value = data.templates ?? [];
  } catch { /* ignore */ }
});

function gradientStyle(t: TemplateData) {
  const c = t.colors || {};
  const from = c.primary || "#667eea";
  const to = c.accent || c.secondary || "#764ba2";
  return { background: `linear-gradient(135deg, ${from}, ${to})` };
}
</script>

<style scoped>
.library-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.library-modal {
  background: var(--card);
  border-radius: var(--radius-lg);
  width: 90vw;
  max-width: 720px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
}

.library-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-lg) var(--space-xl);
  border-bottom: 1px solid var(--border);
}
.library-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}

.btn-close {
  background: none;
  border: none;
  color: var(--muted);
  cursor: pointer;
  padding: var(--space-xs);
  border-radius: var(--radius-sm);
}
.btn-close:hover {
  color: var(--text);
  background: var(--border-light);
}

.library-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--space-lg);
  padding: var(--space-lg) var(--space-xl);
  overflow-y: auto;
}

.library-card {
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--border);
  transition: box-shadow var(--transition-fast);
}
.library-card:hover {
  box-shadow: var(--shadow-md);
}

.color-bar {
  height: 48px;
}

.card-body {
  padding: var(--space-md);
}

.card-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: var(--space-xs);
}

.card-desc {
  font-size: 12px;
  color: var(--muted);
  line-height: 1.5;
  margin-bottom: var(--space-sm);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.palette {
  display: flex;
  gap: 4px;
}
.swatch {
  width: 16px;
  height: 16px;
  border-radius: 3px;
  border: 1px solid var(--border);
}
</style>
