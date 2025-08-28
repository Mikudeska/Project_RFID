<!-- Logs.vue -->
<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';
import { Icon } from '@iconify/vue';
import { useToast } from 'primevue/usetoast';
import { useAuthStore } from '@/stores/auth';
import { storeToRefs } from 'pinia';

const API_BASE = import.meta.env.VITE_API_BASE;

const auth = useAuthStore();
const { user } = storeToRefs(auth);

const toast = useToast();
const logs = ref([]);
const loading = ref(false);

// รีเซ็ตข้อมูล
const confirmResetDialog1 = ref(false);
const confirmResetDialog2 = ref(false);
const resetKeyword = ref('');

const confirmResetdatabase = () => {
    confirmResetDialog1.value = true;
};

const handleResetStep1 = () => {
    confirmResetDialog1.value = false;
    confirmResetDialog2.value = true;
};

const handleResetStep2 = async () => {
    if (resetKeyword.value.toUpperCase() !== 'RESET') {
        toast.add({
            severity: 'error',
            summary: 'ยืนยันไม่สำเร็จ',
            detail: 'กรุณาพิมพ์คำว่า "RESET" ให้ถูกต้อง',
            life: 3000
        });
        resetKeyword.value = '';
        return;
    }
    try {
        await axios.post(`${API_BASE}/api/resetlog/`);
        await fetchLogs();
        toast.add({
            severity: 'success',
            summary: 'รีเซ็ตสำเร็จ',
            detail: 'ลบข้อมูลทั้งหมดเรียบร้อย',
            life: 5000
        });
    } catch (error) {
        toast.add({
            severity: 'error',
            summary: 'รีเซ็ตล้มเหลว',
            detail: error.response?.data?.error || 'เกิดข้อผิดพลาด',
            life: 5000
        });
    } finally {
        confirmResetDialog2.value = false;
        resetKeyword.value = '';
    }
};

// ฟังก์ชันแปลงรายละเอียด Log
const parsedDetails = (details) => {
    const labels = {
        name: 'ชื่อ',
        nisit: 'รหัสนิสิต',
        degree: 'ปริญญา',
        seat: 'ที่นั่ง',
        verified: 'สถานะ',
        rfid: 'RFID'
    };

    return details.split('|').map((part) => {
        const [fieldRaw, oldRaw, newRaw] = part.split('::');

        const field = fieldRaw?.trim();
        const old = oldRaw?.trim();
        const newVal = newRaw?.trim();

        const processValue = (value, field) => {
            if (field === 'verified') {
                const statusMap = {
                    ยังไม่รายงานตัว: 0,
                    รายงานตัวแล้ว: 1,
                    อยู่ในห้องพิธี: 2
                };
                return statusMap[value] ?? value;
            }
            return value;
        };

        const item = {
            field,
            label: labels[field] || field,
            old: processValue(old, field),
            new: processValue(newVal, field)
        };

        return item;
    });
};

function extractStatus(text) {
    const match = text.match(/เป็น (\d)/); // หาเลข 0,1 หรือ 2 หลังคำว่า "เป็น "
    return match ? Number(match[1]) : null;
}

// ฟังก์ชันจัดการไอคอน verified
const getVerifiedIcon = (value) => {
    const icons = {
        0: 'rivet-icons:close-circle-solid',
        1: 'rivet-icons:check-circle-solid',
        2: 'rivet-icons:exclamation-mark-circle-solid'
    };
    const status = Number(value);
    return icons[status] || 'rivet-icons:check-circle-solid';
};

// ฟังก์ชันจัดการสี verified
const getVerifiedColor = (value) => {
    // ตรวจสอบชนิดข้อมูลของ value
    const status = Number(value);
    if (status === 1) return 'text-green-500';
    if (status === 0) return 'text-red-500';
    if (status === 2) return 'text-yellow-300';
    return 'text-gray-400';
};

const fetchLogs = async () => {
    loading.value = true;
    try {
        let allLogs = [];
        let nextUrl = `${API_BASE}/api/logs/`;

        while (nextUrl) {
            const response = await axios.get(nextUrl);
            const data = response.data;

            // ตรวจสอบโครงสร้างข้อมูล
            const pageLogs = data.results || data;

            // กรอง null และเพิ่มข้อมูล
            allLogs.push(...pageLogs.filter((log) => log !== null));

            // อัปเดต URL ถัดไป (ใช้ API_BASE เสมอ)
            nextUrl = data.next ? data.next.replace(/^http:\/\/(localhost|127\.0\.0\.1):8000/, API_BASE) : null;
        }

        logs.value = allLogs;
    } catch (error) {
        console.error('Error fetching logs:', error);
        toast.add({
            severity: 'error',
            summary: 'เกิดข้อผิดพลาด',
            detail: 'ดึงข้อมูลไม่สำเร็จ',
            life: 3000
        });
    } finally {
        loading.value = false;
    }
};

