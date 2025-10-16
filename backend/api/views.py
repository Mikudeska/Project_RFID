from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.db import transaction, connection
from django.http import JsonResponse, StreamingHttpResponse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from tablib import Dataset
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView, View
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
from .resources import PersonResource
from .consumers import broadcast_to_crud01, broadcast_stats_update, broadcast_ws
from .models import Person, Log, Profile
from .serializers import PersonSerializer, LogSerializer
from datetime import datetime, timedelta
from urllib.parse import quote
import json
import urllib.parse
import os, io
import logging

logger = logging.getLogger(__name__)

# ✅ แจก CSRF token (frontend ต้องเรียกก่อน)
@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({"detail": "CSRF cookie set"})


# ✅ Login
def login_view(request):
    data = json.loads(request.body)
    username = data.get("username")
    password = data.get("password")
    expires_in = int(data.get("expires_in", 24 * 60 * 60))  # 1 วันเป็นค่า default หากไม่ได้ส่งมา

    user = authenticate(request, username=username, password=password)
    if user is not None:
        # สร้าง refresh token และ access token
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        # กำหนดเวลาหมดอายุของ access token ตาม expires_in ที่ส่งมาจาก frontend
        access_token.set_exp(lifetime=timedelta(seconds=expires_in))

        # Login ระบบ session ของ Django (จะสร้าง sessionid ให้)
        login(request, user)

        # ส่ง token กลับไปยัง frontend
        return JsonResponse({
            "access": str(access_token),
            "refresh": str(refresh),
            "detail": "Login success"
        })

    else:
        return JsonResponse({"detail": "Invalid credentials"}, status=400)
    
@login_required
@require_POST
def change_password_view(request):
    try:
        data = json.loads(request.body)
        new_password = data.get('new_password')

        if not new_password:
            return JsonResponse({'error': 'New password not provided'}, status=400)

        user = request.user
        user.set_password(new_password) # เข้ารหัสและตั้งรหัสผ่านใหม่
        user.save()

        # อัปเดต session ของผู้ใช้เพื่อไม่ให้หลุดออกจากระบบ
        update_session_auth_hash(request, user)

        return JsonResponse({'message': 'Password updated successfully'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ✅ Logout
@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({"detail": "Logged out"})


# ✅ ดึง user ปัจจุบัน
@login_required
def profile_view(request):
    user = request.user # <-- ย้าย user มาไว้ข้างบนเพื่อใช้ร่วมกัน

    if request.method == 'GET':
        if user.groups.filter(name='Dev').exists():
            status = 'Dev'
        else:
            status = 'Staff'

        return JsonResponse({
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "nickname": user.profile.nickname if hasattr(user, 'profile') else '',
            "status": status
        })

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)

            user.first_name = data.get('first_name', user.first_name)
            user.last_name = data.get('last_name', user.last_name)
            user.save()
            profile, created = Profile.objects.get_or_create(user=user)
            if created:
                print(f"Created a new profile for user: {user.username}")

            profile.nickname = data.get('nickname', profile.nickname)
            profile.save()
                
            if user.groups.filter(name='Dev').exists():
                status = 'Dev'
            else:
                status = 'Staff'

            return JsonResponse({
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "nickname": profile.nickname, # ใช้ profile.nickname ที่เราเพิ่งบันทึก
                "status": status
            }, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

def file_iterator(buffer, chunk_size=8192):
    buffer.seek(0)
    while True:
        chunk = buffer.read(chunk_size)
        if not chunk:
            break
        yield chunk

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
                    record_id=None,
                    user=request.user,
                    user_nickname=request.user.profile.nickname if hasattr(request.user, 'profile') else ''
                )
                broadcast_ws("reset")
                broadcast_stats_update()
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
                user=request.user,
                user_nickname=request.user.profile.nickname if hasattr(request.user, 'profile') else ''
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
                    record_id=None,
                    user=request.user,
                    user_nickname=request.user.profile.nickname if hasattr(request.user, 'profile') else ''
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
                user=request.user,
                user_nickname=request.user.profile.nickname if hasattr(request.user, 'profile') else ''
            )
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

