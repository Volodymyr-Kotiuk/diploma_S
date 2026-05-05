import { API_BASE, api, post } from './client';
import type { Node } from '$lib/types';

export interface AgentTokenResponse {
  node: Node;
  token: string;
  token_preview: string;
  install_command: string;
}

export const agentsApi = {
  register: (payload: { name: string; description?: string; hostname?: string; role?: string; environment_id?: number }) =>
    post<AgentTokenResponse>('/agents/register', payload),
  token: (nodeId: number) => post<AgentTokenResponse>(`/agents/${nodeId}/token`),
  installCommand: (nodeId: number) => api<{ node_id: number; install_command: string }>(`/agents/install-command/${nodeId}`),
  downloadUrl: () => `${API_BASE}/agents/download`
};
