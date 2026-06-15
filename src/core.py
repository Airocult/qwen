"""
Deterministic PCB Design System - Core Module

This module provides the foundational data structures and IPC-compliant
calculators for PCB design including impedance, current capacity, and
clearance calculations.

Standards Implemented:
- IPC-2141: Controlled Impedance
- IPC-2152: Current-Carrying Capacity
- IPC-2221: Generic PCB Design
- IEC 60950: Safety Clearances
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple, Union
from collections import defaultdict


# ============================================================================
# Unit Conversion Utilities
# ============================================================================

class Unit(Enum):
    """Supported length units for PCB design."""
    MM = "mm"
    MILS = "mils"
    INCHES = "inches"
    MICROMETERS = "um"


class UnitConverter:
    """Convert between different length units used in PCB design."""
    
    CONVERSION_TO_MM = {
        Unit.MM: 1.0,
        Unit.MILS: 0.0254,
        Unit.INCHES: 25.4,
        Unit.MICROMETERS: 0.001,
    }
    
    @classmethod
    def convert(cls, value: float, from_unit: Unit, to_unit: Unit) -> float:
        """Convert a value from one unit to another."""
        mm_value = value * cls.CONVERSION_TO_MM[from_unit]
        return mm_value / cls.CONVERSION_TO_MM[to_unit]
    
    @classmethod
    def to_mm(cls, value: float, from_unit: Unit) -> float:
        """Convert any unit to millimeters."""
        return value * cls.CONVERSION_TO_MM[from_unit]
    
    @classmethod
    def to_mils(cls, value: float, from_unit: Unit) -> float:
        """Convert any unit to mils (thousandths of an inch)."""
        mm_value = value * cls.CONVERSION_TO_MM[from_unit]
        return mm_value / 0.0254


# ============================================================================
# Material Properties
# ============================================================================

@dataclass
class DielectricMaterial:
    """Represents a dielectric material used in PCB stackup."""
    name: str
    epsilon_r: float  # Relative permittivity (dielectric constant)
    loss_tangent: float  # Dissipation factor
    thermal_conductivity: float  # W/(m·K)
    breakdown_voltage: float  # V/mil
    
    # Common materials
    @classmethod
    def fr4_standard(cls) -> 'DielectricMaterial':
        """Standard FR-4 material."""
        return cls(
            name="FR-4 Standard",
            epsilon_r=4.2,
            loss_tangent=0.02,
            thermal_conductivity=0.3,
            breakdown_voltage=800
        )
    
    @classmethod
    def fr4_high_speed(cls) -> 'DielectricMaterial':
        """High-speed FR-4 (e.g., Isola 370HR)."""
        return cls(
            name="FR-4 High-Speed",
            epsilon_r=3.8,
            loss_tangent=0.008,
            thermal_conductivity=0.35,
            breakdown_voltage=850
        )
    
    @classmethod
    def rogers_ro4003c(cls) -> 'DielectricMaterial':
        """Rogers RO4003C for RF applications."""
        return cls(
            name="Rogers RO4003C",
            epsilon_r=3.55,
            loss_tangent=0.0027,
            thermal_conductivity=0.61,
            breakdown_voltage=600
        )


@dataclass
class CopperMaterial:
    """Represents copper foil used in PCB layers."""
    weight_oz: float  # Copper weight in oz/ft²
    thickness_um: float  # Thickness in micrometers
    conductivity: float  # S/m (5.96e7 for pure copper)
    roughness_um: float  # Surface roughness in micrometers
    
    @classmethod
    def standard_1oz(cls) -> 'CopperMaterial':
        """Standard 1 oz copper."""
        return cls(
            weight_oz=1.0,
            thickness_um=35,
            conductivity=5.96e7,
            roughness_um=1.5
        )
    
    @classmethod
    def heavy_2oz(cls) -> 'CopperMaterial':
        """Heavy 2 oz copper for high current."""
        return cls(
            weight_oz=2.0,
            thickness_um=70,
            conductivity=5.96e7,
            roughness_um=2.0
        )


# ============================================================================
# Layer Stackup
# ============================================================================

class LayerType(Enum):
    """Types of layers in a PCB stackup."""
    SIGNAL = "signal"
    PLANE = "plane"
    POWER = "power"
    DIELECTRIC = "dielectric"
    SOLDER_MASK = "solder_mask"
    SILKSCREEN = "silkscreen"


@dataclass
class Layer:
    """Represents a single layer in the PCB stackup."""
    name: str
    type: LayerType
    thickness_mm: float
    material: Optional[Union[DielectricMaterial, CopperMaterial]] = None
    epsilon_r: float = 4.2  # For dielectric layers
    copper_weight_oz: float = 0.0  # For copper layers
    is_external: bool = False
    
    @property
    def thickness_mils(self) -> float:
        """Layer thickness in mils."""
        return UnitConverter.to_mils(self.thickness_mm, Unit.MM)
    
    @property
    def copper_thickness_mm(self) -> float:
        """Copper thickness in mm (for copper layers)."""
        if self.copper_weight_oz > 0:
            return self.copper_weight_oz * 0.035
        return 0.0


@dataclass
class Stackup:
    """Complete PCB layer stackup definition."""
    name: str
    layers: List[Layer] = field(default_factory=list)
    board_thickness_mm: float = 1.6
    finish_type: str = "HASL"  # HASL, ENIG, OSP, etc.
    
    def add_layer(self, layer: Layer) -> None:
        """Add a layer to the stackup."""
        layer.is_external = (len(self.layers) == 0 or 
                            len(self.layers) == self.total_layers - 1)
        self.layers.append(layer)
    
    @property
    def total_layers(self) -> int:
        """Total number of layers in stackup."""
        return len(self.layers)
    
    @property
    def signal_layers(self) -> List[int]:
        """Indices of signal layers."""
        return [i for i, l in enumerate(self.layers) 
                if l.type == LayerType.SIGNAL]
    
    @property
    def plane_layers(self) -> List[int]:
        """Indices of plane layers."""
        return [i for i, l in enumerate(self.layers) 
                if l.type in (LayerType.PLANE, LayerType.POWER)]
    
    def get_dielectric_above(self, layer_idx: int) -> Optional[Layer]:
        """Get the dielectric layer above a signal layer."""
        for i in range(layer_idx - 1, -1, -1):
            if self.layers[i].type == LayerType.DIELECTRIC:
                return self.layers[i]
        return None
    
    def get_reference_plane(self, layer_idx: int) -> Optional[int]:
        """Find the reference plane for a signal layer."""
        # Search downward first
        for i in range(layer_idx + 1, self.total_layers):
            if self.layers[i].type in (LayerType.PLANE, LayerType.POWER):
                return i
        # Search upward
        for i in range(layer_idx - 1, -1, -1):
            if self.layers[i].type in (LayerType.PLANE, LayerType.POWER):
                return i
        return None


# ============================================================================
# Coordinate System
# ============================================================================

@dataclass
class Coordinate:
    """2D coordinate with unit support."""
    x: float
    y: float
    unit: Unit = Unit.MM
    
    def to_mm(self) -> Tuple[float, float]:
        """Convert coordinates to millimeters."""
        return (UnitConverter.to_mm(self.x, self.unit),
                UnitConverter.to_mm(self.y, self.unit))
    
    def to_mils(self) -> Tuple[float, float]:
        """Convert coordinates to mils."""
        return (UnitConverter.to_mils(self.x, self.unit),
                UnitConverter.to_mils(self.y, self.unit))
    
    def distance_to(self, other: 'Coordinate') -> float:
        """Calculate Euclidean distance to another coordinate in mm."""
        x1, y1 = self.to_mm()
        x2, y2 = other.to_mm()
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def __add__(self, other: 'Coordinate') -> 'Coordinate':
        """Add two coordinates."""
        if self.unit != other.unit:
            other_x = UnitConverter.convert(other.x, other.unit, self.unit)
            other_y = UnitConverter.convert(other.y, other.unit, self.unit)
        else:
            other_x, other_y = other.x, other.y
        return Coordinate(self.x + other_x, self.y + other_y, self.unit)
    
    def __sub__(self, other: 'Coordinate') -> 'Coordinate':
        """Subtract two coordinates."""
        if self.unit != other.unit:
            other_x = UnitConverter.convert(other.x, other.unit, self.unit)
            other_y = UnitConverter.convert(other.y, other.unit, self.unit)
        else:
            other_x, other_y = other.x, other.y
        return Coordinate(self.x - other_x, self.y - other_y, self.unit)


@dataclass
class Coordinate3D(Coordinate):
    """3D coordinate extending 2D coordinate."""
    z: float = 0.0
    layer_index: int = 0
    
    def __post_init__(self):
        self.z = 0.0  # Initialize after parent


# ============================================================================
# PCB Components and Primitives
# ============================================================================

@dataclass
class Pad:
    """Represents a pad on a PCB."""
    name: str
    center: Coordinate
    width_mm: float
    height_mm: float
    shape: str = "rect"  # rect, circle, oval
    layers: List[int] = field(default_factory=list)
    hole_diameter_mm: float = 0.0  # For through-hole pads
    plating: bool = True
    
    @property
    def area_mm2(self) -> float:
        """Calculate pad area in mm²."""
        if self.shape == "circle":
            return math.pi * (self.width_mm / 2) ** 2
        elif self.shape == "oval":
            return math.pi * (self.width_mm / 2) * (self.height_mm / 2) + \
                   (self.width_mm - self.height_mm) * self.height_mm if self.width_mm > self.height_mm else \
                   math.pi * (self.width_mm / 2) ** 2
        else:  # rect
            return self.width_mm * self.height_mm


@dataclass
class Via:
    """Represents a via connecting different layers."""
    position: Coordinate
    outer_diameter_mm: float
    inner_diameter_mm: float
    start_layer: int
    end_layer: int
    tented: bool = False  # Covered by solder mask
    filled: bool = False  # Filled with conductive material
    
    @property
    def aspect_ratio(self) -> float:
        """Calculate via aspect ratio (board thickness / hole diameter)."""
        return self.inner_diameter_mm / 0.1  # Assuming 1.6mm board
    
    @property
    def current_capacity_a(self) -> float:
        """Estimate current capacity per IPC-2152."""
        # Simplified: ~1A per 0.3mm via diameter
        return self.inner_diameter_mm / 0.3


@dataclass
class TraceSegment:
    """A single segment of a routed trace."""
    start: Coordinate
    end: Coordinate
    width_mm: float
    layer: int
    net_name: str
    
    @property
    def length_mm(self) -> float:
        """Calculate segment length in mm."""
        return self.start.distance_to(self.end)
    
    @property
    def angle_degrees(self) -> float:
        """Calculate segment angle in degrees."""
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        return math.degrees(math.atan2(dy, dx))


@dataclass
class Component:
    """Represents a component on the PCB."""
    ref_designator: str
    footprint_name: str
    position: Coordinate
    rotation_degrees: float = 0.0
    layer: int = 0  # Top=0, Bottom=last
    value: str = ""
    manufacturer_part_number: str = ""
    pads: List[Pad] = field(default_factory=list)
    
    @property
    def bounding_box(self) -> Tuple[Coordinate, Coordinate]:
        """Calculate component bounding box."""
        min_x = min(p.center.x for p in self.pads) if self.pads else self.position.x
        min_y = min(p.center.y for p in self.pads) if self.pads else self.position.y
        max_x = max(p.center.x for p in self.pads) if self.pads else self.position.x
        max_y = max(p.center.y for p in self.pads) if self.pads else self.position.y
        return (Coordinate(min_x, min_y), Coordinate(max_x, max_y))


# ============================================================================
# Nets and Connectivity
# ============================================================================

@dataclass
class Net:
    """Represents an electrical net (connection)."""
    name: str
    net_class: str = "default"  # default, power, ground, high_speed, differential
    voltage: float = 0.0  # Nominal voltage
    current_max: float = 0.0  # Maximum expected current
    impedance_target: float = 0.0  # Target impedance (0 = no control)
    is_power: bool = False
    is_ground: bool = False
    is_differential: bool = False
    diff_pair_id: Optional[str] = None
    length_match_group: Optional[str] = None
    max_length_mm: float = float('inf')
    min_clearance_mm: float = 0.2
    
    connections: List[Tuple[str, str]] = field(default_factory=list)  # [(ref_des, pad_name)]


@dataclass
class DifferentialPair:
    """Represents a differential pair of nets."""
    name: str
    positive_net: str
    negative_net: str
    impedance_diff: float = 100.0  # Differential impedance target
    impedance_single: float = 50.0  # Single-ended impedance
    max_skew_mm: float = 0.0  # Maximum length mismatch
    spacing_mm: float = 0.2  # Trace-to-trace spacing
    coupled: bool = True  # Whether traces should be coupled


@dataclass
class Netlist:
    """Complete netlist extracted from schematic."""
    nets: Dict[str, Net] = field(default_factory=dict)
    components: Dict[str, Component] = field(default_factory=dict)
    differential_pairs: List[DifferentialPair] = field(default_factory=list)
    
    def add_net(self, net: Net) -> None:
        """Add a net to the netlist."""
        self.nets[net.name] = net
    
    def add_component(self, component: Component) -> None:
        """Add a component to the netlist."""
        self.components[component.ref_designator] = component
    
    def get_connections_for_net(self, net_name: str) -> List[Tuple[str, str]]:
        """Get all connections for a specific net."""
        if net_name in self.nets:
            return self.nets[net_name].connections
        return []


# ============================================================================
# Routes
# ============================================================================

@dataclass
class Route:
    """Represents a routed connection."""
    net_name: str
    segments: List[TraceSegment] = field(default_factory=list)
    vias: List[Via] = field(default_factory=list)
    total_length_mm: float = 0.0
    layer_changes: int = 0
    
    def add_segment(self, segment: TraceSegment) -> None:
        """Add a segment to the route."""
        self.segments.append(segment)
        self.total_length_mm += segment.length_mm
        if len(self.segments) > 1:
            prev_layer = self.segments[-2].layer
            if segment.layer != prev_layer:
                self.layer_changes += 1
    
    @property
    def impedance_profile(self) -> List[float]:
        """Return impedance for each segment (to be calculated)."""
        # Placeholder - actual calculation requires stackup info
        return [50.0] * len(self.segments)


# ============================================================================
# Design Rules
# ============================================================================

@dataclass
class DesignRules:
    """Manufacturing and electrical design rules."""
    # Physical constraints
    min_trace_width_mm: float = 0.15
    min_trace_spacing_mm: float = 0.15
    min_via_outer_mm: float = 0.3
    min_via_inner_mm: float = 0.15
    min_annular_ring_mm: float = 0.1
    
    # Electrical constraints
    clearance_by_voltage: Dict[float, float] = field(default_factory=dict)
    impedance_tolerance_percent: float = 10.0
    
    # Thermal constraints
    max_temp_rise_c: float = 20.0
    
    # Manufacturing constraints
    edge_clearance_mm: float = 0.5
    silkscreen_clearance_mm: float = 0.1
    
    def __post_init__(self):
        """Initialize default voltage clearances per IPC-2221."""
        if not self.clearance_by_voltage:
            self.clearance_by_voltage = {
                0.0: 0.1,    # 0-15V
                15.0: 0.2,   # 15-30V
                30.0: 0.4,   # 30-60V
                60.0: 0.8,   # 60-125V
                125.0: 1.6,  # 125-250V
                250.0: 3.2,  # 250-500V
                500.0: 6.4,  # 500-1000V
            }


# ============================================================================
# IPC-2141: Impedance Calculator
# ============================================================================

class ImpedanceCalculator:
    """
    Calculate controlled impedance traces per IPC-2141.
    
    Supports:
    - Microstrip (outer layer)
    - Stripline (inner layer)
    - Differential pairs (edge-coupled)
    """
    
    def __init__(self, stackup: Stackup):
        self.stackup = stackup
    
    def calculate_microstrip_impedance(self, width_mm: float, layer_idx: int,
                                       epsilon_eff: Optional[float] = None) -> float:
        """
        Calculate microstrip impedance using IPC-2141 formula.
        
        Z₀ = (87 / √(εᵣ + 1.41)) × ln(5.98h / (0.8w + t))
        
        Parameters:
        - width_mm: Trace width in mm
        - layer_idx: Layer index
        - epsilon_eff: Effective dielectric constant (optional)
        
        Returns:
        - Characteristic impedance in ohms
        """
        if layer_idx >= len(self.stackup.layers):
            raise ValueError(f"Invalid layer index: {layer_idx}")
        
        layer = self.stackup.layers[layer_idx]
        dielectric = self.stackup.get_dielectric_above(layer_idx)
        
        if dielectric is None:
            # Use default values
            h_mm = 0.2  # Assume 0.2mm dielectric
            epsilon_r = 4.2
        else:
            h_mm = dielectric.thickness_mm
            epsilon_r = dielectric.epsilon_r
        
        # Convert to mils for IPC-2141 formula
        w_mils = UnitConverter.to_mils(width_mm, Unit.MM)
        h_mils = UnitConverter.to_mils(h_mm, Unit.MM)
        t_mils = UnitConverter.to_mils(layer.copper_thickness_mm, Unit.MM)
        
        # IPC-2141 microstrip formula
        denominator = math.sqrt(epsilon_r + 1.41)
        numerator = 87.0
        ln_arg = (5.98 * h_mils) / (0.8 * w_mils + t_mils)
        
        if ln_arg <= 0:
            raise ValueError("Invalid trace geometry for microstrip calculation")
        
        impedance = (numerator / denominator) * math.log(ln_arg)
        return max(impedance, 0.0)
    
    def calculate_stripline_impedance(self, width_mm: float, layer_idx: int) -> float:
        """
        Calculate stripline impedance using IPC-2141 formula.
        
        Z₀ = (60 / √εᵣ) × ln(4h / (0.67πw + t))
        
        Parameters:
        - width_mm: Trace width in mm
        - layer_idx: Layer index
        
        Returns:
        - Characteristic impedance in ohms
        """
        if layer_idx >= len(self.stackup.layers):
            raise ValueError(f"Invalid layer index: {layer_idx}")
        
        layer = self.stackup.layers[layer_idx]
        
        # Find distance to nearest reference plane
        ref_plane = self.stackup.get_reference_plane(layer_idx)
        if ref_plane is None:
            raise ValueError(f"No reference plane found for layer {layer_idx}")
        
        # Calculate effective dielectric thickness
        h_mm = sum(self.stackup.layers[min(layer_idx, ref_plane):max(layer_idx, ref_plane)+1].thickness_mm 
                   for i in range(min(layer_idx, ref_plane), max(layer_idx, ref_plane)))
        h_mm = max(h_mm, 0.1)  # Minimum 0.1mm
        
        epsilon_r = 4.2  # Default
        
        # Convert to mils
        w_mils = UnitConverter.to_mils(width_mm, Unit.MM)
        h_mils = UnitConverter.to_mils(h_mm, Unit.MM)
        t_mils = UnitConverter.to_mils(layer.copper_thickness_mm, Unit.MM)
        
        # IPC-2141 stripline formula
        denominator = math.sqrt(epsilon_r)
        numerator = 60.0
        ln_arg = (4.0 * h_mils) / (0.67 * math.pi * w_mils + t_mils)
        
        if ln_arg <= 0:
            raise ValueError("Invalid trace geometry for stripline calculation")
        
        impedance = (numerator / denominator) * math.log(ln_arg)
        return max(impedance, 0.0)
    
    def calculate_differential_impedance(self, width_mm: float, spacing_mm: float,
                                         layer_idx: int, is_microstrip: bool = True) -> float:
        """
        Calculate differential pair impedance.
        
        Z_diff = 2 × Z₀ × (1 - 0.48 × e^(-0.96 × s/h))
        
        Parameters:
        - width_mm: Single trace width
        - spacing_mm: Spacing between traces
        - layer_idx: Layer index
        - is_microstrip: True for outer layer, False for inner
        
        Returns:
        - Differential impedance in ohms
        """
        if is_microstrip:
            z0 = self.calculate_microstrip_impedance(width_mm, layer_idx)
        else:
            z0 = self.calculate_stripline_impedance(width_mm, layer_idx)
        
        # Get dielectric thickness
        dielectric = self.stackup.get_dielectric_above(layer_idx)
        h_mm = dielectric.thickness_mm if dielectric else 0.2
        
        # Ratio s/h
        s_h = spacing_mm / h_mm
        
        # Differential impedance formula
        z_diff = 2 * z0 * (1 - 0.48 * math.exp(-0.96 * s_h))
        return max(z_diff, 0.0)
    
    def get_width_for_impedance(self, target_impedance: float, layer_idx: int,
                                is_differential: bool = False,
                                spacing_mm: float = 0.2) -> float:
        """
        Calculate required trace width for target impedance.
        
        Uses iterative bisection method to find width.
        
        Parameters:
        - target_impedance: Target impedance in ohms
        - layer_idx: Layer index
        - is_differential: True for differential pair
        - spacing_mm: Spacing for differential pair
        
        Returns:
        - Required trace width in mm
        """
        # Bisection search
        min_width = 0.05  # 50 microns
        max_width = 5.0   # 5 mm
        tolerance = 0.1   # 0.1 ohm tolerance
        
        for _ in range(50):  # Max iterations
            mid_width = (min_width + max_width) / 2
            
            if is_differential:
                impedance = self.calculate_differential_impedance(
                    mid_width, spacing_mm, layer_idx)
            else:
                impedance = self.calculate_microstrip_impedance(mid_width, layer_idx)
            
            if abs(impedance - target_impedance) < tolerance:
                return mid_width
            
            if impedance > target_impedance:
                min_width = mid_width
            else:
                max_width = mid_width
        
        return (min_width + max_width) / 2


# ============================================================================
# IPC-2152: Current Capacity Calculator
# ============================================================================

class CurrentCapacityCalculator:
    """
    Calculate current-carrying capacity per IPC-2152.
    
    I = k × ΔT^0.44 × A^0.725
    where k = 0.048 (external), 0.024 (internal)
    """
    
    def __init__(self, stackup: Stackup):
        self.stackup = stackup
    
    def calculate_current_capacity(self, width_mm: float, layer_idx: int,
                                   temp_rise_c: float = 20.0) -> float:
        """
        Calculate maximum current for a trace.
        
        Parameters:
        - width_mm: Trace width in mm
        - layer_idx: Layer index
        - temp_rise_c: Allowable temperature rise in °C
        
        Returns:
        - Maximum current in Amperes
        """
        if layer_idx >= len(self.stackup.layers):
            raise ValueError(f"Invalid layer index: {layer_idx}")
        
        layer = self.stackup.layers[layer_idx]
        
        # Determine if external or internal layer
        is_external = layer.is_external
        k = 0.048 if is_external else 0.024
        
        # Cross-sectional area in mils²
        width_mils = UnitConverter.to_mils(width_mm, Unit.MM)
        thickness_mils = UnitConverter.to_mils(layer.copper_thickness_mm, Unit.MM)
        area_mils2 = width_mils * thickness_mils
        
        # IPC-2152 formula
        current = k * (temp_rise_c ** 0.44) * (area_mils2 ** 0.725)
        return current
    
    def get_width_for_current(self, current_a: float, layer_idx: int,
                              temp_rise_c: float = 20.0) -> float:
        """
        Calculate minimum trace width for required current.
        
        Parameters:
        - current_a: Required current in Amperes
        - layer_idx: Layer index
        - temp_rise_c: Allowable temperature rise
        
        Returns:
        - Minimum trace width in mm
        """
        if layer_idx >= len(self.stackup.layers):
            raise ValueError(f"Invalid layer index: {layer_idx}")
        
        layer = self.stackup.layers[layer_idx]
        is_external = layer.is_external
        k = 0.048 if is_external else 0.024
        
        thickness_mils = UnitConverter.to_mils(layer.copper_thickness_mm, Unit.MM)
        
        # Rearrange IPC-2152 formula to solve for area
        # I = k × ΔT^0.44 × A^0.725
        # A = (I / (k × ΔT^0.44))^(1/0.725)
        area_mils2 = (current_a / (k * (temp_rise_c ** 0.44))) ** (1 / 0.725)
        
        # Width = Area / Thickness
        width_mils = area_mils2 / thickness_mils
        width_mm = UnitConverter.convert(width_mils, Unit.MILS, Unit.MM)
        
        return width_mm


# ============================================================================
# IPC-2221 / IEC 60950: Clearance Calculator
# ============================================================================

class ClearanceCalculator:
    """
    Calculate minimum clearances per IPC-2221 and IEC 60950.
    
    Considers:
    - Working voltage
    - Pollution degree
    - Material group
    - Altitude
    """
    
    POLLUTION_DEGREE_FACTORS = {
        1: 1.0,   # Clean environment
        2: 1.6,   # Normal office/industrial
        3: 2.5,   # Harsh environment
        4: 4.0,   # Conductive pollution
    }
    
    ALTITUDE_DERATING = {
        0: 1.0,      # Sea level to 3000m
        3000: 1.25,  # 3000-6000m
        6000: 1.6,   # Above 6000m
    }
    
    def __init__(self, design_rules: DesignRules):
        self.rules = design_rules
        self.pollution_degree = 2  # Default: normal environment
        self.altitude_m = 0  # Default: sea level
    
    def get_clearance_for_voltage(self, voltage_v: float, 
                                  pollution_degree: Optional[int] = None) -> float:
        """
        Calculate minimum clearance for working voltage.
        
        Parameters:
        - voltage_v: Working voltage (peak or DC)
        - pollution_degree: 1-4 (default from instance)
        
        Returns:
        - Minimum clearance in mm
        """
        pd = pollution_degree or self.pollution_degree
        pd_factor = self.POLLUTION_DEGREE_FACTORS.get(pd, 1.6)
        
        # Find base clearance from voltage table
        base_clearance = 0.1
        for volt_threshold, clearance in sorted(self.rules.clearance_by_voltage.items()):
            if voltage_v >= volt_threshold:
                base_clearance = clearance
            else:
                break
        
        # Apply pollution degree factor
        clearance = base_clearance * pd_factor
        
        # Apply altitude derating
        for alt_threshold, factor in sorted(self.ALTITUDE_DERATING.items()):
            if self.altitude_m >= alt_threshold:
                clearance *= factor
        
        return clearance
    
    def get_creepage_for_voltage(self, voltage_v: float,
                                 material_group: int = 2,
                                 pollution_degree: Optional[int] = None) -> float:
        """
        Calculate minimum creepage distance.
        
        Creepage is the surface distance, typically larger than clearance.
        
        Parameters:
        - voltage_v: Working voltage
        - material_group: 1, 2, or 3 (CTI rating)
        - pollution_degree: 1-4
        
        Returns:
        - Minimum creepage in mm
        """
        clearance = self.get_clearance_for_voltage(voltage_v, pollution_degree)
        
        # Material group factors (Comparative Tracking Index)
        mg_factors = {1: 1.0, 2: 1.6, 3: 2.5}
        mg_factor = mg_factors.get(material_group, 1.6)
        
        creepage = clearance * mg_factor
        return max(creepage, clearance)
    
    def validate_clearance(self, distance_mm: float, voltage1: float, 
                          voltage2: float, **kwargs) -> Tuple[bool, str]:
        """
        Validate if a clearance distance is sufficient.
        
        Parameters:
        - distance_mm: Actual distance between conductors
        - voltage1: Voltage on first conductor
        - voltage2: Voltage on second conductor
        - kwargs: Additional parameters (pollution_degree, etc.)
        
        Returns:
        - (is_valid, message)
        """
        voltage_diff = abs(voltage1 - voltage2)
        required = self.get_clearance_for_voltage(voltage_diff, **kwargs)
        
        if distance_mm >= required:
            return True, f"Clearance OK: {distance_mm:.3f}mm >= {required:.3f}mm required"
        else:
            margin = (distance_mm - required) / required * 100
            return False, f"Clearance VIOLATION: {distance_mm:.3f}mm < {required:.3f}mm required ({margin:.1f}% margin)"


# ============================================================================
# Utility Functions
# ============================================================================

def calculate_trace_resistance(length_mm: float, width_mm: float, 
                               copper_weight_oz: float, 
                               temperature_c: float = 20.0) -> float:
    """
    Calculate DC resistance of a trace.
    
    R = ρ × L / A
    
    Parameters:
    - length_mm: Trace length
    - width_mm: Trace width
    - copper_weight_oz: Copper weight in oz/ft²
    - temperature_c: Temperature in °C
    
    Returns:
    - Resistance in milliohms
    """
    # Copper resistivity at 20°C: 1.68e-8 Ω·m
    rho_20 = 1.68e-8
    
    # Temperature coefficient: 0.00393 per °C
    alpha = 0.00393
    rho = rho_20 * (1 + alpha * (temperature_c - 20))
    
    # Cross-sectional area
    thickness_mm = copper_weight_oz * 0.035
    area_m2 = (width_mm * 1e-3) * (thickness_mm * 1e-3)
    length_m = length_mm * 1e-3
    
    # Resistance
    resistance = rho * length_m / area_m2
    return resistance * 1000  # Convert to milliohms


def calculate_via_resistance(via: Via, temperature_c: float = 20.0) -> float:
    """
    Calculate DC resistance of a plated via.
    
    Parameters:
    - via: Via object
    - temperature_c: Temperature
    
    Returns:
    - Resistance in milliohms
    """
    # Plating thickness (assume 25 microns)
    plating_thickness_m = 25e-6
    
    # Via dimensions
    outer_radius_m = via.outer_diameter_mm / 2 / 1000
    inner_radius_m = via.inner_diameter_mm / 2 / 1000
    
    # Plating cross-section (annulus)
    if outer_radius_m > inner_radius_m:
        area_m2 = math.pi * (outer_radius_m**2 - inner_radius_m**2)
    else:
        # Solid via
        area_m2 = math.pi * outer_radius_m**2
    
    # Via length (assume through-board)
    length_m = 1.6e-3  # 1.6mm board
    
    # Copper resistivity
    rho = 1.68e-8 * (1 + 0.00393 * (temperature_c - 20))
    
    resistance = rho * length_m / area_m2
    return resistance * 1000  # milliohms


# Module exports
__all__ = [
    # Enums
    'Unit', 'LayerType',
    
    # Data classes
    'Coordinate', 'Coordinate3D',
    'DielectricMaterial', 'CopperMaterial',
    'Layer', 'Stackup',
    'Pad', 'Via', 'TraceSegment', 'Component',
    'Net', 'DifferentialPair', 'Netlist',
    'Route', 'DesignRules',
    
    # Calculators
    'UnitConverter',
    'ImpedanceCalculator',
    'CurrentCapacityCalculator',
    'ClearanceCalculator',
    
    # Utilities
    'calculate_trace_resistance',
    'calculate_via_resistance',
]
