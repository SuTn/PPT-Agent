import { defineStore } from "pinia";
import { ref } from "vue";
import type { Message, SSEEvent } from "../api/types";
import client from "../api/client";

const storeMap = new Map<string, ReturnType<typeof createSessionStore>>();

const TOOL_TO_STEP: Record<string, string> = {
  generate_outline: "outline_done",
  select_template: "template_done",
  generate_slides: "slides_done",
  export_pptx: "exported",
};

function createSessionStore(sessionId: string) {
  return defineStore(`session-${sessionId}`, () => {
    const messages = ref<Message[]>([]);
    const isStreaming = ref(false);
    const error = ref<string | null>(null);
    const loaded = ref(false);
    const pipelineStep = ref("idle");
    const outline = ref<any>(null);

    async function loadHistory() {
      if (loaded.value) return;
      try {
        const { data } = await client.get(`/sessions/${sessionId}`);
        if (data.step) pipelineStep.value = data.step;
        if (data.messages && Array.isArray(data.messages)) {
          messages.value = data.messages
            .filter((m: any) => m.content || m.tool_calls)
            .map((m: any) => {
              const msg: Message = { role: m.type === "ai" ? "assistant" : m.type === "tool" ? "system" : m.type, content: m.content || "" };
              if (m.tool_calls) msg.toolCalls = m.tool_calls;
              if (m.type === "tool") msg.toolResult = true;
              return msg;
            });
          // Restore outline from history
          for (const msg of messages.value) {
            if (msg.toolResult && msg.content.startsWith("[generate_outline]")) {
              const jsonStr = msg.content.replace(/^\[generate_outline\]\s*/, "");
              try { outline.value = JSON.parse(jsonStr); } catch { /* ignore */ }
              break;
            }
          }
        }
      } catch {
        // session not found or no history yet
      } finally {
        loaded.value = true;
      }
    }

    async function sendMessage(content: string) {
      messages.value.push({ role: "user", content });
      isStreaming.value = true;
      error.value = null;

      let assistantMsg: Message | null = null;

      try {
        const res = await fetch(
          `/api/v1/sessions/${sessionId}/stream?message=${encodeURIComponent(content)}`
        );

        if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let lastChunk = "";

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
              const event: SSEEvent = JSON.parse(payload);

              if (event.type === "content" && event.content) {
                if (!assistantMsg) {
                  assistantMsg = { role: "assistant", content: event.content };
                  messages.value.push(assistantMsg);
                } else {
                  assistantMsg.content += event.content;
                }
              } else if (event.type === "tool_call") {
                assistantMsg = null;
                const toolName = event.name!;
                messages.value.push({
                  role: "assistant",
                  content: "",
                  toolCalls: [{ name: toolName, args: event.args ?? {} }],
                });
                // Update pipeline step based on tool being called
                if (TOOL_TO_STEP[toolName]) {
                  pipelineStep.value = TOOL_TO_STEP[toolName];
                }
              } else if (event.type === "tool_result") {
                const toolName = event.name!;
                const toolContent = event.content ?? "";
                messages.value.push({
                  role: "system",
                  content: `[${toolName}] ${toolContent}`,
                  toolResult: true,
                });
                // Parse outline from generate_outline tool result
                if (toolName === "generate_outline" && toolContent.trim().startsWith("{")) {
                  try {
                    outline.value = JSON.parse(toolContent);
                  } catch {
                    // not valid JSON
                  }
                }
              } else if (event.type === "error") {
                error.value = event.message ?? "Unknown error";
              }
            } catch {
              // skip malformed JSON
            }
          }

          // Flush remaining buffer after stream ends
          if (lastChunk) {
            const trimmed = lastChunk.trim();
            if (trimmed.startsWith("data: ")) {
              const payload = trimmed.slice(6);
              if (payload !== "[DONE]") {
                try {
                  const event: SSEEvent = JSON.parse(payload);
                  if (event.type === "content" && event.content) {
                    if (!assistantMsg) {
                      assistantMsg = { role: "assistant", content: event.content };
                      messages.value.push(assistantMsg);
                    } else {
                      assistantMsg.content += event.content;
                    }
                  }
                } catch { /* ignore */ }
              }
            }
          }
        }
      } catch (e) {
        error.value = e instanceof Error ? e.message : "Request failed";
      } finally {
        isStreaming.value = false;
      }
    }

    function addSystemNotice(text: string) {
      messages.value.push({ role: "system", content: text });
    }

    return { messages, isStreaming, error, pipelineStep, outline, sendMessage, addSystemNotice, loadHistory };
  })();
}

export function useSessionStore(sessionId: string) {
  if (!storeMap.has(sessionId)) {
    storeMap.set(sessionId, createSessionStore(sessionId));
  }
  return storeMap.get(sessionId)!;
}
