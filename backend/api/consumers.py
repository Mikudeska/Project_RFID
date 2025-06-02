# api/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class TestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send_json({'message': 'Connected!'})

    async def receive(self, text_data):
        # รับข้อความจาก client แล้วส่งกลับ
        await self.send_json({'message': f"Echo: {text_data}"})

    async def disconnect(self, close_code):
        pass
