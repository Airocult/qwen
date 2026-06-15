# Examples

Sample projects and test cases demonstrating the deterministic PCB design system capabilities.

## 📁 Example Projects

### 1. Simple LED Blinker (`simple-led/`)
**Complexity**: Beginner  
**Layers**: 2  
**Components**: 5  

A basic LED blinking circuit using a 555 timer. Perfect for learning the workflow.

**Files**:
- `schematic.sch`: Circuit schematic
- `design.json`: Project configuration
- `gerbers/`: Generated output files

**Learning Objectives**:
- Basic schematic entry
- Component placement
- Simple routing
- Gerber generation

### 2. Arduino Nano Shield (`arduino-shield/`)
**Complexity**: Intermediate  
**Layers**: 4  
**Components**: 25  

Custom shield for Arduino Nano with motor driver and sensors.

**Features**:
- Mixed-signal design (digital + analog)
- Power plane management
- Controlled impedance for SPI lines
- Thermal considerations for motor driver

**Files**:
- `schematic.kicad_sch`: KiCAD schematic
- `placement.csv`: Component coordinates
- `constraints.json`: Design rules

### 3. Raspberry Pi CM4 Carrier (`cm4-carrier/`)
**Complexity**: Advanced  
**Layers**: 6  
**Components**: 85  

Carrier board for Raspberry Pi Compute Module 4.

**Highlights**:
- High-speed DDR routing (length matching ±10 mil)
- PCIe differential pairs (90Ω ±10%)
- HDMI TMDS pairs (100Ω differential)
- Power integrity for 3.3V, 5V, 12V rails
- BGA fanout optimization

**Files**:
- `schematic.pdf`: Annotated schematic
- `stackup.json`: 6-layer stackup definition
- `simulation/`: SI/PI simulation results

### 4. FPGA Development Board (`fpga-dev/`)
**Complexity**: Expert  
**Layers**: 10  
**Components**: 250+  

High-end FPGA board with DDR4, Ethernet, and high-speed transceivers.

**Advanced Features**:
- DDR4 memory interface (2400 Mbps)
- 10G Ethernet (SFP+)
- JTAG boundary scan
- Multi-gigabit transceiver routing
- Rigid-flex design option

**Files**:
- `constraint_files/`: XDC timing constraints
- `si_analysis/`: Signal integrity reports
- `emc_testing/`: Pre-compliance results

## 🎯 Tutorials

### Tutorial 1: Your First PCB
**Duration**: 30 minutes  
**Prerequisites**: None  

Step-by-step guide to creating a simple LED circuit:
1. Create new project
2. Add components from library
3. Draw schematic connections
4. Define board outline
5. Place components
6. Route traces
7. Generate Gerbers

[View Tutorial](./tutorials/01-first-pcb.md)

### Tutorial 2: Impedance-Controlled Routing
**Duration**: 45 minutes  
**Prerequisites**: Tutorial 1  

Learn to route high-speed signals with controlled impedance:
1. Define layer stackup
2. Calculate trace widths
3. Set up differential pairs
4. Route with impedance constraints
5. Verify with DRC

[View Tutorial](./tutorials/02-impedance-routing.md)

### Tutorial 3: Multi-Layer Design
**Duration**: 60 minutes  
**Prerequisites**: Tutorial 2  

Master 4+ layer board design:
1. Planes and splits
2. Via strategies
3. Return path management
4. EMI reduction techniques
5. Manufacturing considerations

[View Tutorial](./tutorials/03-multilayer.md)

### Tutorial 4: Advanced DRC and Validation
**Duration**: 40 minutes  
**Prerequisites**: Tutorial 3  

Comprehensive design validation:
1. Custom rule creation
2. Signal integrity checks
3. Power integrity analysis
4. Thermal validation
5. DF
