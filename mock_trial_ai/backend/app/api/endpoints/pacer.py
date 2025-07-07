from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def read_pacer():
    return {"message": "PACER endpoint is now running"}