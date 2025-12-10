# Phase 2.5: Advanced Features & Polish

## Overview

| Attribute | Value |
|-----------|-------|
| **Phase** | 2.5 |
| **Focus** | Alerts, Scheduling, Themes, Sharing, UX |
| **Estimated Effort** | 3-4 days |
| **Prerequisites** | Phase 2.4 complete |

## Goal

Implement data alerts with notifications, scheduled queries, comprehensive theme system with presets and custom themes, dashboard sharing via public links, onboarding wizard, and keyboard shortcuts for power users.

## Success Criteria

- [ ] Data alerts trigger when conditions are met
- [ ] Toast and browser notifications display alerts
- [ ] Scheduled queries run at configured intervals
- [ ] Theme presets available (Ocean, Forest, Sunset, etc.)
- [ ] Custom theme builder with color picker
- [ ] Dashboard sharing generates public links
- [ ] Onboarding wizard guides first-time users
- [ ] Keyboard shortcuts work (Ctrl+Enter, Ctrl+K, etc.)
- [ ] UI is tablet-responsive

## Implementation Plan

### Step 1: Data Alerts Backend

#### 1.1 Alert Scheduler Service

```python
# src/services/alert_scheduler.py
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import structlog

from src.api.models.database import DataAlert

logger = structlog.get_logger()

class AlertScheduler:
    """Service for scheduling and evaluating data alerts."""
    
    def __init__(self, session_factory):
        self.scheduler = AsyncIOScheduler()
        self.session_factory = session_factory
        self._running = False
    
    async def start(self):
        """Start the alert scheduler."""
        if self._running:
            return
        
        # Add job to check alerts every minute
        self.scheduler.add_job(
            self._check_alerts,
            IntervalTrigger(minutes=1),
            id="alert_checker",
            replace_existing=True,
        )
        
        self.scheduler.start()
        self._running = True
        logger.info("alert_scheduler_started")
    
    async def stop(self):
        """Stop the alert scheduler."""
        if self._running:
            self.scheduler.shutdown()
            self._running = False
            logger.info("alert_scheduler_stopped")
    
    async def _check_alerts(self):
        """Check all active alerts."""
        async with self.session_factory() as db:
            # Get active alerts
            query = select(DataAlert).where(DataAlert.is_active == True)
            result = await db.execute(query)
            alerts = result.scalars().all()
            
            for alert in alerts:
                try:
                    await self._evaluate_alert(db, alert)
                except Exception as e:
                    logger.error("alert_evaluation_error", alert_id=alert.id, error=str(e))
    
    async def _evaluate_alert(self, db: AsyncSession, alert: DataAlert):
        """Evaluate a single alert."""
        # Execute the query
        try:
            result = await db.execute(text(alert.query))
            row = result.fetchone()
            
            if not row:
                return
            
            current_value = float(row[0])
        except Exception as e:
            logger.error("alert_query_error", alert_id=alert.id, error=str(e))
            return
        
        # Check condition
        threshold = float(alert.threshold) if alert.threshold else 0
        triggered = False
        
        if alert.condition == "greater_than":
            triggered = current_value > threshold
        elif alert.condition == "less_than":
            triggered = current_value < threshold
        elif alert.condition == "equals":
            triggered = abs(current_value - threshold) < 0.001
        elif alert.condition == "changes":
            if alert.last_value is not None:
                triggered = abs(current_value - float(alert.last_value)) > 0.001
        
        # Update alert record
        alert.last_checked_at = datetime.utcnow()
        alert.last_value = str(current_value)
        
        if triggered:
            alert.last_triggered_at = datetime.utcnow()
            await self._send_notification(alert, current_value)
        
        await db.commit()
    
    async def _send_notification(self, alert: DataAlert, value: float):
        """Send notification for triggered alert."""
        from src.services.notification_service import NotificationService
        
        notification = NotificationService()
        await notification.send_alert(
            alert_id=alert.id,
            alert_name=alert.name,
            condition=alert.condition,
            threshold=float(alert.threshold) if alert.threshold else 0,
            current_value=value,
        )
```

#### 1.2 Notification Service

```python
# src/services/notification_service.py
from typing import Dict, Any, List
import asyncio
import structlog

logger = structlog.get_logger()

# In-memory store for connected WebSocket clients
_connected_clients: Dict[str, List] = {}


class NotificationService:
    """Service for sending notifications."""
    
    @staticmethod
    def register_client(client_id: str, websocket):
        """Register a WebSocket client for notifications."""
        if client_id not in _connected_clients:
            _connected_clients[client_id] = []
        _connected_clients[client_id].append(websocket)
    
    @staticmethod
    def unregister_client(client_id: str, websocket):
        """Unregister a WebSocket client."""
        if client_id in _connected_clients:
            _connected_clients[client_id] = [
                ws for ws in _connected_clients[client_id] if ws != websocket
            ]
    
    async def send_alert(
        self,
        alert_id: int,
        alert_name: str,
        condition: str,
        threshold: float,
        current_value: float,
    ):
        """Send alert notification to all connected clients."""
        message = {
            "type": "alert",
            "data": {
                "id": alert_id,
                "name": alert_name,
                "condition": condition,
                "threshold": threshold,
                "current_value": current_value,
                "message": self._format_message(alert_name, condition, threshold, current_value),
            },
        }
        
        # Send to all connected clients
        for client_id, websockets in _connected_clients.items():
            for websocket in websockets:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error("notification_send_error", error=str(e))
        
        logger.info("alert_notification_sent", alert_id=alert_id)
    
    def _format_message(
        self,
        name: str,
        condition: str,
        threshold: float,
        value: float,
    ) -> str:
        """Format alert message."""
        condition_text = {
            "greater_than": f"exceeded {threshold}",
            "less_than": f"dropped below {threshold}",
            "equals": f"equals {threshold}",
            "changes": "changed",
        }
        return f"{name}: Value {condition_text.get(condition, condition)} (current: {value})"
```

