<template>
  <div class="outline-preview" v-if="outline">
    <div class="outline-header">
      <div class="outline-icon">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M2 3h12M2 6h12M2 9h8M2 12h6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </div>
      <div>
        <div class="outline-title">{{ outline.title }}</div>
        <div class="outline-meta">{{ outline.slides?.length ?? 0 }} 页</div>
      </div>
    </div>
    <div class="slide-list">
      <div v-for="slide in outline.slides" :key="slide.page" class="slide-item">
        <div class="slide-page">{{ slide.page }}</div>
        <div class="slide-content">
          <div class="slide-top">
            <span class="badge" :class="layoutBadge(slide.layout)">{{ layoutLabel(slide.layout) }}</span>
            <span class="slide-title">{{ slide.title }}</span>
          </div>
          <div v-if="slide.key_points?.length" class="key-points">
            <div v-for="(kp, ki) in slide.key_points" :key="ki" class="key-point">
              <span class="emphasis-dot" :class="`dot-${kp.emphasis ?? 'medium'}`"></span>
              <div>
                <span class="kp-text">{{ kp.text }}</span>
                <div v-if="kp.sub_points?.length" class="sub-points">
                  <span v-for="(sp, si) in kp.sub_points" :key="si" class="sub-point">{{ sp }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  outline: any;
}>();

const LAYOUT_LABELS: Record<string, string> = {
  cover: "封面",
  toc: "目录",
  content: "内容",
  section: "章节",
  ending: "结尾",
};

const LAYOUT_BADGES: Record<string, string> = {
  cover: "badge--primary",
  toc: "badge--info",
  section: "badge--warning",
  ending: "badge--success",
  content: "",
};

function layoutLabel(layout: string): string {
  return LAYOUT_LABELS[layout] ?? layout;
}

function layoutBadge(layout: string): string {
  return LAYOUT_BADGES[layout] ?? "";
}
</script>

<style scoped>
.outline-preview {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
  max-width: 560px;
  box-shadow: var(--shadow-sm);
}

.outline-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
  padding-bottom: var(--space-md);
  border-bottom: 1px solid var(--border-light);
}

.outline-icon {
  width: 32px;
  height: 32px;
  background: #eef2ff;
  color: var(--primary);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.outline-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.outline-meta {
  font-size: 12px;
  color: var(--muted);
  margin-top: 2px;
}

.slide-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.slide-item {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}
.slide-item:hover {
  background: var(--border-light);
}

.slide-page {
  width: 24px;
  height: 24px;
  background: var(--border-light);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  flex-shrink: 0;
  margin-top: 1px;
}

.slide-content {
  flex: 1;
  min-width: 0;
}

.slide-top {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: 2px;
}

.slide-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
}

.key-points {
  margin-top: var(--space-xs);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.key-point {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.emphasis-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 5px;
}
.dot-high { background: var(--warning); }
.dot-medium { background: var(--primary-light); }
.dot-low { background: var(--border); }

.kp-text {
  color: var(--text-secondary);
}

.sub-points {
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding-left: var(--space-sm);
  margin-top: 1px;
}
.sub-point {
  font-size: 11px;
  color: var(--muted);
  padding-left: var(--space-sm);
  border-left: 2px solid var(--border);
}
</style>
