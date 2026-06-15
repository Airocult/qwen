export interface Coordinate {
  x: number;
  y: number;
  layer: number;
}

export interface Pad {
  id: string;
  name: string;
  x: number;
  y: number;
  layer: number;
  shape: 'circle' | 'rect' | 'oval';
  width: number;
  height: number;
  drillDiameter?: number;
}

export interface Component {
  id: string;
  name: string;
  footprint: string;
  x: number;
  y: number;
  rotation: number;
  layer: number;
  pads: Pad[];
  value?: string;
  library?: string;
}

export interface Net {
  id: string;
  name: string;
  connections: string[]; // pad IDs
  impedance?: number;
  current?: number;
  voltage?: number;
  isPowerNet?: boolean;
  isGroundNet?: boolean;
  differentialPair?: string;
}

export interface TraceSegment {
  id: string;
  netId: string;
  start: Coordinate;
  end: Coordinate;
  width: number;
  layer: number;
}

export interface Via {
  id: string;
  x: number;
  y: number;
  drillDiameter: number;
  outerDiameter: number;
  startLayer: number;
  endLayer: number;
  netId: string;
}

export interface Route {
  id: string;
  netId: string;
  segments: TraceSegment[];
  vias: Via[];
  totalLength: number;
  impedanceControlled: boolean;
  lengthMatched: boolean;
}

export interface LayerStackup {
  id: string;
  name: string;
  type: 'signal' | 'power' | 'ground' | 'dielectric';
  material: string;
  thickness: number;
  copperWeight: number;
}

export interface DesignRule {
  id: string;
  name: string;
  minTraceWidth: number;
  minClearance: number;
  minViaDrill: number;
  minViaDiameter: number;
  impedanceTolerance: number;
}

export interface PCBDesign {
  id: string;
  name: string;
  components: Component[];
  nets: Net[];
  routes: Route[];
  stackup: LayerStackup[];
  designRules: DesignRule;
  boardOutline: Coordinate[];
  status: 'draft' | 'routed' | 'validated' | 'ready_for_gerber';
  createdAt: string;
  updatedAt: string;
}

export interface ValidationResult {
  passed: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  drcChecks: DRCResult[];
}

export interface ValidationError {
  id: string;
  severity: 'error' | 'critical';
  message: string;
  location?: Coordinate;
  netId?: string;
  componentId?: string;
}

export interface ValidationWarning {
  id: string;
  message: string;
  suggestion?: string;
}

export interface DRCResult {
  checkName: string;
  passed: boolean;
  violations: number;
  details?: string;
}

export interface RoutingProgress {
  status: 'idle' | 'running' | 'completed' | 'failed';
  progress: number;
  currentNet?: string;
  totalNets: number;
  routedNets: number;
  failedNets: number;
  elapsedTime: number;
  estimatedTimeRemaining?: number;
}

export interface ImpedanceCalculation {
  traceWidth: number;
  dielectricHeight: number;
  dielectricConstant: number;
  copperThickness: number;
  calculatedImpedance: number;
  targetImpedance: number;
  tolerance: number;
  passed: boolean;
}
