from channels.generic.websocket import AsyncWebsocketConsumer, AsyncJsonWebsocketConsumer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json

def broadcast_to_crud01(message: str):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "crud01_group",
        {
            "type": "send_update",
            "message": message,
        }
    )  

def broadcast_stats_update():
    from django.db.models import Count
    from .models import Person
    stats = {
        'total': Person.objects.count(),
        'checked_in': Person.objects.filter(verified=0).count(),
        'in_checkin_room': Person.objects.filter(verified=1).count(),
        'in_graduation_room': Person.objects.filter(verified=2).count()
    }
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "crud01_group",
        {
            "type": "send_update",
            "message": {
                "action": "stats",
                "data": stats
            }
        }
    )

class TestConsumer(AsyncJsonWebsocketConsumer):
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
