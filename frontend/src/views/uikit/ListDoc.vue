<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import axios from 'axios';
import { Icon } from '@iconify/vue';
import { useWebSocketStore } from '@/stores/websocket';

const API_BASE = import.meta.env.VITE_API_BASE;

// สร้างตัวแปรต่างๆ
const persons = ref([]);
const loading = ref(false);

const visibleMachines = ref({
    A: true, // ตั้งค่าเริ่มต้นให้แสดงเสา A
    B: true, // ตั้งค่าเริ่มต้นให้แสดงเสา B
    C: false // ตั้งค่าเริ่มต้นให้ซ่อนเสา C
});

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

const wsStore = useWebSocketStore();
let unregisterWsHandler = null;

function handleWsMessage(msg) {
    if (!msg || !msg.action) {
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
    unregisterWsHandler = wsStore.registerHandler(handleWsMessage);
});

onBeforeUnmount(() => {
    if (unregisterWsHandler) {
        unregisterWsHandler();
    }
});

const statusLabels = {
    0: 'ยังไม่รายงานตัว',
    1: 'รายงานตัวแล้ว',
    unknown: 'ไม่ทราบสถานะ'
};

function lastNByVerifiedAt(arr, n = 15, verifiedField = 'verified1', updatedAtField = 'verified_updated_at1') {
    return [...arr]
        .filter((p) => Number(p[verifiedField]) === 1)
        .sort((a, b) => new Date(b[updatedAtField] || 0) - new Date(a[updatedAtField] || 0))
        .slice(0, n);
}

const personsA = computed(() => lastNByVerifiedAt(persons.value, 15, 'verified1', 'verified_updated_at1'));
const personsB = computed(() => lastNByVerifiedAt(persons.value, 15, 'verified2', 'verified_updated_at2'));
const personsC = computed(() => lastNByVerifiedAt(persons.value, 15, 'verified3', 'verified_updated_at3'));
</script>

