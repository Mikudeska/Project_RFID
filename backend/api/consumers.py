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

class CrudConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("crud01_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("crud01_group", self.channel_name)

    async def send_update(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message']
        }))
