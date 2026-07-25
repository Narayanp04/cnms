# ConnectXperts Network Monitoring System (CNMS)

Enterprise-grade, AI-powered network ping monitoring platform designed for ISPs and enterprise WAN monitoring. Similar to PRTG, Uptime Kuma, and LibreNMS but focused on ICMP-based monitoring with advanced analytics.

## 🚀 Features

### Core Features
- **Real-time ICMP Ping Monitoring** - Multi-threaded monitoring engine
- **Live Dashboard** - Real-time status with auto-refresh
- **Device Management** - Add, edit, delete, bulk import/export
- **Historical Graphs** - 1h to 365d with zoom, pan, export
- **SLA Reporting** - Automatic availability calculation (PDF, Excel, CSV)
- **Alert System** - WhatsApp, Email, Telegram, Webhook
- **AI Analytics** - Pattern detection, failure prediction, recommendations
- **Multi-Customer Support** - Role-based access control
- **Maps** - Geographic device visualization
- **Event Logs** - Complete audit trail
- **Reports** - Daily, weekly, monthly, yearly
- **API** - RESTful with Swagger documentation

### Technical Highlights
- 10,000+ device support
- Multi-threaded ping engine
- Dark/Light mode
- JWT Authentication with RBAC
- Automated database backups
- Docker containerization
- Rate limiting & security

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python FastAPI |
| **Frontend** | React 18 + Tailwind CSS + ECharts |
| **Database** | PostgreSQL 16 |
| **Cache/Queue** | Redis 7 |
| **Background Tasks** | Celery |
| **Monitoring** | ICMP Ping (ping3) |
| **Deployment** | Docker + Nginx |

## 📋 Prerequisites

- Docker Engine 24+
- Docker Compose v2+
- Git

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/cnms.git
cd cnms
```

### 2. Configure Environment
```bash
# Copy and modify environment variables
cp .env .env.local
# Edit .env.local with your settings
```

### 3. Start the Application
```bash
# Build and start all services
docker-compose up -d --build

# Check if all services are running
docker-compose ps
```

### 4. Seed Sample Data (Optional)
```bash
# Run the seed script to populate sample data
docker-compose exec backend python seed.py
```

### 5. Access the Application
- **Web UI**: https://localhost
- **API Docs**: https://localhost/api/docs
- **API (ReDoc)**: https://localhost/api/redoc

### Default Credentials
| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Operator | operator | operator123 |
| Viewer | viewer | viewer123 |

## 🐳 Docker Services

| Service | Port | Description |
|---------|------|-------------|
| Nginx | 80/443 | Reverse proxy |
| Frontend | :80 (internal) | React SPA |
| Backend | 8000 | FastAPI REST API |
| Celery Worker | - | Background ping tasks |
| Celery Beat | - | Scheduled tasks |
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache & message broker |

## 📁 Project Structure

```
cnms/
├── backend/
│   ├── app/
│   │   ├── api/          # REST API endpoints
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── utils/        # Utilities (ping, security)
│   ├── alembic/          # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # Reusable components
│   │   ├── context/      # React contexts
│   │   ├── pages/        # Page components
│   │   └── services/     # API client
│   ├── Dockerfile
│   └── package.json
├── nginx/
│   └── nginx.conf        # Nginx configuration
├── docker-compose.yml
└── README.md
```

## 🔧 Configuration

### Environment Variables
Key configuration options in `.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://cnms:cnms123@postgres:5432/cnms_db

# JWT
JWT_SECRET_KEY=your-secret-key-here

# Monitoring
PING_TIMEOUT=5.0
PING_COUNT=4
PING_THREADS=50

# Alerts (configure as needed)
WHATSAPP_PHONE_NUMBER_ID=your-id
WHATSAPP_ACCESS_TOKEN=your-token
SMTP_HOST=smtp.gmail.com
TELEGRAM_BOT_TOKEN=your-token

# SLA
SLA_TARGET_PERCENTAGE=99.9
```

### Alert Channel Setup

#### WhatsApp Cloud API
1. Go to [Meta Developer Portal](https://developers.facebook.com/)
2. Create a WhatsApp app
3. Get Phone Number ID and Access Token
4. Set `WHATSAPP_PHONE_NUMBER_ID` and `WHATSAPP_ACCESS_TOKEN`

#### Email (SMTP)
1. Enable 2FA on Gmail
2. Generate App Password
3. Set `SMTP_USER` and `SMTP_PASSWORD`

#### Telegram
1. Create bot via [@BotFather](https://t.me/botfather)
2. Get bot token
3. Set `TELEGRAM_BOT_TOKEN`

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Current user

### Devices
- `GET /api/v1/devices` - List devices
- `POST /api/v1/devices` - Create device
- `GET /api/v1/devices/{id}` - Get device
- `PUT /api/v1/devices/{id}` - Update device
- `DELETE /api/v1/devices/{id}` - Delete device
- `POST /api/v1/devices/bulk-import` - Bulk import
- `GET /api/v1/devices/export/csv` - Export CSV

### Monitoring
- `GET /api/v1/monitoring/devices/status` - All device status
- `GET /api/v1/monitoring/device/{id}/history` - Ping history
- `GET /api/v1/monitoring/device/{id}/stats` - Ping statistics
- `GET /api/v1/monitoring/device/{id}/live` - Live status

### Alerts
- `GET /api/v1/alerts` - List alerts
- `GET /api/v1/alerts/unresolved` - Unresolved alerts
- `POST /api/v1/alerts/{id}/acknowledge` - Acknowledge
- `POST /api/v1/alerts/{id}/resolve` - Resolve

### Reports & SLA
- `GET /api/v1/reports/daily|weekly|monthly|yearly` - Reports
- `GET /api/v1/sla/reports` - SLA reports
- `POST /api/v1/sla/reports/generate` - Generate SLA

### AI Analysis
- `GET /api/v1/ai/device/{id}` - Device analysis
- `GET /api/v1/ai/summary` - All devices summary

### Maps
- `GET /api/v1/maps/devices` - Map data
- `GET /api/v1/maps/heatmap` - Heatmap data

### Backup
- `POST /api/v1/backup/create` - Create backup
- `GET /api/v1/backup/list` - List backups
- `POST /api/v1/backup/restore` - Restore backup

## 🔒 Security

- JWT token-based authentication
- Password hashing with bcrypt
- Role-based access control (Admin, Operator, Read-Only)
- Rate limiting on API endpoints
- CSRF protection
- HTTP security headers
- HTTPS enforced via Nginx
- Input validation via Pydantic
- SQL injection prevention via SQLAlchemy

## 🧪 Testing

```bash
# Run backend tests
docker-compose exec backend pytest

# Run with coverage
docker-compose exec backend pytest --cov=app --cov-report=term-missing

# Frontend lint
docker-compose exec frontend npm run lint
```

## 📈 Performance

- **Scalability**: Supports 10,000+ devices
- **Concurrency**: Multi-threaded ping engine (configurable threads)
- **Caching**: Redis caching for dashboard data
- **Database**: Connection pooling, query optimization
- **Frontend**: Lazy loading, code splitting, asset caching

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Documentation**: [docs.connectxperts.com](https://docs.connectxperts.com)
- **Email**: support@connectxperts.com
- **GitHub Issues**: [github.com/connectxperts/nms/issues](https://github.com/connectxperts/nms/issues)
