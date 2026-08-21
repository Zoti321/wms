"""仓脉 WMS API 入口。"""

from fastapi import FastAPI

app = FastAPI(title="仓脉 WMS API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
