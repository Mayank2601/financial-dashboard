# Deploy dashboard to Streamlit Community Cloud (GitHub)

Follow these steps to get a public shareable link for your Financial Dashboard.

---

## 1. Create a new repository on GitHub

1. Go to [github.com](https://github.com) and sign in.
2. Click **+** → **New repository**.
3. **Repository name:** e.g. `financial-dashboard` (no spaces).
4. Choose **Public**. Do **not** add a README, .gitignore, or license (we already have files).
5. Click **Create repository**.

---

## 2. Push this project to GitHub

Open a terminal in this folder (`Account_statement analyzer`) and run:

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# First commit
git commit -m "Financial dashboard for XLSX statements"

# Rename branch to main (GitHub default)
git branch -M main

# Add your GitHub repo as remote (replace YOUR_USERNAME and REPO_NAME with yours)
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Push
git push -u origin main
```

**Example:** If your repo is `https://github.com/mayankkaura/financial-dashboard`:

```bash
git remote add origin https://github.com/mayankkaura/financial-dashboard.git
git push -u origin main
```

If GitHub asks for login, use a **Personal Access Token** (not your password):  
GitHub → Settings → Developer settings → Personal access tokens → Generate new token (repo scope).

---

## 3. Deploy on Streamlit Community Cloud

1. Go to **[share.streamlit.io](https://share.streamlit.io)**.
2. Sign in with **GitHub** (authorize if asked).
3. Click **New app**.
4. **Repository:** select your repo (e.g. `mayankkaura/financial-dashboard`).
5. **Branch:** `main`.
6. **Main file path:** `dashboard.py`.
7. **App URL:** optional subdomain (e.g. `financial-dashboard`).
8. Click **Deploy**.

Wait a few minutes. When it’s ready, you’ll get a link like:

**https://your-app-name.streamlit.app**

Share this link; anyone can open it and upload their XLSX files. Data is not stored on the server; it’s only processed in the browser session.

---

## 4. Updating the live app

After you change code locally:

```bash
git add .
git commit -m "Your update message"
git push
```

Streamlit Cloud will redeploy automatically, or you can trigger **Reboot app** from the app’s dashboard on share.streamlit.io.
