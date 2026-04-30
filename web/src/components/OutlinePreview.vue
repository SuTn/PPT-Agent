<template>
  <div class="outline-preview" v-if="outline">
    <!-- Header -->
    <div class="outline-header">
      <div class="outline-icon">
        <svg width="18" height="18" viewBox="0 0 16 16" fill="none">
          <path d="M2 3h12M2 6h12M2 9h8M2 12h6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </div>
      <div class="header-text">
        <div class="outline-title">{{ outline.title }}</div>
        <div class="outline-meta">
          {{ outline.slides?.length ?? 0 }} 页
          <template v-if="outline.audience"> · {{ outline.audience }}</template>
          <template v-if="outline.objective"> · {{ objectiveLabel(outline.objective) }}</template>
        </div>
      </div>
      <button v-if="hasNarrative" class="narrative-btn" @click="showNarrative = !showNarrative">
        {{ frameworkLabel(outline.narrative.framework) }}
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none"
          :style="{ transform: showNarrative ? 'rotate(180deg)' : '' }"
          style="transition: transform 150ms ease">
          <path d="M3 4.5l3 3 3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>

    <!-- Narrative (collapsible) -->
    <div v-if="showNarrative && hasNarrative" class="narrative-section">
      <div v-if="outline.narrative.situation" class="narrative-row">
        <span class="ntag nt-s">S</span>
        <span>{{ outline.narrative.situation }}</span>
      </div>
      <div v-if="outline.narrative.complication" class="narrative-row">
        <span class="ntag nt-c">C</span>
        <span>{{ outline.narrative.complication }}</span>
      </div>
      <div v-if="outline.narrative.core_question" class="narrative-row">
        <span class="ntag nt-q">Q</span>
        <span>{{ outline.narrative.core_question }}</span>
      </div>
      <div v-if="outline.narrative.core_answer" class="narrative-row">
        <span class="ntag nt-a">A</span>
        <span>{{ outline.narrative.core_answer }}</span>
      </div>
    </div>

    <!-- Card Grid -->
    <div class="slide-grid">
      <div
        v-for="slide in outline.slides"
        :key="slide.page"
        class="slide-card"
        :class="[`card--${slide.layout}`, { 'card--active': selectedPage === slide.page }]"
        @click="selectSlide(slide.page)"
      >
        <div class="card-bar" :class="`bar--${slide.section || 'none'}`"></div>
        <div class="card-content">
          <div class="card-top">
            <span class="layout-chip" :class="`lc--${slide.layout}`">{{ layoutLabel(slide.layout) }}</span>
            <span class="page-num">{{ slide.page }}</span>
          </div>
          <div class="card-headline">{{ slide.headline }}</div>
        </div>
      </div>
    </div>

    <!-- Detail Panel (shown when a card is selected) -->
    <div v-if="selectedSlide" class="detail-panel">
      <div class="detail-accent" :class="`bar--${selectedSlide.section || 'none'}`"></div>
      <div class="detail-inner">
        <div class="detail-head">
          <span class="detail-page">第 {{ selectedSlide.page }} 页</span>
          <span class="layout-chip" :class="`lc--${selectedSlide.layout}`">{{ layoutLabel(selectedSlide.layout) }}</span>
          <span v-if="selectedSlide.section" class="section-chip" :class="`sc--${selectedSlide.section}`">{{ sectionLabel(selectedSlide.section) }}</span>
          <span v-if="selectedSlide.visual_hint" class="visual-chip">{{ visualLabel(selectedSlide.visual_hint) }}</span>
        </div>
        <div v-if="selectedSlide.body_text" class="detail-body">{{ selectedSlide.body_text }}</div>
        <div v-if="selectedSlide.supporting_points?.length" class="points-list">
          <div v-for="(sp, i) in selectedSlide.supporting_points" :key="i" class="pt-item">
            <div class="pt-dot"></div>
            <div>
              <div class="pt-msg">{{ sp.message }}</div>
              <div v-if="sp.evidence?.length" class="ev-list">
                <div v-for="(ev, j) in sp.evidence" :key="j" class="ev-item">
                  <span class="ev-badge" :class="`ev-${ev.evidence_type}`">{{ evidenceIcon(ev.evidence_type) }}</span>
                  <span>{{ ev.claim }}</span>
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
import { ref, computed } from "vue";

