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
        # เก็บ debug ข้อมูลใน instance variable
        if not hasattr(self, 'debug_messages'):
            self.debug_messages = []
            
        self.debug_messages.append(f"🔄 กำลังประมวลผลแถวข้อมูล: {row}")
        
        # ถ้ามีเลขที่บัณฑิตในไฟล์ จะใช้ค่านั้นเป็น id
        id_value = row.get('เลขที่บัณฑิต')
        if id_value:
            try:
                row['id'] = str(id_value)  # แปลงเป็น string เพื่อให้ตรงกับ CharField
                self.debug_messages.append(f"   📝 ตั้งค่า ID เป็น: {row['id']}")
            except ValueError:
                self.debug_messages.append(f"   ❌ ค่า ID ไม่ถูกต้อง: {id_value}")
                pass  # ถ้าไม่ใช่ตัวเลขข้ามไป

        # จัดการฟิลด์ verified (ถ้ามี) ให้แมปไปยัง verified1
        if 'verified' in row:
            verified_value = row.get('verified')
            try:
                val = int(verified_value) if verified_value in ['0', '1', '2'] else 0
                row['verified1'] = val
                self.debug_messages.append(f"   📊 แมป verified ไปยัง verified1: {val}")
            except (ValueError, TypeError):
                val = 0
                row['verified1'] = val
                self.debug_messages.append(f"   ⚠️ ค่า verified ไม่ถูกต้อง: {verified_value}, ใช้ค่าเริ่มต้น: 0")

        # จัดการฟิลด์ verified1
        if 'verified1' in row:
            value = row.get('verified1')
            try:
                val = int(value) if value in ['0', '1', '2'] else 0
                self.debug_messages.append(f"   📊 ตั้งค่า verified1 เป็น: {val}")
            except (ValueError, TypeError):
                val = 0
                self.debug_messages.append(f"   ⚠️ ค่า verified1 ไม่ถูกต้อง: {value}, ใช้ค่าเริ่มต้น: 0")
            row['verified1'] = val

        # จัดการฟิลด์ สถานะรายงานตัว (legacy)
        if 'สถานะรายงานตัว' in row:
            value = row.get('สถานะรายงานตัว')
            try:
                val = int(value) if value in ['0', '1', '2'] else 0
                self.debug_messages.append(f"   📊 ตั้งค่า verified1 จาก สถานะรายงานตัว เป็น: {val}")
            except (ValueError, TypeError):
                val = 0
                self.debug_messages.append(f"   ⚠️ ค่า สถานะรายงานตัว ไม่ถูกต้อง: {value}, ใช้ค่าเริ่มต้น: 0")
            row['verified1'] = val
        
        # ตรวจสอบว่ามีข้อมูลอยู่แล้วหรือไม่
        try:
            existing = self._meta.model.objects.get(id=row.get('id'))
            self.debug_messages.append(f"   🔍 พบข้อมูลที่มีอยู่: {existing.id} - {existing.name}")
            self.debug_messages.append(f"   📊 สถานะปัจจุบัน verified1: {existing.verified1}")
            self.debug_messages.append(f"   📊 สถานะใหม่ verified1: {row.get('verified1', 'N/A')}")
            self.debug_messages.append(f"   🔄 ข้อมูลจะถูกอัปเดตโดย django-import-export")
            
        except self._meta.model.DoesNotExist:
            self.debug_messages.append(f"   🆕 สร้างข้อมูลใหม่สำหรับ ID: {row.get('id')}")
        
        self.debug_messages.append(f"   ✅ แถวข้อมูลสุดท้าย: {row}")
        self.debug_messages.append("-" * 30)

    def save_instance(self, instance, *args, **kwargs):
        # เก็บ debug ข้อมูลใน instance variable
        if not hasattr(self, 'debug_messages'):
            self.debug_messages = []
            
        self.debug_messages.append(f"💾 กำลังบันทึกข้อมูล: {instance}")
        self.debug_messages.append(f"   ID: {instance.id}")
        self.debug_messages.append(f"   ชื่อ: {instance.name}")
        self.debug_messages.append(f"   สถานะรายงานตัว: {instance.verified1}")
        
        # ตั้งค่าเริ่มต้นสำหรับฟิลด์ verified1 ถ้าเป็น None
        if hasattr(instance, 'verified1') and instance.verified1 is None:
            instance.verified1 = 0
            self.debug_messages.append(f"   ⚠️ ตั้งค่า verified1 เป็นค่าเริ่มต้น: 0")
        
        result = super().save_instance(instance, *args, **kwargs)
        self.debug_messages.append(f"   ✅ บันทึกข้อมูลเสร็จสิ้น")
        self.debug_messages.append("-" * 30)
        return result
    
