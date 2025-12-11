import { create } from 'zustand';
import type { Dashboard, DashboardWidget, WidgetPosition } from '@/types/dashboard';

interface DashboardState {
  // Current dashboard
  currentDashboard: Dashboard | null;
  widgets: DashboardWidget[];

  // Edit mode
  isEditing: boolean;
  hasUnsavedChanges: boolean;

  // Original widgets for cancel operation
  originalWidgets: DashboardWidget[];

  // Actions
  setCurrentDashboard: (dashboard: Dashboard | null) => void;
  setWidgets: (widgets: DashboardWidget[]) => void;
  updateWidgetPosition: (id: number, position: WidgetPosition) => void;
  updateWidget: (id: number, updates: Partial<DashboardWidget>) => void;
  removeWidget: (id: number) => void;
  addWidget: (widget: DashboardWidget) => void;

  // Edit mode
  setIsEditing: (editing: boolean) => void;
  startEditing: () => void;
  cancelEditing: () => void;
  commitChanges: () => void;

  // Reset
  reset: () => void;
}

const initialState = {
  currentDashboard: null,
  widgets: [],
  isEditing: false,
  hasUnsavedChanges: false,
  originalWidgets: [],
};

export const useDashboardStore = create<DashboardState>((set) => ({
  ...initialState,

  setCurrentDashboard: (dashboard) =>
    set({
      currentDashboard: dashboard,
      widgets: [],
      isEditing: false,
      hasUnsavedChanges: false,
    }),

  setWidgets: (widgets) =>
    set({
      widgets,
      originalWidgets: widgets,
      hasUnsavedChanges: false,
    }),

  updateWidgetPosition: (id, position) =>
    set((state) => ({
      widgets: state.widgets.map((w) =>
        w.id === id ? { ...w, position } : w
      ),
      hasUnsavedChanges: true,
    })),

  updateWidget: (id, updates) =>
    set((state) => ({
      widgets: state.widgets.map((w) =>
        w.id === id ? { ...w, ...updates } : w
      ),
      hasUnsavedChanges: true,
    })),

  removeWidget: (id) =>
    set((state) => ({
      widgets: state.widgets.filter((w) => w.id !== id),
      hasUnsavedChanges: true,
    })),

  addWidget: (widget) =>
    set((state) => ({
      widgets: [...state.widgets, widget],
      hasUnsavedChanges: true,
    })),

  setIsEditing: (isEditing) => set({ isEditing }),

  startEditing: () =>
    set((state) => ({
      isEditing: true,
      originalWidgets: [...state.widgets],
    })),

  cancelEditing: () =>
    set((state) => ({
      isEditing: false,
      widgets: state.originalWidgets,
      hasUnsavedChanges: false,
    })),

  commitChanges: () =>
    set((state) => ({
      isEditing: false,
      originalWidgets: state.widgets,
      hasUnsavedChanges: false,
    })),

  reset: () => set(initialState),
}));

// Selectors
export const selectCurrentDashboard = (state: DashboardState) => state.currentDashboard;
export const selectWidgets = (state: DashboardState) => state.widgets;
export const selectIsEditing = (state: DashboardState) => state.isEditing;
export const selectHasUnsavedChanges = (state: DashboardState) => state.hasUnsavedChanges;
