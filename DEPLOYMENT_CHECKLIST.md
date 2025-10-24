# ✅ Checklist การ Deploy ไปเซิร์ฟเวอร์จริง

## 📌 สรุปการแก้ไขที่ทำไป

### 1. แก้ไข API URL paths (ทุกไฟล์ .vue)
- **เดิม:** `api.get('api/login/')` → URL ซ้ำซ้อน `/api/api/login/`
- **ใหม่:** `api.get('login/')` → URL ถูกต้อง `/api/login/`
- **ผลกระทบ:** ✅ ใช้ได้ทั้ง Development และ Production

### 2. แก้ไข Config URL (frontend/src/config/index.js)
```javascript
// Development: http://localhost:8001/api/
// Production:  https://ssrurufi.com/api/ (อ่านจาก window.location)
```
- **ผลกระทบ:** ✅ ใช้ได้ทั้ง Development และ Production

### 3. แก้ไข WebSocket Store (frontend/src/stores/websocket.js)
```javascript
// Development: ปิด WebSocket (ไม่มี Redis)
// Production:  เปิด WebSocket (มี Redis)
```
- **ผลกระทบ:** ✅ ใช้ได้ทั้ง Development และ Production

---

## 🚀 ขั้นตอนการ Deploy

### ขั้นที่ 1: Build Frontend
```bash
cd frontend
npm run build
```

**สิ่งที่เกิดขึ้น:**
- ✅ Vite จะตั้ง `MODE = 'production'`
- ✅ `isDevelopment = false`
- ✅ URL จะอ่านจาก `window.location.host` อัตโนมัติ
- ✅ WebSocket จะเปิดใช้งาน (พร้อมเชื่อมต่อ Redis)

### ขั้นที่ 2: ตรวจสอบ Backend (.env)
ไฟล์: `backend/.env`
```env
# สำคัญ! ต้องตั้งค่าเหล่านี้
USE_CHANNEL=true
DEBUG=False
ALLOWED_HOSTS=ssrurufi.com,www.ssrurufi.com
SECRET_KEY=your-production-secret-key
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
```

### ขั้นที่ 3: ตรวจสอบ settings.py
ไฟล์: `backend/myproject/settings.py`

**ต้องมี domain ของคุณใน CORS:**
```python
CORS_ALLOWED_ORIGINS = [
    "https://ssrurufi.com",
    "https://www.ssrurufi.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://ssrurufi.com",
    "https://www.ssrurufi.com",
]
```

### ขั้นที่ 4: Upload ไฟล์ไปเซิร์ฟเวอร์

**Backend:**
```bash
# อัพโหลดโฟลเดอร์ backend ทั้งหมด
git pull origin main
cd backend
python manage.py migrate
python manage.py collectstatic --noinput
```

**Frontend:**
```bash
# อัพโหลดเฉพาะโฟลเดอร์ dist/
# แล้ววางไว้ที่ /var/www/rfid-ssru/frontend/
```

### ขั้นที่ 5: เริ่มต้น Services

**1. เริ่ม Redis (สำหรับ WebSocket):**
```bash
sudo systemctl start redis
sudo systemctl enable redis
```

**2. เริ่ม Django (Daphne สำหรับ WebSocket):**
```bash
daphne -b 0.0.0.0 -p 8001 myproject.asgi:application
```

หรือใช้ systemd service (แนะนำ):
```bash
sudo systemctl start daphne-rfid
sudo systemctl enable daphne-rfid
```

**3. เริ่ม Nginx:**
```bash
sudo systemctl restart nginx
```

---

## ⚠️ ข้อควรระวัง

### 1. WebSocket Protocol
- **HTTP:** ใช้ `ws://`
- **HTTPS:** ใช้ `wss://` (secure)

✅ Config ของเราจัดการให้อัตโนมัติแล้ว:
```javascript
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
```

### 2. Redis ต้องรันอยู่
หากไม่มี Redis, WebSocket จะไม่ทำงาน:
```bash
# ตรวจสอบ Redis
sudo systemctl status redis
# หรือ
redis-cli ping
# ควรได้ PONG
```

### 3. Port ต้องตรงกัน
- Backend รันที่: `8001` (ตาม Nginx config)
- Nginx proxy ไปที่: `127.0.0.1:8001`

### 4. HTTPS Certificate
ถ้าใช้ HTTPS (แนะนำ), ต้องมี SSL Certificate:
```bash
# ติดตั้ง Let's Encrypt
sudo certbot --nginx -d ssrurufi.com -d www.ssrurufi.com
```

---

## 🧪 การทดสอบหลัง Deploy

### 1. ทดสอบ API
```bash
curl https://ssrurufi.com/api/profile/
# ควรได้ response (หรือ 401 ถ้ายังไม่ login)
```

### 2. ทดสอบ WebSocket
เปิด Browser Console:
```javascript
// ควรเห็น
✅ WebSocket connected
```

**ไม่ควรเห็น:**
```javascript
❌ WebSocket disabled in development mode
```

### 3. ทดสอบ Real-time Updates
- เปิด 2 tabs
- แก้ไขข้อมูลใน tab 1
- ควรเห็นการอัพเดทใน tab 2 ทันที (ไม่ต้อง refresh)

---

## 🔧 Troubleshooting

### ปัญหา: WebSocket ไม่เชื่อมต่อ
```bash
# 1. เช็ค Redis
sudo systemctl status redis

# 2. เช็ค Daphne log
journalctl -u daphne-rfid -f

# 3. เช็ค Nginx log
tail -f /var/log/nginx/error.log
```

### ปัญหา: API ไม่ทำงาน
```bash
# เช็ค ALLOWED_HOSTS
python manage.py shell
>>> from django.conf import settings
>>> print(settings.ALLOWED_HOSTS)
```

### ปัญหา: CORS Error
ตรวจสอบว่า domain ใน `CORS_ALLOWED_ORIGINS` ตรงกับที่เข้าถึงจริง:
```python
# ห้ามลืม https://
CORS_ALLOWED_ORIGINS = [
    "https://ssrurufi.com",  # ✅ ถูกต้อง
    "ssrurufi.com",          # ❌ ผิด (ขาด https://)
]
```

---

## 📊 สรุป

| ฟีเจอร์ | Development | Production |
|---------|-------------|------------|
| API URL | `localhost:8001/api/` | `ssrurufi.com/api/` |
| WebSocket | ปิด (ไม่มี Redis) | เปิด (มี Redis) |
| Protocol | HTTP / WS | HTTPS / WSS |
| Build Mode | development | production |

✅ **โค้ดที่แก้ไขแล้วพร้อม Deploy โดยไม่ต้องแก้อะไรเพิ่มเติม!**

---

## 🎓 คำแนะนำเพิ่มเติม

### ก่อน Deploy ทุกครั้ง:
```bash
# 1. ทดสอบใน local ให้ดี
npm run dev

# 2. ทดสอบ production build ใน local
npm run build
npm run preview

# 3. แล้วค่อย deploy
```

### หลัง Deploy:
```bash
# ตรวจสอบ log
journalctl -u daphne-rfid -n 50
tail -f /var/log/nginx/access.log
```

---

**📅 อัพเดทล่าสุด:** $(date)  
**👨‍💻 ผู้จัดทำ:** SSRU RFID Team

