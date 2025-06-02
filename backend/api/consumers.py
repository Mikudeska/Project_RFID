from channels.generic.websocket import AsyncWebsocketConsumer
import json

class TestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({"message": "Connected!"}))

    async def receive(self, text_data):
        await self.send(text_data=json.dumps({"message": f"Echo: {text_data}"}))
