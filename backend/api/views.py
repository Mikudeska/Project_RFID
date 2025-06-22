from collections import Counter
from django.http import HttpResponse
from django.utils import timezone
from django.conf import settings
from django.db import transaction, connection
from django.http import JsonResponse
from tablib import Dataset
from rest_framework.views import APIView, View
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework import status, generics
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
from .resources import PersonResource
from .consumers import broadcast_to_crud01, broadcast_stats_update
from .models import Person, Log
from .serializers import PersonSerializer, LogSerializer
from datetime import datetime
import urllib.parse
import os, io, json
import traceback

class ResetDatabase(APIView):
    def post(self, request):
        try:
            with transaction.atomic():
                # 1. บันทึกจำนวนข้อมูลก่อนลบ (Option)
                total_records = Person.objects.count()
                
                # 2. ลบข้อมูลทั้งหมด
                Person.objects.all().delete()
                
                # 3. รีเซ็ต AUTO_INCREMENT (MySQL/MariaDB)
                reset_auto_increment = False
                if 'mysql' in connection.settings_dict['ENGINE']:
                    cursor = connection.cursor()
                    table_name = Person._meta.db_table
                    cursor.execute(f"ALTER TABLE {table_name} AUTO_INCREMENT = 1;")
                    reset_auto_increment = True
                
                # 4. บันทึก Log
                log_details = (
                    f"รีเซ็ตฐานข้อมูล | ลบข้อมูลทั้งหมด {total_records} รายการ"
                )
                
                Log.objects.create(
                    action='Reset',
                    model='Database',
                    details=log_details,
                    record_id=None
                )
                
                return Response(
                    {'success': 'รีเซ็ตฐานข้อมูลสำเร็จ'}, 
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            # บันทึก Log กรณี error
            Log.objects.create(
                action='Reset',
                model='Database',
                details=f"รีเซ็ตล้มเหลว: {str(e)}",
                record_id=None,
            )
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class ResetLog(APIView):
    def post(self, request):
        try:
            with transaction.atomic():
                # 1. บันทึกจำนวนข้อมูลก่อนลบ (Option)
                total_records = Log.objects.count()
                
                # 2. ลบข้อมูลทั้งหมด
                Log.objects.all().delete()
                
                # 3. รีเซ็ต AUTO_INCREMENT (MySQL/MariaDB)
                reset_auto_increment = False
                if 'mysql' in connection.settings_dict['ENGINE']:
                    cursor = connection.cursor()
                    table_name = Log._meta.db_table
                    cursor.execute(f"ALTER TABLE {table_name} AUTO_INCREMENT = 1;")
                    reset_auto_increment = True
                
                # 4. บันทึก Log
                log_details = (
                    f"รีเซ็ตประวัติ | ลบข้อมูลทั้งหมด {total_records} รายการ"
                )
                
                Log.objects.create(
                    action='Reset',
                    model='Database',
                    details=log_details,
                    record_id=None
                )   
                
                return Response(
                    {'success': 'รีเซ็ตประวัติสำเร็จ'}, 
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            # บันทึก Log กรณี error
            Log.objects.create(
                action='Reset',
                model='Database',
                details=f"รีเซ็ตล้มเหลว: {str(e)}",
                record_id=None,
            )
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ExportPDF(View):
    def get(self, request):
        try:
            # ตั้งค่า Font ไทย
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            FONT_PATH = os.path.join(BASE_DIR, 'fonts', 'THSarabunNew.ttf')
            pdfmetrics.registerFont(TTFont('THSarabun', FONT_PATH))

            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            p.setFont('THSarabun', 14)

            # เขียนหัวตาราง
            p.drawString(50, 800, "ลำดับ")
            p.drawString(150, 800, "ชื่อ-นามสกุล")
            p.drawString(300, 800, "รหัสนิสิต")
            p.drawString(400, 800, "สถานะรายงานตัว")

            # ดึงข้อมูล
            persons = Person.objects.all().order_by('seat')
            y_position = 780  # ตำแหน่งเริ่มต้น
            def get_verified_status(person):
                return "รายงานตัวแล้ว" if person.verified1 == 1 or person.verified2 == 1 or person.verified3 == 1 else "ยังไม่รายงานตัว"
            
            for i, person in enumerate(persons, start=1):
                p.drawString(50, y_position, f"{i:04d}")
                p.drawString(150, y_position, person.name)
                p.drawString(300, y_position, person.nisit)
                p.drawString(400, y_position, get_verified_status(person))
                y_position -= 20  # เลื่อนบรรทัด

                # ขึ้นหน้าใหม่หากข้อมูลเต็มหน้า
                if y_position < 50:
                    p.showPage()
                    y_position = 800
                    p.setFont('THSarabun', 14)

            p.save()
            buffer.seek(0)

            # สร้าง HTTP Response
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = 'inline; filename="graduates.pdf"'
            response["Access-Control-Expose-Headers"] = "Content-Disposition"
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Content-Length'] = str(len(buffer.getvalue()))
            Log.objects.create(
                action='Export',
                model='Person',
                details="โหลดไฟล์เป็น PDF",
                record_id=None
            )
            return response

        except Exception as e:
            print('PDF Export Error:', str(e))
            return JsonResponse({'error': str(e)}, status=500)

from datetime import datetime

class ExportPDFResult(View):
    def get(self, request):
        try:
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            FONT_PATH = os.path.join(BASE_DIR, 'fonts', 'THSarabunNew.ttf')
            pdfmetrics.registerFont(TTFont('THSarabun', FONT_PATH))

            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            p.setFont('THSarabun', 25)

            def degree_group(name):
                if 'ดุษฎีบัณฑิต' in name:
                    return 'ป.เอก'
                elif 'มหาบัณฑิต' in name:
                    return 'ป.โท'
                return 'ป.ตรี'

            def is_verified(person):
                return person.verified1 == 1 or person.verified2 == 1 or person.verified3 == 1

            persons = Person.objects.all()

            degree_summary = {
                'ป.ตรี': {'total': 0, 'present': 0},
                'ป.โท': {'total': 0, 'present': 0},
                'ป.เอก': {'total': 0, 'present': 0},
            }

            branch_summary = {}

            # เก็บ id ที่ยังไม่รายงานตัว
            missing_ids = []

            for person in persons:
                dg = degree_group(person.degree)
                degree_summary[dg]['total'] += 1

                if is_verified(person):
                    degree_summary[dg]['present'] += 1
                else:
                    missing_ids.append(person.id)

                branch = person.degree if person.degree else 'ไม่ระบุ'
                if branch not in branch_summary:
                    branch_summary[branch] = {'total': 0, 'present': 0}
                branch_summary[branch]['total'] += 1

                if is_verified(person):
                    branch_summary[branch]['present'] += 1

            date_str = datetime.now().strftime("%d/%m/%Y")
            p.drawRightString(width - 40, height - 40, f"วันที่ {date_str}")

            p.setFont('THSarabun', 25)
            p.drawCentredString(width / 2, height - 80, "ใบสรุปผล")

            p.setFont('THSarabun', 18)
            y = height - 140
            p.drawString(40, y, "ชื่อ")
            p.drawString(160, y, "จำนวนนศ. ทั้งหมด")
            p.drawString(320, y, "จำนวนนศ. ที่มา")
            p.drawString(460, y, "จำนวนนศ. ที่ขาด")
            y -= 50

            total_all = present_all = 0
            for degree in ['ป.ตรี', 'ป.โท', 'ป.เอก']:
                total = degree_summary[degree]['total']
                present = degree_summary[degree]['present']
                absent = total - present
                p.drawString(40, y, degree)
                p.drawRightString(230, y, f"{total}     คน")
                p.drawRightString(380, y, f"{present}   คน")
                p.drawRightString(530, y, f"{absent}    คน")
                total_all += total
                present_all += present
                y -= 40

            absent_all = total_all - present_all
            p.setFont('THSarabun', 18)
            p.drawString(40, y, "ยอดรวมทั้งหมด")
            p.drawRightString(230, y, f"{total_all}     คน")
            p.drawRightString(380, y, f"{present_all}   คน")
            p.drawRightString(530, y, f"{absent_all}    คน")
            y -= 50

            # --- หน้าใหม่ และส่วนสาขา ---
            p.showPage()

            p.setFont('THSarabun', 25)
            p.drawRightString(width - 40, height - 40, f"วันที่ {date_str}")

            p.setFont('THSarabun', 25)
            p.drawCentredString(width / 2, height - 80, "ตารางแต่ละสาขา")

            p.setFont('THSarabun', 14)
            y = height - 120
            p.drawString(40, y, "ชื่อสาขา")
            p.drawString(210, y, "จำนวนนศ. ทั้งหมด")
            p.drawString(320, y, "จำนวนนศ. ที่มา")
            p.drawString(420, y, "จำนวนนศ. ที่ขาด")
            p.drawString(530, y, "คิดเป็น %")

            y -= 25

            for branch, vals in sorted(branch_summary.items()):
                total = vals['total']
                present = vals['present']
                absent = total - present
                percent = (present / total * 100) if total > 0 else 0

                p.drawString(40, y, branch)
                p.drawRightString(260, y, f"{total} คน")
                p.drawRightString(360, y, f"{present} คน")
                p.drawRightString(470, y, f"{absent} คน")
                p.drawRightString(560, y, f"{percent:.2f} %")

                y -= 20
                if y < 50:
                    p.showPage()
                    y = height - 80
                    p.setFont('THSarabun', 14)
                    p.drawString(40, y, "ชื่อสาขา")
                    p.drawString(210, y, "จำนวนนศ. ทั้งหมด")
                    p.drawString(320, y, "จำนวนนศ. ที่มา")
                    p.drawString(420, y, "จำนวนนศ. ที่ขาด")
                    p.drawString(530, y, "คิดเป็น %")
                    y -= 25

            # --- หน้าใหม่สำหรับ ID ที่ยังไม่รายงานตัว ---
            p.showPage()
            p.setFont('THSarabun', 25)
            p.drawCentredString(width / 2, height - 80, "รายชื่อที่ยังไม่รายงานตัว")
            p.setFont('THSarabun', 16)

            # จัดเรียง id ก่อนแสดง
            missing_persons = Person.objects.filter(
                verified1=0,
                verified2=0,
                verified3=0
            ).order_by('id')

            y = height - 120
            for person in missing_persons:
                line = f"- [{person.id}] {person.nisit} {person.name} {person.degree}"
                p.drawString(40, y, line)
                y -= 20

                if y < 50:
                    p.showPage()
                    y = height - 80
                    p.setFont('THSarabun', 16)

            p.save()
            buffer.seek(0)

            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response["Access-Control-Expose-Headers"] = "Content-Disposition"
            response['Content-Disposition'] = 'attachment; filename="result.pdf"'
            response['Content-Transfer-Encoding'] = 'binary'
            response['Cache-Control'] = 'no-cache'

            Log.objects.create(
                action='Export',
                model='Person',
                details="โหลดไฟล์สรุป PDF",
                record_id=None
            )

            return response

        except Exception as e:
            print("ERROR:", str(e))
            import traceback
            print(traceback.format_exc())
            return HttpResponse(f'เกิดข้อผิดพลาด: {str(e)}', status=500)


class ExportData(APIView):
    def get(self, request, format_type):
        resource = PersonResource()
        dataset = resource.export()
        response = None  # กำหนดค่าเริ่มต้น

        try:
            format_type = format_type.lower()  # แปลงเป็นตัวเล็กทั้งหมด

            if format_type == 'xlsx':
                response = HttpResponse(
                    dataset.xlsx,
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                filename = urllib.parse.quote('รายชื่อบัณฑิต.xlsx')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'

            elif format_type == 'csv':
                response = HttpResponse(dataset.csv, content_type='text/csv; charset=utf-8-sig')
                filename = urllib.parse.quote('รายชื่อบัณฑิต.csv')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'

            else:
                return Response(
                    {'error': 'รูปแบบไฟล์ไม่ถูกต้อง'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            Log.objects.create(
                action='Export',
                model='Person',
                details=f"โหลดไฟล์เป็น {format_type}"
            )
            return response

        except Exception as e:
            return Response(
                {'error': 'Internal Server Error'}, 
                status=500
            )

class ImportData(APIView):
    def post(self, request):
        file = request.FILES['file']
        dataset = Dataset()
        resource = PersonResource()

        try:
            # อ่านไฟล์
            if file.name.endswith('.xlsx'):
                dataset.load(file.read(), format='xlsx')
            elif file.name.endswith('.csv'):
                dataset.load(file.read().decode('utf-8-sig'), format='csv')

            # ตรวจสอบข้อมูล
            if len(dataset) == 0:
                raise ValueError("ไฟล์ที่อัปโหลดว่างเปล่า")

            # นำเข้าข้อมูล
            result = resource.import_data(dataset, dry_run=False, raise_errors=True)
            
            # แก้ไขการนับจำนวนรายการ
            imported_count = (
                result.totals.get('new', 0)    # ข้อมูลใหม่
                + result.totals.get('update', 0)  # ข้อมูลที่อัปเดต
            )

            # บันทึก Log
            Log.objects.create(
                action='Import',
                model='Person',
                details=f"นำเข้าฐานข้อมูล {imported_count} รายการ ( ใหม่ {result.totals.get('new', 0)} อัปเดต {result.totals.get('update', 0)} )",
                record_id=None
            )

            return Response(
                {'success': f'นำเข้าข้อมูลสำเร็จ {imported_count} รายการ'}, 
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            Log.objects.create(
                action='Import',
                model='Person',
                details=f"นำเข้าข้อมูลล้มเหลว: {str(e)}",
                record_id=None
            )
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class StatsView(APIView):
    def get(self, request):
        from collections import Counter
        verified_counter = Counter()
        persons = Person.objects.all()
        total = persons.count()

        for person in persons:
            verified_with_time = []
            for i in range(1, 4):
                value = getattr(person, f'verified{i}', None)
                timestamp = getattr(person, f'verified_updated_at{i}', None)
                if value in [0, 1, 2]:
                    # ถ้า timestamp ไม่มี ให้ใช้วันที่เก่ามากๆ แทน เพื่อให้ไม่เลือกก่อน timestamp อื่น
                    if not timestamp:
                        timestamp = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
                    verified_with_time.append((timestamp, value))

            if verified_with_time:
                latest_value = sorted(verified_with_time, reverse=True)[0][1]
                verified_counter[latest_value] += 1

        stats = {
            'total': total,
            'checked_in': verified_counter[0],
            'in_checkin_room': verified_counter[1],
            'in_graduation_room': verified_counter[2],
        }
        return Response(stats, status=200)

class PersonList(APIView):
    def get(self, request):
        persons = Person.objects.all()
        serializer = PersonSerializer(persons, many=True)
        # ตรวจสอบข้อมูลก่อนส่ง response
        safe_data = []
        for item in serializer.data:
            safe_item = {
                k: v for k, v in item.items() 
                if isinstance(v, (str, int, float, bool, type(None)))
            }
            safe_data.append(safe_item)
        return Response(safe_data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = PersonSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()  # เก็บ instance ที่สร้าง
            Log.objects.create(
                action='Add',
                model='Person',
                details=f"เพิ่มข้อมูล: {instance.name}",
                record_id=instance.id
            )
            if settings.USE_CHANNEL:
                broadcast_to_crud01({
                    'action': 'add',
                    'id': instance.id,
                    'fields': {
                        'name': instance.name,
                        'nisit': instance.nisit,
                        'degree': instance.degree,
                        'seat': instance.seat,
                        'verified1': instance.verified1,
                        'verified2': instance.verified2,
                        'verified3': instance.verified3,
                        'verified': instance.verified,
                        'read_flag': instance.read_flag,
                        'read_light': instance.read_light,
                        'rfid': instance.rfid,
                    }
                })
                broadcast_stats_update()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            person = Person.objects.get(pk=pk)
            original_data = {
                'name': person.name,
                'nisit': person.nisit,
                'degree': person.degree,
                'seat': person.seat,
                'verified1': person.verified1,
                'verified2': person.verified2,
                'verified3': person.verified3,
                'verified_updated_at1': person.verified_updated_at1,
                'verified_updated_at2': person.verified_updated_at2,
                'verified_updated_at3': person.verified_updated_at3,
                'read_flag': person.read_flag,
                'read_light': person.read_light,
                'rfid': person.rfid,
            }
            
            data = request.data.copy()

            now = timezone.localtime(timezone.now())  # เวลาปัจจุบันตาม TIME_ZONE ใน settings.py

            for i in range(1, 4):
                verified_key = f"verified{i}"
                updated_key = f"verified_updated_at{i}"
                if verified_key in data:
                    new_verified_val = data.get(verified_key)
                    old_verified_val = getattr(person, verified_key)
                    if str(new_verified_val) != str(old_verified_val):
                        # ✅ ตรงนี้ต้องใช้ localtime เพื่อให้เวลาตรงกับ Asia/Bangkok
                        data[updated_key] = timezone.localtime(timezone.now()).isoformat()

            serializer = PersonSerializer(person, data=data)
            if serializer.is_valid():
                serializer.save()
                person.refresh_from_db()
                
                changes = []
                fields_to_check = [
                    'name', 'degree', 'seat', 
                    'verified1', 'verified2', 'verified3',
                    'verified_updated_at1', 'verified_updated_at2', 'verified_updated_at3',
                    'read_flag_in', 'read_flag_out', 'read_light_in', 'read_light_out', 'rfid'
                ]
                for field in fields_to_check:
                    old_val = original_data[field]
                    new_val = getattr(person, field)
                    if isinstance(old_val, (type(None),)) and new_val is not None:
                        changed = True
                    elif isinstance(old_val, (type(None),)) and new_val is None:
                        changed = False
                    elif hasattr(old_val, 'isoformat') and hasattr(new_val, 'isoformat'):
                        changed = old_val.isoformat() != new_val.isoformat()
                    else:
                        changed = old_val != new_val
                    
                    if changed:
                        changes.append(f"{field}::{old_val}::{new_val}")

                if changes:
                    log_message = " | ".join(changes)
                    Log.objects.create(
                        action='Edit',
                        model='Person',
                        details=log_message, 
                        record_id=person.id
                    )
                if settings.USE_CHANNEL:
                    broadcast_to_crud01({
                        'action': 'update',
                        'id': person.id,
                        'fields': {
                            'name': person.name,
                            'nisit': person.nisit,
                            'degree': person.degree,
                            'seat': person.seat,
                            'verified1': person.verified1,
                            'verified2': person.verified2,
                            'verified3': person.verified3,
                            'verified_updated_at1': person.verified_updated_at1,
                            'verified_updated_at2': person.verified_updated_at2,
                            'verified_updated_at3': person.verified_updated_at3,
                            'read_flag': person.read_flag,
                            'read_light': person.read_light,
                            'rfid': person.rfid,
                        }
                    })
                    broadcast_stats_update()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Person.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


    def delete(self, request):
        ids = request.data.get('ids', [])
        
        if not ids:
            return Response({'error': 'No IDs provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                persons = Person.objects.filter(id__in=ids)
                # เก็บ ID ก่อนลบ
                ids_str = ','.join(str(p.id) for p in persons)
                Log.objects.create(
                    action='Delete',
                    model='Person',
                    details=f"[ID: {ids_str}] ลบข้อมูลแบบกลุ่ม",
                    record_id=None
                )
                persons.delete()
                
                # ส่ง WebSocket สำหรับแต่ละ ID
                if settings.USE_CHANNEL:
                    for id in ids_str:
                        broadcast_to_crud01({
                            'action': 'delete',
                            'id': id,
                        })
                    
                    broadcast_stats_update()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PersonDetail(APIView):
    def get(self, request, pk):
        try:
            person = Person.objects.get(pk=pk)
        except Person.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PersonSerializer(person)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            person = Person.objects.get(pk=pk)
            person_id = person.id  # เก็บ ID ก่อนลบ
            
            Log.objects.create(
                action='Delete',
                model='Person',
                details=f"ลบข้อมูลของ {person.name}",
                record_id=person.id
            )
            
            person.delete()
            
            # ส่ง WebSocket action delete
            if settings.USE_CHANNEL:
                broadcast_to_crud01({
                    'action': 'delete',
                    'id': person_id,
                })
                broadcast_stats_update()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Person.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, pk):
        try:
            person = Person.objects.get(pk=pk)
            original_data = {
                'name': person.name,
                'nisit': person.nisit,
                'degree': person.degree,
                'seat': person.seat,
                'verified1': person.verified1,
                'verified2': person.verified2,
                'verified3': person.verified3,
                'verified_updated_at1': person.verified_updated_at1,
                'verified_updated_at2': person.verified_updated_at2,
                'verified_updated_at3': person.verified_updated_at3,
                'read_flag': person.read_flag,
                'read_light_out': person.read_light,
                'rfid': person.rfid,
            }
            serializer = PersonSerializer(person, data=request.data)
            if serializer.is_valid():
                serializer.save()
                person.refresh_from_db()
                changes = []
                for field in ['name', 'degree', 'seat', 'verified1', 'verified2', 'verified3', 'read_flag_in', 'read_flag_out', 'read_light_in', 'read_light_in', 'rfid']:
                    old_val = original_data[field]
                    new_val = getattr(person, field)
                    if old_val != new_val:
                        changes.append(f"{field}::{old_val}::{new_val}")
                if changes:
                    log_message = " | ".join(changes)
                    Log.objects.create(
                        action='Edit',
                        model='Person',
                        details=log_message, 
                        record_id=person.id
                    )
                if settings.USE_CHANNEL:
                    broadcast_to_crud01({
                        'action': 'update',
                        'id': person.id,
                        'fields': {
                            'name': person.name,
                            'nisit': person.nisit,
                            'degree': person.degree,
                            'seat': person.seat,
                            'verified1': person.verified1,
                            'verified2': person.verified2,
                            'verified3': person.verified3,
                            'verified_updated_at1': person.verified_updated_at1,
                            'verified_updated_at2': person.verified_updated_at2,
                            'verified_updated_at3': person.verified_updated_at3,
                            'read_flag': person.read_flag,
                            'read_light': person.read_light,
                            'rfid': person.rfid,
                        }
                    })
                    broadcast_stats_update()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Person.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    
class RFIDSimulator(APIView):
    parser_classes = [JSONParser]

    def post(self, request):
        try:
            simulated_tags = request.data.get('tags', [])
            scanner_id = request.data.get('scanner_id')

            try:
                scanner_id = int(scanner_id)
            except (TypeError, ValueError):
                scanner_id = None

            if not simulated_tags or scanner_id not in [1, 2, 3]:
                return Response(
                    {'error': 'Missing tags or invalid scanner_id (1-3)'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            results = []

            for tag in simulated_tags:
                epc = tag.get('epc')
                if not epc:
                    continue

                try:
                    person = Person.objects.get(rfid=epc)

                    verified_field = f"verified{scanner_id}"
                    time_field = f"verified_updated_at{scanner_id}"
                    current_status = getattr(person, verified_field, 0)

                    if current_status == 1:
                        results.append({
                            'epc': epc,
                            'name': person.name,
                            'message': 'แท็กนี้ถูกสแกนแล้ว',
                        })
                    else:
                        setattr(person, verified_field, 1)
                        setattr(person, time_field, timezone.now())
                        person.save()

                        if settings.USE_CHANNEL:
                            broadcast_to_crud01({
                                'action': 'update',
                                'id': person.id,
                                'fields': {
                                    'name': person.name,
                                    'nisit': person.nisit,
                                    'degree': person.degree,
                                    'seat': person.seat,
                                    'verified1': person.verified1,
                                    'verified2': person.verified2,
                                    'verified3': person.verified3,
                                    'verified_updated_at1': person.verified_updated_at1,
                                    'verified_updated_at2': person.verified_updated_at2,
                                    'verified_updated_at3': person.verified_updated_at3,
                                    'rfid': person.rfid,
                                    'read_flag': person.read_flag,
                                    'read_light': person.read_light,
                                }
                            })
                            broadcast_stats_update()

                        results.append({
                            'epc': epc,
                            'name': person.name,
                            'message': 'อัปเดตสถานะสำเร็จ',
                        })

                except Person.DoesNotExist:
                    # ถ้าไม่เจอ rfid นี้ในระบบ ให้ลองหา Person ที่ rfid ว่าง (null หรือ empty string)
                    person_with_empty_rfid = Person.objects.filter(rfid__isnull=True).first()
                    if not person_with_empty_rfid:
                        # ลองเช็คกรณีที่ rfid เป็น empty string ด้วย
                        person_with_empty_rfid = Person.objects.filter(rfid='').first()

                    if not person_with_empty_rfid:
                        results.append({
                            'epc': epc,
                            'name': None,
                            'message': 'ไม่พบข้อมูลแท็กนี้ในระบบ'
                        })
                    else:
                        # อัปเดต rfid ของคนนี้เป็น epc ที่ส่งมา
                        person_with_empty_rfid.rfid = epc

                        verified_field = f"verified{scanner_id}"
                        time_field = f"verified_updated_at{scanner_id}"

                        setattr(person_with_empty_rfid, verified_field, 1)
                        setattr(person_with_empty_rfid, time_field, timezone.now())

                        person_with_empty_rfid.save()

                        if settings.USE_CHANNEL:
                            broadcast_to_crud01({
                                'action': 'update',
                                'id': person_with_empty_rfid.id,
                                'fields': {
                                    'name': person_with_empty_rfid.name,
                                    'nisit': person_with_empty_rfid.nisit,
                                    'degree': person_with_empty_rfid.degree,
                                    'seat': person_with_empty_rfid.seat,
                                    'verified1': person_with_empty_rfid.verified1,
                                    'verified2': person_with_empty_rfid.verified2,
                                    'verified3': person_with_empty_rfid.verified3,
                                    'verified_updated_at1': person_with_empty_rfid.verified_updated_at1,
                                    'verified_updated_at2': person_with_empty_rfid.verified_updated_at2,
                                    'verified_updated_at3': person_with_empty_rfid.verified_updated_at3,
                                    'rfid': person_with_empty_rfid.rfid,
                                    'read_flag': person_with_empty_rfid.read_flag,
                                    'read_light': person_with_empty_rfid.read_light,
                                }
                            })
                            broadcast_stats_update()

                        results.append({
                            'epc': epc,
                            'name': person_with_empty_rfid.name,
                            'message': 'เพิ่มรหัส RFID สำเร็จและอัปเดตสถานะแล้ว',
                        })

            return Response({'results': results}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LogList(generics.ListAPIView):
    serializer_class = LogSerializer
    
    def get_queryset(self):
        # กรองข้อมูลที่อาจมี timestamp เป็น null
        return Log.objects.exclude(timestamp__isnull=True).order_by('-timestamp')

class LogCreateView(APIView):
    def post(self, request):
        serializer = LogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)