#### 1.3 Alert API Routes

```python
# src/api/routes/alerts.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from src.api.deps import get_db
from src.api.models.database import DataAlert

router = APIRouter()


class AlertCreate(BaseModel):
    name: str
    query: str
    condition: str  # 'greater_than', 'less_than', 'equals', 'changes'
    threshold: Optional[float] = None


class AlertUpdate(BaseModel):
    name: Optional[str] = None
    query: Optional[str] = None
    condition: Optional[str] = None
    threshold: Optional[float] = None
    is_active: Optional[bool] = None


class AlertResponse(BaseModel):
    id: int
    name: str
    query: str
    condition: str
    threshold: Optional[float]
    is_active: bool
    last_checked_at: Optional[datetime]
    last_triggered_at: Optional[datetime]
    last_value: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[AlertResponse])
async def list_alerts(db: AsyncSession = Depends(get_db)):
    """List all data alerts."""
    query = select(DataAlert).order_by(DataAlert.created_at.desc())
    result = await db.execute(query)
    alerts = result.scalars().all()
    return [AlertResponse.model_validate(a) for a in alerts]


@router.post("", response_model=AlertResponse)
async def create_alert(
    data: AlertCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new data alert."""
    alert = DataAlert(
        name=data.name,
        query=data.query,
        condition=data.condition,
        threshold=data.threshold,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return AlertResponse.model_validate(alert)


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    data: AlertUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a data alert."""
    alert = await db.get(DataAlert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(alert, field, value)
    
    await db.commit()
    await db.refresh(alert)
    return AlertResponse.model_validate(alert)


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a data alert."""
    alert = await db.get(DataAlert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    await db.delete(alert)
    await db.commit()
    return {"status": "deleted"}
```

---

### Step 2: Scheduled Queries

#### 2.1 Query Scheduler

```python
# src/services/query_scheduler.py
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import structlog

from src.api.models.database import ScheduledQuery

logger = structlog.get_logger()


class QueryScheduler:
    """Service for scheduling query execution."""
    
    def __init__(self, session_factory):
        self.scheduler = AsyncIOScheduler()
        self.session_factory = session_factory
        self._running = False
    
    async def start(self):
        """Start the query scheduler."""
        if self._running:
            return
        
        # Load existing scheduled queries
        async with self.session_factory() as db:
            query = select(ScheduledQuery).where(ScheduledQuery.is_active == True)
            result = await db.execute(query)
            queries = result.scalars().all()
            
            for sq in queries:
                self._add_job(sq)
        
        self.scheduler.start()
        self._running = True
        logger.info("query_scheduler_started", job_count=len(queries))
    
    async def stop(self):
        """Stop the query scheduler."""
        if self._running:
            self.scheduler.shutdown()
            self._running = False
            logger.info("query_scheduler_stopped")
    
    def _add_job(self, scheduled_query: ScheduledQuery):
        """Add a job for a scheduled query."""
        try:
            trigger = CronTrigger.from_crontab(scheduled_query.cron_expression)
            self.scheduler.add_job(
                self._execute_query,
                trigger,
                args=[scheduled_query.id],
                id=f"scheduled_query_{scheduled_query.id}",
                replace_existing=True,
            )
            logger.info("scheduled_query_added", query_id=scheduled_query.id)
        except Exception as e:
            logger.error("scheduled_query_add_error", query_id=scheduled_query.id, error=str(e))
    
    def _remove_job(self, query_id: int):
        """Remove a scheduled query job."""
        job_id = f"scheduled_query_{query_id}"
        try:
            self.scheduler.remove_job(job_id)
            logger.info("scheduled_query_removed", query_id=query_id)
        except Exception:
            pass  # Job may not exist
    
    async def _execute_query(self, query_id: int):
        """Execute a scheduled query."""
        async with self.session_factory() as db:
            sq = await db.get(ScheduledQuery, query_id)
            if not sq or not sq.is_active:
                return
            
            try:
                result = await db.execute(text(sq.query))
                rows = result.fetchall()
                
                sq.last_run_at = datetime.utcnow()
                # Calculate next run time
                trigger = CronTrigger.from_crontab(sq.cron_expression)
                sq.next_run_at = trigger.get_next_fire_time(None, datetime.utcnow())
                
                await db.commit()
                
                logger.info("scheduled_query_executed", query_id=query_id, rows=len(rows))
                
                # Optionally store results or trigger notifications
                
            except Exception as e:
                logger.error("scheduled_query_error", query_id=query_id, error=str(e))
    
    async def add_scheduled_query(self, scheduled_query: ScheduledQuery):
        """Add a new scheduled query to the scheduler."""
        self._add_job(scheduled_query)
    
    async def update_scheduled_query(self, scheduled_query: ScheduledQuery):
        """Update an existing scheduled query."""
        self._remove_job(scheduled_query.id)
        if scheduled_query.is_active:
            self._add_job(scheduled_query)
    
    async def remove_scheduled_query(self, query_id: int):
        """Remove a scheduled query from the scheduler."""
        self._remove_job(query_id)
```

#### 2.2 Scheduled Query API