def file_iterator(file, chunk_size=8192):
    while True:
        chunk = file.read(chunk_size)
        if not chunk:
            break
        yield chunk

class ExportPDF(View):
    def get(self, request):
        try:
            # ตั้งค่า Font ไทย
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            FONT_PATH = os.path.join(BASE_DIR, 'fonts', 'THSarabunNew.ttf')
            pdfmetrics.registerFont(TTFont('THSarabun', FONT_PATH))
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            
            # ฟังก์ชันวาดเส้นตาราง
            def draw_table_grid(canvas, x_list, y_list):
                canvas.setStrokeColorRGB(0, 0, 0)  # สีดำ
                canvas.setLineWidth(1)  # ความหนาเส้น
                
                # วาดเส้นแนวตั้ง
                for x in x_list:
                    canvas.line(x, min(y_list) - 20, x, max(y_list))
                
                # วาดเส้นแนวนอน
                for y in y_list:
                    canvas.line(min(x_list), y, max(x_list), y)
                
                # วาดเส้นล่างสุดเพิ่มเติม
                canvas.line(min(x_list), min(y_list) - 20, max(x_list), min(y_list) - 20)
            
            # ตั้งค่าตำแหน่งคอลัมน์และความกว้าง
            col_positions = [50, 75, 260, 440, 540]
            col_widths = [25, 185, 180, 100, 0]  # ความกว้างของแต่ละคอลัมน์
            
            # คำนวณตำแหน่งกึ่งกลางของแต่ละคอลัมน์
            header_positions = []
            for i in range(len(col_positions) - 1):
                center_x = col_positions[i] + (col_widths[i] / 2)
                header_positions.append(center_x)
            
            # ข้อมูลส่วนหัว
            p.setFont('THSarabun', 25)
            date_str = datetime.now().strftime("%d/%m/%Y")
            p.drawRightString(width - 40, height - 40, f"วันที่ {date_str}")
            p.setFont('THSarabun', 15)
            time_str = datetime.now().strftime("%H:%M")
            p.drawRightString(width - 40, height - 60, f"เวลา {time_str}")

            p.setFont('THSarabun', 20)
            p.drawCentredString(width / 2, 780, "รายชื่อบัณฑิต")

            # เขียนหัวตาราง - จัดกึ่งกลางแต่ละคอลัมน์
            p.setFont('THSarabun', 14)
            
            # วาดหัวตารางจัดกึ่งกลาง
            headers = ["ลำดับ", "ชื่อ-นามสกุล", "รหัสนักศึกษา", "สถานะรายงานตัว"]
            for i, header in enumerate(headers):
                p.drawCentredString(header_positions[i], 735, header)

            # เก็บตำแหน่งแถวสำหรับวาดเส้นตาราง
            rows_y = [750]  # เริ่มจากหัวตาราง
            
            # ดึงข้อมูล
            persons = Person.objects.all().order_by('seat')
            y_position = 730  # ตำแหน่งเริ่มต้นของข้อมูล
            
            def get_verified_status(person):
                """
                หาค่า verified ล่าสุดโดยอิงจาก timestamp ที่ใหม่ที่สุด
                """
                latest_status = None
                latest_time = None
                has_any_timestamp = False

                # วนลูปเพื่อหา timestamp ที่ใหม่ที่สุด
                for i in range(1, 4):
                    updated_time = getattr(person, f'verified_updated_at{i}')
                    if updated_time:
                        has_any_timestamp = True
                        if latest_time is None or updated_time > latest_time:
                            latest_time = updated_time
                            latest_status = getattr(person, f'verified{i}')

                # ถ้าไม่มี timestamp เลย ให้ยึดตามค่า verified ที่ไม่ใช่ 0 ตัวแรกที่เจอ
                if not has_any_timestamp:
                    for i in range(1, 4):
                        status_value = getattr(person, f'verified{i}')
                        if status_value in [1, 2]:
                            latest_status = status_value
                            break

                # แปลงค่าตัวเลขเป็นข้อความ
                if latest_status == 2:
                    return "อยู่ในห้องพิธี"
                elif latest_status == 1:
                    return "รายงานตัวแล้ว"
                else: # รวมถึงกรณี latest_status เป็น 0 หรือ None
                    return "ยังไม่รายงานตัว"
                
            # เขียนข้อมูล - จัดกึ่งกลางทั้งแนวตั้งและแนวนอน
            for i, person in enumerate(persons, start=1):
                # คำนวณตำแหน่งกึ่งกลางแนวตั้งของแถว
                vertical_center = y_position - 15  # กึ่งกลางของความสูง 20 points
                
                # วาดข้อมูลแต่ละคอลัมน์ โดยจัดกึ่งกลางทั้งแนวนอนและแนวตั้ง
                p.drawCentredString(header_positions[0], vertical_center, f"{i:04d}")
                p.drawCentredString(header_positions[1], vertical_center, person.name)
                p.drawCentredString(header_positions[2], vertical_center, person.nisit)
                p.drawCentredString(header_positions[3], vertical_center, get_verified_status(person))
                
                # เก็บตำแหน่ง y ปัจจุบัน
                rows_y.append(y_position)
                
                y_position -= 20  # เลื่อนบรรทัด

                # ตรวจสอบว่าขึ้นหน้าใหม่หรือไม่
                if y_position < 50:
                    # วาดเส้นตารางก่อนขึ้นหน้าใหม่
                    draw_table_grid(p, col_positions, rows_y)
                    p.showPage()
                    
                    # รีเซ็ตค่าสำหรับหน้าใหม่
                    y_position = 800
                    rows_y = []
                    
                    # วาดหัวตารางในหน้าใหม่
                    p.setFont('THSarabun', 20)
                    p.drawCentredString(width / 2, 780, "รายชื่อบัณฑิต (ต่อ)")
                    
                    # วาดหัวตารางจัดกึ่งกลางในหน้าใหม่
                    p.setFont('THSarabun', 14)
                    for i, header in enumerate(headers):
                        p.drawCentredString(header_positions[i], 735, header)
                    
                    rows_y = [750]
                    y_position = 730

            # วาดเส้นตารางสำหรับหน้าสุดท้าย (หากมีข้อมูล)
            if len(rows_y) > 0:
                draw_table_grid(p, col_positions, rows_y)

            p.save()
            buffer.seek(0)

            # สร้าง response สำหรับดาวน์โหลดไฟล์
            date_str = datetime.now().strftime('%Y%m%d')
            filename = f"รายชื่อ_{date_str}.pdf"
            quoted_filename = quote(filename)

            response = StreamingHttpResponse(
                file_iterator(buffer), 
                content_type='application/pdf'
            )
            response['Cache-Control'] = 'no-store'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            response['Content-Disposition'] = (
                f'attachment; filename="{quoted_filename}"; '
                f'filename*=UTF-8\'\'{quoted_filename}'
            )
            response["Access-Control-Expose-Headers"] = "Content-Disposition"
            response['Content-Security-Policy'] = "upgrade-insecure-requests"
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
            # บันทึก Log
            Log.objects.create(
                action='Export',
                model='Person',
                details="โหลดไฟล์เป็น PDF",
                record_id=None,
                user=request.user,
                user_nickname=request.user.profile.nickname if hasattr(request.user, 'profile') else ''
            )
            return response

        except Exception as e:
            print('PDF Export Error:', str(e))
            return JsonResponse({'error': str(e)}, status=500)

