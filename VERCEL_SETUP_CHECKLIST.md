# Vercel Deployment Checklist

## Quick Setup - Follow These Steps

### ✅ Phase 1: Preparation (Local Machine)

- [ ] Ensure all code is committed: `git add . && git commit -m "Prepare for Vercel deployment"`
- [ ] Verify `vercel.json` exists and is configured
- [ ] Verify `api/index.py` imports app correctly
- [ ] Verify `.vercelignore` exists with all exclusions
- [ ] Verify `.env.example` exists (for reference)
- [ ] Test app locally: `python app.py` or with your local dev server

### ✅ Phase 2: Database Setup (Choose One)

**Option A: Neon PostgreSQL (RECOMMENDED - Free tier)**
- [ ] Go to https://neon.tech
- [ ] Sign up for free account
- [ ] Create a new project
- [ ] Copy the connection string (looks like: `postgresql://user:password@...`)
- [ ] Save this string - you'll need it for Vercel

**Option B: Vercel Postgres (Paid)**
- [ ] Already set up if using Vercel
- [ ] Follow Vercel docs

**Option C: AWS RDS**
- [ ] Create RDS PostgreSQL instance
- [ ] Configure security groups for Vercel IPs
- [ ] Get connection string

### ✅ Phase 3: Email Setup (Gmail + App Password)

- [ ] Go to your Gmail account: https://myaccount.google.com
- [ ] Enable 2-Step Verification (Settings → Security → 2-Step Verification)
- [ ] Go to App Passwords: https://myaccount.google.com/apppasswords
- [ ] Select "Mail" and "Windows" (or your OS)
- [ ] Google will generate a 16-character password
- [ ] Copy this password - you'll need it for MAIL_PASSWORD

### ✅ Phase 4: Generate Security Key

In your terminal, run:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
This will output a random 64-character string. Copy it - you'll need it for SECRET_KEY.

### ✅ Phase 5: Create Vercel Account & Project

- [ ] Go to https://vercel.com
- [ ] Click "Sign Up" and create an account
- [ ] Connect your GitHub account
- [ ] Select your repository
- [ ] Name your project
- [ ] Click "Create"

### ✅ Phase 6: Configure Environment Variables in Vercel

In your Vercel project dashboard:
1. Go to **Settings** → **Environment Variables**
2. Add each variable below for **Production** environment:

**Required Variables:**

| Variable | Value | Example |
|----------|-------|---------|
| `FLASK_ENV` | `production` | `production` |
| `FLASK_CONFIG` | `production` | `production` |
| `SECRET_KEY` | Your 64-char key from Phase 4 | `abc123def456...` |
| `DATABASE_URL` | Your Neon/RDS connection string | `postgresql://user:pass@...` |
| `MAIL_USERNAME` | Your Gmail address | `yourname@gmail.com` |
| `MAIL_PASSWORD` | Your 16-char app password from Phase 3 | `xxxx xxxx xxxx xxxx` |
| `MAIL_DEFAULT_SENDER` | Sender email | `noreply@chiwetocare.local` |
| `MAIL_SUPPRESS_SEND` | `false` | `false` |

3. Click "Save" for each variable

### ✅ Phase 7: Deploy

Option A: Via Vercel Dashboard
- [ ] Go back to your project page
- [ ] Click "Deploy" button
- [ ] Wait for build to complete (2-5 minutes)
- [ ] Check build logs for errors

Option B: Via CLI
```bash
npm i -g vercel
vercel login
vercel --prod
```

### ✅ Phase 8: Verify Deployment

After deployment:

1. **Check Build Status**
   - [ ] Vercel dashboard shows ✅ "Ready"
   - [ ] Check "Deployments" tab for any errors

2. **Test Application**
   - [ ] Open your Vercel URL (e.g., yourapp.vercel.app)
   - [ ] Test login page loads
   - [ ] Try to login with a test account
   - [ ] Verify database is working (check user registration)

3. **Check Logs**
   - [ ] Go to Vercel dashboard
   - [ ] Click "Functions" tab
   - [ ] Click `api/index.py`
   - [ ] Check for errors in the logs

4. **Test Core Features**
   - [ ] User login/registration
   - [ ] Submit a symptom report
   - [ ] Verify prediction works
   - [ ] Check if email notifications send
   - [ ] Test PDF export (if applicable)

### ✅ Phase 9: Post-Deployment Setup

- [ ] Set up custom domain (optional)
  - Go to Settings → Domains
  - Add your custom domain
  - Update DNS records

- [ ] Enable production analytics
  - Go to Settings → Analytics
  - Enable Web Vitals

- [ ] Set up error monitoring (optional)
  - Connect to error tracking service (Sentry, Rollbar)
  - Add error alerts

### ✅ Phase 10: Troubleshooting

**Issue: Build fails with "ModuleNotFoundError"**
- [ ] Check `api/index.py` has correct imports
- [ ] Verify all dependencies are in `requirements.txt`
- [ ] Check that `app.py` exists in project root

**Issue: Database connection failed**
- [ ] Verify `DATABASE_URL` is correct in Vercel env vars
- [ ] Test connection string locally
- [ ] Check database firewall allows Vercel IPs
- [ ] Verify database exists and is accessible

**Issue: Emails not sending**
- [ ] Verify `MAIL_USERNAME` and `MAIL_PASSWORD` are correct
- [ ] Verify you used app-specific password, not Gmail password
- [ ] Check `MAIL_SUPPRESS_SEND` is set to `false`
- [ ] Check logs for SMTP errors

**Issue: Static files (CSS/JS) not loading**
- [ ] Check `static/` folder exists in project root
- [ ] Verify file paths in templates are relative (use `url_for()`)
- [ ] Clear browser cache and hard refresh (Ctrl+Shift+R)

**Issue: Files/uploads not persisting**
- [ ] Upload folder is `/tmp` which clears after serverless execution
- [ ] For persistent storage, implement S3 or cloud storage
- [ ] This is expected behavior for serverless

### 🎉 Success!

Your application is now deployed on Vercel! 

**Next Steps:**
- Monitor application performance in Vercel dashboard
- Set up regular database backups
- Plan for database scaling if needed
- Keep dependencies updated for security

---

## Support & Resources

- **Vercel Docs**: https://vercel.com/docs
- **Flask Guide**: https://flask.palletsprojects.com/
- **Neon Docs**: https://neon.tech/docs
- **PostgreSQL**: https://www.postgresql.org/docs/

---

## Quick Reference: Important Files

| File | Purpose | Notes |
|------|---------|-------|
| `vercel.json` | Vercel configuration | Routes all requests to `api/index.py` |
| `api/index.py` | Serverless entry point | Imports Flask app |
| `.vercelignore` | Files to exclude | Prevents uploading unnecessary files |
| `.env.example` | Environment template | Copy to `.env.local` for dev |
| `config.py` | Flask configuration | Supports dev/prod environments |
| `requirements.txt` | Python dependencies | Must include all packages |

---

**Last Updated**: 2024-08-16  
**Version**: 1.0
