<script setup>
import { ref, computed, onMounted } from 'vue';
import api from '@/plugins/axios';
import { FilterMatchMode } from '@primevue/core/api';
import { createLocalToast } from '@/components/utils/toastUtils';
import { useAuthStore } from '@/stores/auth';

const auth = useAuthStore();

const toast = createLocalToast();

const filters = ref({
    percentage: { value: [0, 100], matchMode: FilterMatchMode.BETWEEN }
});

const persons = ref([]);
const loading = ref(false);

// เรียกข้อมูลจาก API
async function fetchPersons() {
    loading.value = true;
    try {
        const response = await api.get(`person/`);
        persons.value = response.data;
    } catch (error) {
        console.error('Error:', error);
    } finally {
        loading.value = false;
    }
}

const exportPDFResult = async () => {
    try {
        const response = await api.get(`export-pdf-result/`, {
            responseType: 'blob',
            timeout: 30000
        });

        if (response.status !== 200) {
            const errorText = await new Promise((resolve) => {
                const reader = new FileReader();
                reader.onload = () => resolve(reader.result);
                reader.readAsText(response.data);
            });
            throw new Error(`Server error: ${errorText}`);
        }

        if (response.data.size < 1024) {
            throw new Error('ไฟล์ PDF ว่างเปล่าหรือมีขนาดเล็กเกินไป');
        }

        const disposition = response.headers['content-disposition'];
        let filename = 'รายชื่อสรุป.pdf';

        const getFilenameFromDisposition = (disp) => {
            if (!disp) return null;
            const utf8Match = disp.match(/filename\*=UTF-8''([\w%\-\.]+)/i);
            if (utf8Match && utf8Match[1]) {
                return decodeURIComponent(utf8Match[1]);
            }
            const filenameMatch = disp.match(/filename="?([^"]+)"?/i);
            if (filenameMatch && filenameMatch[1]) {
                return filenameMatch[1].replace(/['"]/g, '');
            }
            return null;
        };

        const extractedFilename = getFilenameFromDisposition(disposition);
        if (extractedFilename) {
            filename = extractedFilename;
        }

        const blob = new Blob([response.data], { type: 'application/pdf' });
        const blobUrl = URL.createObjectURL(blob);
        const downloadLink = document.createElement('a');
        downloadLink.href = blobUrl;
        downloadLink.download = filename;
        downloadLink.style.display = 'none';
        document.body.appendChild(downloadLink);
        downloadLink.click();

        setTimeout(() => {
            document.body.removeChild(downloadLink);
            URL.revokeObjectURL(blobUrl);
        }, 100);
    } catch (error) {
        console.error('PDF Export Error:', error);
        toast.error(`โหลด PDF ล้มเหลว`, error.response?.data?.error || error.message);
    }
};

function getDegreeType(degreeName) {
    if (degreeName.includes('ดุษฎีบัณฑิต')) return 'ดุษฎีบัณฑิต';
    if (degreeName.includes('มหาบัณฑิต')) return 'มหาบัณฑิต';
    return 'บัณฑิต';
}

function getDegreeLevel(degreeName) {
    if (degreeName.includes('ดุษฎีบัณฑิต')) return 'ป.เอก';
    if (degreeName.includes('มหาบัณฑิต')) return 'ป.โท';
    return 'ป.ตรี';
}

// สรุปข้อมูลตามชื่อปริญญา
const summaryByDegree = computed(() => {
    const summary = {};

    persons.value.forEach((person) => {
        const degree = person.degree || 'ไม่ระบุ';
        if (!summary[degree]) {
            summary[degree] = {
                degree,
                level: getDegreeLevel(degree),
                total: 0,
                reported: 0,
                absent: 0
            };
        }
        summary[degree].total += 1;

        if (person.verified === 1) {
            summary[degree].reported += 1;
        }
    });

    Object.values(summary).forEach((entry) => {
        entry.absent = entry.total - entry.reported;
        entry.percentage = entry.total > 0 ? Math.round((entry.reported / entry.total) * 100) : 0;
    });

    const degreeOrder = ['บัณฑิต', 'ดุษฎีบัณฑิต', 'มหาบัณฑิต'];
    return Object.values(summary).sort((a, b) => {
        return degreeOrder.indexOf(getDegreeType(a.degree)) - degreeOrder.indexOf(getDegreeType(b.degree));
    });
});

// ⭐ เพิ่ม: สรุปข้อมูลตามระดับปริญญา (ป.เอก, ป.โท, ป.ตรี)
const summaryByLevel = computed(() => {
    const levels = {
        'ป.เอก': { total: 0, reported: 0 },
        'ป.โท': { total: 0, reported: 0 },
        'ป.ตรี': { total: 0, reported: 0 }
    };

    summaryByDegree.value.forEach((item) => {
        const level = item.level;
        if (levels[level]) {
            levels[level].total += item.total;
            levels[level].reported += item.reported;
        }
    });

    // คำนวณค่า absent และ percentage เพิ่มเติม
    for (const level in levels) {
        levels[level].absent = levels[level].total - levels[level].reported;
        levels[level].percentage = levels[level].total > 0 ? Math.round((levels[level].reported / levels[level].total) * 100) : 0;
    }

    return levels;
});


// รวมสรุปทั้งหมด
const totalSummary = computed(() => {
    const total = { degree: 'รวมทั้งหมด', total: 0, reported: 0, absent: 0, percentage: '0' };
    summaryByDegree.value.forEach((item) => {
        total.total += item.total;
        total.reported += item.reported;
        total.absent += item.absent;
    });
    total.percentage = total.total > 0 ? Math.round((total.reported / total.total) * 100).toString() : '0';
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

        <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div class="p-4 border-b-8 border-purple-500 shadow card rounded-3xl">
                <h2 class="mb-2 text-lg xl:text-xl font-bold text-center">ปริญญาเอก</h2>
                <div class="grid grid-cols-3 gap-1 text-center">
                    <div>
                        <div class="text-base xl:text-lg font-semibold dark:text-white/70">ทั้งหมด</div>
                        <div class="text-2xl xl:text-4xl font-bold">{{ summaryByLevel['ป.เอก'].total }}</div>
                    </div>
                    <div>
                        <div class="text-base xl:text-lg font-semibold dark:text-white/70">รายงานตัว</div>
                        <div class="text-2xl xl:text-4xl font-bold text-green-600">{{ summaryByLevel['ป.เอก'].reported }}</div>
                    </div>
                    <div>
                        <div class="text-base xl:text-lg font-semibold dark:text-white/70">ขาด</div>
                        <div class="text-2xl xl:text-4xl font-bold text-red-600">{{ summaryByLevel['ป.เอก'].absent }}</div>
                    </div>
                </div>
            </div>

            <div class="p-4 border-b-8 border-indigo-500 shadow card rounded-3xl">
                <h2 class="mb-2 text-lg xl:text-xl font-bold text-center">ปริญญาโท</h2>
                <div class="grid grid-cols-3 gap-1 text-center">
                    <div>
                        <div class="text-base xl:text-lg font-semibold dark:text-white/70">ทั้งหมด</div>
                        <div class="text-2xl xl:text-4xl font-bold">{{ summaryByLevel['ป.โท'].total }}</div>
                    </div>
                    <div>
                        <div class="text-base xl:text-lg font-semibold dark:text-white/70">รายงานตัว</div>
                        <div class="text-2xl xl:text-4xl font-bold text-green-600">{{ summaryByLevel['ป.โท'].reported }}</div>
                    </div>
                    <div>
                        <div class="text-base xl:text-lg font-semibold dark:text-white/70">ขาด</div>
                        <div class="text-2xl xl:text-4xl font-bold text-red-600">{{ summaryByLevel['ป.โท'].absent }}</div>
                    </div>
                </div>
            </div>

            <div class="p-4 border-b-8 border-teal-500 shadow card rounded-3xl">
                <h2 class="mb-2 text-lg xl:text-xl font-bold text-center">ปริญญาตรี</h2>
                <div class="grid grid-cols-3 gap-1 text-center">
                    <div>
                        <div class="text-base xl:text-lg font-semibold dark:text-white/70">ทั้งหมด</div>
                        <div class="text-2xl xl:text-4xl font-bold">{{ summaryByLevel['ป.ตรี'].total }}</div>
                    </div>
                    <div>
                        <div class="text-base xl:text-lg font-semibold dark:text-white/70">รายงานตัว</div>
                        <div class="text-2xl xl:text-4xl font-bold text-green-600">{{ summaryByLevel['ป.ตรี'].reported }}</div>
                    </div>
                    <div>
                        <div class="text-base xl:text-lg font-semibold dark:text-white/70">ขาด</div>
                        <div class="text-2xl xl:text-4xl font-bold text-red-600">{{ summaryByLevel['ป.ตรี'].absent }}</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="grid grid-cols-2 gap-4 md:grid-cols-4">
            <div class="flex items-center justify-between p-4 border-b-8 border-blue-500 rounded-3xl card">
                <div>
                    <div class="text-sm xl:text-lg font-semibold">บัณฑิตทั้งหมด</div>
                    <div class="text-4xl xl:text-5xl font-bold">{{ totalSummary.total }}</div>
                </div>
                <Icon icon="nimbus:user-group" class="text-blue-500" style="width: 36px; height: 36px" />
            </div>

            <div class="flex items-center justify-between p-4 border-b-8 border-green-500 shadow rounded-3xl card">
                <div>
                    <div class="text-sm xl:text-lg font-semibold">รายงานตัวแล้ว</div>
                    <div class="text-4xl xl:text-5xl font-bold">{{ totalSummary.reported }}</div>
                </div>
                <Icon icon="rivet-icons:check-circle" class="text-green-500" style="width: 30px; height: 30px" />
            </div>

            <div class="flex items-center justify-between p-4 border-b-8 border-red-500 shadow rounded-3xl card">
                <div>
                    <div class="text-sm xl:text-lg font-semibold">ขาด</div>
                    <div class="text-4xl xl:text-5xl font-bold">{{ totalSummary.absent }}</div>
                </div>
                <Icon icon="rivet-icons:close-circle" class="text-red-500" style="width: 30px; height: 30px" />
            </div>

            <div class="flex items-center justify-between p-4 border-b-8 border-yellow-300 shadow rounded-3xl card">
                <div>
                    <div class="text-sm xl:text-lg font-semibold">เปอร์เซ็นต์</div>
                    <div class="text-4xl xl:text-5xl font-bold">{{ totalSummary.percentage }}%</div>
                </div>
                <Icon icon="mage:chart-fill" class="text-yellow-300" style="width: 36px; height: 36px" />
            </div>
        </div>


        <div class="card rounded-3xl">
            <div class="relative">
                <Toolbar class="mb-6">
                    <template #start> </template>
                    <template #end>
                        <Button severity="secondary" class="mr-2" @click="exportPDFResult" rounded raised> <Icon icon="lets-icons:export" />โหลดไฟล์เป็น pdf</Button>
                    </template>
                </Toolbar>
            </div>

            <DataTable :value="summaryByDegree" scrollable scrollHeight="500px" class="text-sm" :filters="filters" :loading="loading" filterDisplay="menu">
                <Column field="level" header="วุฒิ" style="min-width: 100px" class="text-lg"></Column>
                <Column field="degree" header="ชื่อปริญญา" style="min-width: 150px" class="text-lg"></Column>
                <Column field="total" header="จำนวนทั้งหมด" style="min-width: 100px" class="text-lg">
                    <template #body="{ data }">
                        <Tag :value="data.total" severity="info" class="px-3 py-1 text-5xl font-bold">
                            <span class="text-lg font-bold">{{ data.total }}</span>
                        </Tag>
                    </template>
                </Column>
                <Column field="reported" header="รายงานตัวแล้ว" style="min-width: 100px" class="text-lg text-green-700">
                    <template #body="{ data }">
                        <Tag :value="data.reported" severity="success" class="px-3 py-1 text-5xl font-bold">
                            <span class="text-lg font-bold">{{ data.reported }}</span>
                        </Tag>
                    </template>
                </Column>
                <Column field="absent" header="ขาด" style="min-width: 100px" class="text-lg text-red-500">
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
                                <div class="h-6 bg-green-500 rounded-full" :style="{ width: Math.round(data.percentage) + '%' }"></div>
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