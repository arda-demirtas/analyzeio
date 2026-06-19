from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base
from backend.routes_auth import router as auth_router
from backend.routes_predict import router as predict_router

# Initialize database tables
# In production, alembic migrations are preferred, but this is clean and automatic for sqlite setup.
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

@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "analyzeio-api",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
