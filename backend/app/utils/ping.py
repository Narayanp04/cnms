"""ConnectXperts NMS - ICMP Ping Utilities"""
import asyncio
import time
import statistics
from typing import Dict, Optional, Tuple
from ping3 import ping as ping3_ping
from app.config import settings


async def async_ping_device(
    ip_address: str,
    timeout: float = None,
    count: int = None
) -> Dict:
    """
    Asynchronously ping a device and return detailed results.
    
    Returns:
        Dict with keys: status, latency_ms, packet_loss_percent, 
                        jitter_ms, response_time_ms, rtt_min, rtt_max, 
                        rtt_avg, error_message
    """
    timeout = timeout or settings.PING_TIMEOUT
    count = count or settings.PING_COUNT
    
    result = {
        "status": "failure",
        "latency_ms": None,
        "packet_loss_percent": 100.0,
        "jitter_ms": None,
        "response_time_ms": None,
        "ttl": None,
        "packet_size": None,
        "rtt_min": None,
        "rtt_max": None,
        "rtt_avg": None,
        "error_message": None,
    }
    
    rtt_values = []
    successful_pings = 0
    
    for i in range(count):
        try:
            start_time = time.time()
            # ping3 returns None on timeout, False on error, or RTT in seconds
            rtt = await asyncio.to_thread(
                ping3_ping,
                ip_address,
                timeout=timeout,
                unit='ms'  # Return milliseconds
            )
            
            if rtt is not None and rtt is not False and rtt >= 0:
                successful_pings += 1
                rtt_values.append(rtt)
            elif rtt is None:
                pass  # Timeout, no RTT
            elif rtt is False:
                pass  # Error
                
        except Exception as e:
            result["error_message"] = str(e)
    
    if successful_pings > 0:
        result["status"] = "success"
        result["packet_loss_percent"] = ((count - successful_pings) / count) * 100
        result["rtt_min"] = min(rtt_values)
        result["rtt_max"] = max(rtt_values)
        result["rtt_avg"] = sum(rtt_values) / len(rtt_values)
        result["latency_ms"] = result["rtt_avg"]
        result["response_time_ms"] = result["rtt_avg"]
        
        if len(rtt_values) > 1:
            result["jitter_ms"] = statistics.stdev(rtt_values)
        else:
            result["jitter_ms"] = 0.0
    else:
        result["status"] = "failure"
        result["packet_loss_percent"] = 100.0
        if not result["error_message"]:
            result["error_message"] = "No response received from device"
    
    return result


def ping_device_sync(
    ip_address: str,
    timeout: float = None,
    count: int = None
) -> Dict:
    """
    Synchronously ping a device (for Celery tasks).
    """
    timeout = timeout or settings.PING_TIMEOUT
    count = count or settings.PING_COUNT
    
    result = {
        "status": "failure",
        "latency_ms": None,
        "packet_loss_percent": 100.0,
        "jitter_ms": None,
        "response_time_ms": None,
        "ttl": None,
        "packet_size": None,
        "rtt_min": None,
        "rtt_max": None,
        "rtt_avg": None,
        "error_message": None,
    }
    
    rtt_values = []
    successful_pings = 0
    
    for i in range(count):
        try:
            rtt = ping3_ping(
                ip_address,
                timeout=timeout,
                unit='ms'
            )
            
            if rtt is not None and rtt is not False and rtt >= 0:
                successful_pings += 1
                rtt_values.append(rtt)
                
        except Exception as e:
            result["error_message"] = str(e)
    
    if successful_pings > 0:
        result["status"] = "success"
        result["packet_loss_percent"] = ((count - successful_pings) / count) * 100
        result["rtt_min"] = min(rtt_values)
        result["rtt_max"] = max(rtt_values)
        result["rtt_avg"] = sum(rtt_values) / len(rtt_values)
        result["latency_ms"] = result["rtt_avg"]
        result["response_time_ms"] = result["rtt_avg"]
        
        if len(rtt_values) > 1:
            result["jitter_ms"] = statistics.stdev(rtt_values)
        else:
            result["jitter_ms"] = 0.0
    else:
        result["status"] = "failure"
        result["packet_loss_percent"] = 100.0
        if not result["error_message"]:
            result["error_message"] = "No response received from device"
    
    return result
