<script setup>
import { ref, computed, onMounted, watch, onBeforeUnmount} from 'vue';
import axios from 'axios';
import { Icon } from '@iconify/vue';
import Dialog from 'primevue/dialog';
import Toast from 'primevue/toast';
import Skeleton from 'primevue/skeleton';
import Badge from 'primevue/badge';
import { useToast } from 'primevue/usetoast';

const API_BASE = import.meta.env.VITE_API_BASE;

const TOTAL_SEATS = 7000;
const COLS = 60;
const ROWS_COUNT = Math.ceil(TOTAL_SEATS / COLS);

const persons = ref([]);
const loading = ref(false);
const searchQuery = ref('');
const verifiedFilter = ref('all');
const showFilters = ref(false);
const dialogVisible = ref(false);
const selectedPerson = ref({});
const toast = useToast();

function handleWsMessage(event) {
    const msg = event.detail.message;
    if (msg.action === 'update') {
        const index = persons.value.findIndex((p) => p.id === msg.id);
        if (index !== -1) {
            persons.value[index] = { ...persons.value[index], ...msg.fields };
        }
    }
}

onMounted(async () => {
    const { data } = await axios.get(`${API_BASE}/api/person/`);
    persons.value = data.map((p) => ({ ...p, seat: Number(p.seat) })).filter((p) => p.seat >= 1 && p.seat <= TOTAL_SEATS);
    window.addEventListener('ws-message', handleWsMessage);
});

onBeforeUnmount(() => {
    window.removeEventListener('ws-message', handleWsMessage);
});

async function fetchPersons() {
    loading.value = true;
    try {
        const { data } = await axios.get(`${API_BASE}/api/person/`);
        persons.value = data.map((p) => ({ ...p, seat: Number(p.seat) })).filter((p) => p.seat >= 1 && p.seat <= TOTAL_SEATS);
    } catch (e) {
        console.error(e);
    } finally {
        loading.value = false;
    }
}

const filteredPersons = computed(() => {
    let r = [...persons.value];
    if (verifiedFilter.value === 'verified') r = r.filter((p) => p.verified === 1);
    else if (verifiedFilter.value === 'unverified') r = r.filter((p) => p.verified === 0);
    else if (verifiedFilter.value === 'unknown') r = r.filter((p) => p.verified !== 0 && p.verified !== 1);

    if (searchQuery.value) {
        const q = searchQuery.value.toLowerCase();
        r = r.filter((p) => p.name?.toLowerCase().includes(q) || p.nisit?.includes(q) || p.degree?.toLowerCase().includes(q) || p.seat.toString().includes(q));
        clearTimeout(window._toastTimer);
        window._toastTimer = setTimeout(() => {
            toast.add({ severity: 'info', summary: 'ผลการค้นหา', detail: `พบ ${r.length} รายการ`, life: 2000 });
        }, 300);
    }
    return r;
});

watch(filteredPersons, () => {});

const seatsGrid = computed(() => {
    const rows = Array.from({ length: ROWS_COUNT }, () => Array.from({ length: COLS }, () => null));

    filteredPersons.value.forEach((p) => {
        let seat = p.seat;
        let ri, ci;

        if (seat >= 1777) {
            // แถวที่ 31 เริ่มจาก seat 1777
            const offset = seat - 1777;
            ri = 30 + Math.floor(offset / COLS); // แถว index 30 คือแถวที่ 31
            ci = offset % COLS;
        } else if (seat >= 1006) {
            // แถวที่ 18 เริ่มจาก seat 1006
            const offset = seat - 1006;
            ri = 17 + Math.floor(offset / COLS); // แถว index 17 คือแถวที่ 18
            ci = offset % COLS;
        } else if (seat >= 235) {
            // แถวที่ 5 เริ่มจาก seat 235
            const offset = seat - 235;
            ri = 4 + Math.floor(offset / COLS); // แถว index 4 คือแถวที่ 5
            ci = offset % COLS;
        } else {
            // ก่อนหน้า seat 235
            const idx = seat - 1;
            ri = Math.floor(idx / COLS);
            ci = idx % COLS;
        }

        if (rows[ri] && !rows[ri][ci]) {
            rows[ri][ci] = p;
        }
    });

    return rows;
});

