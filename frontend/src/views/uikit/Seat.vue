<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import axios from 'axios';
import Dialog from 'primevue/dialog';
import { useToast } from 'primevue/usetoast';
import { Icon } from '@iconify/vue';

const NUM_ROWS = 70;
const SEATS_PER_ROW = 70;
const SEATS_PER_SIDE = 35;
const API_BASE = import.meta.env.VITE_API_BASE;
const persons = ref([]);
const loading = ref(false);
const searchQuery = ref('');
const searchType = ref('nisit4'); // เพิ่มตัวแปรประเภทการค้นหา
const verifiedFilter = ref('all');
const dialogVisible = ref(false);
const selectedPerson = ref({});
const toast = useToast();
const showFilterDropdown = ref(false);
const filterDropdownRef = ref(null);
const searchMessage = ref('');
// เพิ่ม ref สำหรับเก้าอี้ที่ถูก highlight
const highlightedSeatRef = ref(null);

function handleClickOutside(event) {
    if (filterDropdownRef.value && !filterDropdownRef.value.contains(event.target)) {
        showFilterDropdown.value = false;
    }
}
onMounted(() => {
    document.addEventListener('mousedown', handleClickOutside);
});
onBeforeUnmount(() => {
    document.removeEventListener('mousedown', handleClickOutside);
});

// ระบบเสาแบบใหม่: กำหนดเสาเป็น array ของ object
const pillars = [
    // เพิ่ม/ลบ/ย้ายเสาได้ที่นี่
    { row: 3, side: 'left', index: 6, length: 3 }, // แถว 4, ฝั่งซ้าย, ตำแหน่งที่ 11, ยาว 3 ช่อง
    { row: 3, side: 'right', index: 16, length: 3 }, // แถว 4, ฝั่งขวา, ตำแหน่งที่ 11, ยาว 3 ช่อง
    { row: 16, side: 'left', index: 6, length: 3 }, // แถว 17, ฝั่งซ้าย, ตำแหน่งที่ 11, ยาว 3 ช่อง
    { row: 16, side: 'left', index: 32, length: 3 }, // แถว 17, ฝั่งซ้าย, ตำแหน่งที่ 32, ยาว 3 ช่อง
    { row: 16, side: 'right', index: 16, length: 3 }, // แถว 17, ฝั่งขวา, ตำแหน่งที่ 11, ยาว 3 ช่อง
    { row: 29, side: 'left', index: 6, length: 3 }, // แถว 30, ฝั่งซ้าย, ตำแหน่งที่ 11, ยาว 3 ช่อง
    { row: 29, side: 'left', index: 32, length: 3 }, // แถว 30, ฝั่งซ้าย, ตำแหน่งที่ 32, ยาว 3 ช่อง
    { row: 29, side: 'right', index: 16, length: 3 } // แถว 30, ฝั่งขวา, ตำแหน่งที่ 11, ยาว 3 ช่อง
];

onMounted(async () => {
    loading.value = true;
    try {
        const { data } = await axios.get(`${API_BASE}/api/person/`);
        persons.value = data.map((p) => ({ ...p, seat: Number(p.seat) }));
    } catch (e) {
        toast.add({ severity: 'error', summary: 'โหลดข้อมูลล้มเหลว', detail: e.message, life: 3000 });
    } finally {
        loading.value = false;
    }
});

const degreeList = computed(() => {
    // สร้างรายการคณะจากข้อมูล persons ทั้งหมด (ไม่ซ้ำ)
    const set = new Set(persons.value.map((p) => p.degree).filter(Boolean));
    return Array.from(set);
});
const selectedDegree = ref('');

const statusLabels = {
    0: 'ยังไม่รายงานตัว',
    1: 'รายงานตัวแล้ว',
    2: 'เข้าหอประชุมเรียบร้อยแล้ว',
    unknown: 'ไม่ทราบสถานะ'
};

