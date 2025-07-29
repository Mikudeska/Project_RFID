from django.contrib import admin
from api.models import Person, Log

# ----- Person Admin -----
@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('display_id', 'name', 'nisit', 'degree', 'seat', 'rfid', 'date')
    list_filter = ('degree', 'verified1', 'verified2', 'verified3', 'read_flag', 'read_light')
    search_fields = ('name', 'nisit', 'rfid')
    ordering = ('seat',)
    readonly_fields = ('date',)

    fieldsets = (
        ('ข้อมูลนิสิต', {
            'fields': ('name', 'nisit', 'degree', 'seat', 'rfid')
        }),
        ('สถานะตรวจสอบ', {
            'fields': (
                ('verified1', 'verified_updated_at1'),
                ('verified2', 'verified_updated_at2'),
                ('verified3', 'verified_updated_at3'),
                ('read_flag', 'read_light'),
            )
        }),
        ('ข้อมูลระบบ', {
            'fields': ('date',),
        }),
    )


# ----- Log Admin -----
@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'action', 'model', 'record_id', 'short_details')
    list_filter = ('action', 'model', 'timestamp')
    search_fields = ('details', 'record_id')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp', 'action', 'model', 'details', 'record_id')

    fieldsets = (
        ('รายละเอียด Log', {
            'fields': ('timestamp', 'action', 'model', 'record_id', 'details')
        }),
    )

    def short_details(self, obj):
        return obj.details[:60] + ('...' if len(obj.details) > 60 else '')
    short_details.short_description = 'รายละเอียด'
