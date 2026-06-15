import axios from 'axios';
import { PCBDesign, ValidationResult, RoutingProgress } from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const designApi = {
  // Schematic parsing
  parseSchematic: async (file: File, format: 'kicad' | 'easyeda' | 'generic') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('format', format);
    
    const response = await api.post<PCBDesign>('/schematic/parse', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Component placement optimization
  optimizePlacement: async (designId: string) => {
    const response = await api.post<PCBDesign>(`/design/${designId}/placement/optimize`);
    return response.data;
  },

  // Routing
  routeDesign: async (designId: string) => {
    const response = await api.post<{ designId: string; jobId: string }>(
      `/design/${designId}/route`
    );
    return response.data;
  },

  // Get routing progress
  getRoutingProgress: async (jobId: string) => {
    const response = await api.get<RoutingProgress>(`/routing/${jobId}/progress`);
    return response.data;
  },

  // Validation
  validateDesign: async (designId: string) => {
    const response = await api.post<ValidationResult>(`/design/${designId}/validate`);
    return response.data;
  },

  // Gerber generation
  generateGerber: async (designId: string) => {
    const response = await api.post<{ downloadUrl: string; gerberFiles: string[] }>(
      `/design/${designId}/gerber`
    );
    return response.data;
  },

  // Impedance calculation
  calculateImpedance: async (params: {
    traceWidth: number;
    dielectricHeight: number;
    dielectricConstant: number;
    copperThickness: number;
    targetImpedance: number;
  }) => {
    const response = await api.post('/calculations/impedance', params);
    return response.data;
  },

  // Trace width calculation
  calculateTraceWidth: async (params: {
    current: number;
    temperatureRise: number;
    copperWeight: number;
    layerType: 'external' | 'internal';
  }) => {
    const response = await api.post('/calculations/trace-width', params);
    return response.data;
  },

  // Clearance calculation
  calculateClearance: async (params: {
    voltage: number;
    pollutionDegree: 1 | 2 | 3;
    materialGroup: 'I' | 'II' | 'III';
  }) => {
    const response = await api.post('/calculations/clearance', params);
    return response.data;
  },
};

export default api;
