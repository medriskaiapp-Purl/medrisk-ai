# Deploy Guide — Step by Step

## Prerequisites

- New Gmail account created (e.g., medrisk.ai.team@gmail.com)
- New GitHub account created with that email
- Anthropic API key (from console.anthropic.com)

---

## Step 1: Configure Git (1 minute)

Open terminal:

```bash
cd ~/Projects/medrisk-ai

# Set identity for THIS repo only (not global)
git config user.name "MedRisk AI"
git config user.email "medrisk.ai.team@gmail.com"

# Verify
git config user.name
git config user.email
```

## Step 2: Test Locally (5 minutes)

```bash
cd ~/Projects/medrisk-ai

# Set your API key temporarily
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Run the app
cd src
streamlit run app.py

# Browser opens at localhost:8501
# Try: describe a device, click Generate, verify 5 risks appear (free tier)
# Press Ctrl+C to stop
```

## Step 3: First Commit (5 minutes)

```bash
cd ~/Projects/medrisk-ai

# Stage files (NOT secrets.toml — it's gitignored)
git add .gitignore
git add pyproject.toml
git add requirements.txt
git add .streamlit/config.toml
git add src/
git add samples/
git add landing/
git add docs/
git add LAUNCH_PLAN.md

# Verify what's staged (secrets.toml should NOT be listed)
git status

# Commit
git commit -m "Initial commit: MedRisk AI MVP with free/pro tier"
```

## Step 4: Push to GitHub (5 minutes)

1. Go to github.com (logged into your NEW account)
2. Click "+" → "New repository"
3. Name: `medrisk-ai`
4. Private (recommended until launch)
5. Do NOT initialize with README
6. Click "Create repository"

Then in terminal:

```bash
cd ~/Projects/medrisk-ai
git remote add origin https://github.com/YOUR_NEW_USERNAME/medrisk-ai.git
git branch -M main
git push -u origin main

# GitHub will ask for credentials:
# Username: your new GitHub username
# Password: use a Personal Access Token (GitHub → Settings → Developer settings → Tokens)
```

## Step 5: Deploy on Streamlit Cloud (10 minutes)

1. Go to share.streamlit.io
2. Sign in with your NEW GitHub account
3. Click "New app"
4. Select repository: `medrisk-ai`
5. Branch: `main`
6. Main file path: `src/app.py`
7. Click "Deploy"

Wait 2-3 minutes for it to build.

## Step 6: Add Secrets (2 minutes)

1. In Streamlit Cloud, click your app → Settings → Secrets
2. Paste:

```toml
ANTHROPIC_API_KEY = "sk-ant-your-actual-key"
LICENSE_KEYS = "DEMO-PRO-2026"
```

3. Click Save. App will reboot.

## Step 7: Verify (5 minutes)

1. Open your app URL (e.g., `medrisk-ai.streamlit.app`)
2. Test free tier: describe a device, generate, verify 5 risks, no download tab
3. Test pro tier: enter `DEMO-PRO-2026` as license key, verify slider unlocks to 25, download tab appears
4. Test on phone: open same URL on phone, verify it's usable

**Done. Your app is live.**

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "ModuleNotFoundError" | Check `requirements.txt` has all dependencies |
| "API key not configured" | Add `ANTHROPIC_API_KEY` in Streamlit Cloud Secrets |
| App shows Streamlit branding | CSS in app.py should hide it — check browser cache |
| Can't push to GitHub | Use Personal Access Token, not password |
| App is slow to start | Normal on free tier — first load takes 10-20 sec |
