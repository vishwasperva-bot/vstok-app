from fastapi import FastAPI

app = FastAPI(
    title="VSTOK Backend",
    description="SEBI-safe technical signal backend",
    version="0.1.0"
)

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "VSTOK backend is running"
    }

@app.get("/health")
def health():
    return {"health": "green"}
