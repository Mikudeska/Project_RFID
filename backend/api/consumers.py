from channels.generic.websocket import AsyncWebsocketConsumer, AsyncJsonWebsocketConsumer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from collections import Counter
from .models import Person
from datetime import datetime, timezone
import json

def broadcast_to_crud01(message):
    if not settings.USE_CHANNEL:
        print("📡 WebSocket disabled. Skipping broadcast.")
        return
    
    print("📡 Broadcasting message to crud01_group:", message)  # <-- เพิ่มตรงนี้
    
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
    print("📊 Stats:", stats)
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

def broadcast_ws(action, data=None):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "crud01_group",  # กลุ่มที่ client join
        {
            "type": "send.message",
            "message": {
                "action": action,
                "data": data or {}
            }
        }
    )

def get_latest_verified(person):
    times = {
        1: person.verified_updated_at1 or datetime.min.replace(tzinfo=timezone.utc),
        2: person.verified_updated_at2 or datetime.min.replace(tzinfo=timezone.utc),
        3: person.verified_updated_at3 or datetime.min.replace(tzinfo=timezone.utc),
    }
    values = {
        1: person.verified1,
        2: person.verified2,
        3: person.verified3,
    }

    latest_time = None
    latest_verified = None

    for key in [1, 2, 3]:
        value = values[key]
        if value in [0, 1, 2]:
            time = times[key]
            if not latest_time or time > latest_time:
                latest_time = time
                latest_verified = value

    return latest_verified

connected_clients = set()

# เก็บชื่อ channel ของผู้เชื่อมต่อทั้งหมด
connected_clients = set()

class CrudConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("crud01_group", self.channel_name)
        await self.accept()

        # 👥 เพิ่มผู้ใช้ใหม่
        connected_clients.add(self.channel_name)
        await self.broadcast_viewer_count()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("crud01_group", self.channel_name)

        # 👥 เอาผู้ใช้ที่ disconnect ออก
        connected_clients.discard(self.channel_name)
        await self.broadcast_viewer_count()

    async def send_update(self, event):
        await self.send(text_data=json.dumps(event['message']))

    async def send_message(self, event):
        print("send_message called:", event)
        await self.send(text_data=json.dumps(event['message']))

    # 📢 ส่งจำนวนผู้ชม
    async def broadcast_viewer_count(self):
        count = len(connected_clients)

        # ส่งให้ทุกคนในกลุ่ม
        await self.channel_layer.group_send(
            "crud01_group",
            {
                "type": "send.viewer.count",
                "count": count
            }
        )

    # 📬 ส่งให้แต่ละ client
    async def send_viewer_count(self, event):
        await self.send(text_data=json.dumps({
            "type": "viewer_count",
            "count": event["count"]
        }))


