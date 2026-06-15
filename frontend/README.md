# Frontend Application

A modern, responsive React + TypeScript frontend for the deterministic PCB design system. Features a 6-screen wizard workflow with real-time visualization and intuitive UI/UX.

## 🚀 Quick Start

```bash
cd frontend
npm install
npm run dev
```

The application will be available at: `http://localhost:3000`

## 🎨 Architecture

Built with:
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tooling
- **Tailwind CSS** - Styling
- **React Router** - Navigation
- **Zustand** - State management
- **React Query** - Data fetching
- **Framer Motion** - Animations

## 📱 Screens & Workflow

### 1. Dashboard (`/`)
- Project overview and recent designs
- Quick actions (New Project, Import)
- System status and notifications

### 2. Schematic Editor (`/editor/schematic/:projectId`)
- Interactive schematic canvas
- Component library browser
- Net connectivity visualization
- ERC (Electrical Rule Check) indicators

### 3. Placement Studio (`/editor/placement/:projectId`)
- 2D board view with components
- Auto-placement controls
- Manual drag-and-drop positioning
- Real-time DRC feedback
- Density heatmaps

### 4. Routing Workspace (`/editor/routing/:projectId`)
- Multi-layer PCB editor
- Interactive routing with keyboard shortcuts
- Impedance profile display
- Differential pair routing mode
- Via placement tools

### 5. Validation Center (`/editor/validate/:projectId`)
- Comprehensive DRC report
- Impedance analysis charts
- Current capacity verification
- Clearance violation highlights
- Fix suggestions

### 6. Manufacturing Output (`/editor/gerber/:projectId`)
- Gerber file preview
- Layer stackup visualization
- Drill file inspection
- Download package generation
- Fab house export presets

## 🧩 Key Components

### Canvas Components
- `SchematicCanvas`: SVG-based schematic rendering
- `PCBViewer`: Multi-layer PCB visualization
- `GerberPreview`: RS-274X Gerber file renderer

### UI Components
- `ComponentLibrary`: Searchable component browser
- `NetInspector`: Net connectivity explorer
- `PropertiesPanel`: Context-aware property editor
- `DRCMarker`: Visual violation indicators
- `LayerManager`: Stackup and visibility controls

### Hooks
- `useProject`: Project state and operations
- `useRouting`: Routing engine interaction
- `useDRC`: Design rule checking
- `useKeyboardShortcuts`: Global shortcut handling

## ⚙️ Configuration

### Environment Variables

Create `.env.local`:
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

### Proxy Setup

Development proxy is configured in `vite.config.ts`:
```typescript
server: {
  proxy: {
    '/api': 'http://localhost:8000',
    '/ws': {
      target: 'ws://localhost:8000',
      ws: true
    }
  }
}
```

## 🎯 Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Space` | Pan mode |
| `R` | Route mode |
| `V` | Via placement |
| `Delete` | Remove selected |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `G` | Toggle grid |
| `L` | Layer cycle |
| `+/-` | Zoom in/out |

## 🧪 Testing

Run unit tests:
```bash
npm test
```

Run E2E tests:
```bash
npm run test:e2e
```

## 📦 Building for Production

```bash
npm run build
npm run preview  # Preview production build
```

Output will be in the `dist/` directory.

## 🎨 Design System

### Colors
- Primary: `#3B82F6` (Blue)
- Success: `#10B981` (Green)
- Warning: `#F59E0B` (Amber)
- Error: `#EF4444` (Red)

### Typography
- Headings: Inter
- Code: JetBrains Mono
- UI: System font stack

## 🔌 API Integration

All API calls use React Query for caching and optimistic updates:

```typescript
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

function useProject(id: string) {
  return useQuery(['project', id], () => api.projects.getById(id));
}
```

## 🐛 Debugging

Enable debug mode:
```bash
VITE_DEBUG=true npm run dev
```

Check browser console for detailed logs.

## 📚 Resources

- [React Docs](https://react.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Framer Motion](https://www.framer.com/motion/)
