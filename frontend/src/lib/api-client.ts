import { API_ENDPOINTS } from "./constants";

export const apiClient = {
  async fetchConfig() {
    const token = localStorage.getItem("auth_token");
    return {
      headers: {
        "Content-Type": "application/json",
        ...(token ? { "Authorization": `Bearer ${token}` } : {})
      }
    };
  },

  async chat(agentId: string, query: string, sessionId?: string) {
    const config = await this.fetchConfig();
    const response = await fetch(`${API_ENDPOINTS.CHAT.BASE}?agent_id=${agentId}`, {
      method: "POST",
      ...config,
      body: JSON.stringify({ query, session_id: sessionId })
    });
    if (!response.ok) throw new Error("Chat failed");
    return response.json();
  },

  async getChatSessions() {
    const config = await this.fetchConfig();
    const response = await fetch(API_ENDPOINTS.CHAT.SESSIONS, { ...config });
    if (!response.ok) throw new Error("Failed to fetch sessions");
    return response.json();
  },

  async createChatSession(title: string) {
    const config = await this.fetchConfig();
    const response = await fetch(`${API_ENDPOINTS.CHAT.SESSIONS}?title=${encodeURIComponent(title)}`, {
      method: "POST",
      ...config,
    });
    if (!response.ok) throw new Error("Failed to create session");
    return response.json();
  },

  async getSessionMessages(sessionId: string) {
    const config = await this.fetchConfig();
    const response = await fetch(`${API_ENDPOINTS.CHAT.SESSIONS}/${sessionId}`, { ...config });
    if (!response.ok) throw new Error("Failed to fetch messages");
    return response.json();
  },

  async updateChatSession(sessionId: string, title: string) {
    const config = await this.fetchConfig();
    const response = await fetch(`${API_ENDPOINTS.CHAT.SESSIONS}/${sessionId}`, {
      method: "PATCH",
      ...config,
      body: JSON.stringify({ title }),
    });
    if (!response.ok) throw new Error("Failed to update session");
    return response.json();
  },

  async deleteChatSession(sessionId: string) {
    const config = await this.fetchConfig();
    const response = await fetch(`${API_ENDPOINTS.CHAT.SESSIONS}/${sessionId}`, {
      method: "DELETE",
      ...config,
    });
    if (!response.ok) throw new Error("Failed to delete session");
    return response.json();
  },

  async getOverallIndexingStatus() {
    const config = await this.fetchConfig();
    const response = await fetch(API_ENDPOINTS.INDEXING.STATUS, { ...config });
    if (!response.ok) throw new Error("Failed to fetch indexing status");
    return response.json();
  },

  async triggerIndexing(source: "who" | "cdc") {
    const config = await this.fetchConfig();
    const endpoint = source === "who" ? API_ENDPOINTS.INDEXING.TRIGGER_WHO : API_ENDPOINTS.INDEXING.TRIGGER_CDC;
    const response = await fetch(endpoint, { method: "POST", ...config });
    if (!response.ok) throw new Error(`Failed to trigger ${source} indexing`);
    return response.json();
  },

  async getCatalog(source?: string, search?: string, status?: string, page = 1, limit = 50) {
    const config = await this.fetchConfig();
    const params = new URLSearchParams({ limit: limit.toString(), offset: ((page - 1) * limit).toString() });
    if (source) params.append("source", source);
    if (search) params.append("q", search);
    if (status) params.append("status", status);
    
    const response = await fetch(`${API_ENDPOINTS.CATALOG.BASE}?${params.toString()}`, { ...config });
    if (!response.ok) throw new Error("Failed to fetch catalog");
    return response.json();
  },
  
  async getLLMSettings() {
    const config = await this.fetchConfig();
    const response = await fetch(API_ENDPOINTS.SETTINGS.LLM, { ...config });
    if (!response.ok) throw new Error("Failed to fetch LLM settings");
    return response.json();
  },

  async getEmbeddingSettings() {
    const config = await this.fetchConfig();
    const response = await fetch(API_ENDPOINTS.SETTINGS.EMBEDDING, { ...config });
    if (!response.ok) throw new Error("Failed to fetch Embedding settings");
    return response.json();
  },

  async getSystemConfig() {
    const config = await this.fetchConfig();
    const response = await fetch(API_ENDPOINTS.SETTINGS.CONFIG, { ...config });
    if (!response.ok) throw new Error("Failed to fetch system config");
    return response.json();
  },

  async login(email: string, password?: string) {
    // Dummy login endpoint wait for 1 second
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return { token: "dummy_token" };
  },

  async signup(name: string, email: string, password?: string) {
    // Dummy signup endpoint wait for 1 second
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return { token: "dummy_token" };
  }
};
