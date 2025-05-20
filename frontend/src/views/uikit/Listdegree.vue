<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { FilterMatchMode } from '@primevue/core/api';
import { useToast } from 'primevue/usetoast';

const API_BASE = import.meta.env.VITE_API_BASE;

const toast = useToast();

const filters = ref({
    percentage: { value: [0, 100], matchMode: FilterMatchMode.BETWEEN }
});

const persons = ref([]);
const loading = ref(false);

// เรียกข้อมูลจาก API
async function fetchPersons() {
    loading.value = true;
    try {
        const response = await axios.get(`${API_BASE}/person/`);
        persons.value = response.data;
    } catch (error) {
        console.error('Error:', error);
    } finally {
        loading.value = false;
    }
}

const ExportPDFResult = async () => {
    try {
        const response = await axios.get(`${API_BASE}/export-pdf-result/`, {
            responseType: 'blob',
            timeout: 30000
        });

        // ตรวจสอบขนาดไฟล์
        if (response.data.size < 1024) {
            throw new Error('ไฟล์ PDF ว่างเปล่า');
        }

        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'รายชื่อสรุปบัณฑิต.pdf');
        document.body.appendChild(link);
        link.click();
        link.remove();
    } catch (error) {
        console.error('PDF Export Error:', error);
        toast.add({ severity: 'error', summary: 'เกิดข้อผิดพลาด', detail: 'โหลดไฟล์สรุป pdf ไม่สำเร็จ', life: 3000 });
    }
};

// ฟังก์ชันช่วยจัดกลุ่มประเภทปริญญา
function getDegreeType(degreeName) {
    if (degreeName.includes('ดุษฎีบัณฑิต')) return 'ดุษฎีบัณฑิต';
    if (degreeName.includes('มหาบัณฑิต')) return 'มหาบัณฑิต';
    return 'บัณฑิต';
}

// สรุปข้อมูลตามชื่อปริญญา และเรียงลำดับประเภท
const summaryByDegree = computed(() => {
    const summary = {};

    persons.value.forEach((person) => {
        const degree = person.degree;
        if (!summary[degree]) {
            summary[degree] = { degree, total: 0, reported: 0, absent: 0 };
        }
        summary[degree].total += 1;
        if (person.verified === 1) {
            summary[degree].reported += 1;
        }
    });

    Object.values(summary).forEach((entry) => {
        entry.absent = entry.total - entry.reported;
        entry.percentage = entry.total > 0 ? +((entry.reported / entry.total) * 100).toFixed(2) : 0;
    });

    // ลำดับประเภทปริญญา
    const degreeOrder = ['บัณฑิต', 'ดุษฎีบัณฑิต', 'มหาบัณฑิต'];

    return Object.values(summary).sort((a, b) => {
        return degreeOrder.indexOf(getDegreeType(a.degree)) - degreeOrder.indexOf(getDegreeType(b.degree));
    });
});

// รวมสรุปทั้งหมด
const totalSummary = computed(() => {
    const total = { degree: 'รวมทั้งหมด', total: 0, reported: 0, absent: 0, percentage: '0.00' };

    summaryByDegree.value.forEach((item) => {
        total.total += item.total;
        total.reported += item.reported;
        total.absent += item.absent;
    });

    total.percentage = total.total > 0 ? ((total.reported / total.total) * 100).toFixed(2) : '0.00';

    return total;
});

onMounted(() => {
    fetchPersons();
});
</script>