const props = defineProps<{ outline: any }>();

const selectedPage = ref<number | null>(null);
const showNarrative = ref(false);

const hasNarrative = computed(() => {
  const n = props.outline?.narrative;
  return n && (n.situation || n.complication || n.core_question || n.core_answer);
});

const selectedSlide = computed(() => {
  if (selectedPage.value === null) return null;
  return props.outline?.slides?.find((s: any) => s.page === selectedPage.value) ?? null;
});

function selectSlide(page: number) {
  selectedPage.value = selectedPage.value === page ? null : page;
}

const LAYOUT_LABELS: Record<string, string> = {
  cover: "封面", toc: "目录", content: "内容", section: "章节", ending: "结尾",
};

const OBJECTIVE_LABELS: Record<string, string> = {
  persuade: "说服", report: "汇报", educate: "培训", inspire: "激励",
};

const FRAMEWORK_LABELS: Record<string, string> = {
  scqa: "SCQA 框架", problem_solution: "问题-方案", chronological: "时间线", custom: "自定义",
};

const SECTION_LABELS: Record<string, string> = {
  situation: "情境", complication: "冲突", core_question: "问题", answer: "答案",
};

const VISUAL_LABELS: Record<string, string> = {
  table: "表格", comparison: "对比", timeline: "时间线", process: "流程",
  chart: "图表", quote_highlight: "金句",
};

function layoutLabel(l: string): string { return LAYOUT_LABELS[l] ?? l; }
function objectiveLabel(o: string): string { return OBJECTIVE_LABELS[o] ?? o; }
function frameworkLabel(f: string): string { return FRAMEWORK_LABELS[f] ?? f; }
function sectionLabel(s: string): string { return SECTION_LABELS[s] ?? s; }
function visualLabel(v: string): string { return VISUAL_LABELS[v] ?? v; }

function evidenceIcon(t: string): string {
  const m: Record<string, string> = {
    data: "数据", case_study: "案例", quote: "引述", analysis: "分析", analogy: "类比",
  };
  return m[t] ?? t;
}
</script>

<style scoped>
.outline-preview {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  max-width: 680px;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

/* ── Header ── */
.outline-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-lg);
  border-bottom: 1px solid var(--border-light);
}

.outline-icon {
  width: 36px;
  height: 36px;
  background: #eef2ff;
  color: var(--primary);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.header-text {
  flex: 1;
  min-width: 0;
}

.outline-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.outline-meta {
  font-size: 12px;
  color: var(--muted);
  margin-top: 2px;
}

.narrative-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--card);
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
  flex-shrink: 0;
}
.narrative-btn:hover {
  background: var(--border-light);
  color: var(--text);
}

/* ── Narrative ── */
.narrative-section {
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--border-light);
  background: #fafbfc;
}

.narrative-row {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 4px;
}
.narrative-row:last-child { margin-bottom: 0; }

