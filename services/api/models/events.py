from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class EventType(str, Enum):
    """Event type enumeration"""
    PHASE_START = "phase_start"
    PHASE_COMPLETE = "phase_complete"
    STEP_START = "step_start"
    STEP_COMPLETE = "step_complete"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    MILESTONE = "milestone"

class ProjectEvent(BaseModel):
    """Project event model"""
    event_type: EventType
    phase: Optional[str] = None
    step_name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[dict] = Field(default_factory=dict)
    success: bool = True
    
    class Config:
        use_enum_values = True

class EventResponse(BaseModel):
    """Event response model"""
    id: int
    created_at: datetime
    event_type: str
    phase: Optional[str]
    step_name: Optional[str]
    description: Optional[str]
    success: bool
    
class TimelineStats(BaseModel):
    """Timeline statistics model"""
    date: str
    total_events: int
    successful_events: int
    failed_events: int
    phases_active: List[str]
    
class SystemHealth(BaseModel):
    """System health model"""
    total_events_today: int
    successful_today: int
    success_rate: float
