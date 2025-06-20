from channels.generic.websocket import AsyncWebsocketConsumer, AsyncJsonWebsocketConsumer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from collections import Counter
from .models import Person
import json

def broadcast_to_crud01(message):
    if not settings.USE_CHANNEL:
        print("📡 WebSocket disabled. Skipping broadcast.")
        return
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "crud01_group",
        {
            "type": "send_message",
            "message": message,
        }
    )

def broadcast_stats_update():
    persons = Person.objects.all()
    total = persons.count()

    verified_counter = Counter()
    for person in persons:
        latest_verified = get_latest_verified(person)
        if latest_verified in [0, 1, 2]:
            verified_counter[latest_verified] += 1

    stats = {
        'total': total,
        'checked_in': verified_counter[0],
        'in_checkin_room': verified_counter[1],
        'in_graduation_room': verified_counter[2],
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

def get_latest_verified(person):
    times = {
        1: person.verified_updated_at1,
        2: person.verified_updated_at2,
        3: person.verified_updated_at3,
    }
    values = {
        1: person.verified1,
        2: person.verified2,
        3: person.verified3,
    }
    latest_time = None
    latest_verified = None

    for key in [1, 2, 3]:
        time = times[key]
        value = values[key]
        if time and value in [0, 1, 2]:
            if not latest_time or time > latest_time:
                latest_time = time
                latest_verified = value
    return latest_verified


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
