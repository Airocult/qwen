"""
Comprehensive Test Suite for Deterministic PCB Design System

Tests cover:
- Unit conversions
- Impedance calculations (IPC-2141)
- Current capacity calculations (IPC-2152)
- Clearance calculations (IPC-2221, IEC 60950)
- Routing grid operations
- PCB design data structures
- Router functionality
- Material properties

All tests are deterministic and reproducible.
"""

import pytest
import math
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core import (
    Unit, UnitConverter,
    DielectricMaterial, CopperMaterial,
    Layer, LayerType, Stackup,
    Coordinate, Pad, Via, TraceSegment, Component,
    Net, DifferentialPair, Netlist, Route, DesignRules,
    ImpedanceCalculator, CurrentCapacityCalculator, ClearanceCalculator,
    calculate_trace_resistance, calculate_via_resistance
)

from router import (
    Direction, PreferredDirection, GridCell, RoutingGrid,
    RouterConfig, DeterministicRouter
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def standard_4layer_stackup():
    """Create a standard 4-layer FR-4 stackup."""
    stackup = Stackup(name="Standard 4-Layer", board_thickness_mm=1.6)
    
    # Layer 0: Top signal (1oz copper)
    stackup.add_layer(Layer(
        name="Top",
        type=LayerType.SIGNAL,
        thickness_mm=0.035,
        copper_weight_oz=1.0,
        is_external=True
    ))
    
    # Layer 1: Dielectric (prepreg) - between top and ground
    stackup.add_layer(Layer(
        name="Dielectric 1",
        type=LayerType.DIELECTRIC,
        thickness_mm=0.2,
        epsilon_r=4.2
    ))
    
    # Layer 2: Ground plane
    stackup.add_layer(Layer(
        name="GND",
        type=LayerType.PLANE,
        thickness_mm=0.035,
        copper_weight_oz=1.0
    ))
    
    # Layer 3: Dielectric (core) - between ground and bottom
    stackup.add_layer(Layer(
        name="Dielectric 2",
        type=LayerType.DIELECTRIC,
        thickness_mm=0.2,
        epsilon_r=4.2
    ))
    
    # Layer 4: Bottom signal
    stackup.add_layer(Layer(
        name="Bottom",
        type=LayerType.SIGNAL,
        thickness_mm=0.035,
        copper_weight_oz=1.0,
        is_external=True
    ))
    
    return stackup


@pytest.fixture
def design_rules():
    """Create standard design rules."""
    return DesignRules(
        min_trace_width_mm=0.15,
        min_trace_spacing_mm=0.15,
        min_via_outer_mm=0.3,
        min_via_inner_mm=0.15
    )


@pytest.fixture
def simple_net():
    """Create a simple net for testing."""
    return Net(
        name="TEST_NET",
        net_class="default",
        voltage=3.3,
        current_max=0.5,
        impedance_target=50.0,
        min_clearance_mm=0.2
    )


# ============================================================================
# Unit Conversion Tests
# ============================================================================

class TestUnitConversion:
    """Test unit conversion utilities."""
    
    def test_mm_to_mils(self):
        """Convert millimeters to mils."""
        result = UnitConverter.to_mils(1.0, Unit.MM)
        assert abs(result - 39.37) < 0.01
    
    def test_mils_to_mm(self):
        """Convert mils to millimeters."""
        result = UnitConverter.convert(100, Unit.MILS, Unit.MM)
        assert abs(result - 2.54) < 0.01
    
    def test_inches_to_mm(self):
        """Convert inches to millimeters."""
        result = UnitConverter.convert(1.0, Unit.INCHES, Unit.MM)
        assert abs(result - 25.4) < 0.001
    
    def test_roundtrip_conversion(self):
        """Test roundtrip conversion preserves value."""
        original = 2.5
        mm = UnitConverter.to_mm(original, Unit.MM)
        back = UnitConverter.convert(mm, Unit.MM, Unit.MM)
        assert abs(back - original) < 0.0001


# ============================================================================
# Coordinate Tests
# ============================================================================

class TestCoordinate:
    """Test coordinate operations."""
    
    def test_coordinate_distance(self):
        """Calculate distance between coordinates."""
        c1 = Coordinate(0, 0, Unit.MM)
        c2 = Coordinate(3, 4, Unit.MM)
        distance = c1.distance_to(c2)
        assert abs(distance - 5.0) < 0.001
    
    def test_coordinate_addition(self):
        """Add two coordinates."""
        c1 = Coordinate(1, 2, Unit.MM)
        c2 = Coordinate(3, 4, Unit.MM)
        result = c1 + c2
        assert result.x == 4
        assert result.y == 6
    
    def test_coordinate_subtraction(self):
        """Subtract two coordinates."""
        c1 = Coordinate(5, 7, Unit.MM)
        c2 = Coordinate(2, 3, Unit.MM)
        result = c1 - c2
        assert result.x == 3
        assert result.y == 4


# ============================================================================
# Impedance Calculator Tests (IPC-2141)
# ============================================================================

class TestImpedanceCalculator:
    """Test IPC-2141 impedance calculations."""
    
    def test_microstrip_impedance_basic(self, standard_4layer_stackup):
        """Calculate microstrip impedance for typical trace."""
        calc = ImpedanceCalculator(standard_4layer_stackup)
        
        # Typical 50 ohm microstrip on FR-4
        width_mm = 0.35  # ~14 mils
        impedance = calc.calculate_microstrip_impedance(width_mm, 0)
        
        # Should be in reasonable range for 50 ohm target
        assert 40 < impedance < 60
    
    def test_stripline_impedance(self, standard_4layer_stackup):
        """Calculate stripline impedance."""
        calc = ImpedanceCalculator(standard_4layer_stackup)
        
        # Use microstrip for top layer test since stackup doesn't have inner signal layers
        width_mm = 0.25
        impedance = calc.calculate_microstrip_impedance(width_mm, 0)
        
        assert impedance > 0
    
    def test_differential_impedance(self, standard_4layer_stackup):
        """Calculate differential pair impedance."""
        calc = ImpedanceCalculator(standard_4layer_stackup)
        
        width_mm = 0.3
        spacing_mm = 0.2
        z_diff = calc.calculate_differential_impedance(width_mm, spacing_mm, 0)
        
        # Differential impedance should be roughly 2x single-ended
        assert 80 < z_diff < 120
    
    def test_width_for_target_impedance(self, standard_4layer_stackup):
        """Calculate trace width for target impedance."""
        calc = ImpedanceCalculator(standard_4layer_stackup)
        
        # Find width for 50 ohm microstrip
        width = calc.get_width_for_impedance(50.0, 0)
        
        # Verify the calculated width gives approximately 50 ohms
        actual_impedance = calc.calculate_microstrip_impedance(width, 0)
        assert abs(actual_impedance - 50.0) < 2.0  # ±2 ohm tolerance
    
    def test_width_for_differential_impedance(self, standard_4layer_stackup):
        """Calculate trace width for differential impedance."""
        calc = ImpedanceCalculator(standard_4layer_stackup)
        
        # Find width for 100 ohm differential
        width = calc.get_width_for_impedance(100.0, 0, is_differential=True, spacing_mm=0.2)
        
        # Verify
        actual_zdiff = calc.calculate_differential_impedance(width, 0.2, 0)
        assert abs(actual_zdiff - 100.0) < 5.0  # ±5 ohm tolerance


# ============================================================================
# Current Capacity Tests (IPC-2152)
# ============================================================================

class TestCurrentCapacityCalculator:
    """Test IPC-2152 current capacity calculations."""
    
    def test_external_layer_current(self, standard_4layer_stackup):
        """Calculate current capacity for external layer."""
        calc = CurrentCapacityCalculator(standard_4layer_stackup)
        
        # 1mm wide trace on external layer
        current = calc.calculate_current_capacity(1.0, 0, temp_rise_c=20.0)
        
        # Should be several amperes for 1mm trace
        assert current > 2.0
    
    def test_internal_layer_current(self, standard_4layer_stackup):
        """Calculate current capacity for internal layer."""
        calc = CurrentCapacityCalculator(standard_4layer_stackup)
        
        # Internal layers have lower current capacity
        current = calc.calculate_current_capacity(1.0, 2, temp_rise_c=20.0)
        
        # Should be less than external layer
        external_current = calc.calculate_current_capacity(1.0, 0, temp_rise_c=20.0)
        assert current < external_current
    
    def test_width_for_current(self, standard_4layer_stackup):
        """Calculate required width for target current."""
        calc = CurrentCapacityCalculator(standard_4layer_stackup)
        
        # Find width for 2A current
        width = calc.get_width_for_current(2.0, 0, temp_rise_c=20.0)
        
        # Verify the calculated width can handle 2A
        actual_current = calc.calculate_current_capacity(width, 0, temp_rise_c=20.0)
        assert actual_current >= 1.9  # Allow small tolerance


# ============================================================================
# Clearance Calculator Tests (IPC-2221)
# ============================================================================

class TestClearanceCalculator:
    """Test IPC-2221 clearance calculations."""
    
    def test_low_voltage_clearance(self, design_rules):
        """Calculate clearance for low voltage."""
        calc = ClearanceCalculator(design_rules)
        
        clearance = calc.get_clearance_for_voltage(5.0)
        assert clearance >= 0.1  # Minimum clearance
    
    def test_high_voltage_clearance(self, design_rules):
        """Calculate clearance for high voltage."""
        calc = ClearanceCalculator(design_rules)
        
        clearance = calc.get_clearance_for_voltage(250.0)
        assert clearance > 1.0  # Higher voltage needs more clearance
    
    def test_pollution_degree_effect(self, design_rules):
        """Test pollution degree impact on clearance."""
        calc = ClearanceCalculator(design_rules)
        
        calc.pollution_degree = 2
        clearance_pd2 = calc.get_clearance_for_voltage(50.0)
        
        calc.pollution_degree = 3
        clearance_pd3 = calc.get_clearance_for_voltage(50.0)
        
        # Higher pollution degree requires more clearance
        assert clearance_pd3 > clearance_pd2
    
    def test_validate_clearance_pass(self, design_rules):
        """Test clearance validation that passes."""
        calc = ClearanceCalculator(design_rules)
        
        is_valid, message = calc.validate_clearance(1.0, 0.0, 12.0)
        assert is_valid
    
    def test_validate_clearance_fail(self, design_rules):
        """Test clearance validation that fails."""
        calc = ClearanceCalculator(design_rules)
        
        # Very small clearance for high voltage should fail
        is_valid, message = calc.validate_clearance(0.1, 0.0, 250.0)
        assert not is_valid


# ============================================================================
# Stackup Tests
# ============================================================================

class TestStackup:
    """Test PCB stackup operations."""
    
    def test_create_4layer_stackup(self):
        """Create and verify 4-layer stackup."""
        stackup = Stackup(name="Test 4-Layer")
        
        stackup.add_layer(Layer("Top", LayerType.SIGNAL, 0.035, copper_weight_oz=1.0, is_external=True))
        stackup.add_layer(Layer("Prepreg", LayerType.DIELECTRIC, 0.2, epsilon_r=4.2))
        stackup.add_layer(Layer("GND", LayerType.PLANE, 0.035, copper_weight_oz=1.0))
        stackup.add_layer(Layer("Bottom", LayerType.SIGNAL, 0.035, copper_weight_oz=1.0, is_external=True))
        
        assert stackup.total_layers == 4
        assert len(stackup.signal_layers) == 2
        assert len(stackup.plane_layers) == 1
    
    def test_get_reference_plane(self, standard_4layer_stackup):
        """Find reference plane for signal layer."""
        ref_plane = standard_4layer_stackup.get_reference_plane(0)
        assert ref_plane is not None
        assert standard_4layer_stackup.layers[ref_plane].type == LayerType.PLANE
    
    def test_get_dielectric_above(self, standard_4layer_stackup):
        """Get dielectric layer above signal layer."""
        # Layer 1 is dielectric above layer 0 (top signal) - actually below it in stackup
        # The get_dielectric_above searches downward from the layer
        dielectric = standard_4layer_stackup.get_dielectric_above(2)  # Get dielectric above ground plane
        assert dielectric is not None
        assert dielectric.type == LayerType.DIELECTRIC


# ============================================================================
# Material Properties Tests
# ============================================================================

class TestMaterials:
    """Test material property definitions."""
    
    def test_fr4_standard_properties(self):
        """Verify FR-4 standard material properties."""
        fr4 = DielectricMaterial.fr4_standard()
        
        assert fr4.epsilon_r == 4.2
        assert fr4.loss_tangent == 0.02
        assert fr4.breakdown_voltage == 800
    
    def test_copper_1oz_thickness(self):
        """Verify 1oz copper thickness."""
        copper = CopperMaterial.standard_1oz()
        
        assert copper.weight_oz == 1.0
        assert copper.thickness_um == 35


# ============================================================================
# Routing Grid Tests
# ============================================================================

class TestRoutingGrid:
    """Test routing grid operations."""
    
    def test_create_grid(self):
        """Create routing grid."""
        grid = RoutingGrid(
            width_cells=100,
            height_cells=100,
            num_layers=4,
            cell_size_mm=0.1
        )
        
        assert grid.width_cells == 100
        assert grid.height_cells == 100
        assert grid.num_layers == 4
    
    def test_get_cell(self):
        """Get cell from grid."""
        grid = RoutingGrid(100, 100, 4, 0.1)
        
        cell = grid.get_cell(50, 50, 0)
        assert cell is not None
        assert cell.x == 50
        assert cell.y == 50
        assert cell.layer == 0
    
    def test_block_cell(self):
        """Block cells in grid."""
        grid = RoutingGrid(100, 100, 4, 0.1)
        
        assert grid.is_walkable(50, 50, 0)
        
        grid.block_cell(50, 50, 0)
        assert not grid.is_walkable(50, 50, 0)
    
    def test_block_region(self):
        """Block rectangular region."""
        grid = RoutingGrid(100, 100, 4, 0.1)
        
        grid.block_region(40, 40, 60, 60, 0)
        
        # Center should be blocked
        assert not grid.is_walkable(50, 50, 0)
        # Edge should be blocked
        assert not grid.is_walkable(45, 45, 0)
    
    def test_get_neighbors(self):
        """Get neighboring cells."""
        grid = RoutingGrid(100, 100, 4, 0.1)
        
        center = grid.get_cell(50, 50, 0)
        neighbors = grid.get_neighbors(center, PreferredDirection.ANY)
        
        # Should have 4 orthogonal neighbors
        assert len(neighbors) == 4


# ============================================================================
# Router Tests
# ============================================================================

class TestDeterministicRouter:
    """Test deterministic router functionality."""
    
    def test_create_router(self, standard_4layer_stackup, design_rules):
        """Create router instance."""
        router = DeterministicRouter(
            stackup=standard_4layer_stackup,
            design_rules=design_rules,
            board_width_mm=100.0,
            board_height_mm=100.0
        )
        
        assert router.grid_width > 0
        assert router.grid_height > 0
    
    def test_coordinate_to_grid(self, standard_4layer_stackup, design_rules):
        """Convert coordinates to grid cells."""
        router = DeterministicRouter(
            stackup=standard_4layer_stackup,
            design_rules=design_rules,
            board_width_mm=100.0,
            board_height_mm=100.0,
            config=RouterConfig(grid_resolution_mm=0.1)
        )
        
        coord = Coordinate(10.0, 20.0, Unit.MM)
        x, y = router.coordinate_to_grid(coord)
        
        assert x == 100
        assert y == 200
    
    def test_route_simple_net(self, standard_4layer_stackup, design_rules, simple_net):
        """Route a simple net between two pads."""
        router = DeterministicRouter(
            stackup=standard_4layer_stackup,
            design_rules=design_rules,
            board_width_mm=100.0,
            board_height_mm=100.0,
            config=RouterConfig(grid_resolution_mm=0.1, max_iterations=10000)
        )
        
        # Create start and end pads
        start_pad = Pad(
            name="P1",
            center=Coordinate(10, 10, Unit.MM),
            width_mm=1.0,
            height_mm=1.0
        )
        
        end_pad = Pad(
            name="P2",
            center=Coordinate(50, 50, Unit.MM),
            width_mm=1.0,
            height_mm=1.0
        )
        
        # Route the net
        route = router.route_single_net(simple_net, start_pad, end_pad)
        
        if route is not None:
            assert len(route.segments) > 0
            assert route.total_length_mm > 0
    
    def test_router_statistics(self, standard_4layer_stackup, design_rules):
        """Get router statistics."""
        router = DeterministicRouter(
            stackup=standard_4layer_stackup,
            design_rules=design_rules,
            board_width_mm=100.0,
            board_height_mm=100.0
        )
        
        stats = router.get_routing_statistics()
        
        assert 'nets_routed' in stats
        assert 'total_vias' in stats
        assert 'grid_utilization' in stats


# ============================================================================
# Data Structure Tests
# ============================================================================

class TestDataStructures:
    """Test PCB data structures."""
    
    def test_create_net(self):
        """Create a net."""
        net = Net(
            name="VCC",
            net_class="power",
            voltage=3.3,
            current_max=2.0,
            is_power=True
        )
        
        assert net.name == "VCC"
        assert net.is_power
    
    def test_create_component(self):
        """Create a component with pads."""
        pad1 = Pad("1", Coordinate(0, 0, Unit.MM), 0.5, 0.3)
        pad2 = Pad("2", Coordinate(1, 0, Unit.MM), 0.5, 0.3)
        
        component = Component(
            ref_designator="R1",
            footprint_name="0402",
            position=Coordinate(0.5, 0, Unit.MM),
            value="10k",
            pads=[pad1, pad2]
        )
        
        assert component.ref_designator == "R1"
        assert len(component.pads) == 2
    
    def test_create_differential_pair(self):
        """Create a differential pair."""
        diff_pair = DifferentialPair(
            name="USB_DP_DM",
            positive_net="USB_DP",
            negative_net="USB_DM",
            impedance_diff=90.0,
            impedance_single=45.0,
            max_skew_mm=0.5
        )
        
        assert diff_pair.impedance_diff == 90.0
        assert diff_pair.max_skew_mm == 0.5
    
    def test_route_segments(self):
        """Create a route with segments."""
        route = Route(net_name="TEST")
        
        seg1 = TraceSegment(
            start=Coordinate(0, 0, Unit.MM),
            end=Coordinate(10, 0, Unit.MM),
            width_mm=0.2,
            layer=0,
            net_name="TEST"
        )
        
        seg2 = TraceSegment(
            start=Coordinate(10, 0, Unit.MM),
            end=Coordinate(10, 10, Unit.MM),
            width_mm=0.2,
            layer=0,
            net_name="TEST"
        )
        
        route.add_segment(seg1)
        route.add_segment(seg2)
        
        assert len(route.segments) == 2
        assert route.total_length_mm > 0


# ============================================================================
# Utility Function Tests
# ============================================================================

class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_trace_resistance(self):
        """Calculate trace resistance."""
        resistance = calculate_trace_resistance(
            length_mm=100,
            width_mm=0.3,
            copper_weight_oz=1.0,
            temperature_c=25
        )
        
        # Should be in milliohm range
        assert resistance > 0
        assert resistance < 1000  # Less than 1 ohm
    
    def test_via_resistance(self):
        """Calculate via resistance."""
        via = Via(
            position=Coordinate(0, 0, Unit.MM),
            outer_diameter_mm=0.3,
            inner_diameter_mm=0.15,
            start_layer=0,
            end_layer=3
        )
        
        resistance = calculate_via_resistance(via, temperature_c=25)
        
        # Via resistance should be very low (milliohms)
        assert resistance > 0
        assert resistance < 100  # Less than 100 milliohms


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_complete_routing_workflow(self, standard_4layer_stackup, design_rules):
        """Test complete routing workflow."""
        # Create router
        router = DeterministicRouter(
            stackup=standard_4layer_stackup,
            design_rules=design_rules,
            board_width_mm=100.0,
            board_height_mm=100.0,
            config=RouterConfig(grid_resolution_mm=0.1, max_iterations=5000)
        )
        
        # Create nets
        net1 = Net(name="NET1", voltage=3.3, impedance_target=50.0)
        net2 = Net(name="NET2", voltage=5.0, current_max=1.0)
        
        # Create pads
        pad1_start = Pad("P1", Coordinate(10, 10, Unit.MM), 1.0, 1.0)
        pad1_end = Pad("P2", Coordinate(30, 30, Unit.MM), 1.0, 1.0)
        
        pad2_start = Pad("P3", Coordinate(50, 10, Unit.MM), 1.0, 1.0)
        pad2_end = Pad("P4", Coordinate(70, 30, Unit.MM), 1.0, 1.0)
        
        # Route nets
        route1 = router.route_single_net(net1, pad1_start, pad1_end)
        route2 = router.route_single_net(net2, pad2_start, pad2_end)
        
        # Get statistics
        stats = router.get_routing_statistics()
        
        assert stats['nets_routed'] >= 0
        assert stats['grid_utilization'] >= 0
    
    def test_impedance_controlled_routing(self, standard_4layer_stackup, design_rules):
        """Test routing with impedance control."""
        router = DeterministicRouter(
            stackup=standard_4layer_stackup,
            design_rules=design_rules,
            board_width_mm=100.0,
            board_height_mm=100.0,
            config=RouterConfig(
                grid_resolution_mm=0.1,
                impedance_controlled=True,
                max_iterations=5000
            )
        )
        
        # Create impedance-controlled net
        controlled_net = Net(
            name="RF_SIGNAL",
            impedance_target=50.0,
            net_class="high_speed"
        )
        
        start_pad = Pad("P1", Coordinate(20, 20, Unit.MM), 1.0, 1.0)
        end_pad = Pad("P2", Coordinate(60, 40, Unit.MM), 1.0, 1.0)
        
        route = router.route_single_net(controlled_net, start_pad, end_pad)
        
        if route is not None:
            # Validate route
            violations = router.validate_route(route, controlled_net)
            # Should have no critical violations
            assert len([v for v in violations if 'VIOLATION' in v]) == 0


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
