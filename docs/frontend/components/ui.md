# UI Components

Reusable UI primitives that serve as building blocks for the application.

## Overview

UI components are low-level, highly reusable components that follow consistent design patterns. They are:

- **Composable**: Can be combined to create complex UIs
- **Accessible**: Built with ARIA support and keyboard navigation
- **Themeable**: Automatically adapt to light/dark themes
- **Type-safe**: Full TypeScript support with proper prop types

---

## Button

Versatile button component with multiple variants and sizes.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | `'default' \| 'secondary' \| 'outline' \| 'ghost' \| 'destructive'` | `'default'` | Visual style variant |
| `size` | `'sm' \| 'md' \| 'lg' \| 'icon'` | `'md'` | Button size |
| `className` | `string` | - | Additional CSS classes |
| `...props` | `ButtonHTMLAttributes` | - | Standard button attributes |

### Variants

**Default**
- Primary brand color background
- White text
- Hover darkens slightly

**Secondary**
- Secondary color background
- Secondary foreground text
- Softer appearance

**Outline**
- Transparent background
- Border outline
- Hover fills background

**Ghost**
- Transparent background
- No border
- Minimal hover effect

**Destructive**
- Red/danger color
- Use for delete/dangerous actions

### Sizes

| Size | Height | Padding | Icon Size |
|------|--------|---------|-----------|
| `sm` | 32px | 12px | 16px |
| `md` | 40px | 16px | 20px |
| `lg` | 48px | 24px | 24px |
| `icon` | 40px | 40px | 20px |

### Usage Examples

```tsx
import { Button } from '@/components/ui/Button';

// Default button
<Button onClick={handleClick}>
  Click Me
</Button>

// With icon
<Button variant="outline" size="sm">
  <Plus className="mr-2 h-4 w-4" />
  Add Item
</Button>

// Icon-only button
<Button variant="ghost" size="icon">
  <Settings className="h-5 w-5" />
</Button>

// Destructive action
<Button variant="destructive">
  Delete
</Button>

// Disabled state
<Button disabled>
  Loading...
</Button>
```

### Accessibility
- Proper focus ring on keyboard navigation
- Disabled state prevents interaction
- Works with screen readers
- Supports `aria-label` for icon-only buttons

### Notes
- **ForwardRef**: Supports ref forwarding
- **Auto-disabled**: Pointer events disabled when `disabled` prop is true
- **Focus Visible**: Only shows focus ring on keyboard navigation

---

## Card

Container component with consistent styling for grouped content.

### Components

The Card component includes sub-components:
- `Card` - Main container
- `CardHeader` - Header section
- `CardTitle` - Title text
- `CardContent` - Content area

### Props

All components accept standard HTML div attributes plus `className`.

### Usage Example

```tsx
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

<Card>
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
  </CardHeader>
  <CardContent>
    <p>Card content goes here...</p>
  </CardContent>
</Card>
```

### Advanced Usage

```tsx
// With custom styling
<Card className="border-primary">
  <CardHeader className="bg-muted">
    <CardTitle className="text-lg">Custom Styled Card</CardTitle>
  </CardHeader>
  <CardContent className="p-8">
    <div className="space-y-4">
      <p>Content with custom padding</p>
    </div>
  </CardContent>
</Card>

// Clickable card
<Card className="cursor-pointer hover:shadow-lg transition-shadow">
  <CardHeader>
    <CardTitle>Clickable Card</CardTitle>
  </CardHeader>
  <CardContent>
    Click anywhere on this card
  </CardContent>
</Card>
```

### Default Styles

**Card**
- Rounded corners (8px)
- Border
- Background color from theme
- Subtle shadow

**CardHeader**
- Padding: 24px
- Flexbox column layout
- Spacing between children

**CardTitle**
- 2xl text size
- Semibold font
- Tight line height
- Letter tracking

**CardContent**
- Padding: 24px (top: 0)
- Inherits card's text color

### Accessibility
- Semantic HTML structure
- Proper heading hierarchy
- Screen reader friendly

### Notes
- **Composable**: Mix and match sub-components as needed
- **ForwardRef**: All components support ref forwarding
- **Themeable**: Colors adapt to theme automatically

---

## Input

Text input component with consistent styling and accessibility.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `type` | `string` | `'text'` | HTML input type |
| `className` | `string` | - | Additional CSS classes |
| `...props` | `InputHTMLAttributes` | - | Standard input attributes |

### Usage Examples

