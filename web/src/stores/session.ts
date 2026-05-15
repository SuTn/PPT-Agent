import { defineStore } from "pinia";
import { ref } from "vue";
import type { Message, SSEEvent, SlideInfo } from "../api/types";
import client from "../api/client";

const storeMap = new Map<string, ReturnType<typeof createSessionStore>>();

const TOOL_TO_STEP: Record<string, string> = {
  research_topic: "research_done",
  generate_outline: "outline_done",
  select_template: "template_done",
  generate_slides: "slides_done",
  export_pptx: "exported",
};

const TOOL_NOTIFICATIONS: Record<string, string> = {
  research_topic: "研究完成，请查看研究笔记",
  generate_outline: "大纲已生成，请确认",
  generate_slides: "幻灯片已生成",
  export_pptx: "PPTX 导出完成，可下载",
};

function createSessionStore(sessionId: string) {
  return defineStore(`session-${sessionId}`, () => {
    const messages = ref<Message[]>([]);
    const isStreaming = ref(false);
    const error = ref<string | null>(null);
    const loaded = ref(false);
    const pipelineStep = ref("idle");
    const outline = ref<any>(null);
    const researchNotes = ref<string>("");
    const slides = ref<SlideInfo[]>([]);
    const mode = ref<"fast" | "standard">("fast");

    async function loadHistory() {
      if (loaded.value) return;
      try {
        const { data } = await client.get(`/sessions/${sessionId}`);
        if (data.step) pipelineStep.value = data.step;
        if (data.mode) mode.value = data.mode;
        if (data.messages && Array.isArray(data.messages)) {
          messages.value = data.messages
            .filter((m: any) => m.content || m.tool_calls)
            .map((m: any) => {
              const msg: Message = { role: m.type === "ai" ? "assistant" : m.type === "human" ? "user" : m.type === "tool" ? "system" : m.type, content: m.content || "" };
              if (m.tool_calls) msg.toolCalls = m.tool_calls;
              if (m.type === "tool") {
                msg.toolResult = true;
                msg.content = `[${m.name}] ${m.content}`;
              }
              return msg;
            });
          // Restore outline from API
          const outlineSteps = ["outline_done", "generating_slides", "slides_done", "exported"];
          if (outlineSteps.includes(pipelineStep.value)) {
            try {
              const { data: od } = await client.get(`/sessions/${sessionId}/outline`);
              if (od) outline.value = od;
            } catch { /* no outline */ }
          }
          // Restore research notes from API
          const researchSteps = ["research_done", "outline_done", "generating_slides", "slides_done", "exported"];
          if (researchSteps.includes(pipelineStep.value)) {
            try {
              const { data: rd } = await client.get(`/sessions/${sessionId}/research`);
              if (rd?.content) researchNotes.value = rd.content;
            } catch { /* no research notes */ }
          }
          // Restore slides from API if any exist on disk
          const slideSteps = ["generating_slides", "slides_done", "exported"];
          if (slideSteps.includes(pipelineStep.value)) {
            try {
              const { data: sd } = await client.get(`/sessions/${sessionId}/slides`);
              if (sd?.slides) slides.value = sd.slides;
            } catch { /* no slides */ }
          }
        }
        // If agent task is still running, reconnect to its event stream
        if (pipelineStep.value === "generating_slides") {
          reconnectStream();
        }
      } catch {
        // session not found or no history yet
      } finally {
        loaded.value = true;
      }
    }

    /** Process a single SSE event, updating store state. */
    function handleEvent(event: SSEEvent, assistantMsg: { value: Message | null }) {
      if (event.type === "content" && event.content) {
        if (!assistantMsg.value) {
          assistantMsg.value = { role: "assistant", content: event.content };
          messages.value.push(assistantMsg.value);
        } else {
          assistantMsg.value.content += event.content;
        }
      } else if (event.type === "tool_call") {
        assistantMsg.value = null;
        const toolName = event.name!;
        messages.value.push({
          role: "assistant",
          content: "",
          toolCalls: [{ name: toolName, args: event.args ?? {} }],
        });
      } else if (event.type === "tool_result") {
        const toolName = event.name!;
        const toolContent = event.content ?? "";
        messages.value.push({
          role: "system",
          content: `[${toolName}] ${toolContent}`,
          toolResult: true,
        });
        if (TOOL_TO_STEP[toolName]) {
          pipelineStep.value = TOOL_TO_STEP[toolName];
        }
        if (toolName === "generate_outline" && toolContent.trim().startsWith("{")) {
          try {
            outline.value = JSON.parse(toolContent);
          } catch {
            client.get(`/sessions/${sessionId}/outline`).then(({ data }) => {
              if (data) outline.value = data;
            }).catch(() => {});
          }
        }
        if (toolName === "research_topic") {
          client.get(`/sessions/${sessionId}/research`).then(({ data }) => {
            if (data?.content) researchNotes.value = data.content;
          }).catch(() => {});
        }
        notifyUser(toolName);
      } else if (event.type === "error") {
        error.value = event.message ?? "Unknown error";
      } else if (event.type === "slide_generated") {
        if (pipelineStep.value !== "slides_done" && pipelineStep.value !== "generating_slides") {
          pipelineStep.value = "generating_slides";
        }
        const slide: SlideInfo = {
          page: event.page!,
          layout: event.layout!,
          filename: event.filename,
        };
        const idx = slides.value.findIndex(s => s.page === slide.page);
        if (idx >= 0) {
          slides.value[idx] = slide;
        } else {
          slides.value.push(slide);
          slides.value.sort((a, b) => a.page - b.page);
        }
      } else if (event.type === "slide_error") {
        console.warn(`Slide ${event.page} error: ${event.message}`);
      }
    }

    /** Read an SSE stream from a fetch Response and process all events. */
    async function processSSEStream(res: Response) {
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let lastChunk = "";
      const assistantMsg = { value: null as Message | null };

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          lastChunk = buffer;
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data: ")) continue;
          const payload = trimmed.slice(6);
          if (payload === "[DONE]") continue;
          try {
            handleEvent(JSON.parse(payload), assistantMsg);
          } catch { /* malformed JSON */ }
        }
      }

      // Flush remaining buffer
      if (lastChunk) {
        const trimmed = lastChunk.trim();
        if (trimmed.startsWith("data: ")) {
          const payload = trimmed.slice(6);
          if (payload !== "[DONE]") {
            try {
              const event: SSEEvent = JSON.parse(payload);
              if (event.type === "content" && event.content) {
                if (!assistantMsg.value) {
                  assistantMsg.value = { role: "assistant", content: event.content };
                  messages.value.push(assistantMsg.value);
                } else {
                  assistantMsg.value.content += event.content;
                }
              }
            } catch { /* ignore */ }
          }
        }
      }
    }

    /** Reconnect to a running agent task's SSE stream (after page refresh). */
    async function reconnectStream() {
      isStreaming.value = true;
      error.value = null;
      try {
        const res = await fetch(`/api/v1/sessions/${sessionId}/events`);
        if (!res.ok || !res.body) return;
        await processSSEStream(res);
      } catch {
        // Connection failed — task may have finished between loadHistory and reconnect
      } finally {
        isStreaming.value = false;
        // Refresh state after reconnect ends
        try {
          const { data } = await client.get(`/sessions/${sessionId}`);
          if (data.step) pipelineStep.value = data.step;
        } catch {}
      }
    }

    async function sendMessage(content: string) {
      messages.value.push({ role: "user", content });
      isStreaming.value = true;
      error.value = null;

      try {
        const res = await fetch(
          `/api/v1/sessions/${sessionId}/stream?message=${encodeURIComponent(content)}&mode=${mode.value}`
        );

        if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
        await processSSEStream(res);
      } catch (e) {
        error.value = e instanceof Error ? e.message : "Request failed";
      } finally {
        isStreaming.value = false;
      }
    }

    function addSystemNotice(text: string) {
      messages.value.push({ role: "system", content: text });
    }

    // --- Browser tab notification ---
    let titleInterval: ReturnType<typeof setInterval> | null = null;
    const originalTitle = document.title;

    function notifyUser(toolName: string) {
      const message = TOOL_NOTIFICATIONS[toolName];
      if (!message) return;

      if ("Notification" in window) {
        if (Notification.permission === "granted") {
          new Notification("PPT-Agent", { body: message });
        } else if (Notification.permission !== "denied") {
          Notification.requestPermission().then((perm) => {
            if (perm === "granted") new Notification("PPT-Agent", { body: message });
          });
        }
      }

      if (titleInterval) clearInterval(titleInterval);
      let toggle = false;
      titleInterval = setInterval(() => {
        document.title = toggle ? `🔔 ${message}` : originalTitle;
        toggle = !toggle;
      }, 1000);
      setTimeout(() => stopTitleFlash(), 10000);
    }

    function stopTitleFlash() {
      if (titleInterval) {
        clearInterval(titleInterval);
        titleInterval = null;
        document.title = originalTitle;
      }
    }

    window.addEventListener("focus", stopTitleFlash);

    async function refreshSlides() {
      try {
        const { data: sd } = await client.get(`/sessions/${sessionId}/slides`);
        if (sd?.slides) slides.value = sd.slides;
      } catch { /* ignore */ }
    }

    return { messages, isStreaming, error, pipelineStep, outline, researchNotes, slides, mode, sendMessage, addSystemNotice, loadHistory, refreshSlides };
  })();
}

export function useSessionStore(sessionId: string) {
  if (!storeMap.has(sessionId)) {
    storeMap.set(sessionId, createSessionStore(sessionId));
  }
  return storeMap.get(sessionId)!;
}
