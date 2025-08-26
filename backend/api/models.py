from django.db import models, transaction
from django.utils import timezone
from django.contrib.auth.models import User
import random

class Person(models.Model):
    name = models.CharField(max_length=100)
    nisit = models.CharField(max_length=11, unique=True, blank=True)
    degree = models.CharField(max_length=100)
    seat = models.IntegerField(unique=True, blank=True)

    verified1 = models.IntegerField(default=0, blank=True)
    verified2 = models.IntegerField(default=0, blank=True)
    verified3 = models.IntegerField(default=0, blank=True)

    verified_updated_at1 = models.DateTimeField(null=True, blank=True)
    verified_updated_at2 = models.DateTimeField(null=True, blank=True)
    verified_updated_at3 = models.DateTimeField(null=True, blank=True)

    read_flag = models.BooleanField(default=False, blank=True) 
    read_light = models.BooleanField(default=False, blank=True) 

    date = models.DateTimeField(auto_now_add=True)
    rfid = models.CharField(max_length=25, unique=True, blank=True, null=True)  

    @staticmethod
    def generate_unique_value(length, model, field):
        while True:
            value = ''.join([str(random.randint(0, 9)) for _ in range(length)])
            if not model.objects.filter(**{field: value}).exists():
                return value

    def save(self, *args, **kwargs):
        if not self.nisit:
            self.nisit = self.generate_unique_value(11, Person, 'nisit')

        if not self.seat:
            with transaction.atomic():
                # Lock the table to prevent concurrent updates
                last_person = Person.objects.select_for_update().order_by('-seat').first()
                self.seat = last_person.seat + 1 if last_person else 1
        
        super().save(*args, **kwargs)

    def display_id(self):   
        return str(self.id).zfill(4)

    def __str__(self):
        local_date = timezone.localtime(self.date)
        return (
            f"ลำดับ {self.display_id()} "
            f"รหัสนิสิต {self.nisit} "
            f"ชื่อ {self.name} "
            f"อยู่คณะ {self.degree} "
            f"นั่งที่ {self.seat} "
            f"เมื่อ {local_date.strftime('%d/%m/%Y %H:%M:%S')}"
        )

class Log(models.Model):
    ACTION_CHOICES = [
        ('add', 'Add'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('import', 'Import'),
        ('export', 'Export'),
        ('reset', 'Reset'),
        ('rfid_scan', 'RFID Scan'),
        ('comment', 'Comment'),
    ]
    
    action = models.CharField(max_length=10)
    model = models.CharField(max_length=50)
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    record_id = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.action = self.action.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.timestamp} - {self.action} - {self.model}"
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.nickname or self.user.username
    