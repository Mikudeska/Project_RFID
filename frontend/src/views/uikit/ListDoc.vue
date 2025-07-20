<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import axios from 'axios';
import { Icon } from '@iconify/vue';
import Dialog from 'primevue/dialog';
import Paginator from 'primevue/paginator';

const API_BASE = import.meta.env.VITE_API_BASE;

// สร้างตัวแปรต่างๆ
const persons = ref([]);
const loading = ref(false);
const searchQuery = ref('');
const dialogVisible = ref(false);
const selectedPerson = ref({});

const currentPage = ref(0);
const rowsPerPage = ref(180);

// ดึงข้อมูลจาก API
async function fetchPersons() {
    loading.value = true;
    try {
        const response = await axios.get(`${API_BASE}/api/person/`);
        persons.value = response.data.map((person) => ({
            ...person,
            formatted_id: person.id.toString().padStart(4, '0')
        }));
    } catch (error) {
        console.error('Error:', error);
    } finally {
        loading.value = false;
    }
}

function handleWsMessage(event) {
    const msg = event.detail;

    if (!msg || !msg.action) {
        // ไม่ใช่ action-based message เช่น viewer_count
        return;
    }

    if (msg.action === 'update') {
        const index = persons.value.findIndex((p) => p.id === msg.id);
        if (index !== -1) {
            if ('verified1' in msg.fields) {
                msg.fields.verified = msg.fields.verified1;
            }

            const updated = { ...persons.value[index], ...msg.fields };
            persons.value.splice(index, 1, updated);
            if (typeof product !== 'undefined' && persons.value?.id === msg.id) {
                persons.value = { ...persons.value, ...msg.fields };
            }
        } else {
            console.warn('Person not found for update id:', msg.id);
        }
    } else if (msg.action === 'add') {
        persons.value.push({ id: msg.id, ...msg.fields });
    } else if (msg.action === 'delete') {
        const deletedId = msg.id;
        if (typeof product !== 'undefined' && persons.value?.id === deletedId) {
            persons.value = null;
        }
        persons.value = persons.value.filter((p) => p && p.id !== deletedId);
    }
}

onMounted(async () => {
    await fetchPersons();
    window.addEventListener('ws-message', handleWsMessage);
});

onBeforeUnmount(() => {
    window.removeEventListener('ws-message', handleWsMessage);
});

const filteredPersons = computed(() => {
    const query = searchQuery.value.toLowerCase();
    return persons.value.filter((p) => Number(p.verified) === 1).filter((p) => p.name?.toLowerCase().includes(query) || p.nisit?.toLowerCase().includes(query) || p.seat?.toString().includes(query));
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
</script>

<template>
    <div>
        <div class="mb-2 text-lg font-bold">เลขบัณฑิตที่แตะ TAG แล้ว</div>

        <div class="mb-4">
            <input v-model="searchQuery" type="text" placeholder="ค้นหาชื่อ, รหัสนิสิต, หรือเลขที่นั่ง" class="w-full max-w-md p-2 border rounded" />
        </div>

        <!-- Loading -->
        <div v-if="loading" class="my-4 text-center">กำลังโหลดข้อมูล...</div>

        <!-- Grid -->
        <div v-else class="flex flex-wrap gap-2 card">
            <div v-for="(person, index) in paginatedPersons" :key="index" class="flex flex-col items-center justify-center w-24 h-24 text-center">
                <Icon
                    icon="material-symbols:person"
                    class="text-4xl cursor-pointer"
                    :class="{
                        'text-green-500': person.verified === 1
                    }"
                    @click="() => showPersonDetail(person)"
                />
                <div class="mt-2 text-xs" v-html="highlightMatch(person.nisit.toString())"></div>
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
