from fastapi import FastAPI, WebSocket

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.websocket("/game")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
