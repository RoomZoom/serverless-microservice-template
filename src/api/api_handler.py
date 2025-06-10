# src/api/api_handler.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from models.payload_models import CreateItemRequest
from adapters import dynamodb_adapter, sqs_adapter

app = FastAPI()


@app.post("/create")
async def create_item(request: Request):
    try:
        data = await request.json()
        item = CreateItemRequest(**data)
        dynamodb_adapter.put_item("my-table-dev", item.dict())
        sqs_adapter.send_message(
            "https://sqs.us-east-1.amazonaws.com/123456789012/my-queue-dev", item.dict()
        )
        return JSONResponse(
            status_code=200, content={"message": "Item created and queued."}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
