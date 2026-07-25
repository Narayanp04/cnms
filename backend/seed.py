"""ConnectXperts NMS - Database Seed Script
Run this to populate the database with sample data for testing.
Usage: python seed.py
"""
import sys
import os

# Force UTF-8 for console output on Windows (emoji support)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore

sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timezone, timedelta
import random
from sqlalchemy.orm import Session, sessionmaker
from app.database import sync_engine
from app.models.user import User, Role, Customer
from app.models.device import Device, DeviceStatus, PollingInterval
from app.models.ping_result import PingResult, PingStatus
from app.models.alert import Alert, AlertType, AlertSeverity, AlertStatus, AlertRecipient
from app.utils.security import get_password_hash


def seed_database():
    """Seed the database with sample data."""
    SessionLocal = sessionmaker(bind=sync_engine)
    session = SessionLocal()
    
    try:
        # Create admin user
        admin = User(
            username="admin",
            email="admin@cnms.local",
            hashed_password=get_password_hash("admin123"),
            full_name="System Administrator",
            role=Role.ADMIN,
            is_active=True,
            is_verified=True,
        )
        session.add(admin)
        
        # Create operator
        operator = User(
            username="operator",
            email="operator@cnms.local",
            hashed_password=get_password_hash("operator123"),
            full_name="Network Operator",
            role=Role.OPERATOR,
            is_active=True,
            is_verified=True,
        )
        session.add(operator)
        
        # Create read-only user
        readonly = User(
            username="viewer",
            email="viewer@cnms.local",
            hashed_password=get_password_hash("viewer123"),
            full_name="Report Viewer",
            role=Role.READ_ONLY,
            is_active=True,
            is_verified=True,
        )
        session.add(readonly)
        
        # Create sample customers
        customers_data = [
            {"name": "Acme Corporation", "code": "ACME", "email": "support@acme.com", "contact_person": "John Smith"},
            {"name": "GlobalTech Solutions", "code": "GTS", "email": "noc@globaltech.com", "contact_person": "Sarah Johnson"},
            {"name": "DataStream Ltd", "code": "DSL", "email": "ops@datastream.com", "contact_person": "Mike Brown"},
            {"name": "NetConnect ISP", "code": "NCI", "email": "support@netconnect.com", "contact_person": "Emily Davis"},
            {"name": "CloudPeak Services", "code": "CPS", "email": "admin@cloudpeak.com", "contact_person": "David Wilson"},
        ]
        
        customers = []
        for c in customers_data:
            customer = Customer(**c)
            session.add(customer)
            customers.append(customer)
        
        session.flush()
        
        # Create sample devices with realistic IPs
        devices_data = [
            {"hostname": "core-router-01", "ip_address": "10.0.1.1", "customer": customers[0], "site": "Data Center 1", "region": "US-East", "provider": "Verizon", "circuit_id": "CIR-001", "lat": 40.7128, "lng": -74.0060},
            {"hostname": "core-router-02", "ip_address": "10.0.1.2", "customer": customers[0], "site": "Data Center 2", "region": "US-West", "provider": "AT&T", "circuit_id": "CIR-002", "lat": 34.0522, "lng": -118.2437},
            {"hostname": "edge-switch-01", "ip_address": "10.0.2.1", "customer": customers[1], "site": "HQ Office", "region": "US-East", "provider": "Comcast", "circuit_id": "CIR-003", "lat": 38.9072, "lng": -77.0369},
            {"hostname": "edge-switch-02", "ip_address": "10.0.2.2", "customer": customers[1], "site": "Branch Office", "region": "EU-West", "provider": "BT", "circuit_id": "CIR-004", "lat": 51.5074, "lng": -0.1278},
            {"hostname": "firewall-01", "ip_address": "10.0.3.1", "customer": customers[2], "site": "Primary DC", "region": "APAC", "provider": "Singtel", "circuit_id": "CIR-005", "lat": 1.3521, "lng": 103.8198},
            {"hostname": "firewall-02", "ip_address": "10.0.3.2", "customer": customers[2], "site": "DR Site", "region": "APAC", "provider": "NTT", "circuit_id": "CIR-006", "lat": 35.6762, "lng": 139.6503},
            {"hostname": "customer-cpe-01", "ip_address": "192.168.1.1", "customer": customers[3], "site": "Customer Premise", "region": "US-East", "provider": "CenturyLink", "circuit_id": "CIR-007", "lat": 39.7392, "lng": -104.9903},
            {"hostname": "customer-cpe-02", "ip_address": "192.168.2.1", "customer": customers[3], "site": "Remote Office", "region": "US-Central", "provider": "Spectrum", "circuit_id": "CIR-008", "lat": 41.8781, "lng": -87.6298},
            {"hostname": "wan-optimizer-01", "ip_address": "10.0.10.1", "customer": customers[4], "site": "Main Office", "region": "US-West", "provider": "Cox", "circuit_id": "CIR-009", "lat": 47.6062, "lng": -122.3321},
            {"hostname": "wan-optimizer-02", "ip_address": "10.0.10.2", "customer": customers[4], "site": "Branch Office", "region": "US-East", "provider": "Verizon", "circuit_id": "CIR-010", "lat": 33.4484, "lng": -112.0740},
        ]
        
        devices = []
        statuses = [DeviceStatus.UP] * 7 + [DeviceStatus.DOWN] * 1 + [DeviceStatus.WARNING] * 2
        
        for d in devices_data:
            device = Device(
                hostname=d["hostname"],
                ip_address=d["ip_address"],
                customer_id=d["customer"].id,
                customer_name=d["customer"].name,
                site_name=d["site"],
                region=d["region"],
                provider=d["provider"],
                circuit_id=d["circuit_id"],
                is_monitoring_enabled=True,
                polling_interval=PollingInterval.THIRTY_SEC,
                latitude=d["lat"],
                longitude=d["lng"],
                location=f"{d['site']}, {d['region']}",
                status=random.choice(statuses),
                current_latency=random.uniform(5, 300) if random.random() > 0.2 else None,
                current_packet_loss=random.uniform(0, 15) if random.random() > 0.6 else 0,
                current_jitter=random.uniform(0, 50) if random.random() > 0.5 else 0,
                last_response=datetime.now(timezone.utc) - timedelta(seconds=random.randint(0, 60)),
                sla_24h=random.uniform(95, 100),
                sla_7d=random.uniform(97, 100),
                sla_30d=random.uniform(98, 100),
                sla_365d=random.uniform(99, 100),
                total_pings=random.randint(1000, 10000),
                successful_pings=0,
                failed_pings=0,
                created_by=admin.id,
            )
            session.add(device)
            devices.append(device)
        
        session.flush()
        
        # Generate historical ping data (last 7 days, ping every 5 minutes)
        now = datetime.now(timezone.utc)
        for device in devices:
            successful = 0
            failed = 0
            for hours_ago in range(0, 24 * 7, 1):  # Every hour
                timestamp = now - timedelta(hours=hours_ago)
                
                # Simulate some failures
                is_success = random.random() > 0.15  # 85% success rate
                status = PingStatus.SUCCESS if is_success else PingStatus.FAILURE
                
                if is_success:
                    successful += 1
                    latency = random.uniform(5, 200)
                    packet_loss = random.uniform(0, 5)
                    jitter = random.uniform(0, 20)
                else:
                    failed += 1
                    latency = None
                    packet_loss = 100
                    jitter = None
                
                ping_result = PingResult(
                    device_id=device.id,
                    status=status,
                    latency_ms=latency if is_success else None,
                    packet_loss_percent=packet_loss if is_success else 100,
                    jitter_ms=jitter if is_success else None,
                    response_time_ms=latency if is_success else None,
                    rtt_min=latency if is_success else None,
                    rtt_max=latency if is_success else None,
                    rtt_avg=latency if is_success else None,
                    error_message=None if is_success else "Request timeout",
                    timestamp=timestamp,
                )
                session.add(ping_result)
            
            device.successful_pings = successful
            device.failed_pings = failed
            device.total_pings = successful + failed
        
        # Create sample alerts
        alert_devices = [d for d in devices if d.status == DeviceStatus.DOWN]
        for device in alert_devices[:2]:
            alert = Alert(
                device_id=device.id,
                alert_type=AlertType.DEVICE_DOWN,
                severity=AlertSeverity.CRITICAL,
                status=AlertStatus.TRIGGERED,
                title=f"🔴 Device Down - {device.hostname}",
                message=f"Device {device.hostname} is not responding to ICMP ping requests.",
                latency_ms=None,
                packet_loss_percent=100.0,
                triggered_at=now - timedelta(minutes=random.randint(5, 60)),
                is_recovered=False
            )
            session.add(alert)
        
        session.commit()
        print("✅ Database seeded successfully!")
        print(f"   - 3 Users created (admin/admin123, operator/operator123, viewer/viewer123)")
        print(f"   - {len(customers)} Customers created")
        print(f"   - {len(devices)} Devices created with ping history")
        print(f"   - Sample alerts generated")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error seeding database: {str(e)}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
