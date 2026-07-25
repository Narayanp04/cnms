"""ConnectXperts NMS - Ping Result Schemas"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.ping_result import PingStatus


class PingResultResponse(BaseModel):
    id: int
    device_id: int
    status: PingStatus
    latency_ms: Optional[float] = None
    packet_loss_percent: Optional[float] = None
    jitter_ms: Optional[float] = None
    response_time_ms: Optional[float] = None
    ttl: Optional[int] = None
    packet_size: Optional[int] = None
    rtt_min: Optional[float] = None
    rtt_max: Optional[float] = None
    rtt_avg: Optional[float] = None
    error_message: Optional[str] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True


class PingHistoryQuery(BaseModel):
    hours: Optional[int] = None
    days: Optional[int] = None
    
    # Specific time range
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class PingChartData(BaseModel):
    timestamps: List[datetime]
    latency: List[Optional[float]]
    packet_loss: List[Optional[float]]
    jitter: List[Optional[float]]
    response_time: List[Optional[float]]
    status: List[str]


class PingStats(BaseModel):
    device_id: int
    total_pings: int
    successful_pings: int
    failed_pings: int
    availability: float
    avg_latency: Optional[float] = None
    max_latency: Optional[float] = None
    min_latency: Optional[float] = None
    avg_packet_loss: Optional[float] = None
    avg_jitter: Optional[float] = None
    start_time: datetime
    end_time: datetime