// เพิ่ม computed สำหรับ activeFilters
const activeFilters = computed(() => {
    const filters = [];
    if (verifiedFilter.value !== 'all') {
        filters.push({
            key: 'verified',
            label: statusLabels[verifiedFilter.value],
            type: 'status'
        });
    }
    if (selectedDegree.value) {
        filters.push({ key: 'degree', label: selectedDegree.value, type: 'degree' });
    }
    return filters;
});
function removeFilter(key) {
    if (key === 'verified') verifiedFilter.value = 'all';
    if (key === 'degree') selectedDegree.value = '';
}

function resetFilter() {
    searchQuery.value = '';
    verifiedFilter.value = 'all';
    selectedDegree.value = '';
}

const filteredPersons = computed(() => {
    // คืนค่าทุกคน ไม่กรองคณะ
    return persons.value.sort((a, b) => a.seat - b.seat);
});

// เพิ่มฟังก์ชันกำหนดสีเก้าอี้ตามสถานะที่เลือก
function getChairColor(person) {
    // ถ้าเลือกคณะ และไม่ตรงกับคนนี้ ให้สีจาง
    if (selectedDegree.value && person.degree !== selectedDegree.value) {
        return 'text-gray-400 opacity-30';
    }

    const filter = verifiedFilter.value;
    const personStatus = person.verified;

    // กำหนดสีตามสถานะ
    let colorClass = 'text-gray-400'; // สถานะไม่แน่ชัด (default)
    if (personStatus === 0) colorClass = 'text-red-500'; // ยังไม่รายงานตัว
    if (personStatus === 1) colorClass = 'text-green-500'; // รายงานตัวแล้ว
    if (personStatus === 2) colorClass = 'text-yellow-300'; // เข้าหอประชุมแล้ว

    // ตรรกะการกรอง
    if (filter === 'all') {
        return colorClass;
    }
    if (filter === 'unknown') {
        // ถ้าตัวกรองเป็น 'ไม่ทราบสถานะ' ให้แสดงเฉพาะคนที่ไม่ใช่สถานะ 0, 1, 2
        return ![0, 1, 2].includes(personStatus) ? colorClass : 'text-gray-400 opacity-30';
    }

    // สำหรับตัวกรองที่เป็นตัวเลข "0", "1", "2"
    // แปลง personStatus เป็น string เพื่อเปรียบเทียบกับค่าจาก select
    return personStatus.toString() === filter ? colorClass : 'text-gray-400 opacity-30';
}

// Pre-calculate layoutMatrix สำหรับทุกแถว
const layoutMatrix = [];
for (let rowIdx = 0; rowIdx < NUM_ROWS; rowIdx++) {
    const layout = Array(SEATS_PER_ROW).fill('seat');
    // แทรกเสาในตำแหน่งที่ต้องการ
    pillars
        .filter((p) => p.row === rowIdx)
        .forEach((p) => {
            let insertIdx = p.side === 'left' ? p.index : SEATS_PER_SIDE + p.index;
            layout.splice(insertIdx, 0, 'pillar');
        });
    layoutMatrix.push(layout);
}

// 4. สร้างฟังก์ชันสำหรับจัดการข้อความ WebSocket

function getRowLayout(rowIdx) {
    // เริ่มต้นด้วย array 70 ช่อง
    const layout = Array(SEATS_PER_ROW).fill('seat');
    // หาเสาในแถวนี้
    const rowPillars = pillars.filter((p) => p.row === rowIdx);
    // แทรกเสาตามความยาว (length)
    rowPillars.forEach((p) => {
        let insertIdx = p.side === 'left' ? p.index : SEATS_PER_SIDE + p.index;
        for (let i = 0; i < (p.length || 1); i++) {
            layout[insertIdx + i] = 'pillar';
        }
    });
    return layout;
}

const seatRows = computed(() => {
    const rows = [];
    const personsList = [...filteredPersons.value];
    let rowIdx = 0;
    while (personsList.length > 0) {
        const layout = getRowLayout(rowIdx);
        const row = [];
        for (const slot of layout) {
            if (slot === 'pillar') {
                row.push({ type: 'pillar' });
            } else if (personsList.length > 0) {
                row.push({ type: 'person', data: personsList.shift() });
            } else {
                row.push({ type: 'empty' });
            }
        }
        rows.push(row);
        rowIdx++;
    }
    return rows;
});

