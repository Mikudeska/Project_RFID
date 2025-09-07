from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Create Lock and Unlock groups'

    def handle(self, *args, **kwargs):
        Group.objects.get_or_create(name="Locked")
        Group.objects.get_or_create(name="Unlocked")
        self.stdout.write(self.style.SUCCESS('Groups Locked and Unlocked created'))
