// Type declarations for react-grid-layout v2.x
// The @types/react-grid-layout package is outdated for v2.x

declare module 'react-grid-layout' {
  import * as React from 'react';

  export interface Layout {
    i: string;
    x: number;
    y: number;
    w: number;
    h: number;
    minW?: number;
    maxW?: number;
    minH?: number;
    maxH?: number;
    static?: boolean;
    isDraggable?: boolean;
    isResizable?: boolean;
    resizeHandles?: Array<'s' | 'w' | 'e' | 'n' | 'sw' | 'nw' | 'se' | 'ne'>;
    isBounded?: boolean;
  }

  export interface GridLayoutProps {
    className?: string;
    style?: React.CSSProperties;
    width?: number;
    autoSize?: boolean;
    cols?: number;
    draggableCancel?: string;
    draggableHandle?: string;
    compactType?: 'vertical' | 'horizontal' | null;
    layout?: Layout[];
    margin?: [number, number];
    containerPadding?: [number, number] | null;
    rowHeight?: number;
    maxRows?: number;
    isBounded?: boolean;
    isDraggable?: boolean;
    isResizable?: boolean;
    isDroppable?: boolean;
    preventCollision?: boolean;
    useCSSTransforms?: boolean;
    transformScale?: number;
    droppingItem?: Partial<Layout>;
    resizeHandles?: Array<'s' | 'w' | 'e' | 'n' | 'sw' | 'nw' | 'se' | 'ne'>;
    resizeHandle?: React.ReactNode | ((resizeHandleAxis: string, ref: React.Ref<HTMLElement>) => React.ReactNode);
    allowOverlap?: boolean;
    onLayoutChange?: (layout: Layout[]) => void;
    onDragStart?: (layout: Layout[], oldItem: Layout, newItem: Layout, placeholder: Layout, e: MouseEvent, element: HTMLElement) => void;
    onDrag?: (layout: Layout[], oldItem: Layout, newItem: Layout, placeholder: Layout, e: MouseEvent, element: HTMLElement) => void;
    onDragStop?: (layout: Layout[], oldItem: Layout, newItem: Layout, placeholder: Layout, e: MouseEvent, element: HTMLElement) => void;
    onResizeStart?: (layout: Layout[], oldItem: Layout, newItem: Layout, placeholder: Layout, e: MouseEvent, element: HTMLElement) => void;
    onResize?: (layout: Layout[], oldItem: Layout, newItem: Layout, placeholder: Layout, e: MouseEvent, element: HTMLElement) => void;
    onResizeStop?: (layout: Layout[], oldItem: Layout, newItem: Layout, placeholder: Layout, e: MouseEvent, element: HTMLElement) => void;
    onDrop?: (layout: Layout[], item: Layout, e: Event) => void;
    onDropDragOver?: (e: DragEvent) => { w?: number; h?: number } | false | undefined;
    innerRef?: React.Ref<HTMLDivElement>;
    children?: React.ReactNode;
  }

  export default class GridLayout extends React.Component<GridLayoutProps> {}

  export interface ResponsiveGridLayoutProps extends Omit<GridLayoutProps, 'cols' | 'layout' | 'onLayoutChange'> {
    breakpoint?: string;
    breakpoints?: { [P: string]: number };
    cols?: { [P: string]: number };
    layouts?: { [P: string]: Layout[] };
    onBreakpointChange?: (newBreakpoint: string, newCols: number) => void;
    onLayoutChange?: (currentLayout: Layout[], allLayouts: { [P: string]: Layout[] }) => void;
    onWidthChange?: (containerWidth: number, margin: [number, number], cols: number, containerPadding: [number, number] | null) => void;
  }

  export class Responsive extends React.Component<ResponsiveGridLayoutProps> {}

  export interface WidthProviderProps {
    measureBeforeMount?: boolean;
  }

  export function WidthProvider<P extends object>(
    ComposedComponent: React.ComponentType<P>
  ): React.ComponentType<Omit<P, 'width'> & WidthProviderProps>;
}
