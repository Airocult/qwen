# Tests

Comprehensive test suite for the deterministic PCB design system.

## 🧪 Test Coverage

### Unit Tests (`test_system.py`)

42 tests covering:

#### Core Engine (28 tests)
- **Unit Conversions** (4 tests)
  - mm to mils, inches, micrometers
  - Bidirectional conversion accuracy
  
- **Impedance Calculations** (4 tests)
  - Microstrip impedance (IPC-2141)
  - Stripline impedance
  - Differential pair impedance
  - Edge cases and validation

- **Current Capacity** (3 tests)
  - External layer calculations (IPC-2152)
  - Internal layer calculations
  - Temperature rise scenarios

- **Clearance Calculations** (4 tests)
  - Voltage-based clearances (IPC-2221)
  - Pollution degree variations
  - Material group effects
  - Altitude corrections

- **Stackup Operations** (3 tests)
  - Layer creation and management
  - Dielectric properties
  - Copper weight handling

- **Data Structures** (5 tests)
  - Coordinate transformations
  - Pad and via creation
  - Net connectivity
  - Route segment validation

- **Material Properties** (2 tests)
  - FR-4 characteristics
  - Rogers material data
  - Temperature coefficients

- **Router Grid** (3 tests)
  - Grid initialization
  - Obstacle placement
  - Path cost calculation

#### Integration Tests (14 tests)
- **Routing Workflows** (3 tests)
  - Simple point-to-point routing
  - Multi-net routing with congestion
  - Differential pair routing

- **End-to-End Flows** (6 tests)
  - Schematic import to Gerber output
  - Placement optimization cycle
  - DRC validation and correction

- **API Integration** (5 tests)
  - REST endpoint responses
  - Authentication flows
  - File upload/download
  - WebSocket real-time updates

## 🚀 Running Tests

### All Tests
```bash
pytest tests/ -v
```

### Specific Categories
```bash
# Core engine tests only
pytest tests/test_system.py -v -k "core"

# Router tests only
pytest tests/test_system.py -v -k "router"

# IPC calculator tests
pytest tests/test_system.py -v -k "impedance or current or clearance"

# Integration tests
pytest tests/test_system.py -v -k "integration"
```

### With Coverage
```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov\\index.html  # Windows
```

## 📊 Coverage Report

Current coverage targets:
- **Core Engine**: >90%
- **Router**: >85%
- **API**: >80%
- **Overall**: >85%

Generate report:
```bash
pytest tests/ --cov=src --cov-fail-under=85
```

## 🔬 Test Examples

### Impedance Calculation Test
```python
def test_microstrip_impedance():
    """Test IPC-2141 microstrip impedance calculation."""
    stackup = create_test_stackup()
    calc = ImpedanceCalculator(stackup)
    
    # Standard FR-4, 50 ohm target
    width = calc.calculate_width(target_impedance=50.0, layer=0)
    
    # Verify calculated width produces target impedance
    impedance = calc.calculate_impedance(width, layer=0)
    assert abs(impedance - 50.0) < 2.0  # ±2 ohm tolerance
```

### Routing Test
```python
def test_point_to_point_routing():
    """Test A* router finds valid path."""
    grid = RoutingGrid(100, 100)
    grid.add_obstacle(Rectangle(20, 20, 40, 40))
    
    router = GridRouter(grid)
    start = Coordinate(10, 10, layer=0)
    end = Coordinate(90, 90, layer=0)
    
    route = router.route(start, end)
    
    assert route is not None
    assert len(route.segments) > 0
    assert not route.has_violations()
```

## 🐛 Debugging Tests

### Verbose Output
```bash
pytest tests/ -v -s
```

### Stop on First Failure
```bash
pytest tests/ -x
```

### Run Specific Test
```bash
pytest tests/test_system.py::test_microstrip_impedance -v
```

### Parallel Execution
```bash
pytest tests/ -n auto  # Requires pytest-xdist
```

## 📝 Writing New Tests

Follow this template:

```python
def test_feature_name():
    """Description of what is being tested."""
    # Arrange
    setup_test_data()
    
    # Act
    result = function_under_test(params)
    
    # Assert
    assert expected_condition(result)
    
    # Optional: Additional validation
    verify_side_effects()
```

## 🔧 Fixtures

Common test fixtures in `tests/conftest.py`:
- `sample_stackup()`: Standard 4-layer FR-4 stackup
- `test_components()`: Sample component library
- `mock_api_client()`: Mocked API for integration tests
- `temp_project()`: Temporary project directory

## 📈 Continuous Integration

Tests run automatically on:
- Every push to main branch
- All pull requests
- Nightly full regression suite

View results: https://github.com/Airocult/qwen/actions

## 🎯 Quality Gates

Before merging PRs:
- ✅ All tests pass
- ✅ Coverage ≥ 85%
- ✅ No flaky tests
- ✅ Performance within bounds

---

*Maintain high test quality for production reliability.*