```python
# src/api/routes/scheduled_queries.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from apscheduler.triggers.cron import CronTrigger

from src.api.deps import get_db
from src.api.models.database import ScheduledQuery

router = APIRouter()


class ScheduledQueryCreate(BaseModel):
    name: str
    query: str
    cron_expression: str  # e.g., "0 8 * * *" for 8am daily


class ScheduledQueryUpdate(BaseModel):
    name: Optional[str] = None
    query: Optional[str] = None
    cron_expression: Optional[str] = None
    is_active: Optional[bool] = None


class ScheduledQueryResponse(BaseModel):
    id: int
    name: str
    query: str
    cron_expression: str
    is_active: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


def validate_cron(cron_expression: str) -> bool:
    """Validate a cron expression."""
    try:
        CronTrigger.from_crontab(cron_expression)
        return True
    except Exception:
        return False


@router.get("", response_model=List[ScheduledQueryResponse])
async def list_scheduled_queries(db: AsyncSession = Depends(get_db)):
    """List all scheduled queries."""
    query = select(ScheduledQuery).order_by(ScheduledQuery.created_at.desc())
    result = await db.execute(query)
    queries = result.scalars().all()
    return [ScheduledQueryResponse.model_validate(q) for q in queries]


@router.post("", response_model=ScheduledQueryResponse)
async def create_scheduled_query(
    data: ScheduledQueryCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new scheduled query."""
    if not validate_cron(data.cron_expression):
        raise HTTPException(status_code=400, detail="Invalid cron expression")
    
    # Calculate next run time
    trigger = CronTrigger.from_crontab(data.cron_expression)
    next_run = trigger.get_next_fire_time(None, datetime.utcnow())
    
    sq = ScheduledQuery(
        name=data.name,
        query=data.query,
        cron_expression=data.cron_expression,
        next_run_at=next_run,
    )
    db.add(sq)
    await db.commit()
    await db.refresh(sq)
    
    # Add to scheduler
    from src.api.deps import get_query_scheduler
    scheduler = get_query_scheduler()
    await scheduler.add_scheduled_query(sq)
    
    return ScheduledQueryResponse.model_validate(sq)


@router.delete("/{query_id}")
async def delete_scheduled_query(
    query_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a scheduled query."""
    sq = await db.get(ScheduledQuery, query_id)
    if not sq:
        raise HTTPException(status_code=404, detail="Scheduled query not found")
    
    # Remove from scheduler
    from src.api.deps import get_query_scheduler
    scheduler = get_query_scheduler()
    await scheduler.remove_scheduled_query(query_id)
    
    await db.delete(sq)
    await db.commit()
    return {"status": "deleted"}
```

---

### Step 3: Theme System

#### 3.1 Theme Presets

```typescript
// frontend/src/lib/themes.ts
export interface ThemeColors {
  background: string;
  foreground: string;
  card: string;
  cardForeground: string;
  primary: string;
  primaryForeground: string;
  secondary: string;
  secondaryForeground: string;
  muted: string;
  mutedForeground: string;
  accent: string;
  accentForeground: string;
  destructive: string;
  destructiveForeground: string;
  border: string;
  input: string;
  ring: string;
}

export interface Theme {
  id: string;
  name: string;
  description: string;
  isPreset: boolean;
  isDark: boolean;
  colors: ThemeColors;
}

export const themePresets: Theme[] = [
  {
    id: 'dark-default',
    name: 'Dark (Default)',
    description: 'Clean dark theme',
    isPreset: true,
    isDark: true,
    colors: {
      background: '222.2 84% 4.9%',
      foreground: '210 40% 98%',
      card: '222.2 84% 4.9%',
      cardForeground: '210 40% 98%',
      primary: '210 40% 98%',
      primaryForeground: '222.2 47.4% 11.2%',
      secondary: '217.2 32.6% 17.5%',
      secondaryForeground: '210 40% 98%',
      muted: '217.2 32.6% 17.5%',
      mutedForeground: '215 20.2% 65.1%',
      accent: '217.2 32.6% 17.5%',
      accentForeground: '210 40% 98%',
      destructive: '0 62.8% 30.6%',
      destructiveForeground: '210 40% 98%',
      border: '217.2 32.6% 17.5%',
      input: '217.2 32.6% 17.5%',
      ring: '212.7 26.8% 83.9%',
    },
  },
  {
    id: 'light-default',
    name: 'Light (Default)',
    description: 'Clean light theme',
    isPreset: true,
    isDark: false,
    colors: {
      background: '0 0% 100%',
      foreground: '222.2 84% 4.9%',
      card: '0 0% 100%',
      cardForeground: '222.2 84% 4.9%',
      primary: '222.2 47.4% 11.2%',
      primaryForeground: '210 40% 98%',
      secondary: '210 40% 96.1%',
      secondaryForeground: '222.2 47.4% 11.2%',
      muted: '210 40% 96.1%',
      mutedForeground: '215.4 16.3% 46.9%',
      accent: '210 40% 96.1%',
      accentForeground: '222.2 47.4% 11.2%',
      destructive: '0 84.2% 60.2%',
      destructiveForeground: '210 40% 98%',
      border: '214.3 31.8% 91.4%',
      input: '214.3 31.8% 91.4%',
      ring: '222.2 84% 4.9%',
    },
  },
  {
    id: 'ocean',
    name: 'Ocean',
    description: 'Deep blue ocean theme',
    isPreset: true,
    isDark: true,
    colors: {
      background: '220 65% 8%',
      foreground: '210 40% 98%',
      card: '220 60% 12%',
      cardForeground: '210 40% 98%',
      primary: '199 89% 48%',
      primaryForeground: '220 65% 8%',
      secondary: '220 50% 20%',
      secondaryForeground: '210 40% 98%',
      muted: '220 50% 20%',
      mutedForeground: '210 30% 70%',
      accent: '199 89% 48%',
      accentForeground: '220 65% 8%',
      destructive: '0 62.8% 40%',
      destructiveForeground: '210 40% 98%',
      border: '220 50% 20%',
      input: '220 50% 20%',
      ring: '199 89% 48%',
    },
  },
  {
    id: 'forest',
    name: 'Forest',
    description: 'Natural green theme',
    isPreset: true,
    isDark: true,
    colors: {
      background: '150 30% 6%',
      foreground: '150 10% 95%',
      card: '150 25% 10%',
      cardForeground: '150 10% 95%',
      primary: '142 76% 36%',
      primaryForeground: '150 30% 6%',
      secondary: '150 20% 18%',
      secondaryForeground: '150 10% 95%',
      muted: '150 20% 18%',
      mutedForeground: '150 10% 65%',
      accent: '142 76% 36%',
      accentForeground: '150 30% 6%',
      destructive: '0 62.8% 40%',
      destructiveForeground: '150 10% 95%',
      border: '150 20% 18%',
      input: '150 20% 18%',
      ring: '142 76% 36%',
    },
  },
  {
    id: 'sunset',
    name: 'Sunset',
    description: 'Warm orange and purple',
    isPreset: true,
    isDark: true,
    colors: {
      background: '270 30% 8%',
      foreground: '30 20% 95%',
      card: '270 25% 12%',
      cardForeground: '30 20% 95%',
      primary: '25 95% 53%',
      primaryForeground: '270 30% 8%',
      secondary: '270 20% 20%',
      secondaryForeground: '30 20% 95%',
      muted: '270 20% 20%',
      mutedForeground: '30 10% 65%',
      accent: '280 60% 50%',
      accentForeground: '30 20% 95%',
      destructive: '0 62.8% 40%',
      destructiveForeground: '30 20% 95%',
      border: '270 20% 20%',
      input: '270 20% 20%',
      ring: '25 95% 53%',
    },
  },
  {
    id: 'corporate',
    name: 'Corporate Blue',
    description: 'Professional business theme',
    isPreset: true,
    isDark: false,
    colors: {
      background: '0 0% 98%',
      foreground: '215 25% 15%',
      card: '0 0% 100%',
      cardForeground: '215 25% 15%',
      primary: '215 100% 40%',
      primaryForeground: '0 0% 100%',
      secondary: '215 20% 93%',
      secondaryForeground: '215 25% 15%',
      muted: '215 20% 93%',
      mutedForeground: '215 15% 50%',
      accent: '215 100% 40%',
      accentForeground: '0 0% 100%',
      destructive: '0 84.2% 60.2%',
      destructiveForeground: '0 0% 100%',
      border: '215 20% 88%',
      input: '215 20% 88%',
      ring: '215 100% 40%',
    },
  },
];

export function applyTheme(theme: Theme): void {
  const root = document.documentElement;
  
  // Set dark/light class
  root.classList.remove('light', 'dark');
  root.classList.add(theme.isDark ? 'dark' : 'light');
  
  // Apply CSS variables
  Object.entries(theme.colors).forEach(([key, value]) => {
    const cssKey = key.replace(/([A-Z])/g, '-$1').toLowerCase();
    root.style.setProperty(`--${cssKey}`, value);
  });
  
  // Save to localStorage
  localStorage.setItem('theme-id', theme.id);
  localStorage.setItem('theme-config', JSON.stringify(theme));
}

export function getStoredTheme(): Theme | null {
  const config = localStorage.getItem('theme-config');
  if (config) {
    try {
      return JSON.parse(config);
    } catch {
      return null;
    }
  }
  return null;
}
```

