# 🚀 คู่มือการ Deploy ระบบ RFID SSRU ไปยัง Production Server

## ✅ ข้อดีของ Dynamic URL Configuration
- ✨ **ไม่ต้องแก้ไข `.env`** เมื่อย้าย server
- ✨ **Frontend อ่าน URL อัตโนมัติ** จาก `window.location`
- ✨ **Deploy ง่าย** แค่ copy dist folder

---

## 📋 สิ่งที่ต้องเตรียม

### 1. Build Frontend
```bash
cd frontend
npm run build
# ✅ จะได้โฟลเดอร์ dist/ พร้อม deploy
```

### 2. ตรวจสอบ Backend Settings
ไฟล์: `backend/myproject/settings.py`
```python
# ต้องมี domain ของคุณใน ALLOWED_HOSTS
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'ssrurufi.com', 'www.ssrurufi.com']

# ตรวจสอบ CORS settings
CORS_ALLOWED_ORIGINS = [
    "https://ssrurufi.com",
    "https://www.ssrurufi.com",
    "http://ssrurufi.com",
    "http://www.ssrurufi.com",
]

# สำหรับ production ควรตั้ง
DEBUG = False
SECURE_SSL_REDIRECT = True  # ถ้าใช้ HTTPS
```

---

## 🌐 วิธีการ Deploy

### 📦 วิธีที่ 1: Deploy ด้วย Nginx (แนะนำ)

#### 1.1 โครงสร้างไฟล์บน Server
```
/var/www/rfid-ssru/
├── frontend/          # คัดลอกทั้งโฟลเดอร์ dist มาวางที่นี่
│   ├── index.html
│   └── assets/
└── backend/          # Django backend
    ├── manage.py
    └── ...
```

#### 1.2 Nginx Configuration
สร้างไฟล์: `/etc/nginx/sites-available/rfid-ssru`

```nginx
# Nginx Configuration สำหรับ RFID SSRU System
# Frontend (Vue.js) + Backend (Django) บน domain เดียวกัน

upstream django_backend {
    server 127.0.0.1:8001;
}

# HTTP -> HTTPS Redirect
server {
    listen 80;
    server_name ssrurufi.com www.ssrurufi.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name ssrurufi.com www.ssrurufi.com;

    # SSL Configuration (ใช้ Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/ssrurufi.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ssrurufi.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend Static Files (Vue.js dist)
    root /var/www/rfid-ssru/frontend;
    index index.html;

    # Frontend Routes (Vue Router)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Django Backend API
    location /api/ {
        proxy_pass http://django_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Django WebSocket (Channels)
    location /ws/ {
        proxy_pass http://django_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_read_timeout 86400;
    }

    # Django Static Files (Admin, DRF)
    location /static/ {
        alias /var/www/rfid-ssru/backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Django Media Files
    location /media/ {
        alias /var/www/rfid-ssru/backend/media/;
        expires 30d;
    }

    # Logs
    access_log /var/log/nginx/rfid-ssru-access.log;
    error_log /var/log/nginx/rfid-ssru-error.log;
}
```

#### 1.3 เปิดใช้งาน Nginx Config
```bash
# สร้าง symbolic link
sudo ln -s /etc/nginx/sites-available/rfid-ssru /etc/nginx/sites-enabled/

# ทดสอบ config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

---

### 🐍 วิธีที่ 2: รัน Django Backend

#### 2.1 ใช้ Gunicorn (Production)
```bash
cd /var/www/rfid-ssru/backend

# ติดตั้ง Gunicorn
pip install gunicorn

# รัน Gunicorn
gunicorn myproject.wsgi:application \
    --bind 127.0.0.1:8001 \
    --workers 4 \
    --timeout 120 \
    --daemon
```

#### 2.2 สร้าง Systemd Service (Auto-start)
สร้างไฟล์: `/etc/systemd/system/rfid-backend.service`

```ini
[Unit]
Description=RFID SSRU Django Backend
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/rfid-ssru/backend
ExecStart=/usr/bin/gunicorn myproject.wsgi:application \
    --bind 127.0.0.1:8001 \
    --workers 4 \
    --timeout 120
Restart=always

[Install]
WantedBy=multi-user.target
```

เปิดใช้งาน:
```bash
sudo systemctl daemon-reload
sudo systemctl enable rfid-backend
sudo systemctl start rfid-backend
sudo systemctl status rfid-backend
```

---

## 🔒 SSL Certificate (HTTPS)

### ติดตั้ง Let's Encrypt (ฟรี!)
```bash
# ติดตั้ง Certbot
sudo apt install certbot python3-certbot-nginx

# ขอ SSL Certificate
sudo certbot --nginx -d ssrurufi.com -d www.ssrurufi.com

