from import_export import resources, fields
from .models import Person

class PersonResource(resources.ModelResource):
    id = fields.Field(attribute='id', column_name='เลขที่บัณฑิต')
    name = fields.Field(attribute='name', column_name='ชื่อ - สกุล')
    nisit = fields.Field(attribute='nisit', column_name='รหัสนักศึกษา')
    degree = fields.Field(attribute='degree', column_name='ชื่อหลักสูตร')
    seat = fields.Field(attribute='seat', column_name='ที่นั่ง')
    verified1 = fields.Field(attribute='verified1', column_name='สถานะรายงานตัว')
    rfid = fields.Field(attribute='rfid', column_name='รหัส RFID')

    class Meta:
        model = Person
        fields = (
            'id',
            'nisit',
            'name',
            'degree',
            'seat',
            'verified1',
            'rfid',
        )
        export_order = [
            'id',
            'nisit',
            'name',
            'degree',
            'seat',
            'verified1',
            'rfid'
        ]
        import_id_fields = ['id']

    def dehydrate_formatted_id(self, person):
        return str(person.id).zfill(4)

    def dehydrate_verified(self, person):
        return person.verified1

    def before_import_row(self, row, **kwargs):
        # ถ้ามีเลขที่บัณฑิตในไฟล์ จะใช้ค่านั้นเป็น id
        id_value = row.get('เลขที่บัณฑิต')
        if id_value:
            try:
                row['id'] = str(id_value)  # แปลงเป็น string เพื่อให้ตรงกับ CharField
            except ValueError:
                pass  # ถ้าไม่ใช่ตัวเลขข้ามไป

        # จัดการฟิลด์ verified (ถ้ามี) ให้แมปไปยัง verified1
        if 'verified' in row:
            verified_value = row.get('verified')
            try:
                val = int(verified_value) if verified_value in ['0', '1', '2'] else 0
                row['verified1'] = val
            except (ValueError, TypeError):
                val = 0
                row['verified1'] = val

        # จัดการฟิลด์ verified1
        if 'verified1' in row:
            value = row.get('verified1')
            try:
                val = int(value) if value in ['0', '1', '2'] else 0
            except (ValueError, TypeError):
                val = 0
            row['verified1'] = val

        # จัดการฟิลด์ สถานะรายงานตัว (legacy)
        if 'สถานะรายงานตัว' in row:
            value = row.get('สถานะรายงานตัว')
            try:
                val = int(value) if value in ['0', '1', '2'] else 0
            except (ValueError, TypeError):
                val = 0
            row['verified1'] = val

    def save_instance(self, instance, *args, **kwargs):
        # ตั้งค่าเริ่มต้นสำหรับฟิลด์ verified1 ถ้าเป็น None
        if hasattr(instance, 'verified1') and instance.verified1 is None:
            instance.verified1 = 0
        
        result = super().save_instance(instance, *args, **kwargs)
        return result
    