#### 3.2 Theme Selector Component

```typescript
// frontend/src/components/settings/ThemeSelector.tsx
import { useState } from 'react';
import { Check, Palette } from 'lucide-react';
import { themePresets, Theme, applyTheme } from '@/lib/themes';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';

interface ThemeSelectorProps {
  currentThemeId: string;
  customThemes?: Theme[];
  onThemeChange: (theme: Theme) => void;
}

export function ThemeSelector({
  currentThemeId,
  customThemes = [],
  onThemeChange,
}: ThemeSelectorProps) {
  const allThemes = [...themePresets, ...customThemes];

  const handleSelect = (theme: Theme) => {
    applyTheme(theme);
    onThemeChange(theme);
  };

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-medium">Theme Presets</h3>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
        {allThemes.map((theme) => (
          <button
            key={theme.id}
            onClick={() => handleSelect(theme)}
            className={cn(
              'relative flex flex-col items-start rounded-lg border p-3 text-left transition-all hover:border-primary',
              currentThemeId === theme.id && 'border-primary ring-2 ring-primary/20'
            )}
          >
            {/* Color preview */}
            <div className="mb-2 flex gap-1">
              <div
                className="h-4 w-4 rounded"
                style={{ backgroundColor: `hsl(${theme.colors.primary})` }}
              />
              <div
                className="h-4 w-4 rounded"
                style={{ backgroundColor: `hsl(${theme.colors.secondary})` }}
              />
              <div
                className="h-4 w-4 rounded"
                style={{ backgroundColor: `hsl(${theme.colors.accent})` }}
              />
            </div>
            
            <span className="text-sm font-medium">{theme.name}</span>
            <span className="text-xs text-muted-foreground">{theme.description}</span>
            
            {currentThemeId === theme.id && (
              <Check className="absolute right-2 top-2 h-4 w-4 text-primary" />
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
```

#### 3.3 Custom Theme Builder

