==========================================================
งานโปรเจกต์จบมหาวิทยาลัย ราชภัฎสวนสุนันทาา ระบบ RFID SSRU (Frontend + Backend) Setup Guide
==========================================================

Requirements:
-------------
- VS Code / Code Editor
- Node.js
- Python
- XAMPP (Apache + MySQL)
- Postman (optional)

#1. Clone Project
----------------
- git clone -b mic https://github.com/Mikudeska/Test01-master.git
- cd Test01-master

#2. Install Dependencies
-----------------------
- cd frontend
- npm install
- npm install concurrently
- cd ../backend
- pip install -r requirements.txt

#3. Create .env Files
--------------------
- Frontend: put .env inside frontend folder (Test01-master/frontend/.env)
- VITE_API_BASE=http://localhost:8001
- VITE_USE_WEBSOCKET=false

- Backend: put .env inside backend folder (Test01-master/backend/.env)
- SECRET_KEY='django-insecure-j=^xs4wja2)#p6%u#63(z2fd-ld0q80xp8jme%h0n6$a#w&7ri'
- DEBUG=True
- ALLOWED_HOSTS=127.0.0.1,localhost,sv.ssrurufi.com

- DB_NAME=ssru_student_db
- DB_USER=root
- DB_PASSWORD=
- DB_HOST=localhost
- DB_PORT=3306

- USE_CHANNEL=false

#4. Start XAMPP
--------------
- Start Apache & MySQL
- เปิด MySQL (Workbench / Command Line / phpMyAdmin)
- รันคำสั่ง SQL:
CREATE DATABASE ssru_student_db CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

#5. Manager Backend
------------------------
- cd backend
- python manage.py makemigrations
- python manage.py migrate
- python manage.py create_groups.py

#6. Start Servers
----------------
- cd ../frontend
npm start

#7. Access
---------
- Frontend: http://localhost:5173
- Backend API: http://localhost:8001/api/
