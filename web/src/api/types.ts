export interface Session {
  session_id: string;
  title: string;
  step: "idle" | "outline_done" | "template_done" | "slides_done" | "exported";
  template_key: string;
  created_at: string;
}

export interface Template {
  key: string;
  name: string;
  description: string;
}

export interface SSEEvent {
  type: "content" | "tool_call" | "tool_result" | "error" | "done";
  content?: string;
  name?: string;
  args?: Record<string, unknown>;
  message?: string;
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
