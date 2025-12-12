from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    """
    Endpoint di health-check.
    Usato da Laravel/React per verificare che il servizio AI è vivo.
    """
    return {"status": "ok"}
