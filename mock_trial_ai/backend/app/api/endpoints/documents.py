from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def read_documents():
    """
    Endpoint to retrieve a list of documents.
    """
    return {"message": "Documents API works!"}

@router.post("/")
def create_document(document: dict):
    """
    Endpoint to create a new document.
    :param document: A dictionary containing document details.
    """
    return {"message": "Document created!", "document": document}