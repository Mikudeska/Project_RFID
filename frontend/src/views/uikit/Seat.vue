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

// เพิ่ม computed สำหรับสถิติ
const statistics = computed(() => {
    const total = persons.value.length;
    const reported = persons.value.filter(p => p.verified === 1).length;
    const inHall = persons.value.filter(p => p.verified === 2).length;
    const notReported = persons.value.filter(p => p.verified === 0).length;
    const unknown = persons.value.filter(p => ![0, 1, 2].includes(p.verified)).length;
    
    return {
        total,
        reported,
        inHall,
        notReported,
        unknown,
        reportedPercentage: total > 0 ? Math.round((reported / total) * 100) : 0,
        inHallPercentage: total > 0 ? Math.round((inHall / total) * 100) : 0,
        notReportedPercentage: total > 0 ? Math.round((notReported / total) * 100) : 0
    };
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
    // ใช้ข้อมูลจาก row โดยตรง
    const left = row.slice(0, SEATS_PER_SIDE);
    const right = row.slice(SEATS_PER_SIDE, SEATS_PER_ROW);
    
    // ถ้าข้อมูลไม่ครบ ให้เติม empty
    while (left.length < SEATS_PER_SIDE) {
        left.push({ type: 'empty' });
    }
    while (right.length < SEATS_PER_SIDE) {
        right.push({ type: 'empty' });
    }
    
    return { left, right };
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

// เพิ่ม Mini Map functions
const showMiniMap = ref(true);
const miniMapZoom = ref(1);
const miniMapPan = ref({ x: 0, y: 0 });

// สร้าง Mini Map data แบบใหม่ - ใช้ข้อมูลจริงทั้งหมด
const miniMapData = computed(() => {
    // หาจำนวนแถวสูงสุดจากข้อมูลจริง
    const maxSeatNumber = Math.max(...persons.value.map(p => p.seat), 0);
    const actualRows = Math.ceil(maxSeatNumber / SEATS_PER_ROW);
    
    // สร้าง Mini Map ตามจำนวนแถวจริง (แนวตั้ง)
    const miniMapRows = [];
    
    for (let rowIdx = 0; rowIdx < actualRows; rowIdx++) {
        const layout = getRowLayout(rowIdx);
        const row = [];
        
        // แสดงแค่ 70 จุด (35 ซ้าย + 35 ขวา) ตามแนวตั้ง
        for (let colIdx = 0; colIdx < SEATS_PER_ROW; colIdx++) {
            if (layout[colIdx] === 'pillar') {
                row.push({ type: 'pillar', row: rowIdx, col: colIdx });
            } else {
                // หาคนที่อยู่ในที่นั่งนี้
                const seatNumber = rowIdx * SEATS_PER_ROW + colIdx + 1;
                const person = persons.value.find(p => p.seat === seatNumber);
                
                if (person) {
                    row.push({ 
                        type: 'person', 
                        seat: person.seat,
                        status: person.verified,
            row: rowIdx,
            col: colIdx
                    });
                } else {
                    row.push({ type: 'empty', row: rowIdx, col: colIdx });
                }
            }
        }
        miniMapRows.push(row);
    }
    
    return miniMapRows;
});

// สถิติ Mini Map
const miniMapStats = computed(() => {
    const stats = { red: 0, green: 0, yellow: 0, gray: 0 };
    miniMapData.value.forEach(row => {
        row.forEach(item => {
            if (item.type === 'person') {
                switch (item.status) {
                    case 0: stats.red++; break;
                    case 1: stats.green++; break;
                    case 2: stats.yellow++; break;
                    default: stats.gray++; break;
                }
            }
        });
    });
    return stats;
});

// Viewport Rectangle
const viewportRect = computed(() => {
    const scrollTop = window.scrollY;
    const scrollLeft = window.scrollX;
    const viewportHeight = window.innerHeight;
    const viewportWidth = window.innerWidth;
    const totalHeight = document.body.scrollHeight;
    const totalWidth = document.body.scrollWidth;
    
    return {
        top: (scrollTop / totalHeight) * 100,
        left: (scrollLeft / totalWidth) * 100,
        width: (viewportWidth / totalWidth) * 100,
        height: (viewportHeight / totalHeight) * 100
    };
});

// ฟังก์ชันคลิก Mini Map แบบง่ายๆ
function clickMiniMapSimple(row, col, side) {
    const seatRowsData = seatRows.value[row];
    let item;
    
    if (side === 'A') {
        // ฝั่งซ้าย (0-34)
        item = seatRowsData[col];
    } else {
        // ฝั่งขวา (35-69)
        item = seatRowsData[col + 35];
    }
    
    if (item && item.type === 'person') {
        searchQuery.value = item.data.seat.toString();
        searchType.value = 'seat';
        
        setTimeout(() => {
            if (highlightedSeatRef.value) {
                highlightedSeatRef.value.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center', 
                    inline: 'center' 
                });
            }
        }, 100);
    }
}