class ExportPDFResult(View):
    def get(self, request):
        try:
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            FONT_PATH = os.path.join(BASE_DIR, 'fonts', 'THSarabunNew.ttf')
            pdfmetrics.registerFont(TTFont('THSarabun', FONT_PATH))

            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4

            # ---------------- ฟังก์ชันวาดเส้นตาราง ----------------
            def draw_table_grid(canvas, x_list, y_list):
                canvas.setStrokeColorRGB(0, 0, 0)
                canvas.setLineWidth(1)
                for x in x_list:  # เส้นตั้ง
                    canvas.line(x, min(y_list) - 20, x, max(y_list))
                for y in y_list:  # เส้นนอน
                    canvas.line(min(x_list), y, max(x_list), y)
                canvas.line(min(x_list), min(y_list) - 20, max(x_list), min(y_list) - 20)

            # ---------------- Helper ----------------
            def degree_group(name):
                if 'ดุษฎีบัณฑิต' in name:
                    return 'ป.เอก'
                elif 'มหาบัณฑิต' in name:
                    return 'ป.โท'
                return 'ป.ตรี'

            def is_verified(person):
                return any(getattr(person, f'verified{i}') in [1, 2] for i in range(1, 4))

            persons = Person.objects.all()
            degree_summary = {'ป.ตรี': {'total': 0, 'present': 0},
                              'ป.โท': {'total': 0, 'present': 0},
                              'ป.เอก': {'total': 0, 'present': 0}}
            branch_summary = {}

            for person in persons:
                dg = degree_group(person.degree)
                degree_summary[dg]['total'] += 1
                if is_verified(person):
                    degree_summary[dg]['present'] += 1

                branch = person.degree if person.degree else 'ไม่ระบุ'
                if branch not in branch_summary:
                    branch_summary[branch] = {'total': 0, 'present': 0}
                branch_summary[branch]['total'] += 1
                if is_verified(person):
                    branch_summary[branch]['present'] += 1

            # ---------------- HEADER ----------------
            p.setFont('THSarabun', 25)
            date_str = datetime.now().strftime("%d/%m/%Y")
            p.drawRightString(width - 40, height - 40, f"วันที่ {date_str}")
            p.setFont('THSarabun', 15)
            time_str = datetime.now().strftime("%H:%M")
            p.drawRightString(width - 40, height - 60, f"เวลา {time_str}")

            # ---------------- 1. ใบสรุปผล ----------------
            p.setFont('THSarabun', 25)
            p.drawCentredString(width / 2, height - 80, "ใบสรุปผล")

            col_positions = [60, 200, 320, 440, 530]
            col_widths = [140, 120, 120, 90]
            header_positions = [col_positions[i] + (col_widths[i] / 2) for i in range(len(col_widths))]

            headers = ["ระดับ", "ทั้งหมด", "มา", "ขาด"]
            p.setFont('THSarabun', 20)

            # --- ควบคุมความสูงของแต่ละแถว ---
            row_height = 30
            rows = ['header', 'ป.ตรี', 'ป.โท', 'ป.เอก', 'รวมทั้งหมด']

            # คำนวณตำแหน่ง y ของเส้นตาราง (บน → ล่าง)
            y_start = height - 110
            rows_y = [y_start - (i * row_height) for i in range(len(rows) + 1)]

            # --- วาดหัวตาราง ---
            for i, h in enumerate(headers):
                p.drawCentredString(header_positions[i], rows_y[0] - row_height/2 - 5, h)

            total_all = present_all = 0

            # --- วาดแถวข้อมูล ---
            for idx, degree in enumerate(['ป.ตรี', 'ป.โท', 'ป.เอก']):
                total = degree_summary[degree]['total']
                present = degree_summary[degree]['present']
                absent = total - present
                vertical_center = rows_y[idx+1] - row_height/2 - 5

                p.drawCentredString(header_positions[0], vertical_center, degree)
                p.drawCentredString(header_positions[1], vertical_center, str(total))
                p.drawCentredString(header_positions[2], vertical_center, str(present))
                p.drawCentredString(header_positions[3], vertical_center, str(absent))

                total_all += total
                present_all += present

            # --- รวมทั้งหมด ---
            absent_all = total_all - present_all
            vertical_center = rows_y[4] - row_height/2 - 5
            p.drawCentredString(header_positions[0], vertical_center, "รวมทั้งหมด")
            p.drawCentredString(header_positions[1], vertical_center, str(total_all))
            p.drawCentredString(header_positions[2], vertical_center, str(present_all))
            p.drawCentredString(header_positions[3], vertical_center, str(absent_all))

            # --- วาดเส้นตาราง ---
            draw_table_grid(p, col_positions, rows_y)


            # ---------------- 2. ตารางแต่ละสาขา ----------------
            p.showPage()
            p.setFont('THSarabun', 25)
            p.drawCentredString(width / 2, height - 80, "ตารางพระราชทานปริญญาบัตร 2568")

            col_positions = [40, 240, 320, 400, 480, 560]
            col_widths = [200, 80, 80, 80, 80]
            header_positions = [col_positions[i] + (col_widths[i] / 2) for i in range(len(col_widths))]
            headers = ["ชื่อหลักสูตร", "ทั้งหมด", "มา", "ขาด", "ร้อยละ"]

            def draw_branch_header():
                p.setFont('THSarabun', 14)
                for i, h in enumerate(headers):
                    p.drawCentredString(header_positions[i], height - 130, h)

            draw_branch_header()
            y_position = height - 140
            rows_y = [height - 110]

            for branch, vals in sorted(branch_summary.items()):
                total = vals['total']
                present = vals['present']
                absent = total - present
                percent = (present / total * 100) if total > 0 else 0

                vertical_center = y_position - 15
                p.drawCentredString(header_positions[0], vertical_center, branch)
                p.drawCentredString(header_positions[1], vertical_center, str(total))
                p.drawCentredString(header_positions[2], vertical_center, str(present))
                p.drawCentredString(header_positions[3], vertical_center, str(absent))
                p.drawCentredString(header_positions[4], vertical_center, f"{int(percent)}%")

                rows_y.append(y_position)
                y_position -= 20

                if y_position < 50:
                    draw_table_grid(p, col_positions, rows_y)
                    p.showPage()
                    draw_branch_header()
                    rows_y = [height - 110]
                    y_position = height - 140

            if rows_y:
                draw_table_grid(p, col_positions, rows_y)

            # ---------------- 3. รายชื่อที่ยังไม่รายงานตัว ----------------
            p.showPage()
            p.setFont('THSarabun', 25)
            p.drawCentredString(width / 2, height - 80, "รายชื่อที่ยังไม่รายงานตัว")

            col_positions = [100, 175, 325, 500]
            col_widths = [75, 150, 175]
            header_positions = [col_positions[i] + (col_widths[i] / 2) for i in range(len(col_widths))]
            headers = ["เลขที่บัณฑิต", "ชื่อ - สกุล", "ชื่อหลักสูตร"]

            def draw_missing_header():
                p.setFont('THSarabun', 14)
                for i, h in enumerate(headers):
                    p.drawCentredString(header_positions[i], height - 130, h)

            draw_missing_header()
            y_position = height - 140
            rows_y = [height - 110]

            missing_persons = Person.objects.filter(
                verified1=0, verified2=0, verified3=0
            ).order_by('id')

            for person in missing_persons:
                vertical_center = y_position - 15
                p.drawCentredString(header_positions[0], vertical_center, str(person.id))
                p.drawCentredString(header_positions[1], vertical_center, person.name)
                p.drawCentredString(header_positions[2], vertical_center, person.degree or "-")

                rows_y.append(y_position)
                y_position -= 20

                if y_position < 50:
                    draw_table_grid(p, col_positions, rows_y)
                    p.showPage()
                    draw_missing_header()
                    rows_y = [height - 110]
                    y_position = height - 140

            if rows_y:
                draw_table_grid(p, col_positions, rows_y)

            # ---------------- SAVE ----------------
            p.save()
            buffer.seek(0)

            date_str = datetime.now().strftime('%Y%m%d')
            filename = f"รายชื่อสรุป_{date_str}.pdf"
            quoted_filename = quote(filename)

            response = StreamingHttpResponse(file_iterator(buffer), content_type='application/pdf')
            response['Content-Disposition'] = (
                f'attachment; filename="{quoted_filename}"; '
                f"filename*=UTF-8''{quoted_filename}"
            )
            response['Cache-Control'] = 'no-store'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

            Log.objects.create(
                action='Export',
                model='Person',
                details="โหลดไฟล์สรุป PDF",
                record_id=None,
                user=request.user,
                user_nickname=getattr(getattr(request.user, "profile", None), "nickname", "")
            )
            return response

        except Exception as e:
            import traceback
            print("PDF Export Error:", str(e))
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
                details=f"โหลดไฟล์เป็น {format_type}",
                user=request.user,
                user_nickname=request.user.profile.nickname if hasattr(request.user, 'profile') else ''
            )
            return response

        except Exception as e:
            logger.error(f"Reset failed: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Internal Server Error'}, 
                status=500
            )