function showPersonDetail(person) {
    selectedPerson.value = person;
    dialogVisible.value = true;
}

function buttonClass(status) {
    return ['px-3 py-1 rounded-full text-sm font-semibold transition', verifiedFilter.value === status ? 'bg-blue-600 text-white shadow' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'].join(' ');
}

onMounted(fetchPersons);
</script>

<template>
    <div>
        <Toast />
        <!-- Search Bar -->
        <div class="relative my-4 sticky-top">
            <Icon icon="material-symbols:search" class="absolute text-2xl text-blue-500 -translate-y-1/2 left-4 top-1/2" />
            <input v-model="searchQuery" type="text" placeholder="ค้นหา (ชื่อ, ID, รหัสนิสิต, ที่นั่ง...)" class="w-full h-12 pl-12 pr-4 border border-blue-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>

        <!-- Filter Speed Dial -->
        <div class="fixed z-50 flex flex-col items-end space-y-3 bottom-6 right-6">
            <transition-group name="fade" tag="div" v-if="showFilters">
                <button key="all" @click="verifiedFilter = 'all'" :class="buttonClass('all')"><Badge value="📋" severity="info" class="mr-1" /> ทั้งหมด</button>
                <button key="verified" @click="verifiedFilter = 'verified'" :class="buttonClass('verified')"><Badge value="✅" /> รายงานตัว</button>
                <button key="unverified" @click="verifiedFilter = 'unverified'" :class="buttonClass('unverified')"><Badge value="❌" /> ยังไม่รายงาน</button>
                <button key="unknown" @click="verifiedFilter = 'unknown'" :class="buttonClass('unknown')"><Badge value="❓" severity="warning" /> ไม่ทราบสถานะ</button>
            </transition-group>
            <button @click="showFilters = !showFilters" class="p-4 text-white transition-transform rounded-full shadow-lg bg-gradient-to-br from-blue-500 to-indigo-600 hover:scale-105">
                <Icon icon="material-symbols:filter-list" class="text-2xl" />
            </button>
        </div>

        <!-- Seat Grid -->
        <div v-if="loading" class="grid grid-cols-5 gap-4 p-4"><Skeleton v-for="n in 10" :key="n" width="100%" height="4rem" /></div>
        <div v-else class="relative max-w-full p-4 overflow-auto rounded-lg shadow-inner card">
            <div v-for="(row, rowIndex) in seatsGrid" :key="rowIndex" class="relative h-16 mb-2">
                <!-- Label -->
                <div class="absolute left-0 flex items-center justify-between w-16 px-3 py-2 text-xs font-bold text-white -translate-y-1/2 bg-purple-600 shadow rounded-xl top-1/2">
                    <span>แถว</span><span>{{ rowIndex + 1 }}</span>
                </div>
                <div class="flex items-center h-full ml-16">
                    <template v-if="rowIndex === 3 || rowIndex === 16 || rowIndex === 29">
                        <!-- 👇 rowIndex 3: เสา 2 ต้น แบบเดิม -->
                        <template v-if="rowIndex === 3">
                            <!-- seats 181–186 -->
                            <div class="flex space-x-1">
                                <div v-for="(p, i) in row.slice(0, 6)" :key="i" class="flex flex-col items-center justify-center h-full w-9">
                                    <Icon
                                        v-if="p"
                                        icon="material-symbols:event-seat"
                                        class="text-2xl rounded shadow cursor-pointer hover:scale-110 hover:shadow-lg"
                                        :class="p.verified === 1 ? 'text-green-500' : p.verified === 0 ? 'text-red-500' : 'text-gray-400'"
                                        v-tooltip="p.name"
                                        @click="showPersonDetail(p)"
                                    />
                                    <div v-else class="w-6 h-6 text-xs text-gray-400">–</div>
                                    <div v-if="p" class="text-[10px] mt-1" v-tooltip="'ที่นั่ง ' + p.seat">{{ p.seat }}</div>
                                </div>
                            </div>

                            <!-- เสา 1 -->
                            <div class="flex-none flex items-center justify-center w-[7.75rem] h-full border-2 border-yellow-400 rounded-lg bg-yellow-100 shadow">
                                <span class="text-xs font-bold text-yellow-800">เสา</span>
                            </div>

                            <!-- seats 187–210 -->
                            <div class="flex space-x-1">
                                <div v-for="(p, i) in row.slice(6, 30)" :key="i" class="flex flex-col items-center justify-center h-full w-9">
                                    <Icon
                                        v-if="p"
                                        icon="material-symbols:event-seat"
                                        class="text-2xl rounded shadow cursor-pointer hover:scale-110 hover:shadow-lg"
                                        :class="p.verified === 1 ? 'text-green-500' : p.verified === 0 ? 'text-red-500' : 'text-gray-400'"
                                        v-tooltip="p.name"
                                        @click="showPersonDetail(p)"
                                    />
                                    <div v-else class="w-6 h-6 text-xs text-gray-400">–</div>
                                    <div v-if="p" class="text-[10px] mt-1" v-tooltip="'ที่นั่ง ' + p.seat">{{ p.seat }}</div>
                                </div>
                            </div>

                            <!-- spacer -->
                            <div class="flex-none w-16"></div>

                            <!-- seats 211–226 -->
                            <div class="flex space-x-1">
                                <div v-for="(p, i) in row.slice(30, 46)" :key="i" class="flex flex-col items-center justify-center h-full w-9">
                                    <Icon
                                        v-if="p"
                                        icon="material-symbols:event-seat"
                                        class="text-2xl rounded shadow cursor-pointer hover:scale-110 hover:shadow-lg"
                                        :class="p.verified === 1 ? 'text-green-500' : p.verified === 0 ? 'text-red-500' : 'text-gray-400'"
                                        v-tooltip="p.name"
                                        @click="showPersonDetail(p)"
                                    />
                                    <div v-else class="w-6 h-6 text-xs text-gray-400">–</div>
                                    <div v-if="p" class="text-[10px] mt-1" v-tooltip="'ที่นั่ง ' + p.seat">{{ p.seat }}</div>
                                </div>
                            </div>

                            <!-- เสา 2 -->
                            <div class="flex-none flex items-center justify-center w-[7.75rem] h-full border-2 border-yellow-400 rounded-lg bg-yellow-100 shadow">
                                <span class="text-xs font-bold text-yellow-800">เสา</span>
                            </div>

                            <!-- seats 227–234 -->
                            <div class="flex space-x-1">
                                <div v-for="(p, i) in row.slice(46, 54)" :key="i" class="flex flex-col items-center justify-center h-full w-9">
                                    <Icon
                                        v-if="p"
                                        icon="material-symbols:event-seat"
                                        class="text-2xl rounded shadow cursor-pointer hover:scale-110 hover:shadow-lg"
                                        :class="p.verified === 1 ? 'text-green-500' : p.verified === 0 ? 'text-red-500' : 'text-gray-400'"
                                        v-tooltip="p.name"
                                        @click="showPersonDetail(p)"
                                    />
                                    <div v-else class="w-6 h-6 text-xs text-gray-400">–</div>
                                    <div v-if="p" class="text-[10px] mt-1" v-tooltip="'ที่นั่ง ' + p.seat">{{ p.seat }}</div>
                                </div>
                            </div>
                        </template>

                        <!-- 👇 rowIndex 16: เสา 3 ต้น -->
                        <template v-else-if="rowIndex === 29">
                            <!-- seats 961–981 -->
                            <div class="flex space-x-1">
                                <div v-for="(p, i) in row.slice(0, 6)" :key="i" class="flex flex-col items-center justify-center h-full w-9">
                                    <Icon
                                        v-if="p"
                                        icon="material-symbols:event-seat"
                                        class="text-2xl rounded shadow cursor-pointer hover:scale-110 hover:shadow-lg"
                                        :class="p.verified === 1 ? 'text-green-500' : p.verified === 0 ? 'text-red-500' : 'text-gray-400'"
                                        v-tooltip="p.name"
                                        @click="showPersonDetail(p)"
                                    />
                                    <div v-else class="w-6 h-6 text-xs text-gray-400">–</div>
                                    <div v-if="p" class="text-[10px] mt-1" v-tooltip="'ที่นั่ง ' + p.seat">{{ p.seat }}</div>
                                </div>
                            </div>

                            <!-- เสา 1 -->
                            <div class="flex-none flex items-center justify-center w-[7.75rem] h-full border-2 border-yellow-400 rounded-lg bg-yellow-100 shadow">
                                <span class="text-xs font-bold text-yellow-800">เสา</span>
                            </div>

                            <!-- seats 982–1001 -->
                            <div class="flex space-x-1">
                                <div v-for="(p, i) in row.slice(6, 27)" :key="i" class="flex flex-col items-center justify-center h-full w-9">
                                    <Icon
                                        v-if="p"
                                        icon="material-symbols:event-seat"
                                        class="text-2xl rounded shadow cursor-pointer hover:scale-110 hover:shadow-lg"
                                        :class="p.verified === 1 ? 'text-green-500' : p.verified === 0 ? 'text-red-500' : 'text-gray-400'"
                                        v-tooltip="p.name"
                                        @click="showPersonDetail(p)"
                                    />
                                    <div v-else class="w-6 h-6 text-xs text-gray-400">–</div>
                                    <div v-if="p" class="text-[10px] mt-1" v-tooltip="'ที่นั่ง ' + p.seat">{{ p.seat }}</div>
                                </div>
                            </div>

                            <!-- เสา 2 -->
                            <div class="flex-none flex items-center justify-center w-[7.45rem] h-full border-2 border-yellow-400 rounded-lg bg-yellow-100 shadow">
                                <span class="text-xs font-bold text-yellow-800">เสา</span>
                            </div>

                            <!-- spacer -->
                            <div class="flex-none w-16"></div>

                            <!-- seats 1002–1016 -->
                            <div class="flex space-x-1">
                                <div v-for="(p, i) in row.slice(27, 43)" :key="i" class="flex flex-col items-center justify-center h-full w-9">
                                    <Icon
                                        v-if="p"
                                        icon="material-symbols:event-seat"
                                        class="text-2xl rounded shadow cursor-pointer hover:scale-110 hover:shadow-lg"
                                        :class="p.verified === 1 ? 'text-green-500' : p.verified === 0 ? 'text-red-500' : 'text-gray-400'"
                                        v-tooltip="p.name"
                                        @click="showPersonDetail(p)"
                                    />
                                    <div v-else class="w-6 h-6 text-xs text-gray-400">–</div>
                                    <div v-if="p" class="text-[10px] mt-1" v-tooltip="'ที่นั่ง ' + p.seat">{{ p.seat }}</div>
                                </div>
                            </div>

                            <!-- เสา 3 -->
                            <div class="flex-none flex items-center justify-center w-[7.75rem] h-full border-2 border-yellow-400 rounded-lg bg-yellow-100 shadow">
                                <span class="text-xs font-bold text-yellow-800">เสา</span>
                            </div>

                            <!-- seats 1017–1020 -->
                            <div class="flex space-x-1">
                                <div v-for="(p, i) in row.slice(43, 51)" :key="i" class="flex flex-col items-center justify-center h-full w-9">
                                    <Icon
                                        v-if="p"
                                        icon="material-symbols:event-seat"
                                        class="text-2xl rounded shadow cursor-pointer hover:scale-110 hover:shadow-lg"
                                        :class="p.verified === 1 ? 'text-green-500' : p.verified === 0 ? 'text-red-500' : 'text-gray-400'"
                                        v-tooltip="p.name"
                                        @click="showPersonDetail(p)"
                                    />
                                    <div v-else class="w-6 h-6 text-xs text-gray-400">–</div>
                                    <div v-if="p" class="text-[10px] mt-1" v-tooltip="'ที่นั่ง ' + p.seat">{{ p.seat }}</div>
                                </div>
                            </div>
                        </template>

                        <!-- 👇 rowIndex 16: เสา 3 ต้น -->
                        <template v-else-if="rowIndex === 16">
                            <!-- seats 961–981 -->
                            <div class="flex space-x-1">
                                <div v-for="(p, i) in row.slice(0, 6)" :key="i" class="flex flex-col items-center justify-center h-full w-9">
                                    <Icon
                                        v-if="p"
                                        icon="material-symbols:event-seat"
                                        class="text-2xl rounded shadow cursor-pointer hover:scale-110 hover:shadow-lg"
                                        :class="p.verified === 1 ? 'text-green-500' : p.verified === 0 ? 'text-red-500' : 'text-gray-400'"
                                        v-tooltip="p.name"
                                        @click="showPersonDetail(p)"
                                    />
                                    <div v-else class="w-6 h-6 text-xs text-gray-400">–</div>
                                    <div v-if="p" class="text-[10px] mt-1" v-tooltip="'ที่นั่ง ' + p.seat">{{ p.seat }}</div>
                                </div>
                            </div>

                            <!-- เสา 1 -->
                            <div class="flex-none flex items-center justify-center w-[7.75rem] h-full border-2 border-yellow-400 rounded-lg bg-yellow-100 shadow">
                                <span class="text-xs font-bold text-yellow-800">เสา</span>
                            </div>

                            <!-- seats 982–1001 -->
                            <div class="flex space-x-1">
                                <div v-for="(p, i) in row.slice(6, 27)" :key="i" class="flex flex-col items-center justify-center h-full w-9">
                                    <Icon
                                        v-if="p"
                                        icon="material-symbols:event-seat"
                                        class="text-2xl rounded shadow cursor-pointer hover:scale-110 hover:shadow-lg"
                                        :class="p.verified === 1 ? 'text-green-500' : p.verified === 0 ? 'text-red-500' : 'text-gray-400'"
                                        v-tooltip="p.name"
                                        @click="showPersonDetail(p)"
                                    />
                                    <div v-else class="w-6 h-6 text-xs text-gray-400">–</div>
                                    <div v-if="p" class="text-[10px] mt-1" v-tooltip="'ที่นั่ง ' + p.seat">{{ p.seat }}</div>
                                </div>
                            </div>

                            <!-- เสา 2 -->
                            <div class="flex-none flex items-center justify-center w-[7.45rem] h-full border-2 border-yellow-400 rounded-lg bg-yellow-100 shadow">
                                <span class="text-xs font-bold text-yellow-800">เสา</span>
                            </div>

                            <!-- spacer -->
                            <div class="flex-none w-16"></div>

                            <!-- seats 1002–1016 -->
                            <div class="flex space-x-1">
                                <div v-for="(p, i) in row.slice(27, 43)" :key="i" class="flex flex-col items-center justify-center h-full w-9">
                                    <Icon
                                        v-if="p"
                                        icon="material-symbols:event-seat"
                                        class="text-2xl rounded shadow cursor-pointer hover:scale-110 hover:shadow-lg"
                                        :class="p.verified === 1 ? 'text-green-500' : p.verified === 0 ? 'text-red-500' : 'text-gray-400'"
                                        v-tooltip="p.name"
                                        @click="showPersonDetail(p)"
                                    />
                                    <div v-else class="w-6 h-6 text-xs text-gray-400">–</div>
                                    <div v-if="p" class="text-[10px] mt-1" v-tooltip="'ที่นั่ง ' + p.seat">{{ p.seat }}</div>
                                </div>
                            </div>

                            <!-- เสา 3 -->
                            <div class="flex-none flex items-center justify-center w-[7.75rem] h-full border-2 border-yellow-400 rounded-lg bg-yellow-100 shadow">
                                <span class="text-xs font-bold text-yellow-800">เสา</span>
                            </div>

                            <!-- seats 1017–1020 -->
                            <div class="flex space-x-1">
                                <div v-for="(p, i) in row.slice(43, 51)" :key="i" class="flex flex-col items-center justify-center h-full w-9">
                                    <Icon
                                        v-if="p"
                                        icon="material-symbols:event-seat"
                                        class="text-2xl rounded shadow cursor-pointer hover:scale-110 hover:shadow-lg"
                                        :class="p.verified === 1 ? 'text-green-500' : p.verified === 0 ? 'text-red-500' : 'text-gray-400'"
                                        v-tooltip="p.name"
                                        @click="showPersonDetail(p)"
                                    />
                                    <div v-else class="w-6 h-6 text-xs text-gray-400">–</div>
                                    <div v-if="p" class="text-[10px] mt-1" v-tooltip="'ที่นั่ง ' + p.seat">{{ p.seat }}</div>
                                </div>
                            </div>
                        </template>
                    </template>

                    <!-- แถวอื่นๆ -->
                    <template v-else>
                        <div class="flex space-x-1">
                            <div v-for="(p, i) in row.slice(0, 33)" :key="i" class="flex flex-col items-center justify-center h-full w-9">
                                <Icon
                                    v-if="p"
                                    icon="material-symbols:event-seat"
                                    class="text-2xl rounded shadow cursor-pointer hover:scale-110 hover:shadow-lg"
                                    :class="p.verified === 1 ? 'text-green-500' : p.verified === 0 ? 'text-red-500' : 'text-gray-400'"
                                    v-tooltip="p.name"
                                    @click="showPersonDetail(p)"
                                />
                                <div v-else class="w-6 h-6 text-xs text-gray-400">–</div>
                                <div v-if="p" class="text-[10px] mt-1" v-tooltip="'ที่นั่ง ' + p.seat">{{ p.seat }}</div>
                            </div>
                        </div>
                        <div class="flex-none w-16"></div>
                        <div class="flex space-x-1">
                            <div v-for="(p, i) in row.slice(33)" :key="i" class="flex flex-col items-center justify-center h-full w-9">
                                <Icon
                                    v-if="p"
                                    icon="material-symbols:event-seat"
                                    class="text-2xl rounded shadow cursor-pointer hover:scale-110 hover:shadow-lg"
                                    :class="p.verified === 1 ? 'text-green-500' : p.verified === 0 ? 'text-red-500' : 'text-gray-400'"
                                    v-tooltip="p.name"
                                    @click="showPersonDetail(p)"
                                />
                                <div v-else class="w-6 h-6 text-xs text-gray-400">–</div>
                                <div v-if="p" class="text-[10px] mt-1" v-tooltip="'ที่นั่ง ' + p.seat">{{ p.seat }}</div>
                            </div>
                        </div>
                    </template>
                </div>
            </div>
        </div>
        <!-- Detail Dialog -->
        <Dialog v-model:visible="dialogVisible" header="รายละเอียดผู้เข้าร่วม" modal :closable="true" class="p-fluid">
            <div class="space-y-4">
                <div class="grid grid-cols-3 gap-2 pt-3 border-t">
                    <label class="font-semibold text-white-600">ชื่อ</label>
                    <p class="col-span-2 text-white-800">{{ selectedPerson.name }}</p>
                </div>
                <div class="grid grid-cols-3 gap-2 pt-3 border-t">
                    <label class="font-semibold text-white-600">รหัสนิสิต</label>
                    <p class="col-span-2 text-white-800">{{ selectedPerson.nisit }}</p>
                </div>
                <div class="grid grid-cols-3 gap-2 pt-3 border-t">
                    <label class="font-semibold text-white-600">คณะ</label>
                    <p class="col-span-2 text-white-800">{{ selectedPerson.degree }}</p>
                </div>
                <div class="grid grid-cols-3 gap-2 pt-3 border-t">
                    <label class="font-semibold text-white-600">ที่นั่ง</label>
                    <p class="col-span-2 text-white-800">{{ selectedPerson.seat }}</p>
                </div>
            </div>
        </Dialog>
    </div>
</template>

<style scoped>
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