```typescript
// frontend/src/components/settings/CustomThemeBuilder.tsx
import { useState } from 'react';
import { Theme, ThemeColors, applyTheme } from '@/lib/themes';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface CustomThemeBuilderProps {
  onSave: (theme: Theme) => void;
  initialTheme?: Theme;
}

const colorFields: (keyof ThemeColors)[] = [
  'background',
  'foreground',
  'primary',
  'secondary',
  'accent',
  'muted',
  'border',
];

export function CustomThemeBuilder({ onSave, initialTheme }: CustomThemeBuilderProps) {
  const [name, setName] = useState(initialTheme?.name || '');
  const [isDark, setIsDark] = useState(initialTheme?.isDark ?? true);
  const [colors, setColors] = useState<Partial<ThemeColors>>(
    initialTheme?.colors || {}
  );

  const handleColorChange = (key: keyof ThemeColors, value: string) => {
    setColors((prev) => ({ ...prev, [key]: value }));
  };

  const handlePreview = () => {
    const theme: Theme = {
      id: `custom-${Date.now()}`,
      name: name || 'Custom Theme',
      description: 'Custom theme',
      isPreset: false,
      isDark,
      colors: {
        ...getDefaultColors(isDark),
        ...colors,
      } as ThemeColors,
    };
    applyTheme(theme);
  };

  const handleSave = () => {
    const theme: Theme = {
      id: initialTheme?.id || `custom-${Date.now()}`,
      name: name || 'Custom Theme',
      description: 'Custom theme',
      isPreset: false,
      isDark,
      colors: {
        ...getDefaultColors(isDark),
        ...colors,
      } as ThemeColors,
    };
    onSave(theme);
  };

  return (
    <div className="space-y-6">
      <div>
        <label className="mb-1 block text-sm font-medium">Theme Name</label>
        <Input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="My Custom Theme"
        />
      </div>

      <div className="flex items-center gap-4">
        <label className="text-sm font-medium">Base Mode:</label>
        <button
          onClick={() => setIsDark(true)}
          className={cn(
            'rounded-md px-3 py-1 text-sm',
            isDark ? 'bg-primary text-primary-foreground' : 'bg-muted'
          )}
        >
          Dark
        </button>
        <button
          onClick={() => setIsDark(false)}
          className={cn(
            'rounded-md px-3 py-1 text-sm',
            !isDark ? 'bg-primary text-primary-foreground' : 'bg-muted'
          )}
        >
          Light
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {colorFields.map((field) => (
          <div key={field}>
            <label className="mb-1 block text-sm font-medium capitalize">
              {field.replace(/([A-Z])/g, ' $1')}
            </label>
            <div className="flex gap-2">
              <Input
                value={colors[field] || ''}
                onChange={(e) => handleColorChange(field, e.target.value)}
                placeholder="e.g., 210 40% 98%"
              />
              <input
                type="color"
                onChange={(e) => {
                  // Convert hex to HSL
                  const hsl = hexToHSL(e.target.value);
                  handleColorChange(field, hsl);
                }}
                className="h-10 w-10 cursor-pointer rounded border"
              />
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <Button variant="outline" onClick={handlePreview}>
          Preview
        </Button>
        <Button onClick={handleSave}>Save Theme</Button>
      </div>
    </div>
  );
}

function getDefaultColors(isDark: boolean): ThemeColors {
  // Return default dark or light colors
  return isDark
    ? themePresets.find((t) => t.id === 'dark-default')!.colors
    : themePresets.find((t) => t.id === 'light-default')!.colors;
}

function hexToHSL(hex: string): string {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;

  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);

    switch (max) {
      case r:
        h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
        break;
      case g:
        h = ((b - r) / d + 2) / 6;
        break;
      case b:
        h = ((r - g) / d + 4) / 6;
        break;
    }
  }

  return `${Math.round(h * 360)} ${Math.round(s * 100)}% ${Math.round(l * 100)}%`;
}
```

---

### Step 4: Dashboard Sharing

#### 4.1 Backend Share Endpoints

```python
# src/api/routes/dashboards.py (add to existing)
import secrets
from datetime import datetime, timedelta

@router.post("/{dashboard_id}/share")
async def create_share_link(
    dashboard_id: int,
    expires_in_days: int = 7,
    db: AsyncSession = Depends(get_db),
):
    """Create a public share link for a dashboard."""
    dashboard = await db.get(Dashboard, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    # Generate token
    token = secrets.token_urlsafe(32)
    dashboard.share_token = token
    dashboard.share_expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
    
    await db.commit()
    
    return {
        "share_url": f"/shared/{token}",
        "expires_at": dashboard.share_expires_at.isoformat(),
    }


@router.delete("/{dashboard_id}/share")
async def revoke_share_link(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Revoke the share link for a dashboard."""
    dashboard = await db.get(Dashboard, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    dashboard.share_token = None
    dashboard.share_expires_at = None
    await db.commit()
    
    return {"status": "revoked"}


@router.get("/shared/{token}")
async def get_shared_dashboard(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a shared dashboard by token."""
    query = select(Dashboard).where(Dashboard.share_token == token)
    result = await db.execute(query)
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    if dashboard.share_expires_at and dashboard.share_expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Share link has expired")
    
    # Get widgets
    widgets_query = select(DashboardWidget).where(
        DashboardWidget.dashboard_id == dashboard.id
    )
    widgets_result = await db.execute(widgets_query)
    widgets = widgets_result.scalars().all()
    
    return {
        "dashboard": DashboardResponse.model_validate(dashboard),
        "widgets": [format_widget(w) for w in widgets],
    }
```

#### 4.2 Share Dialog Component

