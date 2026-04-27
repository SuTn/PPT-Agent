import { defineStore } from "pinia";
import { ref, computed } from "vue";
import client from "../api/client";
import type { Session } from "../api/types";

export const useSessionsStore = defineStore("sessions", () => {
  const sessions = ref<Session[]>([]);
  const currentId = ref<string | null>(null);

  const current = computed(() =>
    sessions.value.find((s) => s.session_id === currentId.value) ?? null
  );

  async function fetchSessions() {
    const { data } = await client.get("/sessions");
    sessions.value = data.sessions;
  }

  async function createSession(title = "") {
    const { data } = await client.post("/sessions", null, { params: { title } });
    await fetchSessions();
    currentId.value = data.session_id;
    return data.session_id;
  }

  async function deleteSession(id: string) {
    await client.delete(`/sessions/${id}`);
    await fetchSessions();
    if (currentId.value === id) {
      currentId.value = sessions.value.length > 0 ? sessions.value[0].session_id : null;
    }
  }

  async function refreshCurrent() {
    if (currentId.value) {
      const { data } = await client.get(`/sessions/${currentId.value}`);
      const idx = sessions.value.findIndex((s) => s.session_id === currentId.value);
      if (idx !== -1) sessions.value[idx] = data;
    }
  }

  return { sessions, currentId, current, fetchSessions, createSession, deleteSession, refreshCurrent };
});
