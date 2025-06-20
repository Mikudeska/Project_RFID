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
                if validated_data[verified_key] != getattr(instance, verified_key):
                    validated_data[updated_key] = timezone.now()
        return super().update(instance, validated_data)

    def get_verified(self, obj):
        verified_values = [obj.verified1, obj.verified2, obj.verified3]
        valid_values = [v for v in verified_values if v is not None]
        if valid_values:
            return max(valid_values)
        return None

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
            'read_flag_in': instance.read_flag_in,
            'read_flag_out': instance.read_flag_out,
            'read_light_in': instance.read_light_in,
            'read_light_out': instance.read_light_out,
        }
        return data


class LogSerializer(serializers.ModelSerializer):
    timestamp = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    
    class Meta:
        model = Log
        fields = '__all__'