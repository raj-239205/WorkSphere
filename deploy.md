# WorkSphere - Cloud Deployment Guide

This document explains how to deploy the **WorkSphere** workforce management system to Render, Railway, or via Docker.

---

## 1. Deploying on Render (Recommended & Free)
Render is an excellent platform for hosting Flask applications directly from GitHub.

### Step 1: Create a Web Service
1. Log in to [Render](https://render.com) and click **New +** > **Web Service**.
2. Connect your GitHub account and select the `WorkSphere` repository: `https://github.com/raj-239205/WorkSphere`.

### Step 2: Configure Service Settings
- **Name**: `worksphere`
- **Region**: Select the closest region to your users.
- **Branch**: `main`
- **Runtime**: `Python`
- **Build Command**: 
  ```bash
  pip install -r requirements.txt && python init_db.py
  ```
- **Start Command**: 
  ```bash
  gunicorn run:app
  ```

### Step 3: Enable Database Persistence (Crucial for SQLite)
Since SQLite is a file-based database, any restarts of Render's default ephemeral disks will clear the database unless you attach a **Persistent Volume**.
1. In your Render service dashboard, go to the **Disk** tab.
2. Click **Add Disk**:
   - **Name**: `worksphere-db`
   - **Mount Path**: `/app/database`
   - **Size**: `1 GiB` (more than enough for SQLite logs).
3. Click **Save**. This ensures that `database/erp.db` survives code redeployments and server restarts.

---

## 2. Deploying on Railway
Railway automatically detects container configurations (`Dockerfile`) and builds the image.

1. Go to [Railway](https://railway.app) and click **New Project** > **Deploy from GitHub repo**.
2. Select your `WorkSphere` repository.
3. Railway will detect the `Dockerfile` at the root and build it automatically.
4. **Persistent Disk (Optional but Recommended)**: 
   Go to the service's settings on Railway, add a Volume mounted at `/app/database` to persist data.

---

## 3. Local Deployment via Docker
To build and run the application inside a container locally:

### Step 1: Build the Docker Image
Navigate to the root directory and run:
```bash
docker build -t worksphere .
```

### Step 2: Run the Container with Volume Persistence
Mount a local directory to host the SQLite database file:
```bash
docker run -d -p 5000:5000 -v "/absolute/path/to/local/folder:/app/database" worksphere
```
The application will start, bootstrap the database in the local folder, and become accessible at `http://localhost:5000`.