# Auto-renewal (เพิ่มใน crontab)
sudo crontab -e
# เพิ่มบรรทัด:
0 3 * * * certbot renew --quiet
```

---

## 📝 Checklist ก่อน Deploy

### Frontend
- [ ] Build ด้วย `npm run build` สำเร็จ
- [ ] ลบหรือเคลียร์ค่าใน `.env` (ไม่จำเป็นต้องใช้แล้ว)
- [ ] ตรวจสอบ `dist/` folder มีไฟล์ครบ

### Backend
- [ ] `ALLOWED_HOSTS` มี domain ของคุณ
- [ ] `CORS_ALLOWED_ORIGINS` ตั้งค่าถูกต้อง
- [ ] `DEBUG = False` สำหรับ production
- [ ] รัน `python manage.py collectstatic`
- [ ] Database migrations เรียบร้อย
- [ ] ตรวจสอบ `requirements.txt` มี dependencies ครบ

### Server
- [ ] Nginx ติดตั้งและ config ถูกต้อง
- [ ] SSL Certificate ติดตั้งแล้ว (HTTPS)
- [ ] Firewall เปิด port 80, 443
- [ ] Backend service รันอยู่ (Gunicorn)

---

## 🧪 ทดสอบหลัง Deploy

### 1. ทดสอบ Frontend
```bash
# เปิดเว็บไซต์
https://ssrurufi.com

# ตรวจสอบ Console ว่ามี error หรือไม่
# F12 > Console
```

### 2. ทดสอบ API
```bash
# ทดสอบ API endpoint
curl https://ssrurufi.com/api/person/

# ตรวจสอบ CORS
curl -H "Origin: https://ssrurufi.com" \
     --verbose https://ssrurufi.com/api/person/
```

### 3. ทดสอบ WebSocket
```javascript
// เปิด Browser Console (F12) และรัน:
const ws = new WebSocket('wss://ssrurufi.com/ws/crud01/');
ws.onopen = () => console.log('✅ WebSocket Connected!');
ws.onerror = (e) => console.error('❌ WebSocket Error:', e);
```

---

## 🐛 Troubleshooting

### ปัญหา: API ไม่ทำงาน (CORS Error)
```python
# backend/myproject/settings.py
CORS_ALLOW_ALL_ORIGINS = True  # ชั่วคราวเพื่อ debug
```

### ปัญหา: WebSocket ไม่ทำงาน
- ตรวจสอบ Django Channels ติดตั้งแล้ว
- ตรวจสอบ Nginx proxy_pass สำหรับ /ws/ ถูกต้อง
- ตรวจสอบ firewall ไม่ได้บล็อก WebSocket

### ปัญหา: Static files ไม่โหลด
```bash
cd /var/www/rfid-ssru/backend
python manage.py collectstatic --noinput
```

### ปัญหา: 404 เมื่อ refresh หน้าเว็บ (Vue Router)
- ตรวจสอบ Nginx มี `try_files $uri $uri/ /index.html;`

---

## 📊 ตรวจสอบสถานะ Server

```bash
# ตรวจสอบ Nginx
sudo systemctl status nginx
sudo nginx -t

# ตรวจสอบ Backend
sudo systemctl status rfid-backend

# ตรวจสอบ Logs
sudo tail -f /var/log/nginx/rfid-ssru-error.log
sudo journalctl -u rfid-backend -f
```

---

## 🎉 สำเร็จ!

เมื่อทุกอย่างเรียบร้อย คุณควรจะสามารถ:
- ✅ เข้าถึงเว็บไซต์ได้ที่ `https://ssrurufi.com`
- ✅ API ทำงานได้ที่ `https://ssrurufi.com/api/`
- ✅ WebSocket เชื่อมต่อได้ที่ `wss://ssrurufi.com/ws/`
- ✅ ไม่มี CORS errors
- ✅ ระบบทำงานเร็วและเสถียร

---

## 💡 Tips

1. **Backup ก่อน Deploy เสมอ**
   ```bash
   # Backup database
   mysqldump -u root -p ssru_student_db > backup_$(date +%Y%m%d).sql
   ```

2. **ใช้ Git สำหรับ Deploy**
   ```bash
   # บน server
   git pull origin main
   cd frontend && npm run build
   sudo systemctl restart rfid-backend
   ```

3. **Monitor Logs**
   - ติดตั้ง tools อย่าง `htop`, `iotop` เพื่อดู resource usage
   - ใช้ `tail -f` เพื่อดู logs แบบ real-time

---

**สร้างโดย:** RFID SSRU Development Team  
**อัพเดทล่าสุด:** 24 ตุลาคม 2568

