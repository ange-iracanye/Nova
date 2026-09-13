import Constants from 'expo-constants';

export type User = { email: string };
export type Session = { token: string; email: string; expires_at?: string; expires_in_seconds?: number };
export type Settings = Record<string, unknown>;

const configured = String(Constants.expoConfig?.extra?.apiUrl || '').trim();
const API_URL = (configured || 'http://127.0.0.1:8000').replace(/\/+$/, '');

let sessionToken = '';
export const setApiSession = (token: string | null) => { sessionToken = token?.trim() || ''; };

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers || {});
  headers.set('Accept', 'application/json');
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  if (sessionToken) headers.set('Authorization', `Bearer ${sessionToken}`);
  const response = await fetch(`${API_URL}${path}`, { ...init, headers });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const message = payload?.error?.message || payload?.detail || payload?.message || `Request failed (HTTP ${response.status})`;
    const error = new Error(String(message));
    (error as Error & { status?: number }).status = response.status;
    throw error;
  }
  return payload as T;
}

export const api = {
  url: API_URL,
  async login(email: string, password: string) { return request<{ success: boolean; email?: string; user?: User; session?: Session; message?: string }>('/login', { method: 'POST', body: JSON.stringify({ email, password }) }); },
  async register(email: string, password: string) { return request<{ success: boolean; email?: string; user?: User; session?: Session; message?: string }>('/register', { method: 'POST', body: JSON.stringify({ email, password }) }); },
  async me() { return request<{ success: boolean; authenticated: boolean; user?: User; session?: Session }>('/auth/me'); },
  async logout() { return request<{ success: boolean }>('/auth/logout', { method: 'POST' }); },
  async chat(email: string, message: string, conversationId?: string) { return request<{ success: boolean; answer: string; response: string; conversation_id: string }>('/chat', { method: 'POST', body: JSON.stringify({ email, message, conversation_id: conversationId || null }) }); },
  async conversations(email: string) { return request<{ success: boolean; conversations: unknown }>('/conversations/' + encodeURIComponent(email)); },
  async conversation(email: string, id: string) { return request<{ success: boolean; conversation: any }>(`/conversation/${encodeURIComponent(email)}/${encodeURIComponent(id)}`); },
  async createConversation(email: string) { return request<{ success: boolean; conversation_id: string; id: string }>('/conversation/new', { method: 'POST', body: JSON.stringify({ email }) }); },
  async renameConversation(email: string, id: string, title: string) { return request<{ success: boolean }>(`/conversation/${encodeURIComponent(email)}/${encodeURIComponent(id)}/rename`, { method: 'PUT', body: JSON.stringify({ email, title }) }); },
  async deleteConversation(email: string, id: string) { return request<{ success: boolean }>(`/conversation/${encodeURIComponent(email)}/${encodeURIComponent(id)}`, { method: 'DELETE' }); },
  async dashboard() { return request<any>('/v1/dashboard'); },
  async settings() { return request<{ success: boolean; settings: Settings }>('/settings'); },
  async saveSettings(settings: Settings) { return request<{ success: boolean; settings: Settings }>('/settings', { method: 'POST', body: JSON.stringify(settings) }); },
};
