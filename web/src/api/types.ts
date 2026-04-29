export interface Session {
  session_id: string;
  title: string;
  step: "idle" | "research_done" | "outline_done" | "template_done" | "slides_done" | "exported";
  template_key: string;
  created_at: string;
}

export interface Template {
  key: string;
  name: string;
  description: string;
}

export interface SSEEvent {
  type: "content" | "tool_call" | "tool_result" | "error" | "done" | "slide_generated" | "slide_error";
  content?: string;
  name?: string;
  args?: Record<string, unknown>;
  message?: string;
  page?: number;
  layout?: string;
  filename?: string;
  total?: number;
}

export interface SlideInfo {
  page: number;
  layout: string;
  filename?: string;
  has_png?: boolean;
}

export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  toolCalls?: ToolCall[];
  toolResult?: boolean;
}

export interface ToolCall {
  name: string;
  args: Record<string, unknown>;
}