onMounted(() => {
    fetchLogs();
});

function extractTotal(text) {
    const match = text.match(/ลบข้อมูลทั้งหมด (\d+) รายการ/);
    return match ? match[1] : '';
}

const extractImportSummary = (text) => {
    // กรณีสำเร็จแบบมีจำนวน
    const match = text.match(/นำเข้าฐานข้อมูล (\d+) รายการ \( ใหม่ (\d+) อัปเดต (\d+) \)/);
    if (match) {
        const total = match[1];
        const added = match[2];
        const updated = match[3];
        return `ข้อมูลใหม่ ${added} + อัปเดตข้อมูล ${updated} = ${total} รายการ`;
    }

    // กรณีล้มเหลว (ใช้ข้อความหลัง `:`)
    if (text.includes('นำเข้าข้อมูลล้มเหลว')) {
        return text.split(':').slice(1).join(':').trim(); // คืนเฉพาะข้อความ error
    }

    // fallback
    return '';
};

const showDialog = ref(false);
const allIDs = ref([]);
const maxDisplay = 30;
const searchText = ref('');

const filteredIDs = computed(() => allIDs.value.filter((id) => id.toLowerCase().includes(searchText.value.toLowerCase())));

function openIDDialog(details) {
    const match = details.match(/\[ID:([^\]]+)\]/);
    if (!match) return;

    const ids = match[1].split(',').map((id) => id.trim());
    allIDs.value = ids;
    showDialog.value = true;
}

const extractShortenedIDs = (details) => {
    const match = details.match(/\[ID:([^\]]+)\]/);
    if (!match) return '';

    const ids = match[1].split(',').map((id) => id.trim());
    if (ids.length > maxDisplay) {
        const shortened = ids.slice(0, maxDisplay).join(', ');
        const remaining = ids.length - maxDisplay;
        return `[ID: ${shortened} ... + ${remaining} รายการ]`;
    }

    return `[ID: ${ids.join(', ')}]`;
};
</script>

