# Vercel Deployment Guide for Animal Health System

## Project Analysis

Your project is a **Flask-based Animal Health Diagnostic System** with the following key components:

### Current Architecture
- **Framework**: Flask 2.3.3 with Flask-SQLAlchemy, Flask-Login, Flask-Mail, Flask-Babel
- **ML Components**: scikit-learn, pandas, numpy for disease prediction
- **Database**: SQLAlchemy ORM (configured for SQLite locally, PostgreSQL recommended for production)
- **Authentication**: Flask-Login with role-based access (farmers, veterinarians, admins)
- **Internationalization**: Flask-Babel (English, Chichewa, Tumbuka)
- **File Handling**: PDF exports with reportlab and matplotlib

---

## Deployment Files Status

### ✅ vercel.json (Current)
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ]
}
```
**Status**: Good baseline configuration. It correctly points to `api/index.py` as the entry point.

### ✅ api/index.py (Current)
```python
from app import app
```
**Status**: Minimal but functional. This is the correct entry point for Vercel.

---

## Issues & Solutions

### Issue 1: App Entry Point
**Problem**: `app.py` contains `app.run(debug=True, port=80)` which won't work on Vercel.
**Solution**: ✅ The entry point in `api/index.py` is correct. Vercel will use this to run the app as a serverless function.

### Issue 2: Environment Variables
**Problem**: Missing production configuration and environment variable setup.
**Solution**: See "Required Environment Variables" section below.

### Issue 3: Database
**Problem**: Currently defaults to SQLite (`database.db`), which won't persist on Vercel.
**Solution**: Configure PostgreSQL or another managed database service and set `DATABASE_URL`.

### Issue 4: File Uploads
**Problem**: Uploads folder needs to be persistent.
**Solution**: Use cloud storage (AWS S3, Vercel Blob Storage) for production file uploads.

---

## Required Environment Variables

You must configure these in your Vercel project settings:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secure-random-key-here
FLASK_CONFIG=production

# Database (change to PostgreSQL for production)
DATABASE_URL=postgresql://user:password@host:port/database_name

# Email Configuration (Gmail SMTP)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
MAIL_DEFAULT_SENDER=noreply@yourapp.com
MAIL_SUPPRESS_SEND=false

# Optional: For file storage (if using external service)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_S3_BUCKET=your-bucket-name
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] Set up PostgreSQL database (Vercel, AWS RDS, or Neon)
- [ ] Generate secure `SECRET_KEY` (use `python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] Set up Gmail app-specific password or use SendGrid/Mailgun
- [ ] Verify all environment variables are configured in Vercel
- [ ] Ensure `requirements.txt` has all dependencies pinned to specific versions

### Configuration Files
- [x] `vercel.json` - Entry point configured
- [x] `api/index.py` - Imports app correctly
- [ ] `.vercelignore` - Excludes unnecessary files (see below)
- [ ] Environment variables in Vercel dashboard

### Code Changes Needed
- [ ] Update `config.py` to detect Vercel environment and use production config
- [ ] Ensure database initialization runs on deployment
- [ ] Test file upload handling (use `/tmp` folder)

---

## Step-by-Step Deployment Instructions

### 1. Prepare Your Repository
```bash
# Ensure all files are committed
git add .
git commit -m "Prepare for Vercel deployment"
```

### 2. Create `.vercelignore` File
Create a file named `.vercelignore` in your project root to exclude unnecessary files:

```
__pycache__
*.pyc
*.pyo
.git
.env
.env.local
.vscode
.claude
.agents
instance
uploads
data
*.log
Dockerfile
docker-compose.yml
.dockerignore
```

### 3. Update Production Configuration
Your `config.py` already has a `ProductionConfig` class. Ensure it's being used in Vercel by:
- Setting `FLASK_ENV=production` environment variable in Vercel
- Updating the app initialization to use the production config

### 4. Set Environment Variables in Vercel

1. Go to your Vercel project dashboard
2. Click "Settings" → "Environment Variables"
3. Add all variables from the "Required Environment Variables" section above
4. Set them for `Production`, `Preview`, and `Development` environments as needed

### 5. Deploy

#### Option A: Deploy via Vercel CLI (Recommended)
```bash
npm i -g vercel
vercel login
vercel --prod
```

