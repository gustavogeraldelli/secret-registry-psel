from fastapi import FastAPI
from .routes import router

app = FastAPI(title="Registry API")

app.include_router(router)