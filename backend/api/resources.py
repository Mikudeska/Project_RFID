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

        # เดิมที่ตรวจ verified1
        value = row.get('สถานะรายงานตัว', None)
        try:
            val = int(value) if value in ['0', '1', '2'] else 0
        except (ValueError, TypeError):
            val = 0
        row['สถานะรายงานตัว'] = val
        row['verified1'] = val

    def save_instance(self, instance, *args, **kwargs):
        if hasattr(instance, 'verified1') and instance.verified1 is None:
            instance.verified1 = 0
        return super().save_instance(instance, *args, **kwargs)
    
    def get_or_init_instance(self, instance_loader, row):
        """
        Override เพื่อให้การอัปเดตทำงานถูกต้อง
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # ลองหาข้อมูลที่มีอยู่แล้ว
            instance = self._meta.model.objects.get(id=row.get('id'))
            logger.info(f"Found existing instance: {instance.id} - {instance.name}")
            return instance, False  # False = ไม่ใช่ instance ใหม่
        except self._meta.model.DoesNotExist:
            # ถ้าไม่พบ ให้สร้างใหม่
            logger.info(f"Creating new instance for id: {row.get('id')}")
            return super().get_or_init_instance(instance_loader, row)
