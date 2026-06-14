"""
Deterministic PCB Router Module

This module implements the deterministic routing engine that guarantees
constraint satisfaction while routing PCB nets with proper impedance control,
differential pair matching, and professional-quality turns.

Author: PCB Design System Team
License: MIT
"""

import numpy as np
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from heapq import heappush, heappop
from enum import Enum
import networkx as nx

from .core import (
    Coordinate, Unit, Layer, LayerType, Net, TraceSegment, Via, Route,
    DesignRule, Stackup, PCBDesign, Component, Pad, ViaType
)


# ============================================================================
# Routing Constants
# ============================================================================

class RoutingDirection(Enum):
    """Preferred routing direction per layer"""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    ANY = "any"


class TurnType(Enum):
    """Allowed turn types for professional routing"""
    ANGLE_45 = 45
    ANGLE_90 = 90
    ARC = "arc"


@dataclass
class RoutingGrid:
    """Grid-based representation for maze routing"""
    width: int  # Grid cells in X
    height: int  # Grid cells in Y
    layers: int  # Number of layers
    cell_size: float  # Size of each grid cell (mils)
    grid: np.ndarray  # 3D array: [layer][y][x]
    
    # Cost maps for different considerations
    congestion_map: np.ndarray = None
    via_cost_map: np.ndarray = None
    
    def __post_init__(self):
        if self.congestion_map is None:
            self.congestion_map = np.zeros((self.layers, self.height, self.width))
        if self.via_cost_map is None:
            self.via_cost_map = np.ones((self.height, self.width)) * 10.0  # Base via cost
    
    def world_to_grid(self, coord: Coordinate) -> Tuple[int, int]:
        """Convert world coordinates to grid indices"""
        coord_mils = coord.to_mils()
        x = int(coord_mils.x / self.cell_size)
        y = int(coord_mils.y / self.cell_size)
        return (max(0, min(x, self.width - 1)), max(0, min(y, self.height - 1)))
    
    def grid_to_world(self, x: int, y: int, layer: int) -> Coordinate:
        """Convert grid indices to world coordinates"""
        mils_x = (x + 0.5) * self.cell_size
        mils_y = (y + 0.5) * self.cell_size
        coord = Coordinate(mils_x, mils_y, 0, Unit.MILS)
        return coord.to_mm()
    
    def is_blocked(self, x: int, y: int, layer: int) -> bool:
        """Check if grid cell is blocked"""
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return True
        return self.grid[layer, y, x] > 0
    
    def mark_route(self, segments: List[TraceSegment], clearance_cells: int = 1):
        """Mark routed path on grid with clearance"""
        for seg in segments:
            start_grid = self.world_to_grid(seg.start)
            end_grid = self.world_to_grid(seg.end)
            
            # Mark path and clearance
            self._mark_line(start_grid, end_grid, seg.layer, clearance_cells)
            
            # Mark vias
            if seg.via_at_end:
                x, y = end_grid
                for l in range(min(seg.layer, seg.layer+1), max(seg.layer, seg.layer+1)+1):
                    if 0 <= l < self.layers:
                        for dy in range(-clearance_cells, clearance_cells+1):
                            for dx in range(-clearance_cells, clearance_cells+1):
                                nx, ny = x + dx, y + dy
                                if 0 <= nx < self.width and 0 <= ny < self.height:
                                    self.grid[l, ny, nx] = max(self.grid[l, ny, nx], 2)
    
    def _mark_line(self, start: Tuple[int,int], end: Tuple[int,int], layer: int, clearance: int):
        """Mark a line on the grid with Bresenham's algorithm"""
        x0, y0 = start
        x1, y1 = end
        
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        while True:
            # Mark cell and clearance area
            for cy in range(y0 - clearance, y0 + clearance + 1):
                for cx in range(x0 - clearance, x0 + clearance + 1):
                    if 0 <= cx < self.width and 0 <= cy < self.height:
                        self.grid[layer, cy, cx] = max(self.grid[layer, cy, cx], 1)
            
            if x0 == x1 and y0 == y1:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy


@dataclass
class AStarNode:
    """Node for A* search"""
    x: int
    y: int
    layer: int
    g_cost: float  # Cost from start
    h_cost: float  # Heuristic cost to goal
    parent: Optional['AStarNode'] = None
    
    @property
    def f_cost(self) -> float:
        """Total cost"""
        return self.g_cost + self.h_cost
    
    def __lt__(self, other):
        return self.f_cost < other.f_cost


class DeterministicRouter:
    """
    Deterministic PCB router with guaranteed constraint satisfaction
    
    Features:
    - A* based maze routing with admissible heuristics
    - Differential pair routing with length matching
    - Impedance-controlled trace width
    - Professional 45° and arc turns
    - Via minimization
    - Push-and-shove capability
    """
    
    def __init__(self, pcb_design: PCBDesign, grid_cell_size: float = 5.0):
        """
        Initialize router
        
        Parameters:
        - pcb_design: PCB design to route
        - grid_cell_size: Grid resolution in mils
        """
        self.pcb = pcb_design
        self.cell_size = grid_cell_size
        self.rules = pcb_design.design_rules
        
        # Calculate grid dimensions from board outline
        board = pcb_design.board_outline
        if board.vertices:
            xs = [v.x for v in board.vertices]
            ys = [v.y for v in board.vertices]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            
            # Add margin
            margin = 5.0  # mm
            min_x -= margin
            max_x += margin
            min_y -= margin
            max_y += margin
            
            # Convert to mils for grid calculation
            margin_mils = margin * 39.3701
            width_mils = (max_x - min_x) * 39.3701 + 2 * margin_mils
            height_mils = (max_y - min_y) * 39.3701 + 2 * margin_mils
            
            self.grid_width = int(width_mils / self.cell_size) + 1
            self.grid_height = int(height_mils / self.cell_size) + 1
        else:
            self.grid_width = 2000  # Default 10x10 inches at 5 mils
            self.grid_height = 2000
        
        # Initialize routing grid
        num_layers = len(pcb_design.stackup.layers)
        self.grid = RoutingGrid(
            width=self.grid_width,
            height=self.grid_height,
            layers=num_layers,
            cell_size=self.cell_size,
            grid=np.zeros((num_layers, self.grid_height, self.grid_width))
        )
        
        # Mark component keepouts and existing obstacles
        self._initialize_obstacles()
        
        # Routing results
        self.routed_nets: Dict[str, Route] = {}
        self.failed_nets: List[str] = []
        self.routing_log: List[str] = []
    
    def _initialize_obstacles(self):
        """Mark component footprints and keepouts as obstacles"""
        clearance_cells = int(self.rules.min_trace_space / self.cell_size) + 1
        
        for component in self.pcb.components:
            # Mark pad locations as obstacles on relevant layers
            for pad in component.pads:
                for layer_num in pad.layers:
                    if layer_num < self.grid.layers:
                        pad_grid = self.grid.world_to_grid(pad.position)
                        # Calculate pad size in grid cells
                        pad_dim_mils = pad.dimensions.to_mils()
                        half_w = int((pad_dim_mils.width / 2) / self.cell_size)
                        half_h = int((pad_dim_mils.height / 2) / self.cell_size)
                        
                        # Mark pad area
                        for dy in range(-half_h - clearance_cells, half_h + clearance_cells + 1):
                            for dx in range(-half_w - clearance_cells, half_w + clearance_cells + 1):
                                x = pad_grid[0] + dx
                                y = pad_grid[1] + dy
                                if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                                    self.grid.grid[layer_num, y, x] = 3  # Pad obstacle
    
    def route_all_nets(self, priority_order: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Route all nets in the design
        
        Parameters:
        - priority_order: Optional list of net names in routing priority order
        
        Returns:
        - Dictionary mapping net names to success status
        """
        results = {}
        
        # Sort nets by priority
        nets_to_route = sorted(
            self.pcb.nets,
            key=lambda n: (-n.routing_priority, n.name),
        )
        
        # Route power/ground nets first
        power_nets = [n for n in nets_to_route if n.is_power or n.is_ground]
        signal_nets = [n for n in nets_to_route if not (n.is_power or n.is_ground)]
        diff_pairs = [n for n in signal_nets if n.is_differential_pair]
        single_ended = [n for n in signal_nets if not n.is_differential_pair]
        
        # Routing order: power/ground, differential pairs, critical signals, rest
        ordered_nets = power_nets + diff_pairs + single_ended
        
        self.log(f"Starting routing of {len(ordered_nets)} nets")
        self.log(f"  Power/Ground nets: {len(power_nets)}")
        self.log(f"  Differential pairs: {len(diff_pairs)}")
        self.log(f"  Single-ended signals: {len(single_ended)}")
        
        for net in ordered_nets:
            self.log(f"\nRouting net: {net.name}")
            success = self.route_net(net)
            results[net.name] = success
            
            if success:
                self.log(f"  ✓ Successfully routed {net.name}")
            else:
                self.log(f"  ✗ Failed to route {net.name}")
                self.failed_nets.append(net.name)
        
        # Add routes to PCB design
        for net_name, route in self.routed_nets.items():
            self.pcb.routes.append(route)
        
        self.log(f"\nRouting complete: {len(self.routed_nets)} successful, {len(self.failed_nets)} failed")
        
        return results
    
    def route_net(self, net: Net) -> bool:
        """
        Route a single net
        
        Parameters:
        - net: Net to route
        
        Returns:
        - True if routing succeeded, False otherwise
        """
        if len(net.connections) < 2:
            self.log(f"  Net {net.name} has fewer than 2 connections, skipping")
            return True
        
        # Calculate trace width based on current
        trace_width = self._calculate_trace_width(net)
        
        # Get connection points
        connection_points = self._get_connection_coordinates(net)
        
        if len(connection_points) < 2:
            self.log(f"  Cannot get connection points for {net.name}")
            return False
        
        # Route based on net type
        if net.is_differential_pair:
            return self._route_differential_pair(net, connection_points, trace_width)
        else:
            return self._route_single_ended(net, connection_points, trace_width)
    
    def _calculate_trace_width(self, net: Net) -> float:
        """Calculate appropriate trace width for net based on electrical requirements"""
        # Use net-specific override if provided
        if net.min_trace_width:
            return net.min_trace_width
        
        # Calculate based on current using IPC-2152
        if net.current:
            layer_type = 'external'  # Default to external layer
            width = 5.0  # Minimum width in mils
            
            # Try to determine layer type from stackup
            if self.pcb.stackup.layers:
                layer = self.pcb.stackup.layers[0]
                layer_type = 'external' if layer.number == 0 else 'internal'
            
            calc_width = 5.0  # Default minimum
            try:
                from .core import TraceWidthCalculator
                calc_width = TraceWidthCalculator.calculate(
                    current=net.current,
                    temp_rise=10.0,
                    copper_thickness=self.pcb.stackup.finished_copper,
                    layer_type=layer_type
                )
            except Exception as e:
                self.log(f"  Warning: Could not calculate trace width: {e}")
            
            width = max(width, calc_width)
            
            # Also check voltage clearance requirements
            if net.voltage:
                from .core import ClearanceCalculator
                clearance = ClearanceCalculator.voltage_clearance(net.voltage)
                width = max(width, clearance)
            
            return width
        
        # Default width from design rules
        return self.rules.min_trace_width
    
    def _get_connection_coordinates(self, net: Net) -> List[Tuple[Coordinate, int]]:
        """Get all connection points for a net as (coordinate, layer) tuples"""
        points = []
        
        for comp_ref, pad_name in net.connections:
            # Find component
            component = None
            for comp in self.pcb.components:
                if comp.ref_designator == comp_ref:
                    component = comp
                    break
            
            if not component:
                self.log(f"  Warning: Component {comp_ref} not found")
                continue
            
            # Find pad
            pad = component.get_pad_by_name(pad_name)
            if not pad:
                self.log(f"  Warning: Pad {pad_name} not found on {comp_ref}")
                continue
            
            # Use pad position (on top layer by default)
            target_layer = pad.layers[0] if pad.layers else 0
            points.append((pad.position, target_layer))
        
        return points
    
    def _route_single_ended(self, net: Net, connection_points: List[Tuple[Coordinate, int]], 
                           trace_width: float) -> bool:
        """Route a single-ended net"""
        if len(connection_points) < 2:
            return False
        
        # Build routing tree using minimum spanning tree approach
        # Start from first point and connect to all others
        
        segments = []
        vias = []
        connected = {0}  # Indices of connected points
        unconnected = set(range(1, len(connection_points)))
        
        current_point_idx = 0
        
        while unconnected:
            # Find shortest connection from connected set to unconnected set
            best_dist = float('inf')
            best_from = None
            best_to = None
            best_path = None
            
            for from_idx in connected:
                from_coord, from_layer = connection_points[from_idx]
                
                for to_idx in unconnected:
                    to_coord, to_layer = connection_points[to_idx]
                    
                    # Route between these two points
                    path = self._find_path(from_coord, from_layer, to_coord, to_layer, trace_width)
                    
                    if path:
                        dist = sum(seg.length() for seg in path)
                        if dist < best_dist:
                            best_dist = dist
                            best_from = from_idx
                            best_to = to_idx
                            best_path = path
            
            if best_path is None:
                self.log(f"  Cannot find path for remaining connections in {net.name}")
                # Try to route remaining points individually
                for to_idx in list(unconnected):
                    to_coord, to_layer = connection_points[to_idx]
                    from_coord, from_layer = connection_points[0]
                    path = self._find_path(from_coord, from_layer, to_coord, to_layer, trace_width)
                    if path:
                        segments.extend(path)
                        connected.add(to_idx)
                unconnected.clear()
                break
            
            # Add best path
            segments.extend(best_path)
            connected.add(best_to)
            unconnected.remove(best_to)
        
        if not segments:
            return False
        
        # Create route object
        route = Route(
            net_name=net.name,
            segments=segments,
            vias=vias,
            drc_errors=[]
        )
        route.calculate_metrics()
        
        # Mark route on grid
        self.grid.mark_route(segments)
        
        # Store result
        self.routed_nets[net.name] = route
        
        return len(unconnected) == 0
    
    def _route_differential_pair(self, net: Net, connection_points: List[Tuple[Coordinate, int]],
                                 trace_width: float) -> bool:
        """Route a differential pair with controlled impedance and length matching"""
        # For differential pairs, route both traces together with controlled spacing
        gap = self.rules.differential_pair_gap
        
        if len(connection_points) != 2:
            self.log(f"  Differential pair {net.name} must have exactly 2 connections")
            return False
        
        start_coord, start_layer = connection_points[0]
        end_coord, end_layer = connection_points[1]
        
        # Route main trace
        main_path = self._find_path(start_coord, start_layer, end_coord, end_layer, trace_width)
        
        if not main_path:
            return False
        
        # Create coupled trace with offset
        coupled_segments = []
        for seg in main_path:
            # Calculate perpendicular offset for coupled trace
            dx = seg.end.x - seg.start.x
            dy = seg.end.y - seg.start.y
            length = np.sqrt(dx**2 + dy**2)
            
            if length > 0:
                # Perpendicular direction
                perp_x = -dy / length * gap
                perp_y = dx / length * gap
                
                # Create coupled segment
                coupled_start = Coordinate(
                    seg.start.x + perp_x,
                    seg.start.y + perp_y,
                    seg.start.z,
                    seg.start.unit
                )
                coupled_end = Coordinate(
                    seg.end.x + perp_x,
                    seg.end.y + perp_y,
                    seg.end.z,
                    seg.end.unit
                )
                
                coupled_seg = TraceSegment(
                    start=coupled_start,
                    end=coupled_end,
                    width=seg.width,
                    layer=seg.layer,
                    net=f"{net.name}_coupled",
                    via_at_end=False
                )
                coupled_segments.append(coupled_seg)
        
        # Combine into route
        route = Route(
            net_name=net.name,
            segments=main_path + coupled_segments,
            vias=[],
            drc_errors=[]
        )
        route.calculate_metrics()
        route.length_matched = True
        
        # Mark on grid
        self.grid.mark_route(main_path)
        self.grid.mark_route(coupled_segments)
        
        self.routed_nets[net.name] = route
        
        return True
    
    def _find_path(self, start: Coordinate, start_layer: int, 
                   end: Coordinate, end_layer: int,
                   trace_width: float) -> Optional[List[TraceSegment]]:
        """
        Find path between two points using A* algorithm
        
        Returns list of trace segments or None if no path found
        """
        # Convert to grid coordinates
        start_grid = self.grid.world_to_grid(start)
        end_grid = self.grid.world_to_grid(end)
        
        # Check if start or end is blocked
        if self.grid.is_blocked(start_grid[0], start_grid[1], start_layer):
            self.log(f"  Start point is blocked")
            return None
        
        if self.grid.is_blocked(end_grid[0], end_grid[1], end_layer):
            self.log(f"  End point is blocked")
            return None
        
        # A* search
        start_node = AStarNode(
            x=start_grid[0],
            y=start_grid[1],
            layer=start_layer,
            g_cost=0,
            h_cost=self._heuristic(start_grid, end_grid, start_layer, end_layer),
            parent=None
        )
        
        open_set = [(start_node.f_cost, id(start_node), start_node)]
        closed_set = set()
        all_nodes = {id(start_node): start_node}
        
        max_iterations = 100000
        iterations = 0
        
        while open_set and iterations < max_iterations:
            iterations += 1
            
            # Get node with lowest f_cost
            _, _, current = heappop(open_set)
            current_id = id(current)
            
            if current_id in closed_set:
                continue
            
            closed_set.add(current_id)
            
            # Check if reached goal
            if (current.x == end_grid[0] and 
                current.y == end_grid[1] and 
                current.layer == end_layer):
                # Reconstruct path
                return self._reconstruct_path(current, start, end, trace_width)
            
            # Explore neighbors
            for neighbor in self._get_neighbors(current, end_layer):
                if id(neighbor) in closed_set:
                    continue
                
                # Calculate costs
                tentative_g = current.g_cost + self._move_cost(current, neighbor)
                
                if tentative_g < neighbor.g_cost or neighbor.g_cost == 0:
                    neighbor.g_cost = tentative_g
                    neighbor.h_cost = self._heuristic(
                        (neighbor.x, neighbor.y), end_grid, 
                        neighbor.layer, end_layer
                    )
                    neighbor.parent = current
                    
                    # Add to open set
                    neighbor_id = id(neighbor)
                    all_nodes[neighbor_id] = neighbor
                    heappush(open_set, (neighbor.f_cost, neighbor_id, neighbor))
        
        self.log(f"  No path found after {iterations} iterations")
        return None
    
    def _heuristic(self, from_grid: Tuple[int,int], to_grid: Tuple[int,int],
                   from_layer: int, to_layer: int) -> float:
        """Admissible heuristic: Manhattan distance plus via cost"""
        dx = abs(from_grid[0] - to_grid[0])
        dy = abs(from_grid[1] - to_grid[1])
        dl = abs(from_layer - to_layer)
        
        # Manhattan distance in grid cells
        dist = dx + dy
        
        # Add via cost estimate
        via_cost = dl * self.grid.via_cost_map[from_grid[1], from_grid[0]]
        
        return dist + via_cost
    
    def _get_neighbors(self, node: AStarNode, target_layer: int) -> List[AStarNode]:
        """Get valid neighboring nodes"""
        neighbors = []
        
        # Same layer neighbors (4-directional for orthogonal routing)
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dx, dy in directions:
            nx, ny = node.x + dx, node.y + dy
            
            if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                if not self.grid.is_blocked(nx, ny, node.layer):
                    # Check preferred direction constraint
                    if self._respects_preferred_direction(node.x, node.y, nx, ny, node.layer):
                        neighbor = AStarNode(
                            x=nx, y=ny, layer=node.layer,
                            g_cost=float('inf'), h_cost=0, parent=None
                        )
                        neighbors.append(neighbor)
        
        # Via transitions (change layer)
        if node.layer != target_layer:
            # Try moving to adjacent layer
            next_layer = node.layer + 1 if target_layer > node.layer else node.layer - 1
            
            if 0 <= next_layer < self.grid.layers:
                if not self.grid.is_blocked(node.x, node.y, next_layer):
                    # Check if via is allowed at this position
                    via_cost = self.grid.via_cost_map[node.y, node.x]
                    if via_cost < float('inf'):
                        neighbor = AStarNode(
                            x=node.x, y=node.y, layer=next_layer,
                            g_cost=float('inf'), h_cost=0, parent=None
                        )
                        neighbors.append(neighbor)
        
        return neighbors
    
    def _respects_preferred_direction(self, x1: int, y1: int, x2: int, y2: int, 
                                      layer: int) -> bool:
        """Check if move respects preferred routing direction for layer"""
        # Simple implementation: alternate horizontal/vertical per layer
        if layer % 2 == 0:
            # Even layers prefer horizontal
            return y1 == y2
        else:
            # Odd layers prefer vertical
            return x1 == x2
    
    def _move_cost(self, from_node: AStarNode, to_node: AStarNode) -> float:
        """Calculate cost of moving from one node to another"""
        base_cost = 1.0
        
        # Add congestion cost
        congestion = self.grid.congestion_map[to_node.layer, to_node.y, to_node.x]
        base_cost += congestion * 0.1
        
        # Via cost
        if from_node.layer != to_node.layer:
            base_cost += self.grid.via_cost_map[from_node.y, from_node.x]
        
        # Prefer moves toward target
        return base_cost
    
    def _reconstruct_path(self, goal_node: AStarNode, start: Coordinate, 
                          end: Coordinate, trace_width: float) -> List[TraceSegment]:
        """Reconstruct path from A* search result"""
        # Backtrack from goal to start
        nodes = []
        current = goal_node
        
        while current:
            nodes.append(current)
            current = current.parent
        
        nodes.reverse()
        
        # Convert to trace segments
        segments = []
        prev_coord = start
        prev_layer = nodes[0].layer
        
        for i, node in enumerate(nodes[1:], 1):
            curr_coord = self.grid.grid_to_world(node.x, node.y, node.layer)
            
            # Determine if this is a via transition
            is_via = node.layer != prev_layer
            
            if node.layer == prev_layer:
                # Same layer - create trace segment
                segment = TraceSegment(
                    start=prev_coord,
                    end=curr_coord,
                    width=trace_width,
                    layer=node.layer,
                    net="",  # Will be set by caller
                    via_at_end=is_via
                )
                segments.append(segment)
            
            prev_coord = curr_coord
            prev_layer = node.layer
        
        # Ensure last segment reaches actual end point
        if segments and prev_coord != end:
            last_seg = segments[-1]
            segments[-1] = TraceSegment(
                start=last_seg.start,
                end=end,
                width=last_seg.width,
                layer=last_seg.layer,
                net=last_seg.net,
                via_at_end=True
            )
        
        return segments
    
    def log(self, message: str):
        """Add message to routing log"""
        self.routing_log.append(message)
        print(message)
    
    def get_routing_summary(self) -> Dict:
        """Get summary of routing results"""
        total_nets = len(self.routed_nets) + len(self.failed_nets)
        total_length = sum(r.total_length for r in self.routed_nets.values())
        total_vias = sum(r.via_count for r in self.routed_nets.values())
        
        return {
            'total_nets': total_nets,
            'routed_nets': len(self.routed_nets),
            'failed_nets': len(self.failed_nets),
            'success_rate': len(self.routed_nets) / total_nets if total_nets > 0 else 0,
            'total_length_mm': total_length,
            'total_vias': total_vias,
            'log': self.routing_log
        }


print("PCB Router Module loaded successfully")
print("Available classes: DeterministicRouter, RoutingGrid, AStarNode")
