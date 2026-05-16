<template>
  <div class="outline-preview" v-if="outline">
    <!-- Header -->
    <div class="op-header">
      <div class="op-icon-wrap">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <rect x="2" y="2" width="14" height="14" rx="2" stroke="currentColor" stroke-width="1.3"/>
          <path d="M2 7h14M7 2v14" stroke="currentColor" stroke-width="1.2"/>
        </svg>
      </div>
      <div class="op-header-text">
        <div class="op-title">{{ outline.title }}</div>
        <div class="op-meta">
          {{ outline.slides?.length ?? 0 }} 页
          <template v-if="outline.audience"> · {{ outline.audience }}</template>
          <template v-if="outline.objective"> · {{ objectiveLabel(outline.objective) }}</template>
        </div>
      </div>
      <button v-if="hasNarrative" class="op-narrative-btn" @click="showNarrative = !showNarrative">
        {{ frameworkLabel(outline.narrative.framework) }}
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none"
          :style="{ transform: showNarrative ? 'rotate(180deg)' : '' }">
          <path d="M2 3.5l3 3 3-3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>

    <!-- Narrative (collapsible) -->
    <Transition name="slide">
      <div v-if="showNarrative && hasNarrative" class="op-narrative">
        <div v-if="outline.narrative.situation" class="nar-row">
          <span class="nar-tag nar-s">S</span>
          <span class="nar-text">{{ outline.narrative.situation }}</span>
        </div>
        <div v-if="outline.narrative.complication" class="nar-row">
          <span class="nar-tag nar-c">C</span>
          <span class="nar-text">{{ outline.narrative.complication }}</span>
        </div>
        <div v-if="outline.narrative.core_question" class="nar-row">
          <span class="nar-tag nar-q">Q</span>
          <span class="nar-text">{{ outline.narrative.core_question }}</span>
        </div>
        <div v-if="outline.narrative.core_answer" class="nar-row">
          <span class="nar-tag nar-a">A</span>
          <span class="nar-text">{{ outline.narrative.core_answer }}</span>
        </div>
      </div>
    </Transition>

    <!-- Slide flow -->
    <div class="op-grid">
      <div
        v-for="slide in outline.slides"
        :key="slide.page"
        class="op-slide"
        :class="[`slide--${slide.layout}`, { 'slide--selected': selectedPage === slide.page }]"
        @click="selectSlide(slide.page)"
      >
        <div class="slide-accent" :class="`accent--${slide.section || 'none'}`"></div>
        <div class="slide-inner">
          <div class="slide-top-row">
            <span class="slide-type" :class="`type--${slide.layout}`">{{ layoutLabel(slide.layout) }}</span>
            <span class="slide-page">{{ String(slide.page).padStart(2, '0') }}</span>
          </div>
          <div class="slide-headline">{{ slide.headline }}</div>
        </div>
      </div>
    </div>

    <!-- Detail drawer -->
    <Transition name="drawer">
      <div v-if="selectedSlide" class="op-detail">
        <div class="detail-bar" :class="`accent--${selectedSlide.section || 'none'}`"></div>
        <div class="detail-content">
          <div class="detail-top">
            <span class="detail-page-label">第 {{ selectedSlide.page }} 页</span>
            <div class="detail-chips">
              <span class="dchip dchip-layout" :class="`type--${selectedSlide.layout}`">{{ layoutLabel(selectedSlide.layout) }}</span>
              <span v-if="selectedSlide.section" class="dchip" :class="`dchip-${selectedSlide.section}`">{{ sectionLabel(selectedSlide.section) }}</span>
              <span v-if="selectedSlide.visual_hint" class="dchip dchip-visual">{{ visualLabel(selectedSlide.visual_hint) }}</span>
            </div>
            <button class="detail-close" @click="selectedPage = null">
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
          <div v-if="selectedSlide.body_text" class="detail-body">{{ selectedSlide.body_text }}</div>
          <div v-if="selectedSlide.supporting_points?.length" class="detail-points">
            <div v-for="(sp, i) in selectedSlide.supporting_points" :key="i" class="sp-item">
              <div class="sp-marker"></div>
              <div class="sp-body">
                <div class="sp-msg">{{ sp.message }}</div>
                <div v-if="sp.evidence?.length" class="sp-evidence">
                  <div v-for="(ev, j) in sp.evidence" :key="j" class="ev-row">
                    <span class="ev-tag" :class="`ev-${ev.evidence_type}`">{{ evidenceIcon(ev.evidence_type) }}</span>
                    <span class="ev-text">{{ ev.claim }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
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
  border-radius: var(--radius-lg);
  max-width: 720px;
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.04),
    0 4px 16px rgba(79, 70, 229, 0.04);
  overflow: hidden;
  transition: box-shadow var(--transition-base);
}
.outline-preview:hover {
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.04),
    0 6px 20px rgba(79, 70, 229, 0.07);
}

/* ── Header ── */
.op-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-lg);
  border-bottom: 1px solid var(--border-light);
}

.op-icon-wrap {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  color: var(--primary);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.op-header-text {
  flex: 1;
  min-width: 0;
}

.op-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.op-meta {
  font-size: 12px;
  color: var(--muted);
  margin-top: 2px;
}

.op-narrative-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--card);
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
  flex-shrink: 0;
}
.op-narrative-btn:hover {
  background: var(--border-light);
  color: var(--text);
}
.op-narrative-btn svg {
  transition: transform 150ms ease;
}

/* ── Narrative ── */
.op-narrative {
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--border-light);
  background: linear-gradient(180deg, #fafafe 0%, #f8f9fb 100%);
}

