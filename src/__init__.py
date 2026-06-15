"""
Deterministic PCB Design System - Main Package

This package provides a complete deterministic PCB design automation system
that transforms schematics into production-ready Gerber files while strictly
adhering to all electrical, mechanical, and manufacturing rules.

Key Features:
- IPC-compliant impedance calculations (IPC-2141)
- Current capacity analysis (IPC-2152)
- Clearance validation (IPC-2221, IEC 60950)
- Deterministic A* maze routing
- Differential pair routing with length matching
- Via optimization
- Grid-based congestion management

Usage Example:
    from src.core import Stackup, Layer, LayerType, DesignRules, Net, Pad, Coordinate
    from src.router import DeterministicRouter, RouterConfig
    
    # Create stackup
    stackup = Stackup(name="4-Layer")
    stackup.add_layer(Layer("Top", LayerType.SIGNAL, 0.035, copper_weight_oz=1.0))
    stackup.add_layer(Layer("Dielectric", LayerType.DIELECTRIC, 0.2, epsilon_r=4.2))
    stackup.add_layer(Layer("GND", LayerType.PLANE, 0.035, copper_weight_oz=1.0))
    stackup.add_layer(Layer("Bottom", LayerType.SIGNAL, 0.035, copper_weight_oz=1.0))
    
    # Create router
    router = DeterministicRouter(
        stackup=stackup,
        design_rules=DesignRules(),
        board_width_mm=100.0,
        board_height_mm=100.0
    )
    
    # Route nets
    net = Net(name="SIGNAL", impedance_target=50.0)
    start_pad = Pad("P1", Coordinate(10, 10), 1.0, 1.0)
    end_pad = Pad("P2", Coordinate(50, 50), 1.0, 1.0)
    route = router.route_single_net(net, start_pad, end_pad)
"""

from .core import (
    # Enums
    Unit,
    LayerType,
    
    # Data Classes
    Coordinate,
    Coordinate3D,
    DielectricMaterial,
    CopperMaterial,
    Layer,
    Stackup,
    Pad,
    Via,
    TraceSegment,
    Component,
    Net,
    DifferentialPair,
    Netlist,
    Route,
    DesignRules,
    
    # Calculators
    UnitConverter,
    ImpedanceCalculator,
    CurrentCapacityCalculator,
    ClearanceCalculator,
    
    # Utilities
    calculate_trace_resistance,
    calculate_via_resistance,
)

from .router import (
    Direction,
    PreferredDirection,
    GridCell,
    RoutingGrid,
    RouterConfig,
    DeterministicRouter,
)

__version__ = "1.0.0"
__author__ = "PCB Design System Team"
__license__ = "MIT"

__all__ = [
    # Version
    '__version__',
    
    # Enums
    'Unit',
    'LayerType',
    'Direction',
    'PreferredDirection',
    
    # Core Data Classes
    'Coordinate',
    'Coordinate3D',
    'DielectricMaterial',
    'CopperMaterial',
    'Layer',
    'Stackup',
    'Pad',
    'Via',
    'TraceSegment',
    'Component',
    'Net',
    'DifferentialPair',
    'Netlist',
    'Route',
    'DesignRules',
    
    # Calculators
    'UnitConverter',
    'ImpedanceCalculator',
    'CurrentCapacityCalculator',
    'ClearanceCalculator',
    
    # Router
    'GridCell',
    'RoutingGrid',
    'RouterConfig',
    'DeterministicRouter',
    
    # Utilities
    'calculate_trace_resistance',
    'calculate_via_resistance',
]
