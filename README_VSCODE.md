# Run and Debug in VS Code

This repo includes VS Code tasks and launch configurations for local development.

## 1. Start Docker images

Use the VS Code task to build and start the Docker Compose services:

- Open the Command Palette.
- Run: `Tasks: Run Task`.
- Select: `Docker: Up (bookmarkbackup) - build & run`.

This runs:

```powershell
docker compose -f docker/docker-compose.yml -p bookmarkbackup up -d --build
```

It builds the images and starts the containers in Docker Desktop.

## 2. Run the app with VS Code debugging

Use the VS Code Run and Debug panel:

- Open `Run and Debug`.
- Select: `Full stack (API + React)`.
- Start debugging.

This compound configuration launches:

- `Bookmark Backup API`
  - runs `uvicorn bookmark_backup.web.app:app --host 127.0.0.1 --port 8000 --reload`
- `Frontend (Vite)`
  - runs `npm run dev` from `frontend/`

## 3. Useful URLs

- API: `http://127.0.0.1:8000`
- Frontend dev: `http://127.0.0.1:5173`

## 4. Notes

- The API debug config loads `.env` from the workspace root.
- `PYTHONPATH` is set to `src` so the app can import `bookmark_backup`.
- If you only want one part:
  - run `Bookmark Backup API` alone for backend
  - run `Frontend (Vite)` alone for frontend

## 5. Stop containers

Use the VS Code task:

- `Docker: Down (bookmarkbackup)`

Or run:

```powershell
docker compose -f docker/docker-compose.yml -p bookmarkbackup down
```
