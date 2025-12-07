from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import date, datetime
import os
from supabase import create_client, Client

from api.models.events import (
    ProjectEvent,
    EventResponse,
    TimelineStats,
    SystemHealth,
    EventType
)

router = APIRouter(prefix="/events", tags=["events"])

def get_supabase() -> Client:
    """Get Supabase client"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise HTTPException(status_code=500, detail="Supabase credentials not configured")
    return create_client(url, key)

@router.post("/", response_model=EventResponse, status_code=201)
async def create_event(
    event: ProjectEvent,
    supabase: Client = Depends(get_supabase)
):
    """Create a new project event"""
    try:
        result = supabase.table("project_events").insert({
            "event_type": event.event_type,
            "phase": event.phase,
            "step_name": event.step_name,
            "description": event.description,
            "metadata": event.metadata,
            "success": event.success
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create event")
            
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[EventResponse])
async def get_events(
    limit: int = 100,
    phase: Optional[str] = None,
    event_type: Optional[EventType] = None,
    supabase: Client = Depends(get_supabase)
):
    """Get recent events with optional filters"""
    try:
        query = supabase.table("project_events").select("*")
        
        if phase:
            query = query.eq("phase", phase)
        if event_type:
            query = query.eq("event_type", event_type.value)
            
        result = query.order("created_at", desc=True).limit(limit).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent", response_model=List[EventResponse])
async def get_recent_events(
    limit: int = 20,
    supabase: Client = Depends(get_supabase)
):
    """Get most recent events using v_recent_events view"""
    try:
        result = supabase.table("v_recent_events").select("*").limit(limit).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/timeline", response_model=List[TimelineStats])
async def get_timeline(
    days: int = 7,
    supabase: Client = Depends(get_supabase)
):
    """Get timeline statistics"""
    try:
        result = supabase.table("project_timeline")\
            .select("*")\
            .order("date", desc=True)\
            .limit(days)\
            .execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=SystemHealth)
async def get_system_health(
    supabase: Client = Depends(get_supabase)
):
    """Get system health status"""
    try:
        result = supabase.table("v_system_health").select("*").limit(1).execute()
        if not result.data:
            return SystemHealth(
                total_events_today=0,
                successful_today=0,
                success_rate=0.0
            )
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-phase")
async def get_events_by_phase(
    supabase: Client = Depends(get_supabase)
):
    """Get events grouped by phase"""
    try:
        result = supabase.table("v_events_by_phase").select("*").execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/phase-progress")
async def get_phase_progress(
    supabase: Client = Depends(get_supabase)
):
    """Get progress by phase"""
    try:
        result = supabase.table("v_phase_progress").select("*").execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