```tsx
import { Input } from '@/components/ui/Input';

// Basic text input
<Input
  type="text"
  placeholder="Enter your name"
  value={name}
  onChange={(e) => setName(e.target.value)}
/>

// Password input
<Input
  type="password"
  placeholder="Password"
  required
/>

// Number input
<Input
  type="number"
  min={0}
  max={100}
  step={1}
/>

// With label
<div className="space-y-2">
  <label htmlFor="email" className="text-sm font-medium">
    Email
  </label>
  <Input
    id="email"
    type="email"
    placeholder="you@example.com"
  />
</div>

// Disabled
<Input disabled value="Read-only value" />

// Error state
<Input
  className="border-destructive focus-visible:ring-destructive"
  placeholder="Invalid input"
/>
```

### Features

**Focus Ring**
- 2px ring on focus
- Ring color matches theme
- Only visible on keyboard focus

**File Input Support**
- Styled file input button
- Maintains native file picker

**Placeholder**
- Muted color
- Italic styling optional

**Disabled State**
- Grayed out appearance
- Cursor changed to not-allowed
- 50% opacity

### Input Types

Supports all HTML5 input types:
- `text`, `email`, `password`, `url`, `tel`
- `number`, `range`
- `date`, `time`, `datetime-local`
- `file`, `search`
- `color`, `checkbox`, `radio`

### Accessibility
- Proper label association via `id`
- Placeholder is not a substitute for labels
- Error messages via `aria-describedby`
- Required fields marked with `required`

### Notes
- **ForwardRef**: Supports ref forwarding for form libraries
- **Validation**: Works with HTML5 validation and form libraries
- **Auto-complete**: Supports browser autocomplete

---

## Toast

Notification component for user feedback.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | Required | Toast title |
| `description` | `string` | - | Toast description |
| `variant` | `'default' \| 'success' \| 'warning' \| 'destructive'` | `'default'` | Visual variant |
| `duration` | `number` | `5000` | Auto-dismiss time (ms) |
| `onClose` | `() => void` | - | Close callback |

### Usage Example

```tsx
import { useToast } from '@/hooks/useToast';

function MyComponent() {
  const { showToast } = useToast();

  const handleSuccess = () => {
    showToast({
      title: 'Success',
      description: 'Your changes have been saved.',
      variant: 'success',
    });
  };

  const handleError = () => {
    showToast({
      title: 'Error',
      description: 'Something went wrong. Please try again.',
      variant: 'destructive',
      duration: 10000, // Show longer for errors
    });
  };

  return (
    <>
      <button onClick={handleSuccess}>Save</button>
      <button onClick={handleError}>Trigger Error</button>
    </>
  );
}
```

### Variants

**Default**
- Neutral background
- Informational

**Success**
- Green background
- Checkmark icon
- Positive feedback

**Warning**
- Yellow/amber background
- Alert icon
- Caution message

**Destructive**
- Red background
- Error icon
- Error/failure message

### Features

**Auto-dismiss**
- Configurable duration
- Pause on hover
- Resume on mouse leave

**Manual Close**
- X button to close
- Swipe to dismiss (mobile)

**Stacking**
- Multiple toasts stack vertically
- New toasts appear at bottom
- Oldest dismissed first

**Animations**
- Slide in from side
- Fade out on dismiss
- Smooth transitions

### Positioning

Default position: bottom-right

```tsx
// Custom position (via toast provider)
<ToastProvider position="top-center">
  <App />
</ToastProvider>
```

### Accessibility
- `role="status"` for screen readers
- `aria-live="polite"` for announcements
- Keyboard dismissible (Escape key)
- Focus management

### Notes
- **Queue**: Toasts queued if multiple shown
- **Persistent**: Set `duration={0}` for persistent toasts
- **Rich Content**: Supports JSX in description

---

## LoadingPage

Full-page loading indicator.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `message` | `string` | `'Loading...'` | Loading message |
| `spinner` | `boolean` | `true` | Show spinner |

### Usage Example

```tsx
import { LoadingPage } from '@/components/ui/LoadingPage';

function MyPage() {
  const { data, isLoading } = useQuery(['data'], fetchData);

  if (isLoading) {
    return <LoadingPage message="Loading your data..." />;
  }

  return <div>{/* Page content */}</div>;
}
```

### Features

**Centered Layout**
- Vertically and horizontally centered
- Full viewport height
- Flexbox positioning

**Spinner Animation**
- Rotating border animation
- Theme-aware colors
- Smooth 1s rotation

**Custom Message**
- Muted text color
- Below spinner
- Optional

### Variations

```tsx
// Simple spinner, no text
<LoadingPage message="" />

// Custom message
<LoadingPage message="Processing your request..." />

// Just text, no spinner
<LoadingPage spinner={false} message="Please wait..." />
```

### Accessibility
- `role="status"` for screen readers
- `aria-live="polite"` announcements
- `aria-busy="true"` on parent

