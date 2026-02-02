# Deployment Guide for Cafeteria Service - Blu-Reserve

Production-ready deployment steps, environment assumptions, health checks, and post-deploy validation.

## Deployment Architecture

### System Components
- **Backend Service**: FastAPI application serving REST APIs
- **Frontend Service**: React SPA served via CDN or static host
- **Database**: PostgreSQL for production (SQLite for local development)
- **Authentication**: IBM W3ID SSO integration
- **Session Storage**: Secure server-side session management

## Pre-Deployment Requirements

### 1. Environment Setup
- Python 3.8+ for backend
- Node.js 18+ for frontend
- PostgreSQL 12+ for production database
- SSL certificate for HTTPS
- Reverse proxy (nginx/Apache) for production

### 2. Environment Variables
Prepare the following environment variables for production:

#### Backend (.env file)
```env
# OIDC Configuration
OIDC_DISCOVERY_URL=https://prod.login.w3.ibm.com/oidc/endpoint/default/.well-known/openid-configuration
OIDC_CLIENT_ID=your_client_id
OIDC_CLIENT_SECRET=your_client_secret
OIDC_REDIRECT_URI=https://yourdomain.com/auth/callback

# Session Security
APP_SESSION_SECRET=your_secure_random_secret_key_here
FRONTEND_URL=https://yourfrontend.com

# Database
DATABASE_URL=postgresql://username:password@host:port/database_name

# Server Configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info
DEBUG=false

# Feature Flags
USE_MOCK_AUTH=false  # Set to false for production
```

#### Frontend (.env file)
```env
VITE_API_BASE_URL=https://your-backend-domain.com
```

## Backend Deployment Steps

### 1. Deploy Backend to Cloud Platform

#### Option A: Render Deployment
1. **Push to GitHub Repository**
   ```bash
   git checkout -b prod-deployment
   git add .
   git commit -m "Production deployment configuration"
   git push origin prod-deployment
   ```

2. **Configure Render Web Service**
   - Connect GitHub repository to Render
   - Create Web Service
   - Set environment variables from `.env` file
   - Configure start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Add PostgreSQL database add-on
   - Enable auto-deploy from main branch

3. **Environment-Specific Configuration**
   - Scale web service appropriately (recommend 1-2 instances initially)
   - Configure SSL certificate
   - Set up custom domain if needed

#### Option B: Self-Hosted Deployment
1. **Server Preparation**
   ```bash
   # Update system packages
   sudo apt update && sudo apt upgrade -y
   
   # Install Python and pip
   sudo apt install python3 python3-pip python3-venv -y
   
   # Install PostgreSQL client
   sudo apt install postgresql-client -y
   ```

2. **Application Setup**
   ```bash
   # Clone repository
   git clone https://github.com/your-repo/cafeteria-service.git
   cd cafeteria-service
   
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Set environment variables
   cp .env.example .env
   # Edit .env with production values
   ```

3. **Database Configuration**
   ```bash
   # For PostgreSQL
   pip install psycopg2-binary
   
   # Run initial setup (auto-creation happens on startup)
   ```

4. **Process Management**
   ```bash
   # Create systemd service file
   sudo nano /etc/systemd/system/cafeteria.service
   ```

   Example service file:
   ```ini
   [Unit]
   Description=Cafeteria Service
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/path/to/cafeteria-service
   ExecStart=/path/to/cafeteria-service/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always
   EnvironmentFile=/path/to/cafeteria-service/.env

   [Install]
   WantedBy=multi-user.target
   ```

   ```bash
   # Enable and start service
   sudo systemctl daemon-reload
   sudo systemctl enable cafeteria
   sudo systemctl start cafeteria
   ```

## Frontend Deployment Steps

### 1. Build Process
```bash
# Navigate to frontend directory
cd Frontend

# Install dependencies
npm install

# Set production API base URL
echo "VITE_API_BASE_URL=https://your-backend-domain.com" > .env.production

# Build for production
npm run build
```

### 2. Deployment Options

#### Option A: Vercel Deployment
1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Deploy**
   ```bash
   vercel --prod
   # Or connect to GitHub for auto-deployment
   ```

3. **Configuration**
   - Set `VITE_API_BASE_URL` in Vercel dashboard
   - Configure custom domain if needed

#### Option B: Netlify Deployment
1. **Connect GitHub Repository**
   - Link GitHub repository to Netlify
   - Set build command: `npm run build`
   - Set publish directory: `dist`
   - Set environment variable: `VITE_API_BASE_URL`

#### Option C: Static Hosting
1. **Upload Build Files**
   - Upload contents of `dist/` folder to your static hosting provider
   - Ensure proper MIME types for static assets

## Health Checks and Monitoring

