<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { FilterMatchMode } from '@primevue/core/api';

const filters = ref({
    percentage: { value: [0, 100], matchMode: FilterMatchMode.BETWEEN }
});

const persons = ref([]);
const loading = ref(false);

// เรียกข้อมูลจาก API
async function fetchPersons() {
    loading.value = true;
    try {
        const response = await axios.get('http://127.0.0.1:8000/api/person/');
        persons.value = response.data;
    } catch (error) {
        console.error('Error:', error);
    } finally {
        loading.value = false;
    }
}

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
        entry.percentage = entry.total > 0 ? +(entry.reported / entry.total * 100).toFixed(2) : 0;
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
        <h1 class="text-2xl font-bold">📋 รายงานสถานะบัณฑิตตามชื่อปริญญา</h1>

        <!-- Summary Grid -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="bg-blue-400 p-4 rounded-lg text-center shadow">
                <div class="text-gray-600 text-xl">บัณฑิตทั้งหมด</div>
                <div class="text-2xl font-bold">{{ totalSummary.total }}</div>
            </div>
            <div class="bg-green-400 p-4 rounded-lg text-center shadow">
                <div class="text-gray-600 text-xl">รายงานตัวแล้ว</div>
                <div class="text-2xl font-bold">{{ totalSummary.reported }}</div>
            </div>
            <div class="bg-red-400 p-4 rounded-lg text-center shadow">
                <div class="text-gray-600 text-xl">ขาด</div>
                <div class="text-2xl font-bold">{{ totalSummary.absent }}</div>
            </div>
            <div class="bg-yellow-400 p-4 rounded-lg text-center shadow">
                <div class="text-gray-600 text-xl">เปอร์เซ็นต์</div>
                <div class="text-2xl font-bold">{{ totalSummary.percentage }}%</div>
            </div>
        </div>

        <!-- Data Table -->
        <div class="card">
            <DataTable :value="summaryByDegree" scrollable scrollHeight="400px" class="text-sm" :filters="filters" :loading="loading" filterDisplay="menu">
                <Column field="degree" header="ชื่อปริญญา" style="min-width: 150px" class="text-lg"></Column>
                <Column field="total" header="จำนวนทั้งหมด" style="min-width: 100px" class="text-lg">
                    <template #body="{ data }">
                        <Tag :value="data.total" severity="info" class="text-5xl font-bold px-3 py-1">
                            <span class="text-lg font-bold">{{ data.total }}</span>
                        </Tag>
                    </template>
                </Column>
                <Column field="reported" header="รายงานตัวแล้ว" style="min-width: 100px" class="text-green-700 text-lg" :body="reportedTemplate">
                    <template #body="{ data }">
                        <Tag :value="data.reported" severity="success" class="text-5xl font-bold px-3 py-1">
                            <span class="text-lg font-bold">{{ data.reported }}</span>
                        </Tag>
                    </template>
                </Column>
                <Column field="absent" header="ขาด" style="min-width: 100px" class="text-red-500 text-lg" :body="absentTemplate">
                    <template #body="{ data }">
                        <Tag :value="data.absent" severity="danger" class="text-5xl font-bold px-3 py-1">
                            <span class="text-lg font-bold">{{ data.absent }}</span>
                        </Tag>
                    </template>
                </Column>
                <Column field="percentage" header="เปอร์เซ็นต์" :showFilterMatchModes="false" :filterField="'percentage'" style="min-width: 200px" class="text-lg">
                    <template #body="{ data }">
                        <div class="w-full relative">
                            <div class="bg-gray-200 rounded-full h-6">
                                <div class="bg-green-500 h-6 rounded-full" :style="{ width: data.percentage + '%' }"></div>
                            </div>
                            <div class="absolute top-1 left-0 w-full h-4 flex items-center justify-center text-lg text-black font-semibold">{{ data.percentage }}%</div>
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