.ntag {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
  margin-top: 1px;
}
.nt-s { background: #dbeafe; color: #2563eb; }
.nt-c { background: #fef3c7; color: #92400e; }
.nt-q { background: #ede9fe; color: #6d28d9; }
.nt-a { background: #dcfce7; color: #166534; }

/* ── Card Grid ── */
.slide-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(145px, 1fr));
  gap: 8px;
  padding: var(--space-lg);
}

.slide-card {
  display: flex;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  overflow: hidden;
  min-height: 72px;
}
.slide-card:hover {
  border-color: var(--primary-light);
  box-shadow: var(--shadow-md);
}
.slide-card.card--active {
  border-color: var(--primary);
  box-shadow: 0 0 0 1px var(--primary);
}

/* Cover */
.slide-card.card--cover {
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  border-color: transparent;
}
.slide-card.card--cover .card-headline,
.slide-card.card--cover .page-num { color: #fff; }
.slide-card.card--cover .layout-chip { background: rgba(255,255,255,.2); color: #fff; }
.slide-card.card--cover .card-bar { background: rgba(255,255,255,.3); }

/* Ending */
.slide-card.card--ending {
  background: linear-gradient(135deg, #10b981, #059669);
  border-color: transparent;
}
.slide-card.card--ending .card-headline,
.slide-card.card--ending .page-num { color: #fff; }
.slide-card.card--ending .layout-chip { background: rgba(255,255,255,.2); color: #fff; }
.slide-card.card--ending .card-bar { background: rgba(255,255,255,.3); }

/* Section divider */
.slide-card.card--section {
  background: #fffbeb;
  border-color: #fde68a;
}

/* TOC */
.slide-card.card--toc {
  background: #eff6ff;
  border-color: #bfdbfe;
}

/* Section accent bar */
.card-bar {
  width: 3px;
  flex-shrink: 0;
  background: transparent;
}
.bar--situation { background: #3b82f6; }
.bar--complication { background: #f59e0b; }
.bar--answer { background: #10b981; }
.bar--core_question { background: #8b5cf6; }

/* Card inner */
.card-content {
  flex: 1;
  padding: 8px 10px;
  min-width: 0;
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.layout-chip {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 3px;
  background: var(--border-light);
  color: var(--text-secondary);
}
.lc--cover { background: #ede9fe; color: #6d28d9; }
.lc--toc { background: #dbeafe; color: #2563eb; }
.lc--section { background: #fef3c7; color: #92400e; }
.lc--ending { background: #dcfce7; color: #166534; }

.page-num {
  font-size: 11px;
  color: var(--muted);
  font-weight: 500;
}

.card-headline {
  font-size: 12px;
  font-weight: 500;
  color: var(--text);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── Detail Panel ── */
.detail-panel {
  display: flex;
  border-top: 1px solid var(--border-light);
  background: #fafbfc;
}

.detail-accent {
  width: 3px;
  flex-shrink: 0;
}

.detail-inner {
  flex: 1;
  padding: var(--space-md) var(--space-lg);
  min-width: 0;
}

.detail-head {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.detail-page {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

.section-chip {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 3px;
}
.sc--situation { background: #dbeafe; color: #2563eb; }
.sc--complication { background: #fef3c7; color: #92400e; }
.sc--answer { background: #dcfce7; color: #166534; }
.sc--core_question { background: #ede9fe; color: #6d28d9; }

.visual-chip {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 3px;
  background: #ede9fe;
  color: #6d28d9;
}

.detail-body {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: var(--space-sm);
}

/* Supporting points */
.points-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.pt-item {
  display: flex;
  gap: var(--space-sm);
  font-size: 12px;
  line-height: 1.5;
}

.pt-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--primary-light);
  margin-top: 7px;
  flex-shrink: 0;
}

.pt-msg {
  color: var(--text);
  font-weight: 500;
}

.ev-list {
  margin-top: 2px;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.ev-item {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.ev-badge {
  font-size: 9px;
  font-weight: 600;
  padding: 0 3px;
  border-radius: 2px;
  flex-shrink: 0;
  margin-top: 2px;
}
.ev-data { background: #dbeafe; color: #2563eb; }
.ev-case_study { background: #fef3c7; color: #92400e; }
.ev-quote { background: #ede9fe; color: #6d28d9; }
.ev-analysis { background: #e0e7ff; color: #4338ca; }
.ev-analogy { background: #fce7f3; color: #9d174d; }
</style>
