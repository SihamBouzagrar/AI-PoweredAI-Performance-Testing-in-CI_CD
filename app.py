import logging

from fastapi import FastAPI

from api.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="AI Performance Test Generator",
    version="2.0",
)

app.include_router(router)


@app.get("/")
def home():
    return {"message": "AI Server Running"}