<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import axios from 'axios';
import { Icon } from '@iconify/vue';
import Dialog from 'primevue/dialog';
import Paginator from 'primevue/paginator';
import Toast from 'primevue/toast';
import { useToast } from 'primevue/usetoast';

const persons = ref([]);
const loading = ref(false);
const searchQuery = ref('');
const verifiedFilter = ref('all'); // all, verified, unverified, unknown
const showFilters = ref(false); // ใช้สำหรับแสดง/ซ่อนปุ่มกรอง
const dialogVisible = ref(false);
const selectedPerson = ref({});
const toast = useToast();

const currentPage = ref(0);
const rowsPerPage = ref(1500);

// ดึงข้อมูล
async function fetchPersons() {
    loading.value = true;
    try {
        const response = await axios.get('http://127.0.0.1:8000/api/person/');
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
// ฟังก์ชันสำหรับยืดหดแสดงตัวกรอง
function toggleFilter() {
    showFilters.value = !showFilters.value;
}

// ฟิลเตอร์ข้อมูล
const filteredPersons = computed(() => {
    let results = persons.value;

    // กรอง verified
    if (verifiedFilter.value === 'verified') {
        results = results.filter((p) => p.verified === 1);
    } else if (verifiedFilter.value === 'unverified') {
        results = results.filter((p) => p.verified === 0);
    } else if (verifiedFilter.value === 'unknown') {
        results = results.filter((p) => p.verified !== 0 && p.verified !== 1);
    }

    // กรองคำค้นหา
    if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase();
        results = results.filter(
            (person) =>
                person.id.toString().includes(query) ||
                person.formatted_id.includes(query) ||
                person.name?.toLowerCase().includes(query) ||
                person.nisit?.includes(query) ||
                person.degree?.toLowerCase().includes(query) ||
                person.seat?.toString().includes(query)
        );
    }

    return results;
});

// จัดหน้าข้อมูล
const paginatedPersons = computed(() => {
    const start = currentPage.value * rowsPerPage.value;
    return filteredPersons.value.slice(start, start + rowsPerPage.value);
});

function showPersonDetail(person) {
    selectedPerson.value = person;
    dialogVisible.value = true;
}

function onBeforeHide() {
    dialogVisible.value = false;
}

function onDialogShow() {
    setTimeout(() => {
        document.querySelector('.p-dialog').classList.add('transition-opacity');
    }, 10);
}

function highlightMatch(text) {
    const query = searchQuery.value.trim();
    if (!query) return text;
    const regex = new RegExp(`(${query})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}

function buttonClass(status) {
    return ['px-4 py-1 rounded-full text-sm font-medium transition', verifiedFilter.value === status ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'].join(' ');
}

let debounceTimer;
watch(searchQuery, () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        toast.add({
            severity: 'info',
            summary: 'ผลการค้นหา',
            detail: `พบ ${filteredPersons.value.length} รายการ`,
            life: 2000
        });
    }, 500);
});

onMounted(fetchPersons);
</script>
<template>
    <div>
        <!-- Toast -->
        <Toast />

        <!-- Search Bar -->
        <div class="my-3 relative">
            <Icon icon="material-symbols:search" class="absolute left-4 top-1/2 -translate-y-1/2 text-blue-400 text-2xl cursor-pointer" />
            <input v-model="searchQuery" type="text" placeholder="ค้นหา (ชื่อ, ID, รหัสนิสิต...)" class="pl-12 pr-4 w-full h-12 rounded-md border border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>

        <!-- Speed Dial Floating Button -->
        <div class="fixed bottom-6 right-6 z-50 flex flex-col items-end space-y-2">
            <!-- Filter Buttons (Speed Dial Items) -->
            <transition-group name="fade" tag="div" v-if="showFilters">
                <button key="all" @click="verifiedFilter = 'all'" :class="buttonClass('all') + ' bg-green shadow-md'" class="rounded-full px-4 py-2 text-sm">📋 รายชื่อทั้งหมด</button>
                <button key="verified" @click="verifiedFilter = 'verified'" :class="buttonClass('verified') + ' bg-green shadow-md'" class="rounded-full px-4 py-2 text-sm">✅ รายงานตัวแล้ว</button>
                <button key="unverified" @click="verifiedFilter = 'unverified'" :class="buttonClass('unverified') + ' bg-green shadow-md'" class="rounded-full px-4 py-2 text-sm">❌ ยังไม่รายงานตัว</button>
                <button key="unknown" @click="verifiedFilter = 'unknown'" :class="buttonClass('unknown') + ' bg-green shadow-md'" class="rounded-full px-4 py-2 text-sm">❓ ไม่ทราบสถานะ</button>
            </transition-group>

            <!-- Main FAB Button -->
            <button @click="toggleFilter" class="bg-blue-500 text-white p-4 rounded-full shadow-xl hover:bg-blue-600 transition">
                <Icon icon="material-symbols:filter-list" class="text-2xl" />
            </button>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="text-center my-4">กำลังโหลดข้อมูล...</div>

        <!-- Persons -->
        <div v-else class="card flex flex-wrap gap-2">
            <div v-for="(person, index) in paginatedPersons" :key="index" class="w-9 h-18 flex flex-col items-center justify-center text-center">
                <Icon
                    icon="material-symbols:event-seat"
                    class="text-4xl cursor-pointer"
                    :class="{
                        'text-green-500': person.verified === 1,
                        'text-red-500': person.verified === 0,
                        'text-gray-400': person.verified !== 1 && person.verified !== 0
                    }"
                    v-tooltip="person.name"
                    @click="() => showPersonDetail(person)"
                />
                <div class="text-xs mt-2" v-html="highlightMatch(person.seat.toString())"></div>
            </div>
        </div>

        <!-- Paginator -->
        <Paginator class="mt-6" :rows="rowsPerPage" :totalRecords="filteredPersons.length" :first="currentPage * rowsPerPage" @page="(e) => (currentPage = e.page)" />

        <!-- Dialog -->
        <Dialog v-model:visible="dialogVisible" header="รายละเอียดผู้เข้าร่วม" modal :closable="true" :style="{ width: '300px', maxWidth: '90vw' }" @before-hide="onBeforeHide" @show="onDialogShow">
            <div>
                <p><strong>ชื่อ:</strong> {{ selectedPerson.name }}</p>
                <p><strong>รหัสนิสิต:</strong> {{ selectedPerson.nisit }}</p>
                <p><strong>คณะ:</strong> {{ selectedPerson.degree }}</p>
                <p><strong>ที่นั่ง:</strong> {{ selectedPerson.seat }}</p>
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
.fade-enter-active,
.fade-leave-active {
    transition: all 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
    opacity: 0;
    transform: translateY(10px);
}
</style>
