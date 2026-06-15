# Core Engine

The heart of the deterministic PCB design system, containing data structures, IPC-compliant calculators, and routing algorithms.

## 📁 Structure

- `core.py` - Main module with all core functionality
  - **Data Structures**: Coordinate, Pad, Via, TraceSegment, Component, Net, Route
  - **Calculators**: Impedance (IPC-2141), Current Capacity (IPC-2152), Clearance (IPC-2221)
  - **Utilities**: Unit conversion, material properties, stackup management

## 🔧 Key Components

### 1. Unit Conversion
Supports seamless conversion between:
- Millimeters (mm)
- Mils (thousandths of an inch)
- Inches
- Micrometers (μm)

```python
from src.core import convert_units
convert_units(10, 'mm', 'mils')  # Returns 393.701
```

### 2. Impedance Calculator (IPC-2141)
Calculates trace impedance for controlled impedance designs:
- **Microstrip**: Outer layer traces over reference plane
- **Stripline**: Inner layer traces between two reference planes
- **Differential Pairs**: Coupled traces for high-speed signaling

```python
from src.core import ImpedanceCalculator, Stackup

stackup = Stackup(...)
calc = ImpedanceCalculator(stackup)
width = calc.calculate_width(target_impedance=50, layer=0)
```

### 3. Current Capacity Calculator (IPC-2152)
Determines minimum trace width for safe current carrying:
- External layers (air exposure)
- Internal layers (embedded in dielectric)
- Temperature rise considerations

```python
from src.core import TraceWidthCalculator

calc = TraceWidthCalculator()
width = calc.calculate_width(current=2.0, temp_rise=10, layer_type='external')
```

### 4. Clearance Calculator (IPC-2221 / IEC 60950)
Ensures safe electrical clearances based on:
- Working voltage
- Pollution degree (1-3)
- Material group (I-IIIb)

```python
from src.core import ClearanceCalculator

calc = ClearanceCalculator()
clearance = calc.calculate_clearance(voltage=250, pollution_degree=2)
```

### 5. Deterministic Router (A* Algorithm)
Grid-based maze routing with:
- Preferred direction constraints per layer
- Impedance-controlled trace width adjustment
- Differential pair length matching
- Via minimization
- Congestion-aware cost functions

## 🧪 Testing

Run core engine tests:
```bash
pytest tests/test_system.py -v -k "core"
```

## 📚 References

- [IPC-2141](https://www.ipc.org/): Controlled Impedance
- [IPC-2152](https://www.ipc.org/): Current-Carrying Capacity
- [IPC-2221](https://www.ipc.org/): Generic Standard on Printed Board Design