### Notes
- **Full Page**: Takes up entire viewport
- **Theme Aware**: Colors adapt to theme
- **No Interaction**: Blocks interaction while loading

---

## Utility Functions

### cn() - Class Name Merger

Combines class names intelligently using clsx and tailwind-merge.

```tsx
import { cn } from '@/lib/utils';

// Basic usage
cn('base-class', 'another-class')
// → 'base-class another-class'

// Conditional classes
cn('base', condition && 'conditional')
// → 'base conditional' (if condition is true)
// → 'base' (if condition is false)

// Override with prop
cn('text-sm', className)
// → Merges with className prop

// Tailwind conflicts resolved
cn('px-2 py-1', 'px-4')
// → 'py-1 px-4' (last px value wins)
```

### Common Patterns

**Button with Conditional Variants**
```tsx
<button
  className={cn(
    'base-button-styles',
    variant === 'primary' && 'bg-primary text-white',
    variant === 'secondary' && 'bg-secondary text-gray-900',
    disabled && 'opacity-50 cursor-not-allowed',
    className // Allow prop override
  )}
>
  {children}
</button>
```

**Responsive Classes**
```tsx
<div className={cn(
  'flex flex-col',  // Mobile
  'md:flex-row',    // Desktop
  'gap-4'
)}>
  {/* Content */}
</div>
```

---

## Theming

All UI components use CSS variables for theming:

### Theme Variables

```css
:root {
  --background: 0 0% 100%;
  --foreground: 240 10% 3.9%;
  --primary: 221 83% 53%;
  --primary-foreground: 0 0% 100%;
  --secondary: 240 4.8% 95.9%;
  --secondary-foreground: 240 5.9% 10%;
  --accent: 240 4.8% 95.9%;
  --accent-foreground: 240 5.9% 10%;
  --muted: 240 4.8% 95.9%;
  --muted-foreground: 240 3.8% 46.1%;
  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 0 0% 100%;
  --border: 240 5.9% 90%;
  --ring: 221 83% 53%;
}

.dark {
  --background: 240 10% 3.9%;
  --foreground: 0 0% 98%;
  /* ... other dark theme values ... */
}
```

### Using Theme Colors

```tsx
// Via Tailwind classes
<div className="bg-primary text-primary-foreground">
  Primary colored box
</div>

// Via CSS variables
<div style={{ backgroundColor: 'hsl(var(--primary))' }}>
  Custom styled box
</div>
```

---

## Form Integration

UI components work seamlessly with form libraries:

### React Hook Form Example

```tsx
import { useForm } from 'react-hook-form';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

function LoginForm() {
  const { register, handleSubmit, formState: { errors } } = useForm();

  const onSubmit = (data) => {
    console.log(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="email">Email</label>
        <Input
          id="email"
          type="email"
          {...register('email', { required: true })}
          className={errors.email && 'border-destructive'}
        />
        {errors.email && (
          <p className="text-sm text-destructive">Email is required</p>
        )}
      </div>

      <div>
        <label htmlFor="password">Password</label>
        <Input
          id="password"
          type="password"
          {...register('password', { required: true, minLength: 8 })}
        />
      </div>

      <Button type="submit">Sign In</Button>
    </form>
  );
}
```

---

## Accessibility Checklist

### Button
- [ ] Descriptive text or aria-label
- [ ] Focus visible ring
- [ ] Disabled state prevents interaction
- [ ] Keyboard accessible (Enter/Space)

### Input
- [ ] Associated label (via id/for)
- [ ] Placeholder is supplementary, not replacement for label
- [ ] Error messages via aria-describedby
- [ ] Required fields marked

### Card
- [ ] Proper heading hierarchy
- [ ] Semantic HTML structure
- [ ] Sufficient color contrast

### Toast
- [ ] Screen reader announcements
- [ ] Keyboard dismissible
- [ ] Does not trap focus
- [ ] Auto-dismiss has sufficient duration

---

## Testing

### Example Component Tests

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '@/components/ui/Button';

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('handles click events', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click</Button>);

    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledOnce();
  });

  it('applies variant classes', () => {
    render(<Button variant="destructive">Delete</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-destructive');
  });

  it('forwards refs', () => {
    const ref = React.createRef<HTMLButtonElement>();
    render(<Button ref={ref}>Button</Button>);
    expect(ref.current).toBeInstanceOf(HTMLButtonElement);
  });
});
```

---

## Related Documentation

- [Layout Components](./layout.md) - Page layout structure
- [Chat Components](./chat.md) - Chat interface
- [Chart Components](./charts.md) - Data visualization
- [Dashboard Components](./dashboard.md) - Dashboard widgets
