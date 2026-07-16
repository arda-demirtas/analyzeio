from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base, run_migrations
from backend.routes_auth import router as auth_router
from backend.routes_predict import router as predict_router
from backend.routes_comments import router as comments_router
from backend.routes_admin import router as admin_router

# Initialize database tables
# Run startup database migrations for SQLite schemas
run_migrations()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Analyzeio API",
    description="Secure, professional API for LSTM-based market closing price predictions.",
    version="1.0.0"
)

# Enable CORS for the frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],  # * allowed for local dev ease, restricted in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(auth_router)
app.include_router(predict_router)
app.include_router(comments_router, prefix="/api")
app.include_router(admin_router)

@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "analyzeio-api",
        "version": "1.0.0"
    }

@app.get("/api/temp-logs")
def get_temp_logs():
    import os
    try:
        env_path = "/var/www/analyzeio/.env"
        env_exists = os.path.exists(env_path)
        env_size = os.path.getsize(env_path) if env_exists else 0
        first_line = ""
        if env_exists:
            with open(env_path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                
        model_cache_path = "/var/www/analyzeio/backend/model_cache"
        model_files = []
        if os.path.exists(model_cache_path):
            model_files = os.listdir(model_cache_path)
                
        out_path = "/root/.pm2/logs/backend-out.log"
        err_path = "/root/.pm2/logs/backend-error.log"
        daemon_out_path = "/root/.pm2/logs/crypto-daemon-out.log"
        daemon_err_path = "/root/.pm2/logs/crypto-daemon-error.log"
        
        out_logs = []
        err_logs = []
        daemon_out = []
        daemon_err = []
        
        if os.path.exists(out_path):
            with open(out_path, "r", encoding="utf-8", errors="ignore") as f:
                out_logs = f.readlines()[-50:]
        if os.path.exists(err_path):
            with open(err_path, "r", encoding="utf-8", errors="ignore") as f:
                err_logs = f.readlines()[-50:]
        if os.path.exists(daemon_out_path):
            with open(daemon_out_path, "r", encoding="utf-8", errors="ignore") as f:
                daemon_out = f.readlines()[-50:]
        if os.path.exists(daemon_err_path):
            with open(daemon_err_path, "r", encoding="utf-8", errors="ignore") as f:
                daemon_err = f.readlines()[-50:]
                
        return {
            "env_file_exists": env_exists,
            "env_file_size": env_size,
            "env_first_line": first_line,
            "model_cache_files": model_files,
            "out": out_logs,
            "error": err_logs,
            "daemon_out": daemon_out,
            "daemon_err": daemon_err,
            "env_smtp_user": os.getenv("SMTP_USER"),
            "env_smtp_pass": "SET" if os.getenv("SMTP_PASSWORD") else "NOT_SET",
            "env_db_url": "SET" if os.getenv("DATABASE_URL") else "NOT_SET"
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    import os
    port = 8001 if os.name == "nt" else 8000
    uvicorn.run("backend.main:app", host="127.0.0.1", port=port, reload=True)
