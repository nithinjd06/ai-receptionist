# Deployment Guide

This guide covers deploying the AI Receptionist to various platforms.

## Table of Contents

- [Render Deployment](#render-deployment)
- [Railway Deployment](#railway-deployment)
- [AWS Deployment](#aws-deployment)
- [DigitalOcean Deployment](#digitalocean-deployment)
- [Production Checklist](#production-checklist)

## Render Deployment

### Step-by-Step

1. **Create Render Account**
   - Visit [render.com](https://render.com) and sign up

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository

3. **Configure Service**
   - Name: `ai-receptionist`
   - Environment: `Python 3`
   - Region: Choose closest to your users
   - Branch: `main`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn server.main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables**
   - Go to Environment tab
   - Add all variables from `env.example`
   - Set `PUBLIC_URL` to your Render URL (e.g., `https://your-app.onrender.com`)

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete
   - Note your URL

6. **Configure Twilio**
   - Update Twilio webhook to: `https://your-app.onrender.com/voice/incoming`

### Database Setup (Render Postgres)

1. Create Postgres database in Render
2. Copy connection string
3. Update `DATABASE_URL` environment variable:
   ```
   postgresql+asyncpg://user:pass@hostname:5432/dbname
   ```

## Railway Deployment

### Step-by-Step

1. **Create Railway Account**
   - Visit [railway.app](https://railway.app) and sign up

2. **New Project from GitHub**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

3. **Configure**
   - Railway auto-detects Python
   - Add environment variables in the Variables tab
   - Set `PUBLIC_URL` to Railway-provided domain

4. **Add Postgres** (Optional)
   - Click "+ New" → "Database" → "PostgreSQL"
   - Connection string is auto-added to environment

5. **Deploy**
   - Railway auto-deploys on push
   - View logs in dashboard

## AWS Deployment

### Using AWS Elastic Beanstalk

1. **Install EB CLI**
   ```bash
   pip install awsebcli
   ```

2. **Initialize EB**
   ```bash
   eb init -p python-3.11 ai-receptionist
   ```

3. **Create Environment**
   ```bash
   eb create ai-receptionist-prod
   ```

4. **Set Environment Variables**
   ```bash
   eb setenv TWILIO_ACCOUNT_SID=xxx OPENAI_API_KEY=xxx ...
   ```

5. **Deploy**
   ```bash
   eb deploy
   ```

### Using AWS ECS (Docker)

1. **Build and push Docker image**
   ```bash
   # Build
   docker build -t ai-receptionist:latest .
   
   # Tag for ECR
   docker tag ai-receptionist:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-receptionist:latest
   
   # Push
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-receptionist:latest
   ```

2. **Create ECS Task Definition**
   - Use Fargate launch type
   - 1 vCPU, 2GB memory minimum
   - Add environment variables
   - Configure health check: `/healthz`

3. **Create ECS Service**
   - Select task definition
   - Configure load balancer
   - Set desired tasks: 2+ for production

## DigitalOcean Deployment

### Using App Platform

1. **Create App**
   - Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
   - Click "Create App" → "GitHub"
   - Select repository

2. **Configure**
   - Detected as Python app
   - Build Command: `pip install -r requirements.txt`
   - Run Command: `uvicorn server.main:app --host 0.0.0.0 --port $PORT`

3. **Add Environment Variables**
   - Click "Environment Variables"
   - Add all required variables

4. **Add Database** (Optional)
   - Create managed PostgreSQL database
   - Link to app

5. **Deploy**
   - Click "Create Resources"

## Production Checklist

### Pre-Deployment

- [ ] All environment variables configured
- [ ] Google Calendar credentials set up (if using)
- [ ] Twilio phone number provisioned
- [ ] All API keys valid and tested
- [ ] Database connection tested
- [ ] Admin password changed from default
- [ ] Business hours configured correctly

### Security

- [ ] HTTPS enabled (required for Twilio)
- [ ] Twilio signature verification enabled
- [ ] Strong admin password set
- [ ] API keys stored as secrets (not in code)
- [ ] Database credentials secured
- [ ] CORS configured appropriately
- [ ] Rate limiting considered (e.g., via Cloudflare)

### Performance

- [ ] Database indexed properly
- [ ] Connection pooling configured
- [ ] Async operations verified
- [ ] Health checks passing
- [ ] Latency targets met (<2s P95)
- [ ] Multiple instances for high availability

### Monitoring

- [ ] Structured logging enabled
- [ ] Log aggregation set up (e.g., Datadog, Sentry)
- [ ] Health check monitoring
- [ ] Uptime monitoring (e.g., UptimeRobot)
- [ ] Error alerting configured
- [ ] Call volume metrics tracked

### Testing

- [ ] All tests passing
- [ ] End-to-end test call successful
- [ ] FAQ responses verified
- [ ] Appointment scheduling tested
- [ ] Message taking tested
- [ ] Off-hours behavior verified
- [ ] Error handling tested

### Documentation

- [ ] API endpoints documented
- [ ] Admin access documented
- [ ] Escalation procedures documented
- [ ] On-call rotation established
- [ ] Runbook created

## Scaling Considerations

### Horizontal Scaling

- Deploy multiple instances behind load balancer
- Use Postgres instead of SQLite
- Enable Redis for distributed caching
- Consider message queue (Celery) for background tasks

### Database Scaling

**SQLite → Postgres Migration:**

1. Export SQLite data:
   ```bash
   sqlite3 data/receptionist.db .dump > backup.sql
   ```

2. Update `DATABASE_URL` to Postgres connection string

3. Import data to Postgres

4. Restart application

### Latency Optimization

- Deploy in region closest to users
- Use CDN for static assets
- Enable HTTP/2
- Optimize LLM prompt length
- Cache frequently used calendar slots
- Use Deepgram partials for faster STT

## Cost Estimation

### Per Call Costs (approximate)

- **STT (Deepgram)**: $0.0043/minute = ~$0.01 per 2-min call
- **LLM (GPT-4o)**: ~$0.02 per call (depends on turns)
- **TTS (ElevenLabs)**: $0.18/1000 chars = ~$0.02 per response
- **Twilio**: $0.0085/minute = ~$0.02 per 2-min call
- **Total**: ~$0.07 per 2-minute call

### Monthly Infrastructure

- **Render/Railway**: $7-25/month (basic plan)
- **DigitalOcean**: $12-48/month
- **AWS**: Variable, $20-100/month typical

### Break-even Analysis

- 100 calls/day: ~$210/month in API costs
- 500 calls/day: ~$1,050/month in API costs
- 1000 calls/day: ~$2,100/month in API costs

Compare to human receptionist: ~$2,500-4,000/month

## Troubleshooting

### Deployment Fails

- Check build logs
- Verify Python version (3.11)
- Ensure all dependencies in requirements.txt
- Check for missing environment variables

### WebSocket Issues

- Ensure HTTPS is enabled
- Verify `PUBLIC_URL` is correct
- Check for proxy/load balancer websocket support
- Increase timeout limits

### High Latency

- Check provider API status pages
- Monitor database query times
- Profile slow endpoints
- Consider geographic deployment

### Database Connection Issues

- Verify connection string format
- Check firewall rules
- Ensure SSL mode is correct for provider
- Test connection locally first

## Support

For deployment assistance:
- GitHub Issues: [repository]/issues
- Documentation: [repository]/wiki
- Community: [Discord/Slack link]

