<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import axios from 'axios';
import { Icon } from '@iconify/vue';

const API_BASE = import.meta.env.VITE_API_BASE;

// สร้างตัวแปรต่างๆ
const persons = ref([]);
const loading = ref(false);
const filterMachine = ref('all'); // 'all', 'A', 'B', 'C'
const machineOptions = [
    { label: 'ทั้งหมด', value: 'all' },
    { label: 'เครื่อง A', value: 'A' },
    { label: 'เครื่อง B', value: 'B' },
    { label: 'เครื่อง C', value: 'C' }
];

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

const statusLabels = {
    0: 'ยังไม่รายงานตัว',
    1: 'รายงานตัวแล้ว',
    2: 'เข้าหอประชุมแล้ว',
    unknown: 'ไม่ทราบสถานะ'
};

function lastNByVerifiedAt(arr, n = 15, verifiedField = 'verified1', updatedAtField = 'verified_updated_at1') {
    return [...arr]
        .filter((p) => Number(p[verifiedField]) === 1 || Number(p[verifiedField]) === 2)
        .sort((a, b) => new Date(b[updatedAtField] || 0) - new Date(a[updatedAtField] || 0))
        .slice(0, n);
}

const personsA = computed(() => lastNByVerifiedAt(persons.value, 15, 'verified1', 'verified_updated_at1'));
const personsB = computed(() => lastNByVerifiedAt(persons.value, 15, 'verified2', 'verified_updated_at2'));
const personsC = computed(() => lastNByVerifiedAt(persons.value, 15, 'verified3', 'verified_updated_at3'));
</script>

<template>
    <div>
        <div class="flex flex-col gap-2 px-2 mb-4 md:flex-row md:items-center md:justify-between">
            <div class="flex items-center justify-center w-full gap-2 md:w-auto">
                <span class="flex items-center text-lg font-extrabold tracking-wide text-blue-700 md:text-2xl dark:text-blue-200">
                    <Icon icon="mdi:tag" class="mr-2 text-blue-400" width="28" height="28" />
                    เลขบัณฑิตที่แตะ TAG แล้ว
                </span>
            </div>
            <div class="flex items-center justify-end w-full gap-2 md:w-auto">
                <label for="machine-filter" class="hidden mr-2 text-xs text-gray-500 md:inline md:text-sm dark:text-gray-300">เลือกเครื่อง:</label>
                <select
                    id="machine-filter"
                    v-model="filterMachine"
                    class="w-full px-3 py-2 text-sm font-semibold text-gray-800 transition-all duration-200 bg-white border border-gray-300 rounded-lg shadow dark:bg-slate-800 dark:border-slate-700 dark:text-gray-100 focus:ring-2 focus:ring-blue-400 md:w-44 md:text-base"
                >
                    <option v-for="opt in machineOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
            </div>
        </div>
        <div class="flex flex-col flex-wrap justify-center w-full max-w-full max-w-screen-xl min-w-0 gap-4 px-1 mx-auto overflow-x-auto md:flex-row md:gap-8 flex-machine-container">
            <!-- เครื่อง A -->
            <div
                v-if="filterMachine === 'all' || filterMachine === 'A'"
                class="flex-1 bg-blue-100/80 dark:bg-blue-900/60 rounded-2xl p-2 md:p-4 shadow-lg border border-blue-200 dark:border-blue-700 min-w-0 w-full max-w-full md:min-w-[260px] md:max-w-md mx-auto transition-all duration-200 mb-4 md:mb-0"
            >
                <div class="mb-2 text-base font-bold text-center text-blue-800 dark:text-blue-200 md:mb-3 md:text-lg">เครื่อง A</div>
                <div v-if="personsA.length === 0" class="text-center text-gray-400">ยังไม่มีข้อมูล</div>
                <div
                    v-for="(person, idx) in personsA"
                    :key="person.id"
                    class="flex items-center gap-2 px-2 py-2 mb-2 transition-all duration-200 rounded-lg shadow-sm md:mb-3 bg-white/90 dark:bg-slate-800/80 md:px-3 hover:shadow-md"
                    :class="idx === 0 ? 'ring-4 ring-yellow-400 border-yellow-400' : ''"
                >
                    <Icon icon="material-symbols:person" class="text-xl text-blue-500 md:text-2xl dark:text-blue-300" />
                    <span class="flex items-center gap-2 font-mono text-sm md:text-base">
                        <!-- <span class="text-gray-600 dark:text-gray-200">xxxxxx</span> -->
                        <span class="inline-block rounded px-2 ml-2 tracking-widest font-bold flex-shrink-0 min-w-[44px] md:min-w-[56px] text-center" :class="idx === 0 ? 'bg-green-600 text-white' : idx === 1 ? 'bg-yellow-400 text-gray-900' : ''">
                            {{ person.nisit.slice(-4) }}
                        </span>
                    </span>
                    <span class="text-gray-700 dark:text-gray-200 font-semibold truncate max-w-[60px] md:max-w-[120px] flex-1 text-xs md:text-base">{{ person.name }}</span>
                    <span
                        class="px-2 py-1 ml-auto text-xs font-bold rounded"
                        :class="{
                            'bg-green-100 text-green-700 dark:bg-green-900/60 dark:text-green-200': person.verified1 == 1,
                            'bg-orange-100 text-orange-700 dark:bg-orange-900/60 dark:text-orange-200': person.verified1 == 2
                        }"
                    >
                        {{ statusLabels[person.verified1?.toString() ?? 'unknown'] }}
                    </span>
                </div>
            </div>
            <!-- เครื่อง B -->
            <div
                v-if="filterMachine === 'all' || filterMachine === 'B'"
                class="flex-1 bg-purple-100/80 dark:bg-purple-900/60 rounded-2xl p-2 md:p-4 shadow-lg border border-purple-200 dark:border-purple-700 min-w-0 w-full max-w-full md:min-w-[260px] md:max-w-md mx-auto transition-all duration-200 mb-4 md:mb-0"
            >
                <div class="mb-2 text-base font-bold text-center text-purple-800 dark:text-purple-200 md:mb-3 md:text-lg">เครื่อง B</div>
                <div v-if="personsB.length === 0" class="text-center text-gray-400">ยังไม่มีข้อมูล</div>
                <div
                    v-for="(person, idx) in personsB"
                    :key="person.id"
                    class="flex items-center gap-2 px-2 py-2 mb-2 transition-all duration-200 rounded-lg shadow-sm md:mb-3 bg-white/90 dark:bg-slate-800/80 md:px-3 hover:shadow-md"
                    :class="idx === 0 ? 'ring-4 ring-yellow-400 border-yellow-400' : ''"
                >
                    <Icon icon="material-symbols:person" class="text-xl text-purple-500 md:text-2xl dark:text-purple-300" />
                    <span class="flex items-center gap-2 font-mono text-sm md:text-base">
                        <!-- <span class="text-gray-600 dark:text-gray-200">xxxxxx</span> -->
                        <span class="inline-block rounded px-2 ml-2 tracking-widest font-bold flex-shrink-0 min-w-[44px] md:min-w-[56px] text-center" :class="idx === 0 ? 'bg-green-600 text-white' : idx === 1 ? 'bg-yellow-400 text-gray-900' : ''">
                            {{ person.nisit.slice(-4) }}
                        </span>
                    </span>
                    <span class="text-gray-700 dark:text-gray-200 font-semibold truncate max-w-[60px] md:max-w-[120px] flex-1 text-xs md:text-base">{{ person.name }}</span>
                    <span
                        class="px-2 py-1 ml-auto text-xs font-bold rounded"
                        :class="{
                            'bg-green-100 text-green-700 dark:bg-green-900/60 dark:text-green-200': person.verified2 == 1,
                            'bg-orange-100 text-orange-700 dark:bg-orange-900/60 dark:text-orange-200': person.verified2 == 2
                        }"
                    >
                        {{ statusLabels[person.verified2?.toString() ?? 'unknown'] }}
                    </span>
                </div>
            </div>
            <!-- เครื่อง C -->
            <div
                v-if="filterMachine === 'all' || filterMachine === 'C'"
                class="flex-1 bg-yellow-100/80 dark:bg-yellow-700/60 rounded-2xl p-2 md:p-4 shadow-lg border border-yellow-200 dark:border-yellow-600 min-w-0 w-full max-w-full md:min-w-[260px] md:max-w-md mx-auto transition-all duration-200 mb-4 md:mb-0"
            >
                <div class="mb-2 text-base font-bold text-center text-yellow-800 dark:text-yellow-200 md:mb-3 md:text-lg">เครื่อง C</div>
                <div v-if="personsC.length === 0" class="text-center text-gray-400">ยังไม่มีข้อมูล</div>
                <div
                    v-for="(person, idx) in personsC"
                    :key="person.id"
                    class="flex items-center gap-2 px-2 py-2 mb-2 transition-all duration-200 rounded-lg shadow-sm md:mb-3 bg-white/90 dark:bg-slate-800/80 md:px-3 hover:shadow-md"
                    :class="idx === 0 ? 'ring-4 ring-yellow-400 border-yellow-400' : ''"
                >
                    <Icon icon="material-symbols:person" class="text-xl text-yellow-500 md:text-2xl dark:text-yellow-300" />
                    <span class="flex items-center gap-2 font-mono text-sm md:text-base">
                        <!-- <span class="text-gray-600 dark:text-gray-200">xxxxxx</span> -->
                        <span class="inline-block rounded px-2 ml-2 tracking-widest font-bold flex-shrink-0 min-w-[44px] md:min-w-[56px] text-center" :class="idx === 0 ? 'bg-green-600 text-white' : idx === 1 ? 'bg-yellow-400 text-gray-900' : ''">
                            {{ person.nisit.slice(-4) }}
                        </span>
                    </span>
                    <span class="text-gray-700 dark:text-gray-200 font-semibold truncate max-w-[60px] md:max-w-[120px] flex-1 text-xs md:text-base">{{ person.name }}</span>
                    <span
                        class="px-2 py-1 ml-auto text-xs font-bold rounded"
                        :class="{
                            'bg-green-100 text-green-700 dark:bg-green-900/60 dark:text-green-200': person.verified3 == 1,
                            'bg-orange-100 text-orange-700 dark:bg-orange-900/60 dark:text-orange-200': person.verified3 == 2
                        }"
                    >
                        {{ statusLabels[person.verified3?.toString() ?? 'unknown'] }}
                    </span>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.heading-contrast {
    color: #222;
    background: linear-gradient(90deg, #fff 60%, #f3f4f6 100%);
    border-radius: 0.5rem;
    padding: 0.5rem 0;
    letter-spacing: 0.01em;
}
.dark .heading-contrast {
    color: #fff;
    background: linear-gradient(90deg, #23272f 60%, #1a1d23 100%);
}
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
.flex-machine-container {
    min-width: 0;
    max-width: 100vw;
    overflow-x: auto;
    flex-wrap: wrap;
    gap: 2rem;
    justify-content: center;
}
@media (max-width: 1200px) {
    .flex-machine-container {
        flex-direction: column;
        min-width: 0;
        padding-left: 0;
        gap: 1rem;
    }
}
</style>