<template>
    <div class="p-6 space-y-6">
        <div class="card rounded-3xl">
            <h1 class="text-2xl font-bold text-center">รายงานสถานะบัณฑิตตามชื่อปริญญา</h1>
        </div>

        <!-- Summary Grid -->
        <div class="grid grid-cols-2 gap-4 md:grid-cols-4">
            <div class="flex items-center justify-between px-4 py-2 border-b-8 border-blue-500 rounded-3xl card">
                <div>
                    <div class="text-lg font-semibold">บัณฑิตทั้งหมด</div>
                    <div class="text-5xl font-bold">{{ totalSummary.total }}</div>
                </div>
                <Icon icon="nimbus:user-group" class="text-blue-500" style="width: 48px; height: 48px" />
            </div>

            <div class="flex items-center justify-between border-b-8 border-green-500 shadow pe-4 rounded-3xl card">
                <div>
                    <div class="text-lg font-semibold">รายงานตัวแล้ว</div>
                    <div class="text-5xl font-bold">{{ totalSummary.reported }}</div>
                </div>
                <Icon icon="rivet-icons:check-circle" class="text-green-500" style="width: 36px; height: 36px" />
            </div>

            <div class="flex items-center justify-between p-4 border-b-8 border-red-500 shadow rounded-3xl card">
                <div>
                    <div class="text-lg font-semibold">ขาด</div>
                    <div class="text-5xl font-bold">{{ totalSummary.absent }}</div>
                </div>
                <Icon icon="rivet-icons:close-circle" class="text-red-500" style="width: 36px; height: 36px" />
            </div>

            <div class="flex items-center justify-between p-4 border-b-8 border-yellow-500 shadow rounded-3xl card">
                <div>
                    <div class="text-lg font-semibold">เปอร์เซ็นต์</div>
                    <div class="text-5xl font-bold">{{ totalSummary.percentage }}%</div>
                </div>
                <Icon icon="mage:chart-fill" class="text-yellow-500" style="width: 36px; height: 36px" />
            </div>
        </div>

        <!-- Data Table -->
        <div class="card rounded-3xl">
            <Toolbar class="mb-6">
                <template #start> </template>

                <template #end>
                    <Button severity="secondary" class="mr-2" @click="ExportPDFResult" rounded raised> <Icon icon="lets-icons:export" />โหลดไฟล์เป็น pdf</Button>
                </template>
            </Toolbar>

            <DataTable :value="summaryByDegree" scrollable scrollHeight="500px" class="text-sm" :filters="filters" :loading="loading" filterDisplay="menu">
                <Column field="degree" header="ชื่อปริญญา" style="min-width: 150px" class="text-lg"></Column>
                <Column field="total" header="จำนวนทั้งหมด" style="min-width: 100px" class="text-lg">
                    <template #body="{ data }">
                        <Tag :value="data.total" severity="info" class="px-3 py-1 text-5xl font-bold">
                            <span class="text-lg font-bold">{{ data.total }}</span>
                        </Tag>
                    </template>
                </Column>
                <Column field="reported" header="รายงานตัวแล้ว" style="min-width: 100px" class="text-lg text-green-700" :body="reportedTemplate">
                    <template #body="{ data }">
                        <Tag :value="data.reported" severity="success" class="px-3 py-1 text-5xl font-bold">
                            <span class="text-lg font-bold">{{ data.reported }}</span>
                        </Tag>
                    </template>
                </Column>
                <Column field="absent" header="ขาด" style="min-width: 100px" class="text-lg text-red-500" :body="absentTemplate">
                    <template #body="{ data }">
                        <Tag :value="data.absent" severity="danger" class="px-3 py-1 text-5xl font-bold">
                            <span class="text-lg font-bold">{{ data.absent }}</span>
                        </Tag>
                    </template>
                </Column>
                <Column field="percentage" header="เปอร์เซ็นต์" :showFilterMatchModes="false" :filterField="'percentage'" style="min-width: 200px" class="text-lg">
                    <template #body="{ data }">
                        <div class="relative w-full">
                            <div class="h-6 bg-gray-200 rounded-full">
                                <div class="h-6 bg-green-500 rounded-full" :style="{ width: data.percentage + '%' }"></div>
                            </div>
                            <div class="absolute left-0 flex items-center justify-center w-full h-4 text-lg font-semibold text-black top-1">{{ data.percentage }}%</div>
                        </div>
                    </template>

                    <template #filter="{ filterModel }">
                        <Slider v-model="filterModel.value" range class="m-4"></Slider>
                        <div class="flex items-center justify-between px-2">
                            <span>{{ filterModel.value ? filterModel.value[0] : 0 }}%</span>
                            <span>{{ filterModel.value ? filterModel.value[1] : 100 }}%</span>
                        </div>
                    </template>
                </Column>
            </DataTable>
        </div>
    </div>
</template>

<style scoped>
table {
    font-family: 'Arial', sans-serif;
}
th,
td {
    text-align: center;
}
</style>
