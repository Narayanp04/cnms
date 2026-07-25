"""ConnectXperts NMS - SLA Report Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from app.models.sla_report import SLAReportPeriod


class SLAReportResponse(BaseModel):
    id: int
    device_id: int
    customer_id: Optional[int] = None
    period: SLAReportPeriod
    period_start: datetime
    period_end: datetime
    availability_percent: float
    uptime_seconds: int
    downtime_seconds: int
    total_pings: int
    successful_pings: int
    failed_pings: int
    avg_latency_ms: Optional[float] = None
    max_latency_ms: Optional[float] = None
    min_latency_ms: Optional[float] = None
    avg_packet_loss_percent: Optional[float] = None
    outage_count: int
    total_outage_duration: int
    longest_outage_duration: int
    outage_events: Optional[Any] = None
    sla_target_percent: float
    sla_met: bool
    generated_at: datetime
    
    class Config:
        from_attributes = True


class SLAReportGenerate(BaseModel):
    device_ids: List[int]
    period: SLAReportPeriod
    period_start: datetime
    period_end: datetime


class SLAReportListResponse(BaseModel):
    total: int
    items: List[SLAReportResponse]
    page: int
    page_size: int
    total_pages: int


class SLAReportExport(BaseModel):
    format: str = Field(..., pattern="^(pdf|excel|csv)$")
    report_ids: List[int]
