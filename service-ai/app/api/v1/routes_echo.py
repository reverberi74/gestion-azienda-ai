from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class EchoRequest(BaseModel):
    message: str


@router.post("/echo")
def echo(payload: EchoRequest):
    """
    Endpoint di test: ritorna esattamente quello che riceve.
    Lo useremo per verificare wiring e JSON.
    """
    return {
        "message": payload.message,
    }
