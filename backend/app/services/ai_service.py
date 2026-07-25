"""ConnectXperts NMS - AI Analysis Engine"""
import logging
import statistics
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Tuple
from collections import defaultdict
import numpy as np
from sqlalchemy import select, func

from app.database import AsyncSessionLocal
from app.models.device import Device, DeviceStatus
from app.models.ping_result import PingResult, PingStatus

logger = logging.getLogger(__name__)


class AIService:
    """AI-powered network analysis engine for detecting patterns and anomalies."""
    
    async def analyze_device(self, device_id: int) -> Dict:
        """Comprehensive AI analysis for a single device."""
        async with AsyncSessionLocal() as db:
            device_result = await db.execute(
                select(Device).where(Device.id == device_id)
            )
            device = device_result.scalar_one_or_none()
            if not device:
                return {"error": "Device not found"}
            
            now = datetime.now(timezone.utc)
            
            # Get ping results for different time windows
            ping_24h = await self._get_ping_results(db, device_id, now - timedelta(hours=24))
            ping_7d = await self._get_ping_results(db, device_id, now - timedelta(days=7))
            ping_14d = await self._get_ping_results(db, device_id, now - timedelta(days=14))
            ping_30d = await self._get_ping_results(db, device_id, now - timedelta(days=30))
            
            analysis = {
                "device_id": device_id,
                "hostname": device.hostname,
                "ip_address": device.ip_address,
                "analysis_timestamp": now.isoformat(),
                
                # Pattern Detection
                "patterns": await self._detect_patterns(ping_14d),
                
                # Anomaly Detection
                "anomalies": await self._detect_anomalies(ping_24h, ping_7d),
                
                # Predictive Analysis
                "predictions": await self._predict_failure(ping_30d),
                
                # Health Scores
                "health_scores": await self._calculate_health_scores(device, ping_7d),
                
                # ISP Quality Score
                "isp_quality_score": await self._calculate_isp_quality_score(ping_30d),
                
                # Recommendations
                "recommendations": await self._generate_recommendations(device, ping_7d),
                
                # AI Summary
                "ai_summary": None  # Will be filled below
            }
            
            # Generate AI summary
            analysis["ai_summary"] = self._generate_ai_summary(analysis)
            
            return analysis
    
    async def _get_ping_results(self, db, device_id: int, since: datetime) -> List:
        """Get ping results for analysis."""
        result = await db.execute(
            select(PingResult).where(
                PingResult.device_id == device_id,
                PingResult.timestamp >= since
            ).order_by(PingResult.timestamp.asc())
        )
        return result.scalars().all()
    
    async def _detect_patterns(self, ping_results: List) -> Dict:
        """Detect patterns in ping results."""
        if not ping_results:
            return {"patterns_found": False, "details": "Insufficient data"}
        
        patterns = {
            "patterns_found": False,
            "evening_packet_loss": None,
            "morning_latency_spikes": None,
            "weekend_stability": None,
            "recurring_outages": [],
            "details": []
        }
        
        # Analyze hourly patterns
        hourly_stats = defaultdict(lambda: {"latencies": [], "packet_losses": [], "failures": 0})
        
        for pr in ping_results:
            hour = pr.timestamp.hour
            hourly_stats[hour]["latencies"].append(pr.latency_ms or 0)
            hourly_stats[hour]["packet_losses"].append(pr.packet_loss_percent or 0)
            if pr.status == PingStatus.FAILURE:
                hourly_stats[hour]["failures"] += 1
        
        # Evening packet loss (7PM - 9PM)
        evening_losses = []
        for h in range(19, 22):
            if h in hourly_stats:
                evening_losses.extend(hourly_stats[h]["packet_losses"])
        
        if evening_losses and statistics.mean(evening_losses) > 3:
            patterns["evening_packet_loss"] = {
                "detected": True,
                "avg_packet_loss": round(statistics.mean(evening_losses), 2),
                "period": "7PM - 9PM"
            }
            patterns["patterns_found"] = True
            patterns["details"].append(
                f"Packet loss detected every evening between 7PM and 9PM "
                f"(avg: {statistics.mean(evening_losses):.1f}%)"
            )
        
        # Morning latency spikes (8AM - 10AM)
        morning_latencies = []
        for h in range(8, 11):
            if h in hourly_stats:
                morning_latencies.extend(hourly_stats[h]["latencies"])
        
        if morning_latencies and statistics.mean(morning_latencies) > 100:
            patterns["morning_latency_spikes"] = {
                "detected": True,
                "avg_latency": round(statistics.mean(morning_latencies), 2),
                "period": "8AM - 10AM"
            }
            patterns["patterns_found"] = True
        
        # Detect recurring outages (same time each day)
        daily_outages = defaultdict(list)
        for pr in ping_results:
            if pr.status == PingStatus.FAILURE:
                day_key = pr.timestamp.strftime("%H:%M")
                daily_outages[day_key].append(pr.timestamp.date().isoformat())
        
        for time_key, dates in daily_outages.items():
            if len(dates) >= 3:
                patterns["recurring_outages"].append({
                    "time": time_key,
                    "occurrences": len(dates),
                    "dates": dates
                })
                patterns["patterns_found"] = True
        
        return patterns
    
    async def _detect_anomalies(self, recent: List, historical: List) -> Dict:
        """Detect anomalies in the recent data compared to historical."""
        if not recent or not historical:
            return {"anomalies_found": False, "details": "Insufficient data"}
        
        anomalies = {
            "anomalies_found": False,
            "high_latency_spikes": [],
            "sudden_packet_loss": [],
            "unexpected_outages": [],
            "details": []
        }
        
        # Calculate historical baseline
        hist_latencies = [pr.latency_ms for pr in historical if pr.latency_ms]
        if hist_latencies:
            hist_mean = statistics.mean(hist_latencies)
            hist_std = statistics.stdev(hist_latencies) if len(hist_latencies) > 1 else 0
            
            # Check recent for anomalies (3 standard deviations from mean)
            for pr in recent:
                if pr.latency_ms and hist_std > 0:
                    z_score = (pr.latency_ms - hist_mean) / hist_std
                    if abs(z_score) > 3:
                        anomalies["anomalies_found"] = True
                        anomalies["high_latency_spikes"].append({
                            "timestamp": pr.timestamp.isoformat(),
                            "latency": pr.latency_ms,
                            "z_score": round(z_score, 2)
                        })
        
        # Check for sudden packet loss
        recent_losses = [pr.packet_loss_percent for pr in recent if pr.packet_loss_percent]
        if recent_losses and max(recent_losses) > 20:
            anomalies["anomalies_found"] = True
            anomalies["sudden_packet_loss"].append({
                "max_loss": max(recent_losses),
                "avg_loss": statistics.mean(recent_losses)
            })
        
        return anomalies
    
    async def _predict_failure(self, ping_results: List) -> Dict:
        """Predict possible link failures based on patterns."""
        if len(ping_results) < 100:
            return {"prediction_possible": False, "details": "Need more data for predictions"}
        
        predictions = {
            "prediction_possible": True,
            "failure_risk": "low",
            "failure_probability": 0.0,
            "contributing_factors": [],
            "estimated_timeframe": None
        }
        
        # Factors that increase failure probability
        risk_score = 0
        factors = []
        
        # 1. Increasing latency trend
        recent = ping_results[-50:]
        older = ping_results[:50]
        
        recent_avg_latency = statistics.mean([pr.latency_ms for pr in recent if pr.latency_ms]) if any(pr.latency_ms for pr in recent) else 0
        older_avg_latency = statistics.mean([pr.latency_ms for pr in older if pr.latency_ms]) if any(pr.latency_ms for pr in older) else 0
        
        if recent_avg_latency > older_avg_latency * 1.5:
            risk_score += 30
            factors.append("Latency increasing trend detected")
        
        # 2. Increasing packet loss
        recent_loss = [pr.packet_loss_percent for pr in recent if pr.packet_loss_percent]
        older_loss = [pr.packet_loss_percent for pr in older if pr.packet_loss_percent]
        
        if recent_loss and older_loss:
            if statistics.mean(recent_loss) > statistics.mean(older_loss) * 2:
                risk_score += 25
                factors.append("Packet loss increasing over time")
        
        # 3. Recent failures
        recent_failures = sum(1 for pr in recent if pr.status == PingStatus.FAILURE)
        if recent_failures > 5:
            risk_score += recent_failures * 2
            factors.append(f"{recent_failures} recent ping failures")
        
        # 4. Jitter (instability)
        recent_jitters = [pr.jitter_ms for pr in recent if pr.jitter_ms]
        if recent_jitters and statistics.mean(recent_jitters) > 50:
            risk_score += 15
            factors.append("High jitter indicating link instability")
        
        # Calculate probability
        predictions["failure_probability"] = min(risk_score / 100, 0.95)
        predictions["contributing_factors"] = factors
        
        if risk_score < 20:
            predictions["failure_risk"] = "low"
        elif risk_score < 50:
            predictions["failure_risk"] = "medium"
        elif risk_score < 75:
            predictions["failure_risk"] = "high"
        else:
            predictions["failure_risk"] = "critical"
        
        if risk_score > 30:
            predictions["estimated_timeframe"] = "Within the next 24-48 hours" if risk_score > 60 else "Within the next week"
        
        return predictions
    
    async def _calculate_health_scores(self, device: Device, ping_results: List) -> Dict:
        """Calculate device health and network stability scores."""
        if not ping_results:
            return {
                "device_health_score": 100,
                "network_stability_score": 100,
                "overall_health": "excellent"
            }
        
        # Device Health Score (0-100)
        health_score = 100
        
        # Deduct for failures
        failures = sum(1 for pr in ping_results if pr.status == PingStatus.FAILURE)
        failure_rate = failures / len(ping_results)
        health_score -= failure_rate * 100 * 0.3  # 30% weight on failures
        
        # Deduct for high latency
        high_latency_count = sum(1 for pr in ping_results if pr.latency_ms and pr.latency_ms > 150)
        health_score -= (high_latency_count / len(ping_results)) * 100 * 0.2
        
        # Deduct for packet loss
        losses = [pr.packet_loss_percent for pr in ping_results if pr.packet_loss_percent]
        if losses:
            avg_loss = statistics.mean(losses)
            health_score -= avg_loss * 2  # 2 points per % loss
        
        device_health = max(0, min(100, health_score))
        
        # Network Stability Score (0-100)
        stability_score = 100
        
        # Jitter reduces stability
        jitters = [pr.jitter_ms for pr in ping_results if pr.jitter_ms]
        if jitters:
            avg_jitter = statistics.mean(jitters)
            stability_score -= avg_jitter * 0.5
        
        # Latency variance reduces stability
        latencies = [pr.latency_ms for pr in ping_results if pr.latency_ms]
        if len(latencies) > 1:
            latency_variance = statistics.stdev(latencies)
            stability_score -= latency_variance * 0.1
        
        network_stability = max(0, min(100, stability_score))
        
        # Overall health
        overall = (device_health + network_stability) / 2
        
        if overall >= 90:
            health_label = "excellent"
        elif overall >= 75:
            health_label = "good"
        elif overall >= 50:
            health_label = "fair"
        else:
            health_label = "poor"
        
        return {
            "device_health_score": round(device_health, 1),
            "network_stability_score": round(network_stability, 1),
            "overall_health": health_label,
            "overall_score": round(overall, 1)
        }
    
    async def _calculate_isp_quality_score(self, ping_results: List) -> Dict:
        """Calculate ISP quality score based on performance metrics."""
        if not ping_results:
            return {"score": 100, "grade": "A+", "details": "Insufficient data"}
        
        score = 100
        
        # Availability
        successes = sum(1 for pr in ping_results if pr.status == PingStatus.SUCCESS)
        availability = successes / len(ping_results) if ping_results else 1
        score -= (1 - availability) * 50
        
        # Average latency
        latencies = [pr.latency_ms for pr in ping_results if pr.latency_ms]
        if latencies:
            avg_latency = statistics.mean(latencies)
            if avg_latency > 200:
                score -= 20
            elif avg_latency > 100:
                score -= 10
            elif avg_latency > 50:
                score -= 5
        
        # Packet loss
        losses = [pr.packet_loss_percent for pr in ping_results if pr.packet_loss_percent]
        if losses:
            avg_loss = statistics.mean(losses)
            score -= avg_loss * 3
        
        # Consistency (jitter)
        jitters = [pr.jitter_ms for pr in ping_results if pr.jitter_ms]
        if jitters and len(jitters) > 1:
            avg_jitter = statistics.mean(jitters)
            if avg_jitter > 50:
                score -= 15
            elif avg_jitter > 20:
                score -= 8
        
        final_score = max(0, min(100, round(score)))
        
        # Grade
        if final_score >= 98:
            grade = "A+"
        elif final_score >= 95:
            grade = "A"
        elif final_score >= 90:
            grade = "A-"
        elif final_score >= 80:
            grade = "B"
        elif final_score >= 70:
            grade = "C"
        elif final_score >= 60:
            grade = "D"
        else:
            grade = "F"
        
        return {
            "score": final_score,
            "grade": grade,
            "availability": round(availability * 100, 2),
            "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else None,
            "avg_packet_loss": round(statistics.mean(losses), 2) if losses else 0,
            "avg_jitter_ms": round(statistics.mean(jitters), 2) if jitters else 0
        }
    
    async def _generate_recommendations(self, device: Device, ping_results: List) -> List[Dict]:
        """Generate troubleshooting recommendations."""
        recommendations = []
        
        if not ping_results:
            return [{"type": "info", "message": "Collect more data for recommendations"}]
        
        # Check for ISP issues
        latencies = [pr.latency_ms for pr in ping_results if pr.latency_ms]
        if latencies and statistics.mean(latencies) > 150:
            recommendations.append({
                "type": "warning",
                "category": "latency",
                "priority": "high",
                "message": f"High average latency ({statistics.mean(latencies):.0f}ms). Consider:",
                "actions": [
                    "Contact ISP to check for routing issues",
                    "Verify bandwidth utilization",
                    "Check for network congestion",
                    "Review firewall rules that may cause delays"
                ]
            })
        
        # Packet loss recommendations
        losses = [pr.packet_loss_percent for pr in ping_results if pr.packet_loss_percent]
        if losses and statistics.mean(losses) > 3:
            recommendations.append({
                "type": "critical",
                "category": "packet_loss",
                "priority": "critical",
                "message": f"Packet loss detected ({statistics.mean(losses):.1f}%). Recommended actions:",
                "actions": [
                    "Check physical cables and connectors",
                    "Verify interface statistics for errors",
                    "Check for duplex mismatches",
                    "Test with different cable/port",
                    "Contact ISP if issue persists"
                ]
            })
        
        # Stability recommendations
        jitters = [pr.jitter_ms for pr in ping_results if pr.jitter_ms]
        if jitters and statistics.mean(jitters) > 30:
            recommendations.append({
                "type": "warning",
                "category": "stability",
                "priority": "medium",
                "message": "Link instability detected (high jitter). Recommendations:",
                "actions": [
                    "Check for wireless interference if applicable",
                    "Verify QoS configurations",
                    "Monitor interface errors and discards",
                    "Consider failover if available"
                ]
            })
        
        # General health recommendations
        failures = sum(1 for pr in ping_results if pr.status == PingStatus.FAILURE)
        if failures > 10:
            recommendations.append({
                "type": "critical",
                "category": "availability",
                "priority": "critical",
                "message": f"Device experienced {failures} failures recently. Actions:",
                "actions": [
                    "Verify device is powered on",
                    "Check if there's a scheduled maintenance",
                    "Verify network path to device",
                    "Check ARP table for the device IP",
                    "Consider configuring a backup link"
                ]
            })
        
        # Proactive recommendations
        if device.current_latency and device.current_latency > device.threshold_latency_warning:
            recommendations.append({
                "type": "info",
                "category": "proactive",
                "priority": "low",
                "message": "Preventive recommendations:",
                "actions": [
                    "Schedule regular firmware updates",
                    "Document network topology changes",
                    "Set up SNMP monitoring for detailed metrics",
                    "Configure automated alerting thresholds"
                ]
            })
        
        return recommendations
    
    def _generate_ai_summary(self, analysis: Dict) -> str:
        """Generate a natural language AI summary of the analysis."""
        parts = []
        hostname = analysis.get("hostname", "Device")
        
        # Health overview
        health = analysis.get("health_scores", {})
        overall = health.get("overall_health", "unknown")
        parts.append(f"📊 **{hostname}** is in **{overall}** condition")
        
        # Patterns
        patterns = analysis.get("patterns", {})
        if patterns.get("patterns_found"):
            if patterns.get("evening_packet_loss"):
                pl = patterns["evening_packet_loss"]
                parts.append(
                    f"🔍 This link has experienced packet loss every evening between "
                    f"{pl['period']} for the last 14 days (avg: {pl['avg_packet_loss']}%)"
                )
            
            if patterns.get("recurring_outages"):
                for outage in patterns["recurring_outages"][:2]:
                    parts.append(
                        f"⚠️ Recurring outages detected at {outage['time']} "
                        f"(occurred {outage['occurrences']} times)"
                    )
        
        # Scores
        scores = []
        if health.get("device_health_score"):
            scores.append(f"Device Health: {health['device_health_score']}/100")
        if health.get("network_stability_score"):
            scores.append(f"Network Stability: {health['network_stability_score']}/100")
        
        isp = analysis.get("isp_quality_score", {})
        if isp.get("grade"):
            scores.append(f"ISP Grade: {isp['grade']}")
        
        if scores:
            parts.append(f"📈 Scores: {' | '.join(scores)}")
        
        # Failure prediction
        prediction = analysis.get("predictions", {})
        if prediction.get("prediction_possible"):
            risk = prediction.get("failure_risk", "low")
            prob = prediction.get("failure_probability", 0) * 100
            parts.append(
                f"🔮 Failure Risk: **{risk.upper()}** ({prob:.0f}% probability)"
            )
        
        # Top recommendation
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            top_rec = recommendations[0]
            parts.append(f"💡 **Top Recommendation:** {top_rec.get('message', '')}")
        
        return "\n\n".join(parts)
