# Deploy Dairy Business Logger to Streamlit Community Cloud

This guide walks you through deploying the Dairy Business Logger app so 3–4 users can access it from anywhere via a public URL. The app will use **Supabase** (free PostgreSQL) for persistent storage instead of local SQLite.

---

## Overview

| Component   | Local (default) | Cloud (Streamlit + Supabase) |
|------------|-----------------|------------------------------|
| Database   | SQLite (`dairy_data.db`) | PostgreSQL (Supabase) |
| Storage    | File on your computer | Cloud-hosted |
| Access     | `localhost:8501` | Public URL (e.g. `your-app.streamlit.app`) |

---

## Prerequisites

- A [GitHub](https://github.com) account  
- A [Supabase](https://supabase.com) account (free)  
- A [Streamlit Community Cloud](https://share.streamlit.io) account (free, sign in with GitHub)

---

## Step 1: Create a Supabase project

1. Go to **[supabase.com](https://supabase.com)** and sign in.
2. Click **New project**.
3. **Name:** e.g. `dairy-logger`
4. **Database password:** Choose a strong password and **save it** (you’ll need it soon).
5. **Region:** Pick the closest to you.
6. Click **Create new project** and wait for it to finish.

---

## Step 2: Get the database connection string

1. In your Supabase project, go to **Project Settings** (gear icon) → **Database**.
2. Find **Connection string** and select **URI**.
3. Copy the connection string. It looks like:
   ```
   postgresql://postgres.[project-ref]:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```
4. Replace `[YOUR-PASSWORD]` with the database password you set in Step 1.
5. If the string starts with `postgres://`, change it to `postgresql://`.
6. Save this string somewhere safe. You’ll add it as a secret in Streamlit.

---

## Step 3: Push the project to GitHub

### 3a. Create a new repository

1. Go to [github.com](https://github.com) → **+** → **New repository**.
2. **Repository name:** e.g. `dairy-logger`
3. **Visibility:** Public
4. Do **not** initialize with README / .gitignore / license.
5. Click **Create repository**.

### 3b. Push the code

Open a terminal in the project folder (`Account_statement analyzer`) and run:

```bash
# Initialize git (if not already)
git init

# Add files
git add .

# Commit
git commit -m "Dairy Business Logger - deploy to Streamlit Cloud"

# Rename branch to main
git branch -M main

# Add your GitHub repo (replace YOUR_USERNAME and REPO_NAME with yours)
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Push
git push -u origin main
```

**Example:** For `https://github.com/mayankkaura/dairy-logger`:

```bash
git remote add origin https://github.com/mayankkaura/dairy-logger.git
git push -u origin main
```

If Git asks for credentials, use a [Personal Access Token](https://github.com/settings/tokens) instead of a password (Settings → Developer settings → Personal access tokens → Generate).

---

## Step 4: Deploy on Streamlit Community Cloud

1. Go to **[share.streamlit.io](https://share.streamlit.io)**.
2. Sign in with GitHub and allow access.
3. Click **New app**.
4. **Repository:** Choose `YOUR_USERNAME/dairy-logger`
5. **Branch:** `main`
6. **Main file path:** `dairy_logger.py`
7. **App URL:** Choose a subdomain (e.g. `dairy-logger`).
8. Open **Advanced settings**:
   - **Python version:** 3.11 or 3.12
9. Before deploying, add the database secret:
   - Click **Secrets**
   - In the editor, add:
     ```toml
     DATABASE_URL = "postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres"
     ```
   - Replace with your full Supabase connection string from Step 2.
   - Click **Save**.
10. Click **Deploy**.

After a few minutes, the app will be live at:

**https://your-app-name.streamlit.app**

Share this link with your 3–4 users so they can log orders, income, and expenses from any device.

---

## Step 5: Test the app

1. Open the app URL.
2. Add an order, income entry, and expense.
3. Visit the Dashboard and confirm the data appears.
4. Refresh and confirm data persists (Supabase is being used).

---

## Security note

Right now, anyone with the link can use the app. There is no login. If you want to restrict access later, you would add something like a simple password check or full authentication (e.g. Streamlit-Authenticator or Supabase Auth).

---

## Updating the live app

After you change code locally:

```bash
git add .
git commit -m "Describe your changes"
git push
```

Streamlit Cloud will redeploy automatically. You can also click **Reboot app** in the Streamlit Cloud dashboard.

---

## Troubleshooting

### App fails to start or “Database error”

- Check that `DATABASE_URL` in Streamlit Secrets matches your Supabase connection string.
- Ensure the password in the string is correct and URL-encoded if it contains special characters.
- In Supabase → Project Settings → Database, confirm the connection string uses `postgresql://` and the correct host/port.

### `ModuleNotFoundError: No module named 'psycopg2'`

- Confirm `requirements.txt` includes `psycopg2-binary`.
- Redeploy the app after pushing the updated `requirements.txt`.

### Data doesn’t persist

- If `DATABASE_URL` is not set in Streamlit Secrets, the app falls back to SQLite, which is ephemeral on Streamlit Cloud. Data will not persist across restarts.
- Add `DATABASE_URL` in Streamlit Secrets with your Supabase connection string and redeploy.

---

## Local development

Locally, the app still uses SQLite by default. To use Supabase locally:

```bash
export DATABASE_URL="postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres"
streamlit run dairy_logger.py
```

(On Windows, use `set DATABASE_URL=...` instead of `export`.)
