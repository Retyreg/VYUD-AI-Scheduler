# 📋 Quick Reference Card - VYUD-AI-Scheduler Deployment

## 🎯 Quick Deploy Commands

```bash
# 1. Clone and setup
git clone https://github.com/Retyreg/VYUD-AI-Scheduler.git
cd VYUD-AI-Scheduler
cp .env.example .env
nano .env  # Add your API keys

# 2. Run deployment script
chmod +x start.sh
./start.sh
```

## 🔑 Required Environment Variables

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
LINKEDIN_ACCESS_TOKEN=your_linkedin_token
LINKEDIN_PROFILE_ID=your_linkedin_profile_id
GROQ_API_KEY=your_groq_api_key
```

## 📦 Architecture

```
┌─────────────────┐
│   Internet      │
│  (Port 80/443)  │
└────────┬────────┘
         │
    ┌────▼─────┐
    │  Nginx   │  ← Reverse Proxy + SSL
    │  :80/443 │
    └────┬─────┘
         │
    ┌────▼─────┐
    │ Streamlit│  ← Python Application
    │  :8501   │
    └──────────┘
```

## 🔧 Essential Commands

| Action | Command |
|--------|---------|
| Start | `docker-compose up -d` |
| Stop | `docker-compose down` |
| Restart | `docker-compose restart` |
| Logs (all) | `docker-compose logs -f` |
| Logs (app) | `docker-compose logs -f app` |
| Status | `docker-compose ps` |
| Update | `git pull && docker-compose up -d --build` |

## 🔐 SSL Certificate (Let's Encrypt)

### Initial Setup
```bash
# Create directories
mkdir -p certbot/conf certbot/www

# Get certificate
docker run --rm \
  -v $(pwd)/certbot/conf:/etc/letsencrypt \
  -v $(pwd)/certbot/www:/var/www/certbot \
  certbot/certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email your-email@example.com \
  --agree-tos \
  -d publisher.vyud.tech
```

### Check Certificate
```bash
docker-compose exec certbot certbot certificates
```

## 🌐 Access Points

- **Production**: https://publisher.vyud.tech
- **HTTP**: http://publisher.vyud.tech (redirects to HTTPS)
- **Health Check**: https://publisher.vyud.tech/_stcore/health

## 🛠️ Troubleshooting

### Container won't start
```bash
docker-compose logs app
docker-compose down && docker-compose up -d --build
```

### SSL issues
```bash
ls -la certbot/conf/live/publisher.vyud.tech/
docker-compose logs nginx
```

### WebSocket not working
Check nginx.conf has:
```nginx
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

## 📁 Important Files

| File | Purpose |
|------|---------|
| `Dockerfile` | App container build instructions |
| `docker-compose.yml` | Multi-container orchestration |
| `nginx.conf` | Nginx configuration with SSL & WebSocket |
| `.env` | Environment variables (not in git) |
| `DEPLOYMENT.md` | Full deployment guide |
| `start.sh` | Quick start script |

## 🔒 Security Checklist

- [ ] `.env` file has correct permissions (600)
- [ ] Firewall allows only ports 22, 80, 443
- [ ] SSL certificate is valid
- [ ] Regular backups of `posts.db`
- [ ] Docker images are up to date

## 📊 Monitoring

```bash
# Resource usage
docker stats

# Disk usage
df -h

# App logs
docker-compose logs -f app

# Nginx access logs
docker-compose exec nginx tail -f /var/log/nginx/access.log
```

## 🔄 Backup & Restore

### Backup
```bash
# Database
cp posts.db posts.db.backup-$(date +%Y%m%d)

# Environment
cp .env .env.backup
```

### Restore
```bash
cp posts.db.backup-YYYYMMDD posts.db
docker-compose restart app
```

## 📞 Support

- Full Guide: [DEPLOYMENT.md](./DEPLOYMENT.md)
- Repository: https://github.com/Retyreg/VYUD-AI-Scheduler
- Issues: https://github.com/Retyreg/VYUD-AI-Scheduler/issues

---

**Last Updated**: 2026-02-03
**Domain**: publisher.vyud.tech
**Ports**: 80 (HTTP), 443 (HTTPS), 8501 (Internal)