function showPersonDetail(person) {
    selectedPerson.value = person;
    dialogVisible.value = true;
}

function isHighlighted(person) {
    if (!searchQuery.value) return false;
    const q = searchQuery.value.toLowerCase();
    if (searchType.value === 'seat') {
        return person.seat?.toString() === q;
    } else if (searchType.value === 'nisit4') {
        return person.nisit && person.nisit.slice(-4).includes(q);
    }
    return false;
}

// ปรับ buildSidesWithPillars ให้รองรับ row ที่เป็น array ของ object (type: 'person'/'pillar'/'empty')
function buildSidesWithPillars(row) {
    return {
        left: row.slice(0, SEATS_PER_SIDE),
        right: row.slice(SEATS_PER_SIDE, SEATS_PER_ROW)
    };
}

watch([searchQuery, searchType], async () => {
    if (!searchQuery.value) {
        searchMessage.value = '';
        return;
    }
    let found = null;
    if (searchType.value === 'seat') {
        found = persons.value.find((p) => p.seat?.toString() === searchQuery.value);
    } else if (searchType.value === 'nisit4') {
        found = persons.value.find((p) => p.nisit && p.nisit.slice(-4) === searchQuery.value);
    }
    if (found) {
        // หาแถวและฝั่งจาก seatRows layout จริง
        let foundRow = null;
        let foundSide = null;
        seatRows.value.forEach((row, rowIdx) => {
            row.forEach((item, i) => {
                if (item.type === 'person' && item.data.seat === found.seat) {
                    foundRow = rowIdx + 1;
                    foundSide = i < SEATS_PER_SIDE ? 'A' : 'B';
                }
            });
        });
        if (foundRow && foundSide) {
            searchMessage.value = `พบที่นั่งเลข ${found.seat} อยู่แถว ${foundSide}${foundRow}`;
        } else {
            searchMessage.value = 'ไม่พบที่นั่งที่ค้นหา';
        }
        // scroll ไปยังเก้าอี้ที่ highlight
        await nextTick();
        if (highlightedSeatRef.value) {
            highlightedSeatRef.value.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
        }
    } else {
        searchMessage.value = 'ไม่พบที่นั่งที่ค้นหา';
    }
});

// ลบ placeholder animation เดิม (animatedPlaceholder, placeholderList, placeholderIndex)

// เพิ่มฟังก์ชัน setHighlightedSeatRef
function setHighlightedSeatRef(el) {
    if (el) highlightedSeatRef.value = el;
}

function handleWsMessage(event) {
    const msg = event.detail;
    if (msg.action === 'update') {
        const index = persons.value.findIndex((p) => p.id === msg.id);
        if (index !== -1) {
            if ('verified1' in msg.fields) {
                msg.fields.verified = msg.fields.verified1;
            }
            const updated = { ...persons.value[index], ...msg.fields };
            persons.value.splice(index, 1, updated);
        } else {
            console.warn('Person not found for update id:', msg.id);
        }
    } else if (msg.action === 'add') {
        persons.value.push({ id: msg.id, ...msg.fields });
    } else if (msg.action === 'delete') {
        const deletedId = msg.id;
        persons.value = persons.value.filter((p) => p && p.id !== deletedId);
    }
}

onMounted(() => {
    window.addEventListener('ws-message', handleWsMessage);
});

onBeforeUnmount(() => {
    window.removeEventListener('ws-message', handleWsMessage);
});
</script>