#### Option B: Connect GitHub Repository
1. Go to Vercel dashboard
2. Click "New Project"
3. Select your GitHub repository
4. Vercel will auto-detect Flask and use `vercel.json` configuration
5. Add environment variables in project settings
6. Deploy

### 6. Post-Deployment

- [ ] Test all routes and functionality
- [ ] Verify file uploads work (check `/tmp` folder permissions)
- [ ] Test email functionality
- [ ] Check database connectivity
- [ ] Monitor Vercel logs for errors
- [ ] Set up automatic deployments from GitHub

---

## Database Setup on Vercel

### Option 1: Neon PostgreSQL (Recommended - Free tier available)
1. Go to https://neon.tech
2. Sign up and create a project
3. Copy the connection string: `postgresql://user:password@...`
4. Set as `DATABASE_URL` in Vercel

### Option 2: AWS RDS
1. Create an RDS PostgreSQL instance
2. Configure security groups to allow Vercel's IP ranges
3. Get the connection string
4. Set as `DATABASE_URL` in Vercel

### Option 3: Vercel Postgres (Paid)
```bash
vercel env pull
vercel postgres create
```

### Database Initialization
The app should automatically create tables on first run. If not, you may need to:
1. Connect to the database manually
2. Run Flask migration commands or initialize the database

---

## Performance Considerations

### Serverless Function Limits
- **Cold Start**: First request takes 5-10 seconds (normal for Vercel)
- **Memory**: 3GB available per function
- **Execution Timeout**: 60 seconds (60 seconds is the maximum for serverless functions on Vercel free plan)

### Optimization Tips
1. **Database Connection Pooling**: Use `pgBouncer` with Neon
2. **Large ML Models**: Keep scikit-learn models optimized (already ~2MB)
3. **Static Files**: Cache `static/` files aggressively
4. **Image Compression**: Consider optimizing uploaded images

---

## Security Checklist

- [ ] `SECRET_KEY` is a strong, random 32+ character string
- [ ] Database credentials are environment variables (never in code)
- [ ] Email credentials use app-specific passwords (never your main password)
- [ ] All sensitive files are in `.vercelignore`
- [ ] HTTPS is enforced (Vercel does this automatically)
- [ ] CORS is configured if API is used by frontend
- [ ] Rate limiting is implemented for authentication routes

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'app'"
- Ensure `api/index.py` contains `from app import app`
- Check that `app.py` is in the root directory
- Verify `requirements.txt` has all dependencies

### "DatabaseError: Can't connect to database"
- Verify `DATABASE_URL` environment variable is set
- Check database credentials and firewall rules
- Test the connection string locally first

### "File upload failed"
- Uploads are stored in `/tmp` which has limited persistence
- Implement S3 or cloud storage for production
- Current setup works but files are temporary

### "Email sending fails"
- Verify `MAIL_USERNAME` and `MAIL_PASSWORD` are correct
- Check Gmail app-specific password is set
- Verify sender email is authorized
- Check `MAIL_SUPPRESS_SEND` is set to `false`

### "Templates not found"
- Verify `templates/` folder is in project root
- Check `app.py` has `template_folder='templates'`
- Ensure `.vercelignore` doesn't exclude templates

---

## Monitoring & Maintenance

1. **Vercel Dashboard**: Monitor function execution time and failures
2. **Logs**: Check real-time logs in Vercel dashboard
3. **Performance**: Use Vercel Analytics to track response times
4. **Database**: Monitor connection pool and query performance
5. **Updates**: Regularly update dependencies for security patches

---

## Next Steps After Deployment

1. Test all user flows in production:
   - User registration and login
   - Symptom submission and prediction
   - Veterinarian review workflow
   - Email notifications
   - PDF report generation

2. Set up monitoring:
   - Email alerts for errors
   - Performance monitoring
   - Database backup strategy

3. Plan for scaling:
   - Monitor cold start times
   - Consider database read replicas if load increases
   - Use Vercel's caching strategies

---

## Support & Resources

- **Vercel Python Docs**: https://vercel.com/docs/functions/python
- **Flask Deployment**: https://flask.palletsprojects.com/deployment/
- **PostgreSQL**: https://www.postgresql.org/
- **Neon PostgreSQL**: https://neon.tech/docs

---

**Version**: 1.0  
**Last Updated**: 2024-08-16  
**Project**: Animal Health Diagnostic System  
**Target Platform**: Vercel (Serverless)