// ฟังก์ชัน Zoom Mini Map
function zoomMiniMap(direction) {
    miniMapZoom.value = Math.max(0.5, Math.min(2, miniMapZoom.value + direction * 0.2));
}

// ฟังก์ชันสี Mini Map
function getMiniMapColor(status) {
    switch (status) {
        case 0: return 'bg-red-500'; // ยังไม่รายงานตัว
        case 1: return 'bg-green-500'; // รายงานตัวแล้ว
        case 2: return 'bg-yellow-400'; // เข้าหอประชุมแล้ว
        default: return 'bg-gray-400'; // ไม่ทราบสถานะ
    }
}
</script>

<template>
    <div>
        <Toast />
        <!-- Filter Icon Button (Right Top) -->
        <div class="fixed z-50 top-20 right-6">
            <button @click="showFilterDropdown = !showFilterDropdown" class="p-2 transition-all duration-300 bg-blue-100 dark:bg-blue-900 border border-blue-300 dark:border-blue-600 rounded-full shadow-lg hover:bg-blue-200 dark:hover:bg-blue-800 hover:scale-110 hover:shadow-xl transform">
                <Icon icon="mdi:filter-variant" class="text-blue-600 dark:text-blue-300 transition-transform duration-300" :class="showFilterDropdown ? 'rotate-180' : ''" width="28" height="28" />
            </button>
            <!-- Dropdown Filter Bar -->
            <div v-if="showFilterDropdown" ref="filterDropdownRef" class="absolute right-0 mt-2 z-50 bg-white/90 dark:bg-gray-800/90 rounded-xl shadow-xl p-4 w-96 max-w-[95vw] flex flex-col gap-3 border border-blue-100 dark:border-gray-600 animate-slide-in">
                <!-- Refresh Button at Top Right -->
                <div class="flex justify-end mb-2">
                    <button @click="resetFilter" class="flex items-center justify-center transition border-none rounded-full h-8 w-8 hover:bg-blue-200 dark:hover:bg-blue-700" title="รีเซ็ตตัวกรอง">
                        <Icon icon="mdi:refresh" class="text-blue-800 dark:text-blue-300 hover:text-blue-600 dark:hover:text-blue-200" width="20" height="20" />
                    </button>
                </div>
                <div class="flex flex-col gap-3">
                    <div class="flex items-center min-w-0 gap-3 px-2 py-1 border-b border-blue-100 dark:border-gray-600">
                        <Icon icon="mdi:magnify" class="text-blue-800 dark:text-blue-300" width="40" height="40" />
                        <div class="relative w-full">
                            <form @submit.prevent style="width: 100%">
                                <input v-model="searchQuery" class="flex-1 w-full min-w-0 pl-3 text-gray-900 dark:text-gray-100 placeholder-transparent border border-blue-400 dark:border-blue-500 rounded-lg shadow h-9 bg-white/80 dark:bg-gray-700/80 focus:ring-0 focus:outline-none dark:focus:ring-blue-500" />
                                <button type="submit" style="display: none"></button>
                            </form>
                            <div v-if="!searchQuery" class="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none w-[calc(100%-2.5rem)] overflow-hidden">
                                <span class="block text-sm text-gray-400 dark:text-gray-200 animate-marquee whitespace-nowrap"> ค้นหาเลขนิสิต 4 ตัวท้าย หรือ เลขที่นั่ง... </span>
                            </div>
                        </div>
                        <select v-model="searchType" class="h-9 bg-white/80 dark:bg-gray-700/80 border border-blue-400 dark:border-blue-500 rounded-lg shadow focus:ring-0 focus:outline-none text-gray-900 dark:text-gray-100 font-semibold px-2 w-auto max-w-[120px]">
                            <option value="nisit4">เลขนิสิต 4 ตัวท้าย</option>
                            <option value="seat">เลขที่นั่ง</option>
                        </select>
                    </div>
                    <div
                        v-if="searchMessage"
                        :class="[
                            'flex items-center w-full justify-center gap-2 mt-2 mb-3 px-4 py-2 rounded-xl text-base font-semibold shadow',
                            searchMessage.includes('ไม่พบ') ? 'bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-700' : 'bg-green-100 dark:bg-green-900/20 text-green-900 dark:text-green-300 border border-green-300 dark:border-green-700'
                        ]"
                    >
                        <Icon :icon="searchMessage.includes('ไม่พบ') ? 'mdi:alert-circle-outline' : 'mdi:check-circle-outline'" :class="searchMessage.includes('ไม่พบ') ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'" width="24" height="24" />
                        <span class="whitespace-pre-line">{{ searchMessage }}</span>
                    </div>
                    <div class="flex items-center gap-2 px-2 py-1 border-b border-blue-100 dark:border-gray-600">
                        <Icon icon="mdi:account-check" class="text-blue-800 dark:text-blue-300" width="20" height="20" />
                        <div class="relative w-full">
                            <select
                                v-model="verifiedFilter"
                                class="w-full h-10 pl-4 pr-10 font-semibold text-blue-700 dark:text-blue-300 transition border border-blue-200 dark:border-gray-600 rounded-lg shadow appearance-none bg-white/80 dark:bg-gray-700/80 focus:ring-2 focus:ring-blue-400 dark:focus:ring-blue-500 focus:outline-none"
                            >
                                <option value="all">ทั้งหมด</option>
                                <option value="1">รายงานตัวแล้ว</option>
                                <option value="0">ยังไม่รายงานตัว</option>
                                <option value="2">เข้าหอประชุมเรียบร้อยแล้ว</option>
                                <option value="unknown">ไม่ทราบสถานะ</option>
                            </select>
                            <span class="absolute text-blue-400 dark:text-blue-300 -translate-y-1/2 pointer-events-none right-3 top-1/2">
                                <Icon icon="mdi:chevron-down" width="20" height="20" />
                            </span>
                        </div>
                    </div>
                    <div class="flex items-center gap-2 px-2 py-1 border-b border-blue-100 dark:border-gray-600">
                        <Icon icon="mdi:school" class="text-blue-800 dark:text-blue-300" width="20" height="20" />
                        <div class="relative w-full">
                            <select
                                v-model="selectedDegree"
                                class="w-full h-10 pl-4 pr-10 font-semibold text-blue-700 dark:text-blue-300 transition border border-blue-200 dark:border-gray-600 rounded-lg shadow appearance-none bg-white/80 dark:bg-gray-700/80 focus:ring-2 focus:ring-blue-400 dark:focus:ring-blue-500 focus:outline-none"
                            >
                                <option value="">ทุกคณะ</option>
                                <option v-for="d in degreeList" :key="d" :value="d">{{ d }}</option>
                            </select>
                            <span class="absolute text-blue-400 dark:text-blue-300 -translate-y-1/2 pointer-events-none right-3 top-1/2">
                                <Icon icon="mdi:chevron-down" width="20" height="20" />
                            </span>
                        </div>
                    </div>

                    <!-- Filter Chips -->
                    <!-- ลบ searchMessage ออกจาก filter chips -->
                    <div v-if="activeFilters.length > 0" class="flex flex-wrap justify-end gap-2 mt-4">
                        <span v-for="f in activeFilters" :key="f.key" class="flex items-center px-2 py-1 text-blue-800 dark:text-blue-300 bg-blue-100 dark:bg-blue-900/30 rounded-full">
                            {{ f.label }}
                            <button @click="removeFilter(f.key)" class="ml-1 text-blue-500 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-200">&times;</button>
                        </span>
                    </div>


                </div>
            </div>
        </div>
        <!-- Seat Layout -->
        <div v-if="loading" class="grid grid-cols-5 gap-4 p-4 animate-pulse">
            <Skeleton v-for="n in 10" :key="n" width="100%" height="4rem" />
        </div>
        <div v-else class="overflow-auto pt-9 animate-fade-in">
            <div class="flex flex-col gap-4">
                <div v-for="(row, rowIdx) in seatRows" :key="rowIdx" class="flex items-center mb-2 animate-slide-up" :style="{ animationDelay: `${rowIdx * 0.1}s` }">
                    <div class="flex-shrink-0 w-24 pr-2 text-xs font-bold text-right text-gray-300">
                        <span class="bg-blue-100 dark:bg-blue-900 border border-blue-400 dark:border-blue-600 rounded px-2 py-1 text-blue-800 dark:text-blue-200 min-w-[4.5rem] transition-all duration-300 hover:scale-105">แถว A{{ rowIdx + 1 }}</span>
                    </div>
                    <!-- ฝั่งซ้าย: 0-34 -->
                    <div class="flex gap-2">
                        <template v-for="(item, i) in buildSidesWithPillars(row).left" :key="i">
                            <div
                                v-if="item.type === 'pillar'"
                                class="flex items-center justify-center text-xs font-bold text-yellow-800 dark:text-yellow-200 bg-yellow-200 dark:bg-yellow-800 border border-yellow-400 dark:border-yellow-600 rounded"
                                :style="item.length > 1 ? { gridColumn: `span ${item.length} / span ${item.length}`, width: `calc(1.5rem * ${item.length})` } : { width: '2.25rem' }"
                            >
                                เสา
                            </div>
                            <div
                                v-else-if="item.type === 'person'"
                                class="flex flex-col items-center cursor-pointer transform transition-all duration-200 hover:scale-110 hover:shadow-lg animate-chair-hover"
                                :title="item.data.name"
                                @click="showPersonDetail(item.data)"
                                :class="isHighlighted(item.data) ? 'ring-4 ring-yellow-400 ring-offset-2 rounded-lg animate-pulse' : ''"
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
                    <div class="flex-shrink-0 w-24 pl-3 text-xs font-bold text-left text-gray-300">
                        <span class="bg-blue-100 dark:bg-blue-900 border border-blue-400 dark:border-blue-600 rounded px-2 py-1 text-blue-800 dark:text-blue-200 min-w-[4.5rem] transition-all duration-300 hover:scale-105">แถว A{{ rowIdx + 1 }}</span>
                    </div>

                    <!-- ช่องว่างตรงกลาง (mx-12) -->
                    <div class="mx-12"></div>

                    <div class="flex-shrink-0 w-24 pr-3 text-xs font-bold text-right text-gray-300">
                        <span class="bg-blue-100 dark:bg-blue-900 border border-blue-400 dark:border-blue-600 rounded px-2 py-1 text-blue-800 dark:text-blue-200 min-w-[4.5rem] transition-all duration-300 hover:scale-105">แถว B{{ rowIdx + 1 }}</span>
                    </div>

                    <!-- ฝั่งขวา: 35-69 -->
                    <div class="flex gap-2">
                        <template v-for="(item, i) in buildSidesWithPillars(row).right" :key="i">
                            <div
                                v-if="item.type === 'pillar'"
                                class="flex items-center justify-center text-xs font-bold text-yellow-800 dark:text-yellow-200 bg-yellow-200 dark:bg-yellow-800 border border-yellow-400 dark:border-yellow-600 rounded"
                                :style="item.length > 1 ? { gridColumn: `span ${item.length} / span ${item.length}`, width: `calc(1.5rem * ${item.length})` } : { width: '2.35rem' }"
                            >
                                เสา
                            </div>
                            <div
                                v-else-if="item.type === 'person'"
                                class="flex flex-col items-center cursor-pointer transform transition-all duration-200 hover:scale-110 hover:shadow-lg animate-chair-hover"
                                :title="item.data.name"
                                @click="showPersonDetail(item.data)"
                                :class="isHighlighted(item.data) ? 'ring-4 ring-yellow-400 ring-offset-2 rounded-lg animate-pulse' : ''"
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
                        <span class="bg-blue-100 dark:bg-blue-900 border border-blue-400 dark:border-blue-600 rounded px-2 py-1 text-blue-800 dark:text-blue-200 min-w-[4.5rem] transition-all duration-300 hover:scale-105">แถว B{{ rowIdx + 1 }}</span>
                    </div>
                </div>
            </div>
        </div>
        <!-- Person Detail Dialog -->
        <Dialog v-model:visible="dialogVisible" header="" modal :closable="false" class="p-fluid max-w-lg w-[98vw] rounded-2xl shadow-2xl ring-2 ring-blue-200/60 backdrop-blur-xl animate-zoom-in" :dismissableMask="true" :closeOnEscape="true">
            <div v-if="selectedPerson" class="relative flex flex-col items-center p-0 shadow-xl bg-gradient-to-br from-white via-blue-50 to-indigo-100 dark:from-gray-800 dark:via-gray-700 dark:to-gray-600 rounded-2xl md:flex-row overflow-hidden">
                <!-- ปุ่มปิด -->
                <button @click="dialogVisible = false" class="absolute flex items-center justify-center w-10 h-10 text-gray-600 dark:text-gray-300 transition-all duration-300 rounded-full shadow-lg top-4 right-4 bg-white/90 dark:bg-gray-800/90 hover:bg-red-100 dark:hover:bg-red-900/30 hover:text-red-600 dark:hover:text-red-400 hover:scale-110 transform z-10" aria-label="ปิด">
                    <Icon icon="mdi:close" width="20" height="20" />
                </button>
                
                <!-- Avatar Section -->
                <div class="flex flex-col items-center justify-center flex-shrink-0 p-8 bg-gradient-to-br from-blue-100 to-indigo-200 dark:from-blue-900/50 dark:to-indigo-800/50">
                    <div class="relative">
                        <div class="w-24 h-24 bg-gradient-to-br from-blue-400 to-indigo-500 dark:from-blue-500 dark:to-indigo-600 rounded-full flex items-center justify-center shadow-lg animate-pulse">
                            <Icon icon="mdi:account-circle" class="text-white" width="60" height="60" />
                        </div>
                        <div class="absolute -bottom-2 -right-2 w-8 h-8 rounded-full flex items-center justify-center shadow-lg" :class="{
                            'bg-green-500': selectedPerson.verified === 1,
                            'bg-yellow-500': selectedPerson.verified === 2,
                            'bg-red-500': selectedPerson.verified === 0,
                            'bg-gray-500': ![0, 1, 2].includes(selectedPerson.verified)
                        }">
                            <Icon :icon="selectedPerson.verified === 1 ? 'mdi:check' : 
                                         selectedPerson.verified === 2 ? 'mdi:account-check' : 
                                         selectedPerson.verified === 0 ? 'mdi:close' : 
                                         'mdi:help'" class="text-white" width="16" height="16" />
                        </div>
                    </div>
                    <div class="mt-4 text-center">
                        <div class="text-sm font-semibold text-blue-700 dark:text-blue-300">สถานะ</div>
                        <div class="text-xs font-bold" :class="{
                            'text-green-600 dark:text-green-400': selectedPerson.verified === 1,
                            'text-yellow-600 dark:text-yellow-400': selectedPerson.verified === 2,
                            'text-red-600 dark:text-red-400': selectedPerson.verified === 0,
                            'text-gray-600 dark:text-gray-400': ![0, 1, 2].includes(selectedPerson.verified)
                        }">
                            {{ selectedPerson.verified === 1 ? 'รายงานตัวแล้ว' : 
                               selectedPerson.verified === 2 ? 'เข้าหอประชุมแล้ว' : 
                               selectedPerson.verified === 0 ? 'ยังไม่รายงานตัว' : 
                               'ไม่ทราบสถานะ' }}
                        </div>
                    </div>
                </div>
                
                <!-- ข้อมูล Section -->
                <div class="flex-1 p-8 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm">
                    <div class="mb-6">
                        <div class="text-3xl font-bold text-gray-900 dark:text-white animate-fade-in mb-2">{{ selectedPerson.name }}</div>
                        <div class="w-16 h-1 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full"></div>
                    </div>
                    
                    <div class="space-y-4">
                        <div class="flex items-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-700 animate-fade-in" style="animation-delay: 0.1s">
                            <Icon icon="mdi:card-account-details" class="text-blue-600 dark:text-blue-400 mr-3" width="20" height="20" />
                            <div>
                                <div class="text-xs text-blue-600 dark:text-blue-400 font-medium">รหัสนิสิต</div>
                                <div class="text-sm font-bold text-gray-900 dark:text-white">{{ selectedPerson.nisit }}</div>
                            </div>
                        </div>
                        
                        <div class="flex items-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-700 animate-fade-in" style="animation-delay: 0.2s">
                            <Icon icon="mdi:school" class="text-green-600 dark:text-green-400 mr-3" width="20" height="20" />
                            <div>
                                <div class="text-xs text-green-600 dark:text-green-400 font-medium">คณะ</div>
                                <div class="text-sm font-bold text-gray-900 dark:text-white">{{ selectedPerson.degree }}</div>
                            </div>
                        </div>
                        
                        <div class="flex items-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-700 animate-fade-in" style="animation-delay: 0.3s">
                            <Icon icon="mdi:chair" class="text-purple-600 dark:text-purple-400 mr-3" width="20" height="20" />
                            <div>
                                <div class="text-xs text-purple-600 dark:text-purple-400 font-medium">ที่นั่ง</div>
                                <div class="text-sm font-bold text-gray-900 dark:text-white">เลขที่ {{ selectedPerson.seat }}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </Dialog>
        
                <!-- Mini Map Overview with Statistics from Filter -->
        <div v-if="showMiniMap" class="fixed bottom-6 right-6 z-50">
            <div class="flex gap-4">
                <!-- Statistics Panel (Left Side) - Moved from Filter -->
                <div class="bg-white/30 dark:bg-gray-800/30 rounded-2xl shadow-2xl border border-white/50 dark:border-gray-600/50 backdrop-blur-xl p-4 w-64 h-fit">
                    <!-- Header -->
                    <div class="flex items-center gap-3 mb-4">
                        <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                            <Icon icon="mdi:chart-line" class="text-white" width="20" height="20" />
                        </div>
                        <div>
                            <h3 class="text-lg font-bold text-gray-800 dark:text-white">สถิติการรายงานตัว</h3>
                            <p class="text-xs text-gray-500 dark:text-gray-400">สรุปสถานะที่นั่ง</p>
                        </div>
                    </div>
                    
                    <!-- Statistics Grid -->
                    <div class="grid grid-cols-2 gap-3 mb-3">
                        <!-- Total -->
                        <div class="text-center p-2 bg-white/80 dark:bg-gray-700/80 rounded-lg border border-blue-200 dark:border-gray-600 transform transition-all duration-300 hover:scale-105 hover:shadow-md">
                            <div class="text-xl font-bold text-blue-600 dark:text-blue-400 animate-pulse">{{ statistics.total }}</div>
                            <div class="text-xs text-blue-500 dark:text-blue-300">ทั้งหมด</div>
                        </div>
                        <!-- Reported -->
                        <div class="text-center p-2 bg-white/80 dark:bg-gray-700/80 rounded-lg border border-green-200 dark:border-green-700 transform transition-all duration-300 hover:scale-105 hover:shadow-md">
                            <div class="text-xl font-bold text-green-600 dark:text-green-400 animate-pulse">{{ statistics.reported }}</div>
                            <div class="text-xs text-green-500 dark:text-green-300">รายงานตัวแล้ว</div>
                            <div class="text-xs text-green-500 dark:text-green-300">({{ statistics.reportedPercentage }}%)</div>
                        </div>
                        <!-- In Hall -->
                        <div class="text-center p-2 bg-white/80 dark:bg-gray-700/80 rounded-lg border border-yellow-200 dark:border-yellow-700 transform transition-all duration-300 hover:scale-105 hover:shadow-md">
                            <div class="text-xl font-bold text-yellow-600 dark:text-yellow-400 animate-pulse">{{ statistics.inHall }}</div>
                            <div class="text-xs text-yellow-500 dark:text-yellow-300">เข้าหอประชุม</div>
                            <div class="text-xs text-yellow-500 dark:text-yellow-300">({{ statistics.inHallPercentage }}%)</div>
                        </div>
                        <!-- Not Reported -->
                        <div class="text-center p-2 bg-white/80 dark:bg-gray-700/80 rounded-lg border border-red-200 dark:border-red-700 transform transition-all duration-300 hover:scale-105 hover:shadow-md">
                            <div class="text-xl font-bold text-red-600 dark:text-red-400 animate-pulse">{{ statistics.notReported }}</div>
                            <div class="text-xs text-red-500 dark:text-red-300">ยังไม่รายงาน</div>
                            <div class="text-xs text-red-500 dark:text-red-300">({{ statistics.notReportedPercentage }}%)</div>
                        </div>
                    </div>
                    
                    <!-- Progress Bar -->
                    <div class="mt-3">
                        <div class="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
                            <span>ความคืบหน้า</span>
                            <span>{{ statistics.reportedPercentage }}%</span>
                        </div>
                        <div class="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                            <div 
                                class="bg-gradient-to-r from-green-500 to-blue-500 dark:from-green-400 dark:to-blue-400 h-2 rounded-full transition-all duration-500 ease-out animate-pulse"
                                :style="{ width: `${statistics.reportedPercentage}%` }"
                            ></div>
                        </div>
                    </div>
                </div>
                
                <!-- Mini Map Panel (Right Side) -->
                <div class="bg-white/30 dark:bg-gray-800/30 rounded-2xl shadow-2xl border border-white/50 dark:border-gray-600/50 backdrop-blur-xl p-4 max-w-lg">
                    <!-- Header -->
                    <div class="flex items-center justify-between mb-4">
                        <div class="flex items-center gap-3">
                            <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                                <Icon icon="mdi:map-marker" class="text-white" width="20" height="20" />
                            </div>
                            <div>
                                <h3 class="text-lg font-bold text-gray-800 dark:text-white">แผนที่ย่อ</h3>
                                <p class="text-xs text-gray-500 dark:text-gray-400">คลิกเพื่อนำทางไปยังที่นั่ง</p>
                            </div>
                        </div>
                        <button @click="showMiniMap = false" class="w-8 h-8 bg-red-100 dark:bg-red-900/30 hover:bg-red-200 dark:hover:bg-red-800/50 text-red-600 dark:text-red-400 rounded-full flex items-center justify-center transition-all duration-300 hover:scale-110">
                            <Icon icon="mdi:close" width="16" height="16" />
                        </button>
                    </div>
                    
                    <!-- Mini Map Grid -->
                    <div class="relative bg-white/50 dark:bg-gray-800/50 rounded-xl border border-white/50 dark:border-gray-600/50 overflow-hidden backdrop-blur-sm">
                        <!-- Header with Row Labels -->
                        <div class="bg-gray-50/80 dark:bg-gray-700/80 px-3 py-2 border-b border-white/30 dark:border-gray-600/30 backdrop-blur-sm">
                            <div class="flex justify-center gap-3 text-xs font-semibold text-gray-600 dark:text-gray-300">
                                <span class="w-28 text-center -ml-4">ฝั่ง A</span>
                                <span class="w-6 text-center -ml-2">กลาง</span>
                                <span class="w-28 text-center">ฝั่ง B</span>
                            </div>
                        </div>
                        
                        <!-- Scrollable Grid -->
                        <div class="p-3 max-h-56 overflow-y-auto">
                            <div v-for="(row, rowIdx) in seatRows" :key="rowIdx" class="mb-1">
                                <!-- Row Label -->
                                <div class="flex justify-center mb-1">
                                    <span class="text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-600 px-1 py-0.5 rounded-full">
                                        แถว {{ rowIdx + 1 }}
                                    </span>
                                </div>
                                
                                <!-- Seat Grid -->
                                <div class="flex justify-center gap-3">
                                    <!-- ฝั่งซ้าย (A) -->
                                    <div class="bg-gray-50/70 dark:bg-gray-700/70 rounded-lg p-1 border border-white/30 dark:border-gray-600/30 backdrop-blur-sm">
                                        <div class="flex gap-0.5 flex-wrap" style="width: 120px;">
                                            <div
                                                v-for="(item, colIdx) in row.slice(0, 35)"
                                                :key="colIdx"
                                                :class="[
                                                    'w-2 h-2 rounded-sm cursor-pointer transition-all duration-300 hover:scale-125 hover:shadow-md border border-gray-200 dark:border-gray-600',
                                                    item.type === 'person' ? getMiniMapColor(item.data.verified) : 
                                                    item.type === 'pillar' ? 'bg-yellow-400 dark:bg-yellow-500' : 'bg-gray-300 dark:bg-gray-600'
                                                ]"
                                                @click="item.type === 'person' ? clickMiniMapSimple(rowIdx, colIdx, 'A') : null"
                                                :title="item.type === 'person' ? `แถว A${rowIdx + 1} ที่นั่ง ${item.data.seat}` : 
                                                       item.type === 'pillar' ? 'เสา' : 'ว่าง'"
                                            ></div>
                                        </div>
                                    </div>
                                    
                                    <!-- ช่องว่างตรงกลาง -->
                                    <div class="w-4 bg-gradient-to-b from-blue-200 to-indigo-200 dark:from-blue-800 dark:to-indigo-800 rounded-lg flex items-center justify-center">
                                        <div class="w-1 h-6 bg-blue-400 dark:bg-blue-300 rounded-full"></div>
                                    </div>
                                    
                                    <!-- ฝั่งขวา (B) -->
                                    <div class="bg-gray-50/70 dark:bg-gray-700/70 rounded-lg p-1 border border-white/30 dark:border-gray-600/30 backdrop-blur-sm">
                                        <div class="flex gap-0.5 flex-wrap" style="width: 120px;">
                                            <div
                                                v-for="(item, colIdx) in row.slice(35, 70)"
                                                :key="colIdx + 35"
                                                :class="[
                                                    'w-2 h-2 rounded-sm cursor-pointer transition-all duration-300 hover:scale-125 hover:shadow-md border border-gray-200 dark:border-gray-600',
                                                    item.type === 'person' ? getMiniMapColor(item.data.verified) : 
                                                    item.type === 'pillar' ? 'bg-yellow-400 dark:bg-yellow-500' : 'bg-gray-300 dark:bg-gray-600'
                                                ]"
                                                @click="item.type === 'person' ? clickMiniMapSimple(rowIdx, colIdx, 'B') : null"
                                                :title="item.type === 'person' ? `แถว B${rowIdx + 1} ที่นั่ง ${item.data.seat}` : 
                                                       item.type === 'pillar' ? 'เสา' : 'ว่าง'"
                                            ></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Legend -->
                        <div class="bg-gray-50/80 dark:bg-gray-700/80 p-3 border-t border-white/30 dark:border-gray-600/30 backdrop-blur-sm">
                            <div class="flex items-center justify-between text-xs">
                                <div class="flex items-center gap-3">
                                    <div class="flex items-center gap-1">
                                        <div class="w-2 h-2 bg-green-500 rounded-sm"></div>
                                        <span class="text-gray-600 dark:text-gray-300">รายงานแล้ว</span>
                                    </div>
                                    <div class="flex items-center gap-1">
                                        <div class="w-2 h-2 bg-red-500 rounded-sm"></div>
                                        <span class="text-gray-600 dark:text-gray-300">ยังไม่รายงาน</span>
                                    </div>
                                    <div class="flex items-center gap-1">
                                        <div class="w-2 h-2 bg-yellow-400 rounded-sm"></div>
                                        <span class="text-gray-600 dark:text-gray-300">เข้าหอประชุม</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Mini Map Toggle Button -->
        <div v-if="!showMiniMap" class="fixed bottom-6 right-6 z-50">
            <button @click="showMiniMap = true" class="p-3 bg-blue-500 hover:bg-blue-600 text-white rounded-full shadow-lg transition-all duration-300 hover:scale-110">
                <Icon icon="mdi:map" width="20" height="20" />
            </button>
        </div>
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

@keyframes slide-in {
    from {
        opacity: 0;
        transform: translateX(100%) scale(0.95);
    }
    to {
        opacity: 1;
        transform: translateX(0) scale(1);
    }
}
.animate-slide-in {
    animation: slide-in 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes zoom-in {
    from {
        opacity: 0;
        transform: scale(0.8);
    }
    to {
        opacity: 1;
        transform: scale(1);
    }
}
.animate-zoom-in {
    animation: zoom-in 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes chair-hover {
    0% {
        transform: scale(1);
    }
    50% {
        transform: scale(1.1);
    }
    100% {
        transform: scale(1);
    }
}
.animate-chair-hover {
    animation: chair-hover 0.3s ease-in-out;
}

@keyframes slide-up {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
.animate-slide-up {
    animation: slide-up 0.5s ease-out;
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