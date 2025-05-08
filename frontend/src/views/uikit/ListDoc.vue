<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import axios from 'axios';
import { Icon } from '@iconify/vue';
import Dialog from 'primevue/dialog';
import Paginator from 'primevue/paginator';
import io from 'socket.io-client';

// สร้างตัวแปรต่างๆ
const persons = ref([]);
const loading = ref(false);
const searchQuery = ref('');
const dialogVisible = ref(false);
const selectedPerson = ref({});

const currentPage = ref(0);
const rowsPerPage = ref(180);

// เชื่อมต่อกับ WebSocket Server
const socket = io('http://127.0.0.1:8000'); // URL ของ WebSocket Server

// ดึงข้อมูลจาก API
async function fetchPersons() {
    loading.value = true;
    try {
        const response = await axios.get('http://127.0.0.1:8000/api/person/');
        persons.value = response.data
            .filter((p) => p.verified === 1) // กรองเฉพาะ verified === 1
            .sort((a, b) => new Date(b.date) - new Date(a.date))
            .map((person) => ({
                ...person,
                formatted_id: person.id.toString().padStart(4, '0')
            }));
    } catch (error) {
        console.error('Error:', error);
    } finally {
        loading.value = false;
    }
}

// ฟังก์ชันเมื่อรับข้อมูลจาก WebSocket
socket.on('new-person', (newPerson) => {
    // ตรวจสอบว่ามีข้อมูลใหม่เข้ามาหรือไม่ ถ้ามีก็จะดึงข้อมูลใหม่
    fetchPersons();
});

// ฟิลเตอร์จาก search
const filteredPersons = computed(() => {
    const query = searchQuery.value.toLowerCase();
    return persons.value.filter((p) => p.name?.toLowerCase().includes(query) || p.nisit?.toLowerCase().includes(query) || p.seat?.toString().includes(query));
});

// Pagination
const paginatedPersons = computed(() => {
    const start = currentPage.value * rowsPerPage.value;
    return filteredPersons.value.slice(start, start + rowsPerPage.value);
});

// เปิด Dialog
function showPersonDetail(person) {
    selectedPerson.value = person;
    dialogVisible.value = true;
}

function onBeforeHide() {
    dialogVisible.value = false;
}

function onDialogShow() {
    setTimeout(() => {
        document.querySelector('.p-dialog')?.classList.add('transition-opacity');
    }, 10);
}

function highlightMatch(text) {
    const query = searchQuery.value.trim();
    if (!query) return text;
    const regex = new RegExp(`(${query})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}

onMounted(() => {
    fetchPersons(); // ดึงข้อมูลแรก

    // อัปเดตข้อมูลใหม่จาก WebSocket ทุกครั้งที่มีการส่งข้อมูลใหม่
    socket.on('new-person', fetchPersons);
});

onBeforeUnmount(() => {
    socket.disconnect(); // ปิดการเชื่อมต่อ WebSocket เมื่อ component ถูกลบ
});
</script>

<template>
    <div>
        <div class="text-lg font-bold mb-2">เลขบัณฑิตที่แตะ TAG แล้ว</div>

        <div class="mb-4">
            <input v-model="searchQuery" type="text" placeholder="ค้นหาชื่อ, รหัสนิสิต, หรือเลขที่นั่ง" class="p-2 border rounded w-full max-w-md" />
        </div>

        <!-- Loading -->
        <div v-if="loading" class="text-center my-4">กำลังโหลดข้อมูล...</div>

        <!-- Grid -->
        <div v-else class="card flex flex-wrap gap-2">
            <div v-for="(person, index) in paginatedPersons" :key="index" class="w-24 h-24 flex flex-col items-center justify-center text-center">
                <Icon
                    icon="material-symbols:person"
                    class="text-4xl cursor-pointer"
                    :class="{
                        'text-green-500': person.verified === 1
                    }"
                    @click="() => showPersonDetail(person)"
                />
                <div class="text-xs mt-2" v-html="highlightMatch(person.nisit.toString())"></div>
            </div>
        </div>

        <!-- Pagination -->
        <Paginator class="mt-6" :rows="rowsPerPage" :totalRecords="filteredPersons.length" :first="currentPage * rowsPerPage" @page="(e) => (currentPage = e.page)" />

        <!-- Dialog -->
        <Dialog v-model:visible="dialogVisible" header="รายละเอียดผู้เข้าร่วม" modal :closable="true" :style="{ width: '300px', maxWidth: '90vw' }" @before-hide="onBeforeHide" @show="onDialogShow">
            <div>
                <p><strong>ชื่อ:</strong> {{ selectedPerson.name }}</p>
                <p><strong>รหัสนิสิต:</strong> {{ selectedPerson.nisit }}</p>
                <p><strong>คณะ:</strong> {{ selectedPerson.degree }}</p>
                <p><strong>ที่นั่ง:</strong> {{ selectedPerson.seat }}</p>
                <p><strong>เวลา:</strong> {{ new Date(selectedPerson.date).toLocaleString() }}</p>
            </div>
        </Dialog>
    </div>
</template>

<style scoped>
.p-dialog {
    transition: opacity 0.3s ease, transform 0.3s ease;
}
.p-dialog-enter-active,
.p-dialog-leave-active {
    transition: opacity 0.3s ease, transform 0.3s ease;
}
.p-dialog-enter,
.p-dialog-leave-to {
    opacity: 0;
    transform: translateY(-50px);
}
.p-dialog .p-dialog-content {
    padding: 20px;
}
.p-dialog-header {
    background-color: #4caf50;
    color: white;
    text-align: center;
}
.p-dialog {
    border-radius: 8px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}
.p-dialog .p-dialog-header-close {
    color: white;
    font-size: 18px;
}
</style>
