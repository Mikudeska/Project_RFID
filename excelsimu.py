import pandas as pd
import random

num_records = 100
first_names = ["สมชาย", "สมหญิง", "ณัฐวุฒิ", "กิตติ", "ปวีณา", "ธนวัฒน์", "วรินทร", "อรทัย", "จิราพร", "สุนทร"]
last_names = ["วงศ์แก้ว", "สังขกุล", "จันทร์แจ่ม", "ทองดี", "บุญมา", "สายทอง", "คำภีร์", "แสงทอง", "ศรีสุข", "รัตนสุข"]

degree_list = [
    "การจัดการมหาบัณฑิต",
    "การแพทย์แผนไทยประยุกต์บัณฑิต",
    "ครุศาสตรบัณฑิต",
    "ครุศาสตรมหาบัณฑิต",
    "นิติศาสตรบัณฑิต",
    "นิเทศศาสตรดุษฎีบัณฑิต",
    "นิเทศศาสตรบัณฑิต",
    "นิเทศศาสตรมหาบัณฑิต",
    "บริหารธุรกิจดุษฎีบัณฑิต",
    "บริหารธุรกิจบัณฑิต",
    "บริหารธุรกิจมหาบัณฑิต",
    "บัญชีบัณฑิต",
    "ปรัชญาดุษฎีบัณฑิต",
    "พยาบาลศาสตรบัณฑิต",
    "รัฐประศาสนศาสตรบัณฑิต",
    "รัฐประศาสนศาสตรมหาบัณฑิต",
    "รัฐศาสตรดุษฎีบัณฑิต",
    "รัฐศาสตรบัณฑิต",
    "รัฐศาสตรมหาบัณฑิต",
    "วิทยาศาสตรบัณฑิต",
    "วิทยาศาสตรมหาบัณฑิต",
    "วิศวกรรมศาสตรบัณฑิต",
    "ศิลปกรรมศาสตรบัณฑิต",
    "ศิลปบัณฑิต",
    "ศิลปศาสตรบัณฑิต",
    "ศิลปศาสตรมหาบัณฑิต",
    "สถาปัตยกรรมศาสตรบัณฑิต",
    "สาธารณสุขศาสตรบัณฑิต",
    "สารสนเทศศาสตรบัณฑิต",
    "เศรษฐศาสตรบัณฑิต"
]
existing_nisits = set()
def generate_nisit():
 while True:
        nisit = ''.join(str(random.randint(0, 9)) for _ in range(11))
        if nisit not in existing_nisits:
            existing_nisits.add(nisit)
            return nisit

data = []
for _ in range(num_records):
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    degree = random.choice(degree_list)
    verified1 = random.choice([0, 1, 2])
    nisit = generate_nisit()
    data.append({
        "รหัสนักศึกษา": nisit,
        "ชื่อ - สกุล": name,
        "ชื่อหลักสูตร": degree,
        "สถานะรายงานตัว": verified1,
    })

df = pd.DataFrame(data)
output_path = r"D:\C O D E\RFID\simu_person2.xlsx"
df.to_excel(output_path, index=False)
print("สร้างไฟล์ simu_person.xlsx สำหรับ import เรียบร้อยแล้ว")
