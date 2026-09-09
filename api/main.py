from fastapi import FastAPI
from pydantic import BaseModel
from src.tower_opt.pipeline import run

app = FastAPI(title="Cell Tower Placement Optimizer")


class OptimizeRequest(BaseModel):
    budget: int
    radius_km: float


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/optimize")
def optimize(req: OptimizeRequest):
    return run(req.budget, req.radius_km)