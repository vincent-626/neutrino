from fastapi import APIRouter, Response

router = APIRouter()

# Set by lifespan after model is loaded
model_ready = False


def set_ready(ready: bool) -> None:
    global model_ready
    model_ready = ready


@router.get("/healthz")
async def healthz():
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(response: Response):
    if not model_ready:
        response.status_code = 503
        return {"status": "loading"}
    return {"status": "ready"}