.nar-row {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  font-size: 12px;
  line-height: 1.55;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.nar-row:last-child { margin-bottom: 0; }

.nar-tag {
  width: 20px;
  height: 20px;
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
  margin-top: 1px;
}
.nar-s { background: #dbeafe; color: #2563eb; }
.nar-c { background: #fef3c7; color: #92400e; }
.nar-q { background: #ede9fe; color: #6d28d9; }
.nar-a { background: #dcfce7; color: #166534; }

.nar-text {
  flex: 1;
  min-width: 0;
}

/* ── Slide grid ── */
.op-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 8px;
  padding: var(--space-lg);
}

.op-slide {
  display: flex;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  overflow: hidden;
  min-height: 68px;
  position: relative;
}
.op-slide:hover {
  border-color: var(--primary-light);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.1);
}
.op-slide.slide--selected {
  border-color: var(--primary);
  box-shadow: 0 0 0 1px var(--primary), 0 2px 8px rgba(79, 70, 229, 0.12);
}

/* Layout-specific card styles */
.op-slide.slide--cover {
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  border-color: transparent;
}
.op-slide.slide--cover .slide-headline,
.op-slide.slide--cover .slide-page { color: #fff; }
.op-slide.slide--cover .slide-type { background: rgba(255,255,255,.2); color: #fff; }
.op-slide.slide--cover .slide-accent { background: rgba(255,255,255,.35); }

.op-slide.slide--ending {
  background: linear-gradient(135deg, #10b981, #059669);
  border-color: transparent;
}
.op-slide.slide--ending .slide-headline,
.op-slide.slide--ending .slide-page { color: #fff; }
.op-slide.slide--ending .slide-type { background: rgba(255,255,255,.2); color: #fff; }
.op-slide.slide--ending .slide-accent { background: rgba(255,255,255,.35); }

.op-slide.slide--section {
  background: #fffbeb;
  border-color: #fde68a;
}

.op-slide.slide--toc {
  background: #eff6ff;
  border-color: #bfdbfe;
}

/* Accent bar */
.slide-accent {
  width: 3px;
  flex-shrink: 0;
  background: transparent;
  border-radius: 0 1px 1px 0;
}
.accent--situation { background: #3b82f6; }
.accent--complication { background: #f59e0b; }
.accent--answer { background: #10b981; }
.accent--core_question { background: #8b5cf6; }

/* Card inner */
.slide-inner {
  flex: 1;
  padding: 8px 10px;
  min-width: 0;
}

.slide-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 5px;
}

.slide-type {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 3px;
  background: var(--border-light);
  color: var(--text-secondary);
  letter-spacing: 0.02em;
}
.type--cover { background: #ede9fe; color: #6d28d9; }
.type--toc { background: #dbeafe; color: #2563eb; }
.type--section { background: #fef3c7; color: #92400e; }
.type--ending { background: #dcfce7; color: #166534; }

.slide-page {
  font-size: 11px;
  color: var(--muted);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.slide-headline {
  font-size: 12px;
  font-weight: 500;
  color: var(--text);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── Detail drawer ── */
.op-detail {
  display: flex;
  border-top: 1px solid var(--border-light);
  background: linear-gradient(180deg, #fafbfc 0%, #f8f9fb 100%);
}

.detail-bar {
  width: 3px;
  flex-shrink: 0;
}

.detail-content {
  flex: 1;
  padding: var(--space-md) var(--space-lg);
  min-width: 0;
}

.detail-top {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.detail-page-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

.detail-chips {
  display: flex;
  gap: 4px;
  flex: 1;
}

.dchip {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 3px;
  background: var(--border-light);
  color: var(--text-secondary);
}
.dchip-layout {
  /* inherits from .slide-type colors */
}
.dchip-situation { background: #dbeafe; color: #2563eb; }
.dchip-complication { background: #fef3c7; color: #92400e; }
.dchip-answer { background: #dcfce7; color: #166534; }
.dchip-core_question { background: #ede9fe; color: #6d28d9; }
.dchip-visual { background: #ede9fe; color: #6d28d9; }

.detail-close {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: var(--border-light);
  color: var(--muted);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}
.detail-close:hover {
  background: var(--border);
  color: var(--text);
}

.detail-body {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.55;
  margin-bottom: var(--space-sm);
}

/* Supporting points */
.detail-points {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.sp-item {
  display: flex;
  gap: var(--space-sm);
  font-size: 12px;
  line-height: 1.5;
}

.sp-marker {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--primary-light);
  margin-top: 7px;
  flex-shrink: 0;
}

.sp-body {
  flex: 1;
  min-width: 0;
}

.sp-msg {
  color: var(--text);
  font-weight: 500;
}

.sp-evidence {
  margin-top: 3px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ev-row {
  display: flex;
  align-items: flex-start;
  gap: 5px;
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.ev-tag {
  font-size: 9px;
  font-weight: 600;
  padding: 1px 4px;
  border-radius: 2px;
  flex-shrink: 0;
  margin-top: 1px;
}
.ev-data { background: #dbeafe; color: #2563eb; }
.ev-case_study { background: #fef3c7; color: #92400e; }
.ev-quote { background: #ede9fe; color: #6d28d9; }
.ev-analysis { background: #e0e7ff; color: #4338ca; }
.ev-analogy { background: #fce7f3; color: #9d174d; }

.ev-text {
  flex: 1;
  min-width: 0;
}

/* ── Transitions ── */
.slide-enter-active,
.slide-leave-active {
  transition: all 200ms ease;
  overflow: hidden;
}
.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.drawer-enter-active,
.drawer-leave-active {
  transition: all 200ms ease;
}
.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
