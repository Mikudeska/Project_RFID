from import_export import resources, fields
from .models import Person

class PersonResource(resources.ModelResource):
    formatted_id = fields.Field(column_name='ลำดับ')
    name = fields.Field(attribute='name', column_name='ชื่อ-นามสกุล')
    nisit = fields.Field(attribute='nisit', column_name='รหัสนิสิต')
    degree = fields.Field(attribute='degree', column_name='ชื่อปริญญา')
    seat = fields.Field(attribute='seat', column_name='ที่นั่ง')
    verified = fields.Field(column_name='สถานะรายงานตัว')
    rfid = fields.Field(attribute='rfid', column_name='รหัส RFID')

    class Meta:
        model = Person
        fields = (
            'formatted_id',  # << ต้องใส่ด้วย
            'nisit',
            'name',
            'degree',
            'seat',
            'verified',
            'rfid',
        )
        export_order = [
            'formatted_id',
            'nisit',
            'name',
            'degree',
            'seat',
            'verified',
            'rfid'
        ]
        import_id_fields = ['nisit']


    def dehydrate_formatted_id(self, person):
        return str(person.id).zfill(4)

    def dehydrate_verified(self, person):
        if person.verified1 == 1 or person.verified2 == 1 or person.verified3 == 1:
            return "รายงานตัวแล้ว"
        return "ยังไม่รายงานตัว"

