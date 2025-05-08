# backend/api/resources.py
from import_export import resources, fields
from .models import Person

class PersonResource(resources.ModelResource):
    formatted_id = fields.Field(attribute='id', column_name='ลำดับ')
    name = fields.Field(attribute='name', column_name='ชื่อ-นามสกุล')
    nisit = fields.Field(attribute='nisit', column_name='รหัสนิสิต')
    degree = fields.Field(attribute='degree', column_name='ชื่อปริญญา')
    seat = fields.Field(attribute='seat', column_name='ที่นั่ง')
    verified = fields.Field(attribute='verified', column_name='สถานะรายงานตัว')
    rfid = fields.Field(attribute='rfid', column_name='รหัส RFID')

    class Meta:
        model = Person
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