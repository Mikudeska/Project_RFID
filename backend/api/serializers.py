from rest_framework import serializers
from .models import Person, Log
from datetime import datetime
from django.utils import timezone

class PersonSerializer(serializers.ModelSerializer):
    verified = serializers.SerializerMethodField()  # ส่ง verified แบบล่าสุดจริง

    class Meta:
        model = Person
        fields = '__all__'

    def update(self, instance, validated_data):
        for i in range(1, 4):
            verified_key = f"verified{i}"
            updated_key = f"verified_updated_at{i}"
            if verified_key in validated_data:
                new_val = validated_data[verified_key]
                old_val = getattr(instance, verified_key)
                if old_val is None or old_val != new_val:
                    validated_data[updated_key] = timezone.now()
        instance = super().update(instance, validated_data)
        instance.save()  # บันทึกจริง
        return instance

    def get_verified(self, obj):
        latest_verified = None
        latest_time = None

        # เช็กจาก timestamp ก่อน
        for i in range(1, 4):
            verified_value = getattr(obj, f'verified{i}')
            updated_time = getattr(obj, f'verified_updated_at{i}')
            if updated_time:
                if latest_time is None or updated_time > latest_time:
                    latest_time = updated_time
                    latest_verified = verified_value

        # ถ้าไม่มี timestamp เลย (null หมด)
        if latest_verified is None:
            for i in range(1, 4):
                verified_value = getattr(obj, f'verified{i}')
                if verified_value is not None:
                    return verified_value
            return None

        return latest_verified

    def validate_nisit(self, value):
        if Person.objects.filter(nisit=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("รหัสนิสิตนี้มีอยู่แล้ว")
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['_original'] = {
            'id': instance.id,
            'name': instance.name,
            'nisit': instance.nisit,
            'degree': instance.degree,
            'seat': instance.seat,
            'verified1': instance.verified1,
            'verified2': instance.verified2,
            'verified3': instance.verified3,
            'verified': data.get('verified'),  # ใช้จาก get_verified
            'rfid': instance.rfid,
            'read_flag': instance.read_flag,
            'read_light': instance.read_light,
        }
        return data


class LogSerializer(serializers.ModelSerializer):
    timestamp = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    
    class Meta:
        model = Log
        fields = '__all__'
        