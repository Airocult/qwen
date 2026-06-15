import { create } from 'zustand';
import { PCBDesign, RoutingProgress, ValidationResult } from '../types';

interface DesignState {
  currentDesign: PCBDesign | null;
  designs: PCBDesign[];
  routingProgress: RoutingProgress;
  validationResult: ValidationResult | null;
  selectedNet: string | null;
  selectedComponent: string | null;
  
  // Actions
  setCurrentDesign: (design: PCBDesign) => void;
  addDesign: (design: PCBDesign) => void;
  updateDesign: (design: PCBDesign) => void;
  setRoutingProgress: (progress: RoutingProgress) => void;
  setValidationResult: (result: ValidationResult) => void;
  setSelectedNet: (netId: string | null) => void;
  setSelectedComponent: (componentId: string | null) => void;
  resetState: () => void;
}

const initialRoutingProgress: RoutingProgress = {
  status: 'idle',
  progress: 0,
  totalNets: 0,
  routedNets: 0,
  failedNets: 0,
  elapsedTime: 0,
};

export const useDesignStore = create<DesignState>((set) => ({
  currentDesign: null,
  designs: [],
  routingProgress: initialRoutingProgress,
  validationResult: null,
  selectedNet: null,
  selectedComponent: null,

  setCurrentDesign: (design) => set({ currentDesign: design }),
  
  addDesign: (design) => set((state) => ({ 
    designs: [...state.designs, design],
    currentDesign: design 
  })),
  
  updateDesign: (design) => set((state) => ({
    currentDesign: design,
    designs: state.designs.map(d => d.id === design.id ? design : d),
  })),
  
  setRoutingProgress: (progress) => set({ routingProgress: progress }),
  
  setValidationResult: (result) => set({ validationResult: result }),
  
  setSelectedNet: (netId) => set({ selectedNet: netId }),
  
  setSelectedComponent: (componentId) => set({ selectedComponent: componentId }),
  
  resetState: () => set({
    currentDesign: null,
    routingProgress: initialRoutingProgress,
    validationResult: null,
    selectedNet: null,
    selectedComponent: null,
  }),
}));
