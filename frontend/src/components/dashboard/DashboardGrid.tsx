import { useCallback, useEffect, useRef, useState } from 'react';
import GridLayout from 'react-grid-layout';
import type { Layout } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import { useDashboardStore } from '@/stores/dashboardStore';
import { DashboardWidgetComponent } from './DashboardWidget';

export function DashboardGrid() {
  const { widgets, isEditing, updateWidgetPosition } = useDashboardStore();
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(1200);

  // Measure container width for responsive grid
  useEffect(() => {
    const updateWidth = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.offsetWidth);
      }
    };

    updateWidth();
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  const layout: Layout[] = widgets.map((widget) => ({
    i: String(widget.id),
    x: widget.position.x,
    y: widget.position.y,
    w: widget.position.w,
    h: widget.position.h,
    minW: 2,
    minH: 2,
    maxW: 12,
    static: !isEditing,
  }));

  const handleLayoutChange = useCallback(
    (newLayout: Layout[]) => {
      if (!isEditing) return;

      newLayout.forEach((item) => {
        const widget = widgets.find((w) => String(w.id) === item.i);
        if (widget) {
          const positionChanged =
            widget.position.x !== item.x ||
            widget.position.y !== item.y ||
            widget.position.w !== item.w ||
            widget.position.h !== item.h;

          if (positionChanged) {
            updateWidgetPosition(widget.id, {
              x: item.x,
              y: item.y,
              w: item.w,
              h: item.h,
            });
          }
        }
      });
    },
    [widgets, isEditing, updateWidgetPosition]
  );

  if (widgets.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border-2 border-dashed border-muted text-muted-foreground">
        <div className="text-center">
          <p className="text-lg font-medium">No widgets yet</p>
          <p className="text-sm">Add widgets to your dashboard to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="w-full">
      <GridLayout
        className="layout"
        layout={layout}
        cols={12}
        rowHeight={80}
        width={containerWidth}
        isDraggable={isEditing}
        isResizable={isEditing}
        onLayoutChange={handleLayoutChange}
        draggableHandle=".drag-handle"
        compactType="vertical"
        preventCollision={false}
        margin={[16, 16]}
      >
        {widgets.map((widget) => (
          <div key={widget.id} className="h-full">
            <DashboardWidgetComponent widget={widget} />
          </div>
        ))}
      </GridLayout>
    </div>
  );
}