<template>
    <div>
        <Toast />
        <!-- Filter Icon Button (Right Top) -->
        <div class="fixed z-50 top-20 right-6">
            <button @click="showFilterDropdown = !showFilterDropdown" class="p-2 transition bg-blue-100 border border-blue-300 rounded-full shadow-lg hover:bg-blue-200">
                <Icon icon="mdi:filter-variant" class="text-blue-600" width="28" height="28" />
            </button>
            <!-- Dropdown Filter Bar -->
            <div v-if="showFilterDropdown" ref="filterDropdownRef" class="absolute right-0 mt-2 z-50 bg-white/90 rounded-xl shadow-xl p-4 w-96 max-w-[95vw] flex flex-col gap-3 border border-blue-100">
                <div class="flex flex-col gap-3">
                    <div class="flex items-center min-w-0 gap-3 px-2 py-1 border-b border-blue-100">
                        <Icon icon="mdi:magnify" class="text-blue-800" width="40" height="40" />
                        <div class="relative w-full">
                            <form @submit.prevent style="width: 100%">
                                <input v-model="searchQuery" class="flex-1 w-full min-w-0 pl-3 text-gray-900 placeholder-transparent border border-blue-400 rounded-lg shadow h-9 bg-white/80 focus:ring-0 focus:outline-none" />
                                <button type="submit" style="display: none"></button>
                            </form>
                            <div v-if="!searchQuery" class="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none w-[calc(100%-2.5rem)] overflow-hidden">
                                <span class="block text-sm text-gray-400 animate-marquee whitespace-nowrap"> ค้นหาเลขนิสิต 4 ตัวท้าย หรือ เลขที่นั่ง... </span>
                            </div>
                        </div>
                        <select v-model="searchType" class="h-9 bg-white/80 border border-blue-400 rounded-lg shadow focus:ring-0 focus:outline-none text-gray-900 font-semibold px-2 w-auto max-w-[120px]">
                            <option value="nisit4">เลขนิสิต 4 ตัวท้าย</option>
                            <option value="seat">เลขที่นั่ง</option>
                        </select>
                    </div>
                    <div
                        v-if="searchMessage"
                        :class="[
                            'flex items-center w-full justify-center gap-2 mt-2 mb-3 px-4 py-2 rounded-xl text-base font-semibold shadow',
                            searchMessage.includes('ไม่พบ') ? 'bg-red-100 text-red-700 border border-red-200' : 'bg-green-100 text-green-900 border border-green-300'
                        ]"
                    >
                        <Icon :icon="searchMessage.includes('ไม่พบ') ? 'mdi:alert-circle-outline' : 'mdi:check-circle-outline'" :class="searchMessage.includes('ไม่พบ') ? 'text-red-600' : 'text-green-600'" width="24" height="24" />
                        <span class="whitespace-pre-line">{{ searchMessage }}</span>
                    </div>
                    <div class="flex items-center gap-2 px-2 py-1 border-b border-blue-100">
                        <Icon icon="mdi:account-check" class="text-blue-800" width="20" height="20" />
                        <div class="relative w-full">
                            <select
                                v-model="verifiedFilter"
                                class="w-full h-10 pl-4 pr-10 font-semibold text-blue-700 transition border border-blue-200 rounded-lg shadow appearance-none bg-white/80 focus:ring-2 focus:ring-blue-400 focus:outline-none"
                            >
                                <option value="all">ทั้งหมด</option>
                                <option value="1">รายงานตัวแล้ว</option>
                                <option value="0">ยังไม่รายงานตัว</option>
                                <option value="2">เข้าหอประชุมเรียบร้อยแล้ว</option>
                                <option value="unknown">ไม่ทราบสถานะ</option>
                            </select>
                            <span class="absolute text-blue-400 -translate-y-1/2 pointer-events-none right-3 top-1/2">
                                <Icon icon="mdi:chevron-down" width="20" height="20" />
                            </span>
                        </div>
                    </div>
                    <div class="flex items-center gap-2 px-2 py-1 border-b border-blue-100">
                        <Icon icon="mdi:school" class="text-blue-800" width="20" height="20" />
                        <div class="relative w-full">
                            <select
                                v-model="selectedDegree"
                                class="w-full h-10 pl-4 pr-10 font-semibold text-blue-700 transition border border-blue-200 rounded-lg shadow appearance-none bg-white/80 focus:ring-2 focus:ring-blue-400 focus:outline-none"
                            >
                                <option value="">ทุกคณะ</option>
                                <option v-for="d in degreeList" :key="d" :value="d">{{ d }}</option>
                            </select>
                            <span class="absolute text-blue-400 -translate-y-1/2 pointer-events-none right-3 top-1/2">
                                <Icon icon="mdi:chevron-down" width="20" height="20" />
                            </span>
                        </div>
                    </div>
                    <!-- เปลี่ยนปุ่มปิดเป็นปุ่มรีเฟรช -->
                    <button @click="resetFilter" class="flex items-center self-end justify-center transition border-none rounded-full h-9 w-9 hover:bg-blue-200" title="รีเซ็ตตัวกรอง">
                        <Icon icon="mdi:refresh" class="text-blue-800 hover:text-blue-600" width="24" height="24" />
                    </button>
                    <!-- Filter Chips -->
                    <!-- ลบ searchMessage ออกจาก filter chips -->
                    <div v-if="activeFilters.length > 0" class="flex flex-wrap justify-end gap-2 mt-4">
                        <span v-for="f in activeFilters" :key="f.key" class="flex items-center px-2 py-1 text-blue-800 bg-blue-100 rounded-full">
                            {{ f.label }}
                            <button @click="removeFilter(f.key)" class="ml-1 text-blue-500 hover:text-blue-700">&times;</button>
                        </span>
                    </div>
                </div>
            </div>
        </div>
        <!-- Seat Layout -->
        <div v-if="loading" class="grid grid-cols-5 gap-4 p-4"><Skeleton v-for="n in 10" :key="n" width="100%" height="4rem" /></div>
        <div v-else class="overflow-auto pt-9">
            <div class="flex flex-col gap-4">
                <div v-for="(row, rowIdx) in seatRows" :key="rowIdx" class="flex items-center mb-2">
                    <div class="flex-shrink-0 w-24 pr-2 text-xs font-bold text-right text-gray-300">
                        <span class="bg-blue-100 border border-blue-400 rounded px-2 py-1 text-blue-800 min-w-[4.5rem]">แถว A{{ rowIdx + 1 }}</span>
                    </div>
                    <!-- ฝั่งซ้าย: 0-34 -->
                    <div class="flex gap-2">
                        <template v-for="(item, i) in buildSidesWithPillars(row).left" :key="i">
                            <div
                                v-if="item.type === 'pillar'"
                                class="flex items-center justify-center text-xs font-bold -800 bg-yellow-200 border border-yellow-400 rounded"
                                :style="item.length > 1 ? { gridColumn: `span ${item.length} / span ${item.length}`, width: `calc(1.5rem * ${item.length})` } : { width: '2.25rem' }"
                            >
                                เสา
                            </div>
                            <div
                                v-else-if="item.type === 'person'"
                                class="flex flex-col items-center cursor-pointer"
                                :title="item.data.name"
                                @click="showPersonDetail(item.data)"
                                :class="isHighlighted(item.data) ? 'ring-4 ring-yellow-400 ring-offset-2 rounded-lg' : ''"
                                :ref="isHighlighted(item.data) ? setHighlightedSeatRef : null"
                            >
                                <Icon icon="mdi:chair" :class="getChairColor(item.data)" width="32" height="32" />
                                <span class="mt-1 text-xs font-bold">{{ item.data.seat }}</span>
                            </div>
                            <div v-else class="flex flex-col items-center rounded opacity-80 bg-gray-100/60 dark:bg-gray-700/30">
                                <Icon icon="mdi:chair" class="text-gray-400 dark:text-gray-400" width="32" height="32" />
                                <span class="mt-1 text-xs font-bold text-gray-400 dark:text-gray-400">ว่าง</span>
                            </div>
                        </template>
                    </div>
                    <!-- ช่องว่างตรงกลาง (mx-12) -->
                    <div class="mx-12"></div>
                    <!-- ฝั่งขวา: 35-69 -->
                    <div class="flex gap-2">
                        <template v-for="(item, i) in buildSidesWithPillars(row).right" :key="i">
                            <div
                                v-if="item.type === 'pillar'"
                                class="flex items-center justify-center text-xs font-bold -800 bg-yellow-200 border border-yellow-400 rounded"
                                :style="item.length > 1 ? { gridColumn: `span ${item.length} / span ${item.length}`, width: `calc(1.5rem * ${item.length})` } : { width: '2.35rem' }"
                            >
                                เสา
                            </div>
                            <div
                                v-else-if="item.type === 'person'"
                                class="flex flex-col items-center cursor-pointer"
                                :title="item.data.name"
                                @click="showPersonDetail(item.data)"
                                :class="isHighlighted(item.data) ? 'ring-4 ring-yellow-400 ring-offset-2 rounded-lg' : ''"
                                :ref="isHighlighted(item.data) ? setHighlightedSeatRef : null"
                            >
                                <Icon icon="mdi:chair" :class="getChairColor(item.data)" width="32" height="32" />
                                <span class="mt-1 text-xs font-bold">{{ item.data.seat }}</span>
                            </div>
                            <div v-else class="flex flex-col items-center rounded opacity-80 bg-gray-100/60 dark:bg-gray-700/30">
                                <Icon icon="mdi:chair" class="text-gray-400 dark:text-gray-400" width="32" height="32" />
                                <span class="mt-1 text-xs font-bold text-gray-400 dark:text-gray-400">ว่าง</span>
                            </div>
                        </template>
                    </div>
                    <div class="flex-shrink-0 w-24 pl-2 text-xs font-bold text-left text-gray-300">
                        <span class="bg-blue-100 border border-blue-400 rounded px-2 py-1 text-blue-800 min-w-[4.5rem]">แถว B{{ rowIdx + 1 }}</span>
                    </div>
                </div>
            </div>
        </div>
        <!-- Person Detail Dialog -->
        <Dialog v-model:visible="dialogVisible" header="" modal :closable="false" class="p-fluid max-w-lg w-[98vw] rounded-2xl shadow-2xl ring-2 ring-blue-200/60 backdrop-blur-xl animate-fade-in" :dismissableMask="true" :closeOnEscape="true">
            <div v-if="selectedPerson" class="relative flex flex-col items-center p-0 shadow-xl bg-white/90 rounded-2xl md:flex-row">
                <!-- ปุ่มปิด -->
                <button @click="dialogVisible = false" class="absolute flex items-center justify-center w-10 h-10 text-blue-400 transition rounded-full shadow-lg top-4 right-4 bg-white/80 hover:bg-blue-200 hover:text-blue-700" aria-label="ปิด">
                    <Icon icon="mdi:close" width="26" height="26" />
                </button>
                <!-- Avatar -->
                <div class="flex flex-col items-center justify-center flex-shrink-0 p-8">
                    <Icon icon="mdi:account-circle" class="text-blue-300" width="80" height="80" />
                </div>
                <!-- ข้อมูล -->
                <div class="flex-1 p-8">
                    <div class="mb-2 text-2xl font-bold text-blue-900">{{ selectedPerson.name }}</div>
                    <div class="mb-1 text-gray-500">
                        รหัสนิสิต: <span class="font-semibold text-gray-800">{{ selectedPerson.nisit }}</span>
                    </div>
                    <div class="mb-1 text-gray-500">
                        คณะ: <span class="font-semibold text-gray-800">{{ selectedPerson.degree }}</span>
                    </div>
                    <div class="text-gray-500">
                        ที่นั่ง: <span class="font-semibold text-gray-800">{{ selectedPerson.seat }}</span>
                    </div>
                </div>
            </div>
        </Dialog>
    </div>
</template>

<style scoped>
.fade-slide-enter-active,
.fade-slide-leave-active {
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.fade-slide-enter-from,
.fade-slide-leave-to {
    opacity: 0;
    transform: translateY(40px) scale(0.98);
}
.fade-slide-enter-to,
.fade-slide-leave-from {
    opacity: 1;
    transform: translateY(0) scale(1);
}
@keyframes fade-in {
    from {
        opacity: 0;
        transform: scale(0.95) translateY(32px);
    }
    to {
        opacity: 1;
        transform: scale(1) translateY(0);
    }
}
.animate-fade-in {
    animation: fade-in 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
@keyframes marquee {
    0% {
        transform: translateX(100%);
    }
    100% {
        transform: translateX(-100%);
    }
}
.animate-marquee {
    animation: marquee 6s linear infinite;
}
</style>