```typescript
// frontend/src/components/dialogs/ShareDashboardDialog.tsx
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import * as Dialog from '@radix-ui/react-dialog';
import { X, Copy, Check, Link, Trash2 } from 'lucide-react';
import { api } from '@/api/client';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface ShareDashboardDialogProps {
  open: boolean;
  onClose: () => void;
  dashboardId: number;
  existingShareUrl?: string;
  expiresAt?: string;
}

export function ShareDashboardDialog({
  open,
  onClose,
  dashboardId,
  existingShareUrl,
  expiresAt,
}: ShareDashboardDialogProps) {
  const queryClient = useQueryClient();
  const [copied, setCopied] = useState(false);
  const [expiresInDays, setExpiresInDays] = useState(7);

  const createShareMutation = useMutation({
    mutationFn: () =>
      api.post<{ share_url: string; expires_at: string }>(
        `/dashboards/${dashboardId}/share`,
        { expires_in_days: expiresInDays }
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
    },
  });

  const revokeShareMutation = useMutation({
    mutationFn: () => api.delete(`/dashboards/${dashboardId}/share`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
    },
  });

  const shareUrl = existingShareUrl
    ? `${window.location.origin}${existingShareUrl}`
    : createShareMutation.data?.share_url
      ? `${window.location.origin}${createShareMutation.data.share_url}`
      : null;

  const handleCopy = () => {
    if (shareUrl) {
      navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-card p-6 shadow-lg">
          <Dialog.Title className="flex items-center gap-2 text-lg font-semibold">
            <Link className="h-5 w-5" />
            Share Dashboard
          </Dialog.Title>

          <div className="mt-4 space-y-4">
            {shareUrl ? (
              <>
                <div>
                  <label className="mb-1 block text-sm font-medium">
                    Share Link
                  </label>
                  <div className="flex gap-2">
                    <Input value={shareUrl} readOnly className="flex-1" />
                    <Button variant="outline" size="icon" onClick={handleCopy}>
                      {copied ? (
                        <Check className="h-4 w-4 text-green-500" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>

                {(expiresAt || createShareMutation.data?.expires_at) && (
                  <p className="text-sm text-muted-foreground">
                    Expires:{' '}
                    {new Date(
                      expiresAt || createShareMutation.data!.expires_at
                    ).toLocaleDateString()}
                  </p>
                )}

                <Button
                  variant="destructive"
                  onClick={() => revokeShareMutation.mutate()}
                  disabled={revokeShareMutation.isPending}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Revoke Link
                </Button>
              </>
            ) : (
              <>
                <div>
                  <label className="mb-1 block text-sm font-medium">
                    Link expires in
                  </label>
                  <select
                    value={expiresInDays}
                    onChange={(e) => setExpiresInDays(parseInt(e.target.value))}
                    className="w-full rounded-md border bg-background px-3 py-2"
                  >
                    <option value={1}>1 day</option>
                    <option value={7}>7 days</option>
                    <option value={30}>30 days</option>
                    <option value={90}>90 days</option>
                  </select>
                </div>

                <div className="rounded-md bg-muted p-3">
                  <p className="text-sm text-muted-foreground">
                    Anyone with this link will be able to view this dashboard
                    without logging in.
                  </p>
                </div>

                <Button
                  onClick={() => createShareMutation.mutate()}
                  disabled={createShareMutation.isPending}
                  className="w-full"
                >
                  Create Share Link
                </Button>
              </>
            )}
          </div>

          <Dialog.Close asChild>
            <button
              className="absolute right-4 top-4 rounded-sm opacity-70 hover:opacity-100"
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
```

---

### Step 5: Onboarding Wizard

```typescript
// frontend/src/components/onboarding/OnboardingWizard.tsx
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import * as Dialog from '@radix-ui/react-dialog';
import { 
  CheckCircle, 
  XCircle, 
  Loader2, 
  Database, 
  Cpu, 
  Box,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import { api } from '@/api/client';
import { HealthStatus } from '@/types';
import { Button } from '@/components/ui/Button';

const ONBOARDING_KEY = 'onboarding-complete';

export function OnboardingWizard() {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);

  // Check if onboarding is needed
  useEffect(() => {
    const complete = localStorage.getItem(ONBOARDING_KEY);
    if (!complete) {
      setOpen(true);
    }
  }, []);

  const { data: health, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.get<HealthStatus>('/health'),
    enabled: open && step === 1,
    refetchInterval: 2000, // Poll while checking
  });

  const handleComplete = () => {
    localStorage.setItem(ONBOARDING_KEY, 'true');
    setOpen(false);
  };

  const steps = [
    {
      title: 'Welcome to Research Analytics',
      content: (
        <div className="space-y-4 text-center">
          <Sparkles className="mx-auto h-16 w-16 text-primary" />
          <p className="text-lg">
            Your AI-powered research analytics platform is ready.
          </p>
          <p className="text-muted-foreground">
            Let's make sure everything is set up correctly.
          </p>
        </div>
      ),
    },
    {
      title: 'System Health Check',
      content: (
        <div className="space-y-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : (
            <div className="space-y-3">
              <ServiceStatus
                name="SQL Server"
                icon={Database}
                status={health?.services.find(s => s.name === 'sql_server')?.status}
              />
              <ServiceStatus
                name="Redis"
                icon={Box}
                status={health?.services.find(s => s.name === 'redis')?.status}
              />
              <ServiceStatus
                name="Ollama"
                icon={Cpu}
                status={health?.services.find(s => s.name === 'ollama')?.status}
              />
            </div>
          )}
          
          {health?.status === 'unhealthy' && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm">
              Some services are not healthy. Please check your Docker containers.
            </div>
          )}
        </div>
      ),
    },
    {
      title: 'Try Some Queries',
      content: (
        <div className="space-y-4">
          <p className="text-muted-foreground">
            Here are some example queries to get you started:
          </p>
          <div className="space-y-2">
            {[
              'Show me total funding by department',
              'List the top 10 researchers by publication count',
              'What projects started this year?',
              'Compare experiment success rates across departments',
            ].map((query, i) => (
              <div
                key={i}
                className="cursor-pointer rounded-md bg-muted p-3 text-sm hover:bg-accent"
                onClick={() => {
                  // Could copy to clipboard or navigate to chat
                  navigator.clipboard.writeText(query);
                }}
              >
                "{query}"
              </div>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">
            Click any query to copy it
          </p>
        </div>
      ),
    },
  ];

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 w-full max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-card p-6 shadow-lg">
          {/* Progress dots */}
          <div className="mb-6 flex justify-center gap-2">
            {steps.map((_, i) => (
              <div
                key={i}
                className={`h-2 w-2 rounded-full transition-colors ${
                  i === step ? 'bg-primary' : 'bg-muted'
                }`}
              />
            ))}
          </div>

          <Dialog.Title className="mb-4 text-center text-xl font-semibold">
            {steps[step].title}
          </Dialog.Title>

          <div className="mb-6">{steps[step].content}</div>

          <div className="flex justify-between">
            {step > 0 ? (
              <Button variant="outline" onClick={() => setStep(step - 1)}>
                Back
              </Button>
            ) : (
              <div />
            )}
            
            {step < steps.length - 1 ? (
              <Button onClick={() => setStep(step + 1)}>
                Next
                <ChevronRight className="ml-2 h-4 w-4" />
              </Button>
            ) : (
              <Button onClick={handleComplete}>
                Get Started
              </Button>
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function ServiceStatus({
  name,
  icon: Icon,
  status,
}: {
  name: string;
  icon: typeof Database;
  status?: string;
}) {
  return (
    <div className="flex items-center justify-between rounded-md border p-3">
      <div className="flex items-center gap-3">
        <Icon className="h-5 w-5 text-muted-foreground" />
        <span>{name}</span>
      </div>
      {status === 'healthy' ? (
        <CheckCircle className="h-5 w-5 text-green-500" />
      ) : status === 'unhealthy' ? (
        <XCircle className="h-5 w-5 text-red-500" />
      ) : (
        <Loader2 className="h-5 w-5 animate-spin" />
      )}
    </div>
  );
}
```

---

### Step 6: Keyboard Shortcuts

```typescript
// frontend/src/hooks/useKeyboardShortcuts.ts
import { useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

interface Shortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  action: () => void;
  description: string;
}

export function useKeyboardShortcuts() {
  const navigate = useNavigate();

  const shortcuts: Shortcut[] = [
    {
      key: 'k',
      ctrl: true,
      action: () => {
        // Open command palette / quick search
        document.dispatchEvent(new CustomEvent('open-command-palette'));
      },
      description: 'Open command palette',
    },
    {
      key: 'n',
      ctrl: true,
      action: () => navigate('/chat'),
      description: 'New chat',
    },
    {
      key: 'd',
      ctrl: true,
      action: () => navigate('/dashboards'),
      description: 'Go to dashboards',
    },
    {
      key: 's',
      ctrl: true,
      action: () => navigate('/settings'),
      description: 'Go to settings',
    },
    {
      key: '/',
      action: () => {
        // Focus chat input
        const input = document.querySelector<HTMLTextAreaElement>('[data-chat-input]');
        input?.focus();
      },
      description: 'Focus chat input',
    },
    {
      key: 'Escape',
      action: () => {
        // Close any open dialogs
        document.dispatchEvent(new CustomEvent('close-dialogs'));
      },
      description: 'Close dialogs',
    },
  ];

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Don't trigger shortcuts when typing in inputs
    if (
      e.target instanceof HTMLInputElement ||
      e.target instanceof HTMLTextAreaElement
    ) {
      // Allow Escape and Ctrl shortcuts in inputs
      if (e.key !== 'Escape' && !e.ctrlKey) {
        return;
      }
    }

    for (const shortcut of shortcuts) {
      const ctrlMatch = shortcut.ctrl ? e.ctrlKey || e.metaKey : !e.ctrlKey && !e.metaKey;
      const shiftMatch = shortcut.shift ? e.shiftKey : !e.shiftKey;
      const altMatch = shortcut.alt ? e.altKey : !e.altKey;

      if (
        e.key.toLowerCase() === shortcut.key.toLowerCase() &&
        ctrlMatch &&
        shiftMatch &&
        altMatch
      ) {
        e.preventDefault();
        shortcut.action();
        break;
      }
    }
  }, [shortcuts]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return shortcuts;
}

// frontend/src/components/dialogs/KeyboardShortcutsDialog.tsx
import * as Dialog from '@radix-ui/react-dialog';
import { X, Keyboard } from 'lucide-react';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';

export function KeyboardShortcutsDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const shortcuts = useKeyboardShortcuts();

  return (
    <Dialog.Root open={open} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-card p-6 shadow-lg">
          <Dialog.Title className="flex items-center gap-2 text-lg font-semibold">
            <Keyboard className="h-5 w-5" />
            Keyboard Shortcuts
          </Dialog.Title>

          <div className="mt-4 space-y-2">
            {shortcuts.map((shortcut, i) => (
              <div
                key={i}
                className="flex items-center justify-between py-2"
              >
                <span className="text-sm text-muted-foreground">
                  {shortcut.description}
                </span>
                <kbd className="rounded bg-muted px-2 py-1 text-xs font-mono">
                  {shortcut.ctrl && 'Ctrl+'}
                  {shortcut.shift && 'Shift+'}
                  {shortcut.alt && 'Alt+'}
                  {shortcut.key.toUpperCase()}
                </kbd>
              </div>
            ))}
          </div>

          <Dialog.Close asChild>
            <button
              className="absolute right-4 top-4 rounded-sm opacity-70 hover:opacity-100"
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
```

---

### Step 7: Toast Notifications

