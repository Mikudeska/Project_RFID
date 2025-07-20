from import_export import resources, fields
from .models import Person

class PersonResource(resources.ModelResource):
    formatted_id = fields.Field(column_name='ลำดับ')
    name = fields.Field(attribute='name', column_name='ชื่อ-นามสกุล')
    nisit = fields.Field(attribute='nisit', column_name='รหัสนิสิต')
    degree = fields.Field(attribute='degree', column_name='ชื่อปริญญา')
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
        value = row.get('สถานะรายงานตัว', '')
        try:
            val = int(value)
            if val not in [0, 1, 2]:
                raise ValueError("ค่าสถานะต้องเป็น 0, 1 หรือ 2 เท่านั้น")
            row['สถานะรายงานตัว'] = val
            row['verified1'] = val
        except (ValueError, TypeError):
            raise ValueError("สถานะรายงานตัวต้องเป็นตัวเลข 0, 1 หรือ 2 เท่านั้น")

    def save_instance(self, instance, *args, **kwargs):
        if hasattr(instance, 'verified1') and instance.verified1 is None:
            instance.verified1 = 0
        return super().save_instance(instance, *args, **kwargs)
