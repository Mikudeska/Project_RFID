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
        print(f"🔄 Processing row: {row}")
        
        # ถ้ามีเลขที่บัณฑิตในไฟล์ จะใช้ค่านั้นเป็น id
        id_value = row.get('เลขที่บัณฑิต')
        if id_value:
            try:
                row['id'] = str(id_value)  # แปลงเป็น string เพื่อให้ตรงกับ CharField
                print(f"   📝 Set id to: {row['id']}")
            except ValueError:
                print(f"   ❌ Invalid id value: {id_value}")
                pass  # ถ้าไม่ใช่ตัวเลขข้ามไป

        # เดิมที่ตรวจ verified1
        value = row.get('สถานะรายงานตัว', None)
        try:
            val = int(value) if value in ['0', '1', '2'] else 0
            print(f"   📊 Set verified1 to: {val}")
        except (ValueError, TypeError):
            val = 0
            print(f"   ⚠️ Invalid verified1 value: {value}, using default: 0")
        row['สถานะรายงานตัว'] = val
        row['verified1'] = val
        
        # ตรวจสอบว่ามีข้อมูลอยู่แล้วหรือไม่ และอัปเดตโดยตรง
        try:
            existing = self._meta.model.objects.get(id=row.get('id'))
            print(f"   🔍 Found existing record: {existing.id} - {existing.name}")
            print(f"   📊 Current verified1: {existing.verified1}")
            print(f"   📊 New verified1: {val}")
            
            # อัปเดตข้อมูลโดยตรง
            existing.name = row.get('ชื่อ - สกุล', existing.name)
            existing.nisit = row.get('รหัสนักศึกษา', existing.nisit)
            existing.degree = row.get('ชื่อหลักสูตร', existing.degree)
            existing.verified1 = val
            existing.rfid = row.get('รหัส RFID', existing.rfid)
            existing.save()
            print(f"   ✅ Updated existing record: {existing.id}")
            
            # ตั้งค่าให้ข้ามการ import ครั้งนี้
            row['_skip_import'] = True
            
        except self._meta.model.DoesNotExist:
            print(f"   🆕 Creating new record for id: {row.get('id')}")
        
        print(f"   ✅ Final row: {row}")
        print("-" * 30)

    def save_instance(self, instance, *args, **kwargs):
        # ตรวจสอบว่าข้อมูลนี้ถูกอัปเดตไปแล้วหรือไม่
        if hasattr(instance, '_skip_import') and instance._skip_import:
            print(f"⏭️ Skipping save for {instance.id} (already updated)")
            return instance
            
        print(f"💾 Saving instance: {instance}")
        print(f"   ID: {instance.id}")
        print(f"   Name: {instance.name}")
        print(f"   Verified1: {instance.verified1}")
        
        if hasattr(instance, 'verified1') and instance.verified1 is None:
            instance.verified1 = 0
            print(f"   ⚠️ Set verified1 to default: 0")
        
        result = super().save_instance(instance, *args, **kwargs)
        print(f"   ✅ Save completed")
        print("-" * 30)
        return result
    