```typescript
// frontend/src/components/ui/Toast.tsx
import { useEffect, useState } from 'react';
import * as ToastPrimitive from '@radix-ui/react-toast';
import { X, AlertCircle, CheckCircle, Info } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'info' | 'alert';
  title: string;
  description?: string;
  duration?: number;
}

const icons = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
  alert: AlertCircle,
};

const colors = {
  success: 'border-green-500 bg-green-500/10',
  error: 'border-red-500 bg-red-500/10',
  info: 'border-blue-500 bg-blue-500/10',
  alert: 'border-yellow-500 bg-yellow-500/10',
};

// Global toast state
let toastListeners: ((toasts: Toast[]) => void)[] = [];
let toasts: Toast[] = [];

export function addToast(toast: Omit<Toast, 'id'>) {
  const id = Math.random().toString(36).slice(2);
  const newToast = { ...toast, id };
  toasts = [...toasts, newToast];
  toastListeners.forEach(listener => listener(toasts));
  
  // Auto-remove after duration
  const duration = toast.duration ?? 5000;
  if (duration > 0) {
    setTimeout(() => removeToast(id), duration);
  }
}

export function removeToast(id: string) {
  toasts = toasts.filter(t => t.id !== id);
  toastListeners.forEach(listener => listener(toasts));
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [currentToasts, setCurrentToasts] = useState<Toast[]>([]);

  useEffect(() => {
    const listener = (newToasts: Toast[]) => setCurrentToasts([...newToasts]);
    toastListeners.push(listener);
    return () => {
      toastListeners = toastListeners.filter(l => l !== listener);
    };
  }, []);

  return (
    <ToastPrimitive.Provider swipeDirection="right">
      {children}
      
      {currentToasts.map((toast) => {
        const Icon = icons[toast.type];
        return (
          <ToastPrimitive.Root
            key={toast.id}
            className={cn(
              'rounded-lg border p-4 shadow-lg',
              colors[toast.type]
            )}
          >
            <div className="flex gap-3">
              <Icon className={cn('h-5 w-5', {
                'text-green-500': toast.type === 'success',
                'text-red-500': toast.type === 'error',
                'text-blue-500': toast.type === 'info',
                'text-yellow-500': toast.type === 'alert',
              })} />
              <div className="flex-1">
                <ToastPrimitive.Title className="font-medium">
                  {toast.title}
                </ToastPrimitive.Title>
                {toast.description && (
                  <ToastPrimitive.Description className="mt-1 text-sm text-muted-foreground">
                    {toast.description}
                  </ToastPrimitive.Description>
                )}
              </div>
              <ToastPrimitive.Close
                className="rounded-sm opacity-70 hover:opacity-100"
                onClick={() => removeToast(toast.id)}
              >
                <X className="h-4 w-4" />
              </ToastPrimitive.Close>
            </div>
          </ToastPrimitive.Root>
        );
      })}

      <ToastPrimitive.Viewport className="fixed bottom-4 right-4 z-50 flex w-96 flex-col gap-2" />
    </ToastPrimitive.Provider>
  );
}
```

---

### Step 8: Alert Notification Integration

```typescript
// frontend/src/hooks/useAlertNotifications.ts
import { useEffect } from 'react';
import { addToast } from '@/components/ui/Toast';

export function useAlertNotifications() {
  useEffect(() => {
    // Connect to notification WebSocket
    const ws = new WebSocket(`${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/notifications`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'alert') {
        // Show toast notification
        addToast({
          type: 'alert',
          title: data.data.name,
          description: data.data.message,
          duration: 10000,
        });

        // Request browser notification permission and show
        if (Notification.permission === 'granted') {
          new Notification(data.data.name, {
            body: data.data.message,
            icon: '/icon.png',
          });
        } else if (Notification.permission !== 'denied') {
          Notification.requestPermission().then((permission) => {
            if (permission === 'granted') {
              new Notification(data.data.name, {
                body: data.data.message,
                icon: '/icon.png',
              });
            }
          });
        }
      }
    };

    return () => ws.close();
  }, []);
}
```

---

## File Structure After Phase 2.5

```
src/
├── services/
│   ├── alert_scheduler.py
│   ├── query_scheduler.py
│   └── notification_service.py
└── api/routes/
    ├── alerts.py
    └── scheduled_queries.py

frontend/src/
├── lib/
│   └── themes.ts
├── components/
│   ├── settings/
│   │   ├── ThemeSelector.tsx
│   │   └── CustomThemeBuilder.tsx
│   ├── dialogs/
│   │   ├── ShareDashboardDialog.tsx
│   │   └── KeyboardShortcutsDialog.tsx
│   ├── onboarding/
│   │   └── OnboardingWizard.tsx
│   └── ui/
│       └── Toast.tsx
└── hooks/
    ├── useKeyboardShortcuts.ts
    └── useAlertNotifications.ts
```

---

## Validation Checkpoints

1. **Data alerts:**
   - Create alert with condition
   - Alert triggers when condition met
   - Toast notification appears
   - Browser notification works

2. **Scheduled queries:**
   - Create scheduled query with cron
   - Query executes at scheduled time
   - Last run time updates

3. **Theme system:**
   - Preset themes apply correctly
   - Custom theme builder works
   - Theme persists on refresh

4. **Dashboard sharing:**
   - Generate share link
   - Shared dashboard accessible
   - Revoke link works
   - Expired links rejected

5. **Onboarding:**
   - Wizard shows on first visit
   - Health checks display correctly
   - Doesn't show again after completion

6. **Keyboard shortcuts:**
   - All shortcuts work
   - Shortcuts dialog displays correctly

---

## Notes for Implementation

- Use APScheduler for Python scheduling (not Celery)
- Browser notifications require HTTPS or localhost
- Store custom themes in database for persistence
- Share tokens should be cryptographically random
- Onboarding completion stored in localStorage