class ImportData(APIView):
    def post(self, request):
        file = request.FILES['file']

        # ตรวจสอบขนาดไฟล์ (ไม่เกิน 15MB)
        max_size = 15 * 1024 * 1024  # 15 MB
        if file.size > max_size:
            return Response(
                {'error': 'ไฟล์มีขนาดเกิน 15MB'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        dataset = Dataset()
        resource = PersonResource()

        try:
            # อ่านไฟล์
            if file.name.endswith('.xlsx'):
                dataset.load(file.read(), format='xlsx')
            elif file.name.endswith('.csv'):
                dataset.load(file.read(), format='csv', encoding='utf-8-sig')

            # ตรวจสอบข้อมูล
            if len(dataset) == 0:
                raise ValueError("ไฟล์ที่อัปโหลดว่างเปล่า")

            # นำเข้าข้อมูล
            result = resource.import_data(dataset, dry_run=False)
            
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
                record_id=None,
                user=request.user,
                user_nickname=request.user.profile.nickname if hasattr(request.user, 'profile') else ''
            )
            broadcast_ws("upload")
            broadcast_stats_update()
            return Response(
                {'success': f'นำเข้าข้อมูลสำเร็จ {imported_count} รายการ'}, 
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            Log.objects.create(
                action='Import',
                model='Person',
                details=f"นำเข้าข้อมูลล้มเหลว: {str(e)}",
                record_id=None,
                user=request.user,
                user_nickname=request.user.profile.nickname if hasattr(request.user, 'profile') else ''
            )
            logger.error(f"Import failed: {str(e)}", exc_info=True)
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
                value = getattr(person, f'verified{i}', 0)
                timestamp = getattr(person, f'verified_updated_at{i}', None)

                # ถ้า timestamp ไม่มี ให้ใช้วันที่เก่ามากๆ แทน เพื่อให้ไม่ถูกเลือกก่อน timestamp อื่น
                if not timestamp:
                    timestamp = datetime.min.replace(tzinfo=timezone.utc)
                verified_with_time.append((timestamp, value))

            if verified_with_time:
                # หาค่าล่าสุดจาก timestamp ที่ใหม่ที่สุด
                latest_value = sorted(verified_with_time, key=lambda x: x[0], reverse=True)[0][1]
                verified_counter[latest_value] += 1
    
        stats = {
            'total': total,
            'not_checked_in': verified_counter[0],      # ยังไม่รายงานตัว (สถานะ 0)
            'in_checkin_room': verified_counter[1],     # รายงานตัวแล้ว (สถานะ 1)
            'in_graduation_room': verified_counter[2],  # อยู่ในห้องพิธี (สถานะ 2)
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
                record_id=instance.id,
                user=request.user,
                user_nickname=request.user.profile.nickname if hasattr(request.user, 'profile') else ''
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
                        'rfid': instance.rfid,
                    }
                })
                broadcast_stats_update()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        ids = request.data.get('ids', [])
        verified = request.data.get('verified')
        verified_field = request.data.get('verified_field')

        if not ids or not verified_field:
            return Response({'error': 'ข้อมูลไม่ครบ'}, status=400)

        now = timezone.now()
        new_val = int(verified)

        updated_field = verified_field.replace('verified', 'verified_updated_at')

        # --- อัปเดตครั้งเดียว ---
        updated_count = Person.objects.filter(id__in=ids).exclude(**{verified_field: new_val}).update(
            **{
                verified_field: new_val,
                updated_field: now
            }
        )

        # --- ส่ง broadcast ทีเดียว ---
        if updated_count > 0 and settings.USE_CHANNEL:
            broadcast_to_crud01({
                'action': 'bulk_update',
                'ids': ids,
                'fields': {
                    verified_field: new_val,
                    updated_field: now.isoformat(),
                }
            })

            Log.objects.create(
                action='Edit',
                model='Person',
                details=f"[ID: {','.join(map(str, ids))}] อัปเดตเป็น {new_val}",
                user=request.user,
                user_nickname=getattr(getattr(request.user, 'profile', None), 'nickname', '')
            )

            broadcast_stats_update()

        return Response({
            'updated_count': updated_count,
            'updated_ids': ids,
        }, status=200)

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
                    record_id=None,
                    user=request.user,
                    user_nickname=request.user.profile.nickname if hasattr(request.user, 'profile') else ''
                )
                persons.delete()
                
                # ส่ง WebSocket สำหรับแต่ละ ID
                if settings.USE_CHANNEL:
                    for id in ids:
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
                record_id=person.id,
                user=request.user,
                user_nickname=request.user.profile.nickname if hasattr(request.user, 'profile') else ''
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
            original_data = person_to_dict(person)
            serializer = PersonSerializer(person, data=request.data)
            if serializer.is_valid():
                serializer.save()
                person.refresh_from_db()
                changes = []
                for field in ['name', 'degree', 'seat', 'verified1', 'verified2', 'verified3', 'rfid']:
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
                        record_id=person.id,
                        user=request.user,
                        user_nickname=request.user.profile.nickname if hasattr(request.user, 'profile') else ''
                    )
                if settings.USE_CHANNEL:
                    fields = person_to_dict(person)
                    fields = convert_datetime_fields(fields, [
                        'verified_updated_at1', 'verified_updated_at2', 'verified_updated_at3'
                    ])
                    broadcast_to_crud01({
                        'action': 'update',
                        'id': person.id,
                        'fields': fields,
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
            scanner_type = request.data.get('scanner_type')  # 'in' or 'out'
            scanner_id = request.data.get('scanner_id')       # 1, 2, or 3

            try:
                scanner_id = int(scanner_id)
            except (TypeError, ValueError):
                scanner_id = None

            if not simulated_tags or scanner_type not in ['in', 'out'] or scanner_id not in [1, 2, 3]:
                return Response(
                    {'error': 'Missing tags or invalid scanner_type (in/out) or scanner_id (1-3)'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            results = []

            for tag in simulated_tags:
                epc = tag.get('epc')
                if not epc:
                    continue
                try:
                    # ✅ Step 1: ดึงข้อมูล person เพื่อตรวจสอบสถานะปัจจุบันก่อน
                    person = Person.objects.get(rfid=epc)

                    verified_field = f"verified{scanner_id}"
                    time_field = f"verified_updated_at{scanner_id}"
                    current_status = getattr(person, verified_field, 0)
                    verified_value = 2 if scanner_type == 'out' else 1

                    if current_status == verified_value:
                        results.append(f"rfid: {epc} name: {person.name} status: แท็กนี้ถูกแสกนแล้ว")
                    else:
                        now = timezone.now()
                        
                        # ✅ Step 2: ใช้ .update() เพื่อสั่งให้ฐานข้อมูลอัปเดตโดยตรง
                        #    วิธีนี้แน่นอนและมีประสิทธิภาพกว่าการใช้ .save()
                        Person.objects.filter(pk=person.pk).update(**{
                            verified_field: verified_value,
                            time_field: now
                        })

                        if settings.USE_CHANNEL:
                            # ✅ Step 3: อัปเดต object ในหน่วยความจำตาม เพื่อส่งข้อมูลที่ถูกต้องผ่าน WebSocket
                            setattr(person, verified_field, verified_value)
                            setattr(person, time_field, now)
                            
                            broadcast_to_crud01({
                                'action': 'update',
                                'id': person.id,
                                'fields': person_to_dict(person),
                                'scanner_type': scanner_type,
                            })
                            broadcast_stats_update()

                        results.append(f"rfid: {epc} name: {person.name} status: อัปเดตสถานะสำเร็จ")

                except Person.DoesNotExist:
                    # ส่วนนี้ทำงานถูกต้องอยู่แล้ว ไม่ต้องแก้ไข
                    person_with_empty_rfid = Person.objects.filter(Q(rfid__isnull=True) | Q(rfid='')).first()

                    if not person_with_empty_rfid:
                        results.append(f"rfid: {epc} name: null status: ไม่พบข้อมูลในระบบ")
                    else:
                        person_with_empty_rfid.rfid = epc
                        verified_field = f"verified{scanner_id}"
                        time_field = f"verified_updated_at{scanner_id}"
                        verified_value = 2 if scanner_type == 'out' else 1
                        setattr(person_with_empty_rfid, verified_field, verified_value)
                        setattr(person_with_empty_rfid, time_field, timezone.now())
                        person_with_empty_rfid.save()

                        if settings.USE_CHANNEL:
                            broadcast_to_crud01({
                                'action': 'update',
                                'id': person_with_empty_rfid.id,
                                'fields': person_to_dict(person_with_empty_rfid),
                                'scanner_type': scanner_type,
                            })
                            broadcast_stats_update()
                        results.append(f"epc: {epc} name: {person_with_empty_rfid.name} status: เพิ่มรหัส RFID สำเร็จและอัปเดตสถานะแล้ว")

            return Response({'results': results}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class LogPagination(PageNumberPagination):
    page_size = 5

class LogList(generics.ListAPIView):
    serializer_class = LogSerializer
    pagination_class = LogPagination
    
    def get_queryset(self):
        # กรองข้อมูลที่อาจมี timestamp เป็น null
        return Log.objects.exclude(timestamp__isnull=True).order_by('-timestamp')

class LogCreateView(APIView):
    def post(self, request):
        serializer = LogSerializer(data=request.data)
        if serializer.is_valid():
            log = serializer.save()

            if log.action == "comment":
                if settings.USE_CHANNEL:
                    broadcast_ws("comment", {
                        "comment": log.details,
                        "time": log.timestamp.isoformat()
                    })

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
def person_to_dict(person):
    return {
        'name': person.name,
        'nisit': person.nisit,
        'degree': person.degree,
        'seat': person.seat,
        'verified1': person.verified1,
        'verified2': person.verified2,
        'verified3': person.verified3,
        'verified_updated_at1': datetime_to_str(person.verified_updated_at1),
        'verified_updated_at2': datetime_to_str(person.verified_updated_at2),
        'verified_updated_at3': datetime_to_str(person.verified_updated_at3),
        'rfid': person.rfid,
    }

def datetime_to_str(dt):
    if dt is None:
        return None
    return dt.isoformat()

def convert_datetime_fields(data: dict, fields: list):
    for f in fields:
        if f in data and isinstance(data[f], datetime):
            data[f] = data[f].isoformat()
    return data