### 1. Backend Health Endpoints
- **Health Check**: `GET /` - Returns `{"message": "Cafeteria Service Running!"}`
- **System Status**: `GET /reservations/verify` - Provides system metrics
- **Admin Stats**: `GET /admin/stats` - Detailed statistics

### 2. Automated Health Monitoring
```bash
# Health check script example
#!/bin/bash
HEALTH_CHECK_URL="https://your-backend-domain.com/"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_CHECK_URL)

if [ $RESPONSE -eq 200 ]; then
  echo "✅ Backend is healthy"
else
  echo "❌ Backend health check failed: HTTP $RESPONSE"
  # Add alerting logic here
fi
```

### 3. Database Connection Health
```bash
# Database connectivity check
curl -s "https://your-backend-domain.com/reservations/verify" | jq '.status'
```

### 4. Frontend Health
- Monitor page load times
- Check JavaScript console for errors
- Verify API connectivity
- Test user flows regularly

## Post-Deployment Validation

### 1. Functional Validation
```bash
# 1. Verify backend is responding
curl -s https://your-backend-domain.com/

# 2. Test authentication endpoints
curl -s https://your-backend-domain.com/auth/managers | jq

# 3. Test reservation endpoints
curl -s "https://your-backend-domain.com/reservations/timeslots?date=$(date +%Y-%m-%d)" | jq

# 4. Test admin endpoints
curl -s https://your-backend-domain.com/admin/dashboard | jq
```

### 2. User Flow Validation
1. **Login Flow**
   - Navigate to frontend URL
   - Verify login page loads
   - Test authentication flow

2. **Booking Flow**
   - Select date and timeslot
   - Verify seat availability displays
   - Test booking process
   - Confirm success page appearance

3. **Admin Flow**
   - Access admin dashboard
   - Verify statistics display
   - Test reset functionality (in staging)

### 3. Performance Validation
- **Response Times**: API endpoints should respond < 500ms
- **Page Load**: Frontend should load < 3 seconds
- **Concurrent Users**: System should handle expected load
- **Database Queries**: Optimize slow queries if needed

### 4. Security Validation
- **SSL Certificate**: Verify HTTPS is working
- **Headers**: Check security headers are present
- **Authentication**: Verify auth is required for protected endpoints
- **Input Validation**: Test for common vulnerabilities

## Rollback Procedure

### 1. Backend Rollback
```bash
# If using Git-based deployment
git checkout previous-stable-commit
git push origin main  # Triggers redeployment

# If using manual deployment
# Stop current service
sudo systemctl stop cafeteria

# Revert to backup
cp -r backup-directory/* current-directory/
sudo systemctl start cafeteria
```

### 2. Frontend Rollback
- Revert to previous build in hosting platform
- Or redeploy previous version from Git tag

## Maintenance Procedures

### 1. Regular Maintenance Tasks
- **Database Backup**: Daily automated backups
- **Log Rotation**: Weekly log cleanup
- **Dependency Updates**: Monthly review
- **Security Patches**: Immediate application

### 2. Monitoring Dashboard
- **Uptime Monitoring**: Use external service (Pingdom, UptimeRobot)
- **Performance Metrics**: Response times, error rates
- **User Analytics**: Booking patterns, popular timeslots
- **Resource Usage**: CPU, memory, disk space

## Troubleshooting Production Issues

### 1. Common Issues and Solutions

**Issue**: Slow response times
- **Diagnosis**: Check database performance, server resources
- **Solution**: Optimize queries, scale resources

**Issue**: Authentication failures
- **Diagnosis**: Check OIDC configuration, SSL certificates
- **Solution**: Verify redirect URIs, certificate validity

**Issue**: Database connection errors
- **Diagnosis**: Check connection pool settings, database health
- **Solution**: Increase pool size, optimize connections

### 2. Emergency Contacts
- **Platform Operations**: [Contact information]
- **Security Team**: [Contact information] 
- **Development Team**: [Contact information]

## Scaling Recommendations

### 1. Traffic Growth
- **Low Traffic** (< 100 concurrent users): Single instance
- **Medium Traffic** (100-500): 2-3 instances with load balancer
- **High Traffic** (> 500): Auto-scaling cluster setup

### 2. Database Scaling
- **Read Replicas**: For high-read scenarios
- **Connection Pooling**: Use PgBouncer for connection management
- **Caching**: Implement Redis for session and cache storage

## Environment-Specific Configurations

### 1. Staging vs Production
- **Staging**: Mock auth enabled, reduced resources
- **Production**: Real IBM W3ID auth, full security measures

### 2. Feature Flags
- **USE_MOCK_AUTH**: false in production
- **DEBUG**: false in production
- **LOG_LEVEL**: info/warn in production

---

**Deployment Complete**: Your Cafeteria Service is now running in production with all necessary validations and monitoring in place.