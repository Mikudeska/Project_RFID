<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { Icon } from '@iconify/vue';
import Dialog from 'primevue/dialog';
import Toast from 'primevue/toast';
import Skeleton from 'primevue/skeleton';
import Badge from 'primevue/badge';
import { useToast } from 'primevue/usetoast';

const TOTAL_SEATS = 7000;
const COLS = 60;

// ระบุเสาว่าอยู่คอลัมน์ใดของแถวไหน
const ROW_PILLARS = {
    3: [4, 54],      // แถว 4: เสาที่คอลัมน์ 5 และ 55 (index เริ่มที่ 0)
    16: [4, 25, 54], // แถว 17: เสาที่คอลัมน์ 5, 30, 55
    29: [4, 29, 54], // แถว 30: เสาที่คอลัมน์ 5, 30, 55
};

const persons = ref([]);
const loading = ref(false);
const searchQuery = ref('');
const verifiedFilter = ref('all');
const showFilters = ref(false);
const dialogVisible = ref(false);
const selectedPerson = ref({});
const toast = useToast();

async function fetchPersons() {
    loading.value = true;
    try {
        const { data } = await axios.get('http://127.0.0.1:8000/api/person/');
        persons.value = data
            .map(p => ({ ...p, seat: Number(p.seat) }))
            .filter(p => p.seat >= 1 && p.seat <= TOTAL_SEATS);
    } catch (e) {
        console.error(e);
    } finally {
        loading.value = false;
    }
}

const filteredPersons = computed(() => {
    let list = [...persons.value];
    if (verifiedFilter.value === 'verified')
        list = list.filter(p => p.verified === 1);
    else if (verifiedFilter.value === 'unverified')
        list = list.filter(p => p.verified === 0);
    else if (verifiedFilter.value === 'unknown')
        list = list.filter(p => p.verified !== 0 && p.verified !== 1);

    if (searchQuery.value) {
        const q = searchQuery.value.toLowerCase();
        list = list.filter(
            p =>
                p.name?.toLowerCase().includes(q) ||
                p.nisit?.includes(q) ||
                p.degree?.toLowerCase().includes(q) ||
                p.seat.toString().includes(q)
        );
        clearTimeout(window._toastTimer);
        window._toastTimer = setTimeout(() => {
            toast.add({
                severity: 'info',
                summary: 'ผลการค้นหา',
                detail: `พบ ${list.length} รายการ`,
                life: 2000,
            });
        }, 300);
    }
    return list.sort((a, b) => a.seat - b.seat);
});

const ROWS_COUNT = Math.ceil(TOTAL_SEATS / COLS);
const seatsGrid = computed(() => {
  const rows = [];
  const list = filteredPersons.value;
  let idx = 0;

  for (let r = 0; r < ROWS_COUNT; r++) {
    const row = [];
    const pillars = ROW_PILLARS[r] || [];

    for (let c = 0; c < COLS; c++) {
      if (pillars.includes(c)) {
        // วางเสา แต่ไม่เพิ่ม idx
        row.push({ type: 'pillar' });
      } else {
        // ถ้ายังมี student ให้ใส่ ถ้าไม่ก็ empty
        if (idx < list.length) {
          row.push({ type: 'student', data: list[idx++] });
        } else {
          row.push({ type: 'empty' });
        }
      }
    }

    rows.push(row);
  }

  return rows;
});


function showPersonDetail(p) {
    selectedPerson.value = p;
    dialogVisible.value = true;
}

function buttonClass(status) {
    return [
        'px-3 py-1 rounded-full text-sm font-semibold transition',
        verifiedFilter.value === status
            ? 'bg-blue-600 text-white shadow'
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300',
    ].join(' ');
}

onMounted(fetchPersons);
</script>


<template>
    <div>
        <Toast />

        <!-- Search Bar -->
        <div class="relative my-4 sticky top-0 bg-gradient-to-br from-blue-900 to-blue-800 z-10">
            <Icon icon="material-symbols:search"
                class="absolute text-2xl text-blue-300 -translate-y-1/2 left-4 top-1/2" />
            <input v-model="searchQuery" type="text" placeholder="ค้นหา (ชื่อ, ID, รหัสนิสิต, ที่นั่ง...)"
                class="w-full h-12 pl-12 pr-4 border border-blue-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white" />
        </div>

        <!-- Filter Speed Dial -->
        <div class="fixed z-50 flex flex-col items-end space-y-3 bottom-6 right-6">
            <transition-group name="fade" tag="div" v-if="showFilters">
                <button key="all" @click="verifiedFilter = 'all'" :class="buttonClass('all')">
                    <Badge value="📋" severity="info" class="mr-1" /> ทั้งหมด
                </button>
                <button key="verified" @click="verifiedFilter = 'verified'" :class="buttonClass('verified')">
                    <Badge value="✅" /> รายงานตัว
                </button>
                <button key="unverified" @click="verifiedFilter = 'unverified'" :class="buttonClass('unverified')">
                    <Badge value="❌" /> ยังไม่รายงาน
                </button>
                <button key="unknown" @click="verifiedFilter = 'unknown'" :class="buttonClass('unknown')">
                    <Badge value="❓" severity="warning" /> ไม่ทราบสถานะ
                </button>
            </transition-group>
            <button @click="showFilters = !showFilters"
                class="p-4 text-white transition-transform rounded-full shadow-lg bg-gradient-to-br from-blue-500 to-indigo-600 hover:scale-105">
                <Icon icon="material-symbols:filter-list" class="text-2xl" />
            </button>
        </div>

        <!-- Seat Grid -->
        <div v-if="loading" class="grid grid-cols-5 gap-4 p-4">
            <Skeleton v-for="n in 10" :key="n" width="100%" height="4rem" />
        </div>
        <div v-else
            class="relative max-w-full p-4 overflow-auto rounded-lg shadow-inner bg-gradient-to-br from-blue-900 to-blue-800">
            <div v-for="(row, r) in seatsGrid" :key="r" class="grid grid-cols-[4rem_1fr] items-center mb-2 h-16">
                <!-- Column 1: Row label -->
                <div
                    class="flex items-center justify-center h-full bg-purple-600 text-white font-bold rounded-l-xl shadow">
                    แถว {{ r + 1 }}
                </div>

                <!-- Column 2: Seats with center aisle -->
                <div class="flex items-center h-full  pl-4">
                    <!-- Left 30 seats -->
                    <div class="flex space-x-1">
                        <template v-for="(cell, c) in row.slice(0, 30)" :key="c">
                            <div v-if="cell.type === 'pillar'"
                                class="flex-none flex items-center justify-center w-[7.25rem] h-full border-2 border-yellow-400 rounded-lg bg-yellow-100 shadow">
                                <span class="text-xs font-bold text-yellow-800">เสา</span>
                            </div>
                            <div v-else-if="cell.type === 'student'"
                                class="flex flex-col items-center justify-center h-full w-9">
                                <Icon icon="material-symbols:event-seat"
                                    class="text-2xl rounded shadow cursor-pointer hover:scale-110 hover:shadow-lg"
                                    :class="cell.data.verified === 1 ? 'text-green-500' : cell.data.verified === 0 ? 'text-red-500' : 'text-gray-400'"
                                    v-tooltip="cell.data.name" @click="showPersonDetail(cell.data)" />
                                <div class="text-[10px] mt-1" v-tooltip="'ที่นั่ง ' + cell.data.seat">
                                    {{ cell.data.seat }}
                                </div>
                            </div>
                            <div v-else class="flex flex-col items-center justify-center h-full w-9 text-gray-400">
                                <div class="w-6 h-6 text-xs">–</div>
                            </div>
                        </template>
                    </div>

                    <!-- Center aisle -->
                    <div class="flex-none w-8 mx-4 border-l-2 border-yellow-400"></div>

                    <!-- Right 30 seats -->
                    <div class="flex space-x-1">
                        <template v-for="(cell, c) in row.slice(30, 60)" :key="c">
                            <div v-if="cell.type === 'pillar'"
                                class="flex-none flex items-center justify-center w-[7.75rem] h-full border-2 border-yellow-400 rounded-lg bg-yellow-100 shadow">
                                <span class="text-xs font-bold text-yellow-800">เสา</span>
                            </div>
                            <div v-else-if="cell.type === 'student'"
                                class="flex flex-col items-center justify-center h-full w-9">
                                <Icon icon="material-symbols:event-seat"
                                    class="text-2xl rounded shadow cursor-pointer hover:scale-110 hover:shadow-lg"
                                    :class="cell.data.verified === 1 ? 'text-green-500' : cell.data.verified === 0 ? 'text-red-500' : 'text-gray-400'"
                                    v-tooltip="cell.data.name" @click="showPersonDetail(cell.data)" />
                                <div class="text-[10px] mt-1" v-tooltip="'ที่นั่ง ' + cell.data.seat">
                                    {{ cell.data.seat }}
                                </div>
                            </div>
                            <div v-else class="flex flex-col items-center justify-center h-full w-9 text-gray-400">
                                <div class="w-6 h-6 text-xs">–</div>
                            </div>
                        </template>
                    </div>
                </div>
            </div>
        </div>

        <!-- Detail Dialog -->
        <Dialog v-model:visible="dialogVisible" header="รายละเอียดผู้เข้าร่วม" modal closable class="p-fluid">
            <!-- … Dialog content … -->
        </Dialog>
    </div>
</template>

<style scoped>
/* Scrollbar for overflow */
.pl-4::-webkit-scrollbar {
    height: 6px;
}

.pl-4::-webkit-scrollbar-thumb {
    background-color: rgba(255, 255, 255, 0.3);
    border-radius: 3px;
}

/* Dialog transition */
.p-dialog {
    transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-active,
.fade-leave-active {
    transition: all 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
    transform: translateY(5px);
}
</style>
