"""
Deterministic PCB Design System - Core Module

This module provides the foundational data structures and interfaces for the
deterministic PCB design system that transforms schematics into production-ready
Gerber files while strictly adhering to all electrical, mechanical, and manufacturing rules.

Author: PCB Design System Team
License: MIT
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum
import numpy as np
from scipy import constants


# ============================================================================
# Enums and Constants
# ============================================================================

class LayerType(Enum):
    """PCB layer types"""
    SIGNAL = "signal"
    POWER = "power"
    GROUND = "ground"
    MECHANICAL = "mechanical"
    KEEPOUT = "keepout"


class Unit(Enum):
    """Measurement units"""
    MILS = "mils"
    MM = "mm"
    INCHES = "inches"
    OZ = "oz"  # Copper weight


class TraceProfile(Enum):
    """Trace cross-section profiles"""
    RECTANGULAR = "rectangular"
    TRAPEZOIDAL = "trapezoidal"


class ViaType(Enum):
    """Via types"""
    THROUGH_HOLE = "through_hole"
    BLIND = "blind"
    BURIED = "buried"
    MICROVIA = "microvia"


# IPC Standards Constants
IPC_2152_EXTERNAL_K = 0.048
IPC_2152_INTERNAL_K = 0.024
IPC_2152_B = 0.44
IPC_2152_C = 0.725
COPPER_THICKNESS_PER_OZ = 1.378  # mils per oz/ft²


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class Coordinate:
    """2D/3D coordinate representation"""
    x: float
    y: float
    z: float = 0.0
    unit: Unit = Unit.MM
    
    def to_mils(self) -> 'Coordinate':
        """Convert to mils"""
        if self.unit == Unit.MILS:
            return self
        elif self.unit == Unit.MM:
            factor = 39.3701
            return Coordinate(self.x * factor, self.y * factor, self.z * factor, Unit.MILS)
        elif self.unit == Unit.INCHES:
            return Coordinate(self.x * 1000, self.y * 1000, self.z * 1000, Unit.MILS)
        return self
    
    def to_mm(self) -> 'Coordinate':
        """Convert to millimeters"""
        if self.unit == Unit.MM:
            return self
        elif self.unit == Unit.MILS:
            factor = 0.0254
            return Coordinate(self.x * factor, self.y * factor, self.z * factor, Unit.MM)
        elif self.unit == Unit.INCHES:
            return Coordinate(self.x * 25.4, self.y * 25.4, self.z * 25.4, Unit.MM)
        return self
    
    def distance_to(self, other: 'Coordinate') -> float:
        """Calculate Euclidean distance in current units"""
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)


@dataclass
class Dimension:
    """Physical dimension with units"""
    width: float
    height: float
    thickness: float = 0.0
    unit: Unit = Unit.MM
    
    def to_mils(self) -> 'Dimension':
        """Convert to mils"""
        if self.unit == Unit.MILS:
            return self
        factor = 39.3701 if self.unit == Unit.MM else 1000
        return Dimension(
            self.width * factor,
            self.height * factor,
            self.thickness * factor,
            Unit.MILS
        )


@dataclass
class Material:
    """PCB material properties"""
    name: str
    dielectric_constant: float  # Er
    loss_tangent: float
    thermal_conductivity: float  # W/m·K
    cte_x: float  # Coefficient of thermal expansion ppm/°C
    cte_y: float
    cte_z: float
    tg: float  # Glass transition temperature °C
    breakdown_voltage: float  # V/mil
    
    # Common materials
    @classmethod
    def fr4(cls) -> 'Material':
        """Standard FR-4 material"""
        return cls(
            name="FR-4",
            dielectric_constant=4.5,
            loss_tangent=0.02,
            thermal_conductivity=0.3,
            cte_x=14,
            cte_y=14,
            cte_z=70,
            tg=130,
            breakdown_voltage=1000
        )
    
    @classmethod
    def rogers_ro4003c(cls) -> 'Material':
        """Rogers RO4003C for RF applications"""
        return cls(
            name="RO4003C",
            dielectric_constant=3.55,
            loss_tangent=0.0027,
            thermal_conductivity=0.64,
            cte_x=16,
            cte_y=16,
            cte_z=24,
            tg=280,
            breakdown_voltage=800
        )


@dataclass
class Layer:
    """PCB layer definition"""
    number: int
    name: str
    type: LayerType
    copper_weight: float  # oz/ft²
    thickness: float  # Dielectric thickness to next layer (mils)
    material: Material = field(default_factory=Material.fr4)
    min_trace_width: float = 5.0  # mils
    min_trace_space: float = 5.0  # mils
    min_via_drill: float = 10.0  # mils
    min_annular_ring: float = 5.0  # mils


@dataclass
class Pad:
    """Component pad definition"""
    name: str
    shape: str  # rect, circle, oval
    dimensions: Dimension
    layers: List[int]  # Layer numbers this pad spans
    drill_diameter: float = 0.0  # For through-hole pads
    position: Coordinate = field(default_factory=lambda: Coordinate(0, 0))
    net: Optional[str] = None
    thermal_relief: bool = False
    solder_mask_expansion: float = 4.0  # mils
    paste_mask_layers: List[int] = field(default_factory=list)


@dataclass
class Component:
    """Electronic component"""
    ref_designator: str
    footprint: str
    value: str
    manufacturer_part_number: Optional[str] = None
    description: str = ""
    position: Coordinate = field(default_factory=lambda: Coordinate(0, 0))
    rotation: float = 0.0  # degrees
    side: str = "top"  # top or bottom
    pads: List[Pad] = field(default_factory=list)
    keepouts: List[Dict] = field(default_factory=list)
    height: float = 0.0  # mm
    power_dissipation: float = 0.0  # Watts
    
    def get_pad_by_name(self, name: str) -> Optional[Pad]:
        """Get pad by name"""
        for pad in self.pads:
            if pad.name == name:
                return pad
        return None


@dataclass
class Net:
    """Electrical net connecting components"""
    name: str
    connections: List[Tuple[str, str]]  # List of (component_ref, pad_name)
    voltage: Optional[float] = None
    current: Optional[float] = None
    is_power: bool = False
    is_ground: bool = False
    is_differential_pair: bool = False
    differential_pair_id: Optional[str] = None
    impedance_target: Optional[float] = None  # Ohms
    length_target: Optional[float] = None  # mm
    length_tolerance: float = 0.0  # mm
    max_skew: Optional[float] = None  # ps or mm
    routing_priority: int = 0  # Higher = route first
    min_trace_width: Optional[float] = None  # Override global default
    clearance_override: Optional[float] = None  # Override global default


@dataclass
class TraceSegment:
    """Individual trace segment"""
    start: Coordinate
    end: Coordinate
    width: float  # mils
    layer: int
    net: str
    via_at_end: bool = False
    
    def length(self) -> float:
        """Calculate segment length in current coordinate units"""
        return self.start.distance_to(self.end)


@dataclass
class Via:
    """Via definition"""
    position: Coordinate
    drill_diameter: float  # mils
    pad_diameter: float  # mils
    start_layer: int
    end_layer: int
    type: ViaType = ViaType.THROUGH_HOLE
    net: Optional[str] = None
    tented: bool = False  # Solder mask covered


@dataclass
class Route:
    """Complete routed net"""
    net_name: str
    segments: List[TraceSegment]
    vias: List[Via]
    total_length: float = 0.0
    via_count: int = 0
    impedance_profile: List[Tuple[float, float]] = field(default_factory=list)  # (position, impedance)
    length_matched: bool = False
    drc_errors: List[Dict] = field(default_factory=list)
    
    def calculate_metrics(self):
        """Calculate route metrics"""
        self.total_length = sum(seg.length() for seg in self.segments)
        self.via_count = len(self.vias)


@dataclass
class DesignRule:
    """Design rule definition"""
    name: str
    category: str  # manufacturing, electrical, assembly
    enabled: bool = True
    
    # Manufacturing rules
    min_trace_width: float = 5.0  # mils
    min_trace_space: float = 5.0  # mils
    min_via_drill: float = 10.0  # mils
    min_via_to_trace: float = 5.0  # mils
    min_via_to_via: float = 10.0  # mils
    min_annular_ring: float = 5.0  # mils
    min_slot_width: float = 20.0  # mils
    
    # Electrical rules
    clearance_matrix: Dict[Tuple[str, str], float] = field(default_factory=dict)  # (net1, net2) -> clearance
    voltage_clearance_table: Dict[float, float] = field(default_factory=dict)  # voltage -> clearance
    impedance_tolerance: float = 0.10  # ±10%
    
    # Assembly rules
    component_keepout: float = 0.0  # mm
    pick_and_place_clearance: float = 2.0  # mm
    reflow_thermal_relief: bool = True
    
    # High-speed rules
    differential_pair_gap: float = 5.0  # mils
    differential_pair_tolerance: float = 0.05  # mm
    length_matching_increment: float = 0.1  # mm
    max_unmatched_length: float = 0.5  # mm


@dataclass
class Stackup:
    """PCB stackup definition"""
    layers: List[Layer]
    total_thickness: float  # mm
    finished_copper: float = 1.0  # oz
    surface_finish: str = "HASL"  # HASL, ENIG, OSP, etc.
    solder_mask_color: str = "green"
    silkscreen_color: str = "white"
    board_thickness_tolerance: float = 0.1  # mm
    
    def get_signal_layers(self) -> List[Layer]:
        """Get all signal layers"""
        return [l for l in self.layers if l.type == LayerType.SIGNAL]
    
    def get_plane_layers(self) -> List[Layer]:
        """Get all plane layers"""
        return [l for l in self.layers if l.type in [LayerType.POWER, LayerType.GROUND]]


@dataclass
class BoardOutline:
    """Board mechanical outline"""
    vertices: List[Coordinate]
    cutouts: List[List[Coordinate]] = field(default_factory=list)
    slots: List[Dict] = field(default_factory=list)  # position, size, rotation
    v_score_lines: List[Tuple[Coordinate, Coordinate]] = field(default_factory=list)
    
    def area(self) -> float:
        """Calculate board area using shoelace formula"""
        if len(self.vertices) < 3:
            return 0.0
        
        n = len(self.vertices)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += self.vertices[i].x * self.vertices[j].y
            area -= self.vertices[j].x * self.vertices[i].y
        
        return abs(area) / 2.0


@dataclass
class PCBDesign:
    """Complete PCB design"""
    name: str
    version: str
    stackup: Stackup
    board_outline: BoardOutline
    components: List[Component]
    nets: List[Net]
    routes: List[Route] = field(default_factory=list)
    design_rules: DesignRule = field(default_factory=DesignRule)
    metadata: Dict = field(default_factory=dict)
    
    # Validation results
    drc_results: Dict = field(default_factory=dict)
    simulation_results: Dict = field(default_factory=dict)
    
    def add_component(self, component: Component):
        """Add component to design"""
        self.components.append(component)
    
    def add_net(self, net: Net):
        """Add net to design"""
        self.nets.append(net)
    
    def get_net_by_name(self, name: str) -> Optional[Net]:
        """Get net by name"""
        for net in self.nets:
            if net.name == name:
                return net
        return None
    
    def get_components_by_net(self, net_name: str) -> List[Component]:
        """Get all components connected to a net"""
        net = self.get_net_by_name(net_name)
        if not net:
            return []
        
        components = []
        refs = set(conn[0] for conn in net.connections)
        for comp in self.components:
            if comp.ref_designator in refs:
                components.append(comp)
        
        return components


# ============================================================================
# File Format Support
# ============================================================================

@dataclass
class KiCADSchematic:
    """KiCAD schematic file representation"""
    version: str
    components: List[Dict]
    wires: List[Dict]
    buses: List[Dict]
    junctions: List[Dict]
    labels: List[Dict]
    sheets: List[Dict]
    
    @classmethod
    def parse_file(cls, filepath: str) -> 'KiCADSchematic':
        """Parse KiCAD .kicad_sch file"""
        # Implementation in parser module
        pass
    
    def to_pcb_design(self, stackup: Stackup, board_outline: BoardOutline) -> PCBDesign:
        """Convert to PCBDesign object"""
        # Implementation in converter module
        pass


@dataclass
class EasyEDASchematic:
    """EasyEDA schematic file representation"""
    version: str
    head: Dict
    shapes: List[Dict]
    tracks: List[Dict]
    pads: List[Dict]
    holes: List[Dict]
    
    @classmethod
    def parse_file(cls, filepath: str) -> 'EasyEDASchematic':
        """Parse EasyEDA JSON file"""
        # Implementation in parser module
        pass
    
    def to_pcb_design(self, stackup: Stackup, board_outline: BoardOutline) -> PCBDesign:
        """Convert to PCBDesign object"""
        # Implementation in converter module
        pass


@dataclass
class GerberFile:
    """Gerber file representation (RS-274X)"""
    aperture_definitions: Dict
    commands: List[Tuple[str, ...]]  # (command_type, parameters)
    layer_type: LayerType
    units: Unit
    
    def to_string(self) -> str:
        """Generate RS-274X formatted string"""
        # Implementation in output module
        pass
    
    @classmethod
    def from_pcb_design(cls, pcb: PCBDesign, layer_number: int) -> 'GerberFile':
        """Generate Gerber from PCB design"""
        # Implementation in output module
        pass


# ============================================================================
# Electrical Calculation Interfaces
# ============================================================================

class ImpedanceCalculator:
    """Interface for impedance calculations"""
    
    @staticmethod
    def microstrip(trace_width: float, dielectric_height: float, 
                   er: float, copper_thickness: float) -> float:
        """
        Calculate microstrip characteristic impedance per IPC-2141
        
        Parameters:
        - trace_width: Trace width (mils)
        - dielectric_height: Dielectric height (mils)
        - er: Relative permittivity
        - copper_thickness: Copper thickness (mils)
        
        Returns: Impedance in Ohms
        """
        # Effective dielectric constant
        eff_er = (er + 1) / 2 + (er - 1) / 2 * (1 + 12 * dielectric_height / trace_width)**(-0.5)
        
        # Impedance calculation based on W/H ratio
        if trace_width / dielectric_height <= 1:
            Z0 = 60 / np.sqrt(eff_er) * np.log(8 * dielectric_height / trace_width + 
                                                trace_width / (4 * dielectric_height))
        else:
            Z0 = 120 * np.pi / (np.sqrt(eff_er) * 
                               (trace_width/dielectric_height + 1.393 + 
                                0.667 * np.log(trace_width/dielectric_height + 1.444)))
        
        return Z0
    
    @staticmethod
    def stripline(trace_width: float, dielectric_height: float,
                  er: float, copper_thickness: float) -> float:
        """
        Calculate stripline characteristic impedance per IPC-2141
        
        Parameters:
        - trace_width: Trace width (mils)
        - dielectric_height: Total dielectric height between planes (mils)
        - er: Relative permittivity
        - copper_thickness: Copper thickness (mils)
        
        Returns: Impedance in Ohms
        """
        # Simplified stripline formula
        Z0 = 60 / np.sqrt(er) * np.log(4 * dielectric_height / (0.67 * np.pi * (0.8 * trace_width + copper_thickness)))
        return Z0
    
    @staticmethod
    def differential_microstrip(trace_width: float, spacing: float,
                                dielectric_height: float, er: float,
                                copper_thickness: float) -> Tuple[float, float]:
        """
        Calculate differential microstrip impedance
        
        Returns: (odd_mode_impedance, even_mode_impedance) in Ohms
        """
        # Single-ended impedance
        Z0_se = ImpedanceCalculator.microstrip(trace_width, dielectric_height, er, copper_thickness)
        
        # Coupling coefficient (simplified)
        k = np.exp(-0.5 * spacing / dielectric_height)
        
        # Odd and even mode impedances
        Z0_odd = Z0_se * np.sqrt(1 - k) / np.sqrt(1 + k)
        Z0_even = Z0_se * np.sqrt(1 + k) / np.sqrt(1 - k)
        
        # Differential impedance
        Z0_diff = 2 * Z0_odd
        
        return (Z0_diff, Z0_even)


class TraceWidthCalculator:
    """Calculate trace width per IPC-2152"""
    
    @staticmethod
    def calculate(current: float, temp_rise: float = 10.0,
                  copper_thickness: float = 1.0, 
                  layer_type: str = 'external') -> float:
        """
        Calculate minimum trace width per IPC-2152
        
        Parameters:
        - current: Current in Amperes
        - temp_rise: Temperature rise in °C (default 10°C)
        - copper_thickness: Copper thickness in oz/ft² (default 1 oz)
        - layer_type: 'internal' or 'external'
        
        Returns: Minimum trace width in mils
        """
        k = IPC_2152_EXTERNAL_K if layer_type == 'external' else IPC_2152_INTERNAL_K
        b = IPC_2152_B
        c = IPC_2152_C
        
        # Calculate cross-sectional area
        area = (current / (k * temp_rise**b))**(1/c)
        
        # Convert area to width
        width = area / (copper_thickness * COPPER_THICKNESS_PER_OZ)
        
        return width
    
    @staticmethod
    def calculate_with_derating(current: float, ambient_temp: float,
                                max_temp: float, copper_thickness: float = 1.0,
                                layer_type: str = 'external') -> float:
        """
        Calculate trace width with temperature derating
        
        Parameters:
        - current: Operating current in Amperes
        - ambient_temp: Ambient temperature in °C
        - max_temp: Maximum allowable temperature in °C
        - copper_thickness: Copper thickness in oz/ft²
        - layer_type: 'internal' or 'external'
        
        Returns: Minimum trace width in mils
        """
        temp_rise = max_temp - ambient_temp
        return TraceWidthCalculator.calculate(current, temp_rise, copper_thickness, layer_type)


class ClearanceCalculator:
    """Calculate electrical clearances per IPC-2221"""
    
    @staticmethod
    def voltage_clearance(voltage: float, coating: str = 'uncoated',
                          altitude: float = 0.0) -> float:
        """
        Calculate minimum clearance based on voltage per IPC-2221
        
        Parameters:
        - voltage: Working voltage (V)
        - coating: 'uncoated', 'conformal_coated', or 'potting'
        - altitude: Operating altitude in meters
        
        Returns: Minimum clearance in mils
        """
        # IPC-2221 Table 6-1 simplified lookup
        if voltage <= 15:
            base_clearance = 25  # mils
        elif voltage <= 30:
            base_clearance = 25
        elif voltage <= 50:
            base_clearance = 25
        elif voltage <= 100:
            base_clearance = 50
        elif voltage <= 150:
            base_clearance = 50
        elif voltage <= 300:
            base_clearance = 100
        elif voltage <= 500:
            base_clearance = 250
        else:
            # Higher voltages: 0.0025 inch per volt above 500V
            base_clearance = 250 + (voltage - 500) * 2.5
        
        # Apply coating factor
        coating_factors = {
            'uncoated': 1.0,
            'conformal_coated': 0.5,
            'potting': 0.25
        }
        clearance = base_clearance * coating_factors.get(coating, 1.0)
        
        # Apply altitude derating (above 3000m)
        if altitude > 3000:
            altitude_factor = 1.0 + (altitude - 3000) / 10000
            clearance *= altitude_factor
        
        return clearance
    
    @staticmethod
    def creepage_distance(voltage: float, material_group: str = 'II',
                          pollution_degree: int = 2) -> float:
        """
        Calculate minimum creepage distance per IEC 60950
        
        Parameters:
        - voltage: Working voltage (V)
        - material_group: 'I', 'II', or 'III' (CTI rating)
        - pollution_degree: 1, 2, or 3
        
        Returns: Minimum creepage in mm
        """
        # IEC 60950-1 Table 2K simplified
        # This is a simplified lookup - full implementation would use complete tables
        creepage_table = {
            (1, 'I'): 0.18, (1, 'II'): 0.18, (1, 'III'): 0.18,
            (2, 'I'): 0.56, (2, 'II'): 0.85, (2, 'III'): 1.2,
            (3, 'I'): 0.85, (3, 'II'): 1.2, (3, 'III'): 1.7,
        }
        
        # For voltages up to 50V, use table
        key = (pollution_degree, material_group)
        if voltage <= 50:
            return creepage_table.get(key, 1.0)
        
        # For higher voltages, scale linearly (simplified)
        base = creepage_table.get(key, 1.0)
        return base * (voltage / 50)


print("PCB Design System Core Module loaded successfully")
print(f"Available classes: Coordinate, Dimension, Material, Layer, Pad, Component, Net,")
print(f"                   TraceSegment, Via, Route, DesignRule, Stackup, BoardOutline, PCBDesign")
print(f"                   ImpedanceCalculator, TraceWidthCalculator, ClearanceCalculator")
