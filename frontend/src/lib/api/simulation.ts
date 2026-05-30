import { api, post } from './client';
import type { Environment, SimulationScenario } from '$lib/types';

export const simulationApi = {
  demo: (name = 'Демонстраційний віртуальний кластер') => post<Environment>('/simulation/environments/demo', { name }),
  createScenario: (payload: {
    environment_id: number;
    target_node_id?: number | null;
    name: string;
    scenario_type: string;
    duration_seconds: number;
    intensity: number;
  }) => post<SimulationScenario>('/simulation/scenarios', payload),
  runScenario: (id: number) => post<SimulationScenario>(`/simulation/scenarios/${id}/run`),
  runNodeScenario: (nodeId: number, payload: { scenario_type: string; duration_seconds: number; intensity: number }) =>
    post<SimulationScenario>(`/simulation/nodes/${nodeId}/run`, payload),
  stopScenario: (id: number) => post<SimulationScenario>(`/simulation/scenarios/${id}/stop`),
  list: () => api<SimulationScenario[]>('/simulation/scenarios')
};
