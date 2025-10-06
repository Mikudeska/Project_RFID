from import_export import resources, fields
from .models import Person

class PersonResource(resources.ModelResource):
    formatted_id = fields.Field(column_name='ลำดับ')
    name = fields.Field(attribute='name', column_name='ชื่อ - สกุล')
    nisit = fields.Field(attribute='nisit', column_name='รหัสนักศึกษา')
    degree = fields.Field(attribute='degree', column_name='ชื่อหลักสูตร')
    seat = fields.Field(attribute='seat', column_name='ที่นั่ง')
    verified1 = fields.Field(attribute='verified1', column_name='สถานะรายงานตัว')
    rfid = fields.Field(attribute='rfid', column_name='รหัส RFID')

    class Meta:
        model = Person
        fields = (
            'formatted_id',
            'nisit',
            'name',
            'degree',
            'seat',
            'verified1',
            'rfid',
        )
        export_order = [
            'formatted_id',
            'nisit',
            'name',
            'degree',
            'seat',
            'verified1',
            'rfid'
        ]
        import_id_fields = ['nisit']

    def dehydrate_formatted_id(self, person):
        return str(person.id).zfill(4)

    def dehydrate_verified(self, person):
        return person.verified1

    def before_import_row(self, row, **kwargs):
        # ตรวจสอบว่ามีคอลัมน์ 'สถานะรายงานตัว' หรือไม่
        value = row.get('สถานะรายงานตัว', None)

        try:
            if value is None or value == '':
                val = 0  # หากไม่มีให้ใช้ค่า default เป็น 0
            else:
                val = int(value)
                if val not in [0, 1, 2]:
                    raise ValueError("ค่าสถานะต้องเป็น 0, 1 หรือ 2 เท่านั้น")
        except (ValueError, TypeError):
            val = 0  # ถ้าแปลงไม่ได้ให้ใช้ค่า default เป็น 0

        # บันทึกค่าที่แปลงแล้วกลับไป
        row['สถานะรายงานตัว'] = val
        row['verified1'] = val

    def save_instance(self, instance, *args, **kwargs):
        if hasattr(instance, 'verified1') and instance.verified1 is None:
            instance.verified1 = 0
        return super().save_instance(instance, *args, **kwargs)