<template>
    <div class="flex flex-col h-full card">
        <Toolbar class="mb-6">
            <template #start>
                <Button severity="secondary" class="mr-2" @click="confirmResetdatabase" rounded raised>
                    <Icon icon="lucide:database-backup" />
                    <span>รีเซ็ตประวัติ</span>
                </Button>
            </template>
        </Toolbar>
        <DataTable
            :value="logs"
            :paginator="true"
            :rows="10"
            paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
            :rowsPerPageOptions="[5, 10, 25]"
            currentPageReportTemplate="จาก   {first} ถึง {last} ของทั้งหมด {totalRecords} คน"
            scrollable
            scrollHeight="flex"
            class="h-full"
            :loading="loading"
            :pt="{
                root: { class: 'flex-1 flex flex-col' },
                loadingOverlay: { class: 'flex-1' },
                wrapper: { class: 'flex-1 flex flex-col' },
                table: { class: 'min-w-[800px]' }
            }"
        >
            <!-- คอลัมน์รายการ -->
            <Column field="id" header="รายการ" style="min-width: 50px">
                <template #body="{ data }">
                    <span v-if="data?.id" class="font-semibold">
                        {{ data.id }}
                    </span>
                </template>
            </Column>

            <!-- คอลัมน์วันที่ -->
            <Column field="timestamp" header="วันที่" style="min-width: 100px">
                <template #body="{ data }">
                    <template v-if="data?.timestamp">
                        {{
                            new Date(data.timestamp).toLocaleDateString('th-TH', {
                                year: 'numeric',
                                month: '2-digit',
                                day: '2-digit'
                            })
                        }}
                    </template>
                    <span v-else class="text-gray-400">N/A</span>
                </template>
            </Column>

            <!-- คอลัมน์เวลา -->
            <Column field="timestamp" header="เวลา" style="min-width: 100px">
                <template #body="{ data }">
                    <template v-if="data?.timestamp">
                        {{
                            new Date(data.timestamp).toLocaleTimeString('th-TH', {
                                hour: '2-digit',
                                minute: '2-digit',
                                second: '2-digit'
                            })
                        }}
                    </template>
                    <span v-else class="text-gray-400">N/A</span>
                </template>
            </Column>

            <!-- คอลัมน์การกระทำ -->
            <Column field="action" header="การกระทำ" style="min-width: 100px">
                <template #body="{ data }">
                    <Tag
                        v-if="data?.action"
                        :value="data.action"
                        :severity="
                            {
                                add: 'success',
                                edit: 'info',
                                delete: 'danger',
                                import: 'warning',
                                export: 'help',
                                reset: 'danger',
                                comment: 'help'
                            }[data.action]
                        "
                    />
                </template>
            </Column>

            <Column header="ผู้ใช้" style="min-width: 100px">
                <template #body>
                    {{ user?.nickname ?? '-' }}
                </template>
            </Column>

            <!-- คอลัมน์รายละเอียด -->
            <Column field="details" header="รายละเอียด" style="min-width: 500px">
                <template #body="{ data }">
                    <div v-if="data?.details" class="flex flex-wrap items-center gap-2">
                        <!-- แสดง [ID: xxx] แค่ครั้งเดียว -->
                        <span v-if="data.record_id" class="font-semibold text-blue-600">[ID: {{ data.record_id }}]</span>

                        <!-- กรณี log แบบกลุ่ม (string ธรรมดา) -->
                        <template v-if="typeof data.details === 'string' && data.details.startsWith('[ID:')">
                            <span class="font-semibold text-blue-600 cursor-pointer" @click="openIDDialog(data.details)">
                                {{ extractShortenedIDs(data.details) }}
                            </span>

                            <span v-if="data.details.includes('อัปเดต')" class="flex items-center gap-1 break-words">
                                อัปเดตสถานะเป็น
                                <Icon icon="mdi:arrow-right" class="inline-block mx-1 text-gray-500" />
                                <span :class="['inline-flex items-center', getVerifiedColor(extractStatus(data.details))]">
                                    <Icon :icon="getVerifiedIcon(extractStatus(data.details))" />
                                </span>
                            </span>

                            <span v-else-if="data.details.includes('ลบข้อมูลแบบกลุ่ม')">
                                <span>ไอดีข้อมูลที่ลบไป</span>
                            </span>
                        </template>

                        <!-- กรณี log แบบ object (ของเดิม) -->
                        <template v-else>
                            <div class="flex flex-wrap items-center gap-2">
                                <template v-if="data.details.includes('รีเซ็ตประวัติ')">
                                    <span class="font-semibold text-red-600">[รีเซ็ตประวัติ]</span>
                                    <span>ลบข้อมูลทั้งหมด {{ extractTotal(data.details) }} รายการ</span>
                                </template>

                                <template v-else-if="data.details.includes('รีเซ็ตฐานข้อมูล')">
                                    <span class="font-semibold text-red-600">[รีเซ็ตฐานข้อมูล]</span>
                                    <span>ลบข้อมูลทั้งหมด {{ extractTotal(data.details) }} รายการ</span>
                                </template>

                                <template v-else-if="data.details.includes('นำเข้าฐานข้อมูล')">
                                    <span class="font-semibold text-green-600">[นำเข้าฐานข้อมูล]</span>
                                    <span>{{ extractImportSummary(data.details) }}</span>
                                </template>

                                <template v-else-if="data.details.includes('นำเข้าข้อมูลล้มเหลว')">
                                    <span class="font-semibold text-red-800">[นำเข้าข้อมูลล้มเหลว] :</span>
                                    <span> {{ extractImportSummary(data.details) }}</span>
                                </template>

                                <template v-else-if="data.details.includes('โหลดไฟล์เป็น PDF')">
                                    <span class="font-semibold">โหลดไฟล์เป็น</span>
                                    <Icon icon="mdi:arrow-right" class="mx-1 text-gray-500" />
                                    <Icon icon="vscode-icons:file-type-pdf2" />
                                    <span class="font-semibold text-red-600">PDF</span>
                                </template>
                                <template v-else-if="data.details.includes('โหลดไฟล์สรุป PDF')">
                                    <span class="font-semibold">โหลดไฟล์สรุปเป็น</span>
                                    <Icon icon="mdi:arrow-right" class="mx-1 text-gray-500" />
                                    <Icon icon="vscode-icons:file-type-pdf2" />
                                    <span class="font-semibold text-red-600">PDF</span>
                                </template>

                                <template v-else-if="data.details.includes('โหลดไฟล์เป็น xlsx')">
                                    <span class="font-semibold">โหลดไฟล์เป็น</span>
                                    <Icon icon="mdi:arrow-right" class="mx-1 text-gray-500" />
                                    <Icon icon="vscode-icons:file-type-excel" />
                                    <span class="font-semibold text-green-600">Excel</span>
                                </template>

                                <template v-else-if="data.details.includes('โหลดไฟล์เป็น csv')">
                                    <span class="font-semibold">โหลดไฟล์เป็น</span>
                                    <Icon icon="mdi:arrow-right" class="mx-1 text-gray-500" />
                                    <Icon icon="catppuccin:csv" />
                                    <span class="font-semibold text-green-600">CSV</span>
                                </template>

                                <template v-else-if="data.action.includes('comment')">
                                    <span class="">พิมข้อความ</span>
                                    <span class="font-semibold text-blue-600">[ {{ data.details }} ]</span>
                                </template>
                                <!-- ✅ แสดงข้อมูลแบบ object ตามปกติ -->
                                <template v-else>
                                    <template v-for="(item, index) in parsedDetails(data.details)" :key="index">
                                        <span class="flex items-center gap-1">
                                            <template v-if="item.field === 'verified1'">
                                                <template v-if="item.old !== item.new">
                                                    <span class="flex-auto">
                                                        อัปเดตสถานะ
                                                        <span :class="getVerifiedColor(item.old)">
                                                            <Icon :icon="getVerifiedIcon(item.old)" class="inline-block" />
                                                        </span>
                                                        <Icon icon="mdi:arrow-right" class="inline-block mx-1 text-gray-500" />
                                                        <span :class="getVerifiedColor(item.new)">
                                                            <Icon :icon="getVerifiedIcon(item.new)" class="inline-block" />
                                                        </span>
                                                    </span>
                                                </template>
                                            </template>
                                            <template v-else>
                                                <span class="font-medium">{{ item.label }}</span>
                                                <span class="text-red-500 line-through">{{ item.old }}</span>
                                                <Icon v-if="item.new !== undefined" icon="mdi:arrow-right" class="mx-1 text-gray-500" />
                                                <span v-if="item.new !== undefined" class="text-green-500">{{ item.new }}</span>
                                            </template>
                                        </span>
                                        <!-- separator -->
                                        <span v-if="index < parsedDetails(data.details).length - 1 && item.new !== undefined">|</span>
                                    </template>
                                </template>
                            </div>
                        </template>
                    </div>
                </template>
            </Column>

            <template #empty>
                <div class="py-6 text-center text-gray-400">ไม่พบข้อมูล Logs</div>
            </template>
        </DataTable>

        <!-- Dialog ยืนยันขั้นที่ 1 -->
        <Dialog v-model:visible="confirmResetDialog1" header="ยืนยันการรีเซ็ต" :modal="true" :style="{ width: '500px' }">
            <div class="flex items-center gap-4 p-4">
                <Icon icon="bi:exclamation-triangle-fill" class="text-yellow-300" />
                <div>
                    <h3 class="mb-2 text-lg font-bold">คุณแน่ใจที่จะรีเซ็ตประวัติทั้งหมด?</h3>
                    <p>การกระทำนี้จะลบข้อมูลทุกรายการและไม่สามารถกู้คืนได้</p>
                </div>
            </div>
            <template #footer>
                <Button label="ยกเลิก" icon="pi pi-times" @click="confirmResetDialog1 = false" severity="secondary" text />
                <Button label="ดำเนินการต่อ" icon="pi pi-arrow-right" @click="handleResetStep1" severity="danger" />
            </template>
        </Dialog>

        <!-- Dialog ยืนยันขั้นที่ 2 -->
        <Dialog v-model:visible="confirmResetDialog2" header="ยืนยันขั้นสุดท้าย" :modal="true" :style="{ width: '500px' }">
            <div class="flex flex-col gap-4 p-4">
                <div class="flex items-center gap-4">
                    <Icon icon="teenyicons:shield-solid" class="text-3xl text-red-500" />
                    <h3 class="text-lg font-bold">กรุณาพิมพ์คำว่า "RESET"</h3>
                </div>

                <InputText v-model="resetKeyword" placeholder="พิมพ์คำว่า RESET ที่นี่" class="w-full" autocomplete="off" @keyup.enter="handleResetStep2" />
            </div>
            <template #footer>
                <Button label="ยกเลิก" icon="pi pi-times" @click="confirmResetDialog2 = false" severity="secondary" text />
                <Button label="ยืนยันรีเซ็ต" icon="pi pi-check" @click="handleResetStep2" :disabled="resetKeyword.toUpperCase() !== 'RESET'" severity="danger" />
            </template>
        </Dialog>

        <Dialog v-model:visible="showDialog" modal>
            <template #header>
                <div class="flex items-center justify-between w-full gap-2">
                    <span class="font-semibold">รายการ ID ทั้งหมด</span>
                    <input v-model="searchText" type="text" placeholder="ค้นหา ID..." class="w-48 px-2 py-1 text-sm border border-gray-300 rounded" />
                </div>
            </template>

            <div class="flex flex-wrap gap-2 text-sm max-h-[70vh] max-w-[120vh] overflow-auto">
                <span v-for="id in filteredIDs" :key="id" class="px-2 py-1 border border-black">
                    {{ id }}
                </span>
            </div>
        </Dialog>
    </div>
</template>

<style scoped></style>