<template>
    <div>
        <div class="flex flex-col gap-4 px-2 mb-4 md:flex-row md:items-center md:justify-between">
            <div class="flex items-center self-center justify-center w-full gap-2 md:w-auto">
                <span class="flex items-center text-lg font-extrabold tracking-wide text-blue-700 md:text-2xl dark:text-blue-200">
                    <Icon icon="mdi:tag" class="mr-2 text-blue-400" width="28" height="28" />
                    เลขบัณฑิตที่แตะ TAG แล้ว
                </span>
            </div>

            <div class="flex items-center justify-center w-full gap-5 md:justify-end md:w-auto">
                <label for="toggleA" class="flex items-center cursor-pointer">
                    <div class="relative">
                        <input type="checkbox" id="toggleA" class="sr-only" v-model="visibleMachines.A" />
                        <div class="block w-12 h-7 bg-gray-300 rounded-full dark:bg-slate-600"></div>
                        <div class="absolute top-1 left-1 w-5 h-5 bg-white rounded-full dot transition-transform"></div>
                    </div>
                    <div class="ml-3 font-semibold text-gray-700 dark:text-gray-200">เสา A</div>
                </label>

                <label for="toggleB" class="flex items-center cursor-pointer">
                    <div class="relative">
                        <input type="checkbox" id="toggleB" class="sr-only" v-model="visibleMachines.B" />
                        <div class="block w-12 h-7 bg-gray-300 rounded-full dark:bg-slate-600"></div>
                        <div class="absolute top-1 left-1 w-5 h-5 bg-white rounded-full dot transition-transform"></div>
                    </div>
                    <div class="ml-3 font-semibold text-gray-700 dark:text-gray-200">เสา B</div>
                </label>

                <label for="toggleC" class="flex items-center cursor-pointer">
                    <div class="relative">
                        <input type="checkbox" id="toggleC" class="sr-only" v-model="visibleMachines.C" />
                        <div class="block w-12 h-7 bg-gray-300 rounded-full dark:bg-slate-600"></div>
                        <div class="absolute top-1 left-1 w-5 h-5 bg-white rounded-full dot transition-transform"></div>
                    </div>
                    <div class="ml-3 font-semibold text-gray-700 dark:text-gray-200">เสา C</div>
                </label>
            </div>
        </div>

        <div class="flex flex-col flex-wrap justify-center w-full max-w-full min-w-0 gap-4 px-1 mx-auto overflow-x-auto md:flex-row md:gap-4 lg:gap-6 xl:gap-8 flex-machine-container">
            <div
                v-if="visibleMachines.A"
                class="flex-1 p-2 bg-blue-100/80 dark:bg-blue-900/60 rounded-2xl md:p-4 shadow-lg border border-blue-200 dark:border-blue-700 min-w-0 w-full max-w-full md:min-w-[280px] lg:min-w-[320px] xl:min-w-[360px] md:max-w-sm lg:max-w-md xl:max-w-lg mx-auto transition-all duration-200 mb-4 md:mb-0"
            >
                <div class="mb-2 text-base font-bold text-center text-blue-800 dark:text-blue-200 md:mb-3 md:text-lg">เสา A</div>
                <div v-if="personsA.length === 0" class="text-center text-gray-400">ยังไม่มีข้อมูล</div>
                <div
                    v-for="(person, idx) in personsA"
                    :key="person.id"
                    class="flex items-center gap-2 px-2 py-2 mb-2 transition-all duration-200 rounded-lg shadow-sm md:mb-3 bg-white/90 dark:bg-slate-800/80 md:px-3 hover:shadow-md"
                    :class="idx === 0 ? 'ring-4 ring-yellow-400 border-yellow-400' : ''"
                >
                    <Icon icon="material-symbols:person" class="text-xl text-blue-500 md:text-2xl dark:text-blue-300" />
                    <span class="flex items-center gap-2 font-mono text-sm md:text-base">
                        <span class="inline-block rounded px-2 ml-2 tracking-widest font-bold flex-shrink-0 min-w-[44px] md:min-w-[56px] text-center" :class="idx === 0 ? 'bg-green-600 text-white' : idx === 1 ? 'bg-yellow-400 text-gray-900' : ''">
                            {{ person.id }}
                        </span>
                    </span>
                    <span class="flex-1 text-xs font-semibold text-gray-700 dark:text-gray-200 md:text-base">{{ person.name }}</span>
                    <span
                        class="px-2 py-1 ml-auto text-xs font-bold rounded"
                        :class="{
                            'bg-green-100 text-green-700 dark:bg-green-900/60 dark:text-green-200': person.verified1 == 1
                        }"
                    >
                        {{ statusLabels[person.verified1?.toString() ?? 'unknown'] }}
                    </span>
                </div>
            </div>

            <div
                v-if="visibleMachines.B"
                class="flex-1 p-2 bg-purple-100/80 dark:bg-purple-900/60 rounded-2xl md:p-4 shadow-lg border border-purple-200 dark:border-purple-700 min-w-0 w-full max-w-full md:min-w-[280px] lg:min-w-[320px] xl:min-w-[360px] md:max-w-sm lg:max-w-md xl:max-w-lg mx-auto transition-all duration-200 mb-4 md:mb-0"
            >
                <div class="mb-2 text-base font-bold text-center text-purple-800 dark:text-purple-200 md:mb-3 md:text-lg">เสา B</div>
                <div v-if="personsB.length === 0" class="text-center text-gray-400">ยังไม่มีข้อมูล</div>
                <div
                    v-for="(person, idx) in personsB"
                    :key="person.id"
                    class="flex items-center gap-2 px-2 py-2 mb-2 transition-all duration-200 rounded-lg shadow-sm md:mb-3 bg-white/90 dark:bg-slate-800/80 md:px-3 hover:shadow-md"
                    :class="idx === 0 ? 'ring-4 ring-yellow-400 border-yellow-400' : ''"
                >
                    <Icon icon="material-symbols:person" class="text-xl text-purple-500 md:text-2xl dark:text-purple-300" />
                    <span class="flex items-center gap-2 font-mono text-sm md:text-base">
                        <span class="inline-block rounded px-2 ml-2 tracking-widest font-bold flex-shrink-0 min-w-[44px] md:min-w-[56px] text-center" :class="idx === 0 ? 'bg-green-600 text-white' : idx === 1 ? 'bg-yellow-400 text-gray-900' : ''">
                            {{ person.id }}
                        </span>
                    </span>
                    <span class="flex-1 text-xs font-semibold text-gray-700 dark:text-gray-200 md:text-base">{{ person.name }}</span>
                    <span
                        class="px-2 py-1 ml-auto text-xs font-bold rounded"
                        :class="{
                            'bg-green-100 text-green-700 dark:bg-green-900/60 dark:text-green-200': person.verified2 == 1
                        }"
                    >
                        {{ statusLabels[person.verified2?.toString() ?? 'unknown'] }}
                    </span>
                </div>
            </div>

            <div
                v-if="visibleMachines.C"
                class="flex-1 p-2 bg-yellow-100/80 dark:bg-yellow-700/60 rounded-2xl md:p-4 shadow-lg border border-yellow-200 dark:border-yellow-600 min-w-0 w-full max-w-full md:min-w-[280px] lg:min-w-[320px] xl:min-w-[360px] md:max-w-sm lg:max-w-md xl:max-w-lg mx-auto transition-all duration-200 mb-4 md:mb-0"
            >
                <div class="mb-2 text-base font-bold text-center text-yellow-800 dark:text-yellow-200 md:mb-3 md:text-lg">เสา C</div>
                <div v-if="personsC.length === 0" class="text-center text-gray-400">ยังไม่มีข้อมูล</div>
                <div
                    v-for="(person, idx) in personsC"
                    :key="person.id"
                    class="flex items-center gap-2 px-2 py-2 mb-2 transition-all duration-200 rounded-lg shadow-sm md:mb-3 bg-white/90 dark:bg-slate-800/80 md:px-3 hover:shadow-md"
                    :class="idx === 0 ? 'ring-4 ring-yellow-400 border-yellow-400' : ''"
                >
                    <Icon icon="material-symbols:person" class="text-xl text-yellow-500 md:text-2xl dark:text-yellow-300" />
                    <span class="flex items-center gap-2 font-mono text-sm md:text-base">
                        <span class="inline-block rounded px-2 ml-2 tracking-widest font-bold flex-shrink-0 min-w-[44px] md:min-w-[56px] text-center" :class="idx === 0 ? 'bg-green-600 text-white' : idx === 1 ? 'bg-yellow-400 text-gray-900' : ''">
                            {{ person.id }}
                        </span>
                    </span>
                    <span class="flex-1 text-xs font-semibold text-gray-700 dark:text-gray-200 md:text-base">{{ person.name }}</span>
                    <span
                        class="px-2 py-1 ml-auto text-xs font-bold rounded"
                        :class="{
                            'bg-green-100 text-green-700 dark:bg-green-900/60 dark:text-green-200': person.verified3 == 1
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
/* --- CSS สำหรับ Toggle Switch --- */
input:checked ~ .dot {
    transform: translateX(100%);
}
#toggleA:checked ~ div.bg-gray-300 {
    background-color: #3b82f6; /* blue-500 */
}
#toggleB:checked ~ div.bg-gray-300 {
    background-color: #8b5cf6; /* purple-500 */
}
#toggleC:checked ~ div.bg-gray-300 {
    background-color: #f59e0b; /* amber-500 */
}

/* --- CSS เดิมของ Component --- */
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

/* Responsive adjustments for different screen sizes */
@media (max-width: 1536px) {
    .flex-machine-container {
        gap: 1.5rem;
    }
}
@media (max-width: 1280px) {
    .flex-machine-container {
        gap: 1rem;
    }
}
@media (max-width: 1200px) {
    .flex-machine-container {
        flex-direction: column;
        min-width: 0;
        padding-left: 0;
        gap: 1rem;
    }
}
@media (max-width: 1024px) {
    .flex-machine-container {
        gap: 0.75rem;
    }
}
@media (max-width: 768px) {
    .flex-machine-container {
        gap: 0.5rem;
    }
}
</style>