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
        <div class="outline-meta">
          {{ outline.slides?.length ?? 0 }} 页
          <span v-if="outline.audience"> · {{ outline.audience }}</span>
          <span v-if="outline.objective"> · {{ objectiveLabel(outline.objective) }}</span>
        </div>
      </div>
    </div>
    <!-- Narrative summary -->
    <div v-if="outline.narrative && (outline.narrative.situation || outline.narrative.complication)" class="narrative-card">
      <div class="narrative-label">{{ frameworkLabel(outline.narrative.framework) }}</div>
      <div v-if="outline.narrative.situation" class="narrative-item"><span class="narrative-tag">S</span> {{ outline.narrative.situation }}</div>
      <div v-if="outline.narrative.complication" class="narrative-item"><span class="narrative-tag">C</span> {{ outline.narrative.complication }}</div>
      <div v-if="outline.narrative.core_question" class="narrative-item"><span class="narrative-tag">Q</span> {{ outline.narrative.core_question }}</div>
      <div v-if="outline.narrative.core_answer" class="narrative-item"><span class="narrative-tag">A</span> {{ outline.narrative.core_answer }}</div>
    </div>
    <div class="slide-list">
      <div v-for="slide in outline.slides" :key="slide.page" class="slide-item">
        <div class="slide-page">{{ slide.page }}</div>
        <div class="slide-content">
          <div class="slide-top">
            <span class="badge" :class="layoutBadge(slide.layout)">{{ layoutLabel(slide.layout) }}</span>
            <span v-if="slide.visual_hint" class="badge badge--visual">{{ visualLabel(slide.visual_hint) }}</span>
            <span v-if="slide.section" class="badge badge--outline">{{ slide.section }}</span>
            <span class="slide-headline">{{ slide.headline }}</span>
          </div>
          <div v-if="slide.body_text" class="body-text">{{ slide.body_text }}</div>
          <div v-if="slide.supporting_points?.length" class="supporting-points">
            <div v-for="(sp, si) in slide.supporting_points" :key="si" class="sp-item">
              <div class="sp-message">{{ sp.message }}</div>
              <div v-if="sp.evidence?.length" class="evidence-list">
                <div v-for="(ev, ei) in sp.evidence" :key="ei" class="evidence-item">
                  <span class="evidence-badge" :class="`ev-${ev.evidence_type}`">{{ ev.evidence_type }}</span>
                  <span class="evidence-claim">{{ ev.claim }}</span>
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
  cover: "封面", toc: "目录", content: "内容", section: "章节", ending: "结尾",
};

const LAYOUT_BADGES: Record<string, string> = {
  cover: "badge--primary", toc: "badge--info", section: "badge--warning", ending: "badge--success", content: "",
};

const OBJECTIVE_LABELS: Record<string, string> = {
  persuade: "说服", report: "汇报", educate: "培训", inspire: "激励",
};

const FRAMEWORK_LABELS: Record<string, string> = {
  scqa: "SCQA 框架", problem_solution: "问题-方案", chronological: "时间线", custom: "自定义",
};

const VISUAL_LABELS: Record<string, string> = {
  table: "表格", comparison: "对比", timeline: "时间线", process: "流程", chart: "图表", quote_highlight: "金句",
};

function layoutLabel(l: string): string { return LAYOUT_LABELS[l] ?? l; }
function layoutBadge(l: string): string { return LAYOUT_BADGES[l] ?? ""; }
function objectiveLabel(o: string): string { return OBJECTIVE_LABELS[o] ?? o; }
function frameworkLabel(f: string): string { return FRAMEWORK_LABELS[f] ?? f; }
function visualLabel(v: string): string { return VISUAL_LABELS[v] ?? v; }
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
  margin-bottom: var(--space-md);
  padding-bottom: var(--space-md);
  border-bottom: 1px solid var(--border-light);
}

.outline-icon {
  width: 32px; height: 32px;
  background: #eef2ff; color: var(--primary);
  border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
}

.outline-title { font-size: 15px; font-weight: 600; color: var(--text); }
.outline-meta { font-size: 12px; color: var(--muted); margin-top: 2px; }

.narrative-card {
  background: var(--bg-secondary, #f8f9fa);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  padding: var(--space-sm) var(--space-md);
  margin-bottom: var(--space-md);
}

.narrative-label {
  font-size: 11px; font-weight: 600; color: var(--primary);
  text-transform: uppercase; margin-bottom: var(--space-xs);
}

.narrative-item {
  display: flex; align-items: flex-start; gap: var(--space-sm);
  font-size: 12px; color: var(--text-secondary); line-height: 1.5;
  margin-bottom: 2px;
}

.narrative-tag {
  width: 16px; height: 16px; border-radius: 50%;
  background: var(--primary-light, #eef2ff); color: var(--primary);
  font-size: 10px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; margin-top: 1px;
}

.slide-list {
  display: flex; flex-direction: column; gap: var(--space-sm);
}

.slide-item {
  display: flex; gap: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}
.slide-item:hover { background: var(--border-light); }

.slide-page {
  width: 24px; height: 24px;
  background: var(--border-light); border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 600; color: var(--text-secondary);
  flex-shrink: 0; margin-top: 1px;
}

.slide-content { flex: 1; min-width: 0; }

.slide-top {
  display: flex; align-items: center; gap: var(--space-sm);
  flex-wrap: wrap; margin-bottom: 2px;
}

.slide-headline { font-size: 13px; font-weight: 500; color: var(--text); }

.body-text { font-size: 12px; color: var(--text-secondary); margin-top: 2px; line-height: 1.4; }

.supporting-points {
  margin-top: var(--space-xs);
  display: flex; flex-direction: column; gap: 3px;
}

.sp-item {
  font-size: 12px; color: var(--text-secondary); line-height: 1.4;
}

.sp-message { color: var(--text-secondary); }

.evidence-list {
  display: flex; flex-direction: column; gap: 1px;
  padding-left: var(--space-sm); margin-top: 1px;
}

.evidence-item {
  display: flex; align-items: flex-start; gap: 4px;
  font-size: 11px; color: var(--muted); line-height: 1.4;
}

.evidence-badge {
  font-size: 9px; font-weight: 600; padding: 0 3px;
  border-radius: 2px; flex-shrink: 0; margin-top: 1px;
  text-transform: uppercase;
}
.ev-data { background: #dbeafe; color: #2563eb; }
.ev-case_study { background: #fef3c7; color: #92400e; }
.ev-quote { background: #ede9fe; color: #6d28d9; }
.ev-analysis { background: #e0e7ff; color: #4338ca; }
.ev-analogy { background: #fce7f3; color: #9d174d; }

.evidence-claim { color: var(--muted); }

.badge {
  font-size: 10px; font-weight: 600; padding: 1px 6px;
  border-radius: 3px; white-space: nowrap;
  background: var(--bg-secondary, #f1f5f9); color: var(--text-secondary);
}
.badge--primary { background: #dbeafe; color: #2563eb; }
.badge--info { background: #e0f2fe; color: #0284c7; }
.badge--warning { background: #fef3c7; color: #92400e; }
.badge--success { background: #dcfce7; color: #166534; }
.badge--outline { background: transparent; border: 1px solid var(--border); }
.badge--visual { background: #ede9fe; color: #6d28d9; }
</style>
