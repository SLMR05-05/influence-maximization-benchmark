# Design Rules — IM-Benchmark-Lab Desktop GUI

## 1. Framework Selection
- **Primary GUI Framework**: CustomTkinter (modern wrapper around Tkinter)
- **Alternative**: ttkbootstrap (for rapid prototyping)
- **Forbidden**: Raw tkinter (deprecated for new development)
- **Backend**: Python + C++ (pybind11) — unchanged
- **Layout System**: Grid-based responsive layout

## 2. Visual Design System
- **Theme**: Dark mode primary, Light mode secondary (customtkinter supports both)
- **Color Palette**:
  - Primary: #2563EB (Blue)
  - Secondary: #64748B (Slate)
  - Success: #16A34A (Green)
  - Warning: #D97706 (Amber)
  - Danger: #DC2626 (Red)
  - Background: #F5F7FA (Light) / #1E1E1E (Dark)
  - Card: #FFFFFF (Light) / #2D2D2D (Dark)
- **Typography**: Inter / Segoe UI, 12px body, 14px headings
- **Border Radius**: 10-14px for cards, 6px for buttons
- **Spacing**: 8px grid system (8, 16, 24, 32px)

## 3. Component Standards
- All buttons must use `ctk.CTkButton`
- All inputs must use `ctk.CTkEntry` / `ctk.CTkComboBox`
- All frames must use `ctk.CTkFrame`
- Tables must use `ttk.Treeview` with custom styling
- Charts must use matplotlib with dark theme support
- Loading states: `ctk.CTkProgressBar`
- Notifications: `ctk.CTkLabel` with color coding

## 4. Layout Rules
- Sidebar: 260px fixed width, collapsible
- Content area: Flexible grid with padding 20px
- Cards: Shadow elevation 2, 12px radius
- Responsive: Min width 1024px, ideal 1440px

## 5. Interaction Patterns
- Hover states on all interactive elements
- Smooth transitions (200ms)
- Loading indicators for async operations
- Toast notifications for success/error
- Modal dialogs for confirmations

## 6. Code Standards
- All GUI files must be in `src/im_research/gui/`
- Each interface = separate module
- Must support both Light and Dark themes
- Must be responsive (resizeable)
- Must integrate with C++ core via pybind11

## 7. Modern UX Principles
- No blocking operations on main thread
- Async data loading with progress bars
- Keyboard shortcuts (Ctrl+S save, Ctrl+R run)
- Right-click context menus
- Drag-and-drop for file imports
- Auto-save configuration changes

## 8. Forbidden Practices
- ❌ Raw tkinter widgets
- ❌ Hardcoded colors (use theme variables)
- ❌ Fixed window sizes without resize
- ❌ No loading states
- ❌ Blocking GUI during computation
