<script setup>
import { FilterMatchMode } from '@primevue/core/api';
import { onMounted, onBeforeUnmount, ref, computed } from 'vue';
import api from '@/plugins/axios';
import { Icon } from '@iconify/vue';
import { createLocalToast } from '@/components/utils/toastUtils';
import { useAuthStore } from '@/stores/auth';
import { useWebSocketStore } from '@/stores/websocket';

const auth = useAuthStore();

console.log(auth.status);

const toast = createLocalToast();

const persons = ref([]);

async function fetchPersons() {
    loading.value = true;
    try {
        const response = await api.get(`/api/person/`);
        const data = Array.isArray(response.data) ? response.data : response.data.results ?? [];
        persons.value = data;
    } catch (error) {
        console.error('Error fetching persons:', error);
    } finally {
        loading.value = false;
    }
}
onMounted(fetchPersons);

const wsStore = useWebSocketStore(); // ✅ 2. สร้าง instance
let unregisterWsHandler = null; // ✅ 3. สร้างตัวแปรไว้เก็บฟังก์ชันยกเลิก

function handleWsMessage(msg) {
    if (msg.action === 'update') {
        const index = persons.value.findIndex((p) => p.id === msg.id);
        if (index !== -1) {
            if ('verified1' in msg.fields || 'verified2' in msg.fields || 'verified3' in msg.fields) {
                const updatedAts = {
                    1: msg.fields.verified_updated_at1 || persons.value[index]?.verified_updated_at1,
                    2: msg.fields.verified_updated_at2 || persons.value[index]?.verified_updated_at2,
                    3: msg.fields.verified_updated_at3 || persons.value[index]?.verified_updated_at3
                };
                const latest = Object.entries(updatedAts).sort((a, b) => new Date(b[1]) - new Date(a[1]))[0]?.[0];
                msg.fields.verified = msg.fields[`verified${latest}`];
            }
            const updated = { ...persons.value[index], ...msg.fields };
            persons.value.splice(index, 1, updated);

            if (product.value && product.value.id === msg.id) {
                product.value = { ...product.value, ...msg.fields };
            }
        } else {
            console.warn('Person not found for update id:', msg.id);
        }
    } else if (msg.action === 'add') {
        persons.value.push({ id: msg.id, ...msg.fields });
    } else if (msg.action === 'delete') {
        const deletedId = msg.id;
        if (product.value && product.value.id === deletedId) {
            product.value = null;
        }
        persons.value = persons.value.filter((p) => p && p.id !== deletedId);
    } else if (msg.action === 'reset' || msg.action === 'upload') {
        fetchPersons();
    } else if (msg.action === 'bulk_update') {
        msg.ids.forEach((id) => {
            const index = persons.value.findIndex((p) => p.id === id);
            if (index !== -1) {
                const updated = {
                    ...persons.value[index],
                    ...msg.fields
                };

                // ✅ ใช้ฟังก์ชันนี้หาค่า verified ล่าสุด
                updated.verified = getLatestVerified(updated);

                persons.value.splice(index, 1, updated);
            }
        });
    }
}
onMounted(() => {
    fetchPersons();
    unregisterWsHandler = wsStore.registerHandler(handleWsMessage);
});

onBeforeUnmount(() => {
    if (unregisterWsHandler) {
        unregisterWsHandler();
    }
    window.removeEventListener('ws-message', handleWsMessage);
});

const dt = ref();

// Dialog
const productDialog = ref(false);
const UploadDialog = ref(false);
const ExportDialog = ref(false);
const deleteProductDialog = ref(false);
const deletepersonsDialog = ref(false);

const product = ref({});
const selectedpersons = ref([]);
const filters = ref({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS }
});
const submitted = ref(false);
const loading = ref(false);
const filteredVerified = ref(null);

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
        toast.error('ยืนยันไม่สำเร็จ', 'กรุณาพิมพ์คำว่า "RESET" ให้ถูกต้อง');
        resetKeyword.value = '';
        return;
    }
    try {
        await api.post(`/api/reset/`);
        await fetchPersons();
    } catch (error) {
        toast.error('รีเซ็ตล้มเหลว', error.response?.data?.error || 'เกิดข้อผิดพลาด');
    } finally {
        confirmResetDialog2.value = false;
        resetKeyword.value = '';
    }
};

// โหลดข้อมูล
const exportPDF = async () => {
    try {
        // 1. ดึงค่าสถานะที่เลือก (null, 0, 1, 2)
        const status = filteredVerified.value; 

        // 2. สร้าง object สำหรับ query params
        const queryParams = {};
        if (status !== null) {
            // จะส่งค่า '0', '1', หรือ '2'
            queryParams.verified_status = status;
        }
        // ถ้า status เป็น null, เราจะไม่ส่ง param, backend จะถือว่าเป็น 'all'

        const response = await api.get(`/api/export-pdf/`, {
            responseType: 'blob',
            timeout: 30000,
            params: queryParams // 👈 3. ส่ง params ที่สร้างไว้
        });

        if (response.data.size < 1024) {
            throw new Error('ไฟล์ PDF ว่างเปล่า');
        }

        // ... (ส่วนที่เหลือของโค้ดคุณ (การดึงชื่อไฟล์, สร้าง link) ถูกต้องแล้ว) ...
        const disposition = response.headers['content-disposition'];
        let filename = 'รายชื่อ.pdf';
        if (disposition) {
            const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
            if (matches && matches[1]) {
                filename = matches[1].replace(/['"]/g, '');
            }
            const utf8Filename = disposition.match(/filename\*=UTF-8''(.*)/)?.[1];
            if (utf8Filename) {
                filename = decodeURIComponent(utf8Filename);
            }
        }
        const blob = new Blob([response.data], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        setTimeout(() => {
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        }, 100);

    } catch (error) {
        console.error('PDF Export Error:', error);
        alert('การส่งออก PDF ล้มเหลว: ' + error.message);
    }
};

// Export ข้อมูล (CSV / Excel)
const exportData = async (format) => { // format คือ 'xlsx' หรือ 'csv'
    try {
        // 1. ดึงค่าสถานะที่เลือก (null, 0, 1, 2)
        const status = filteredVerified.value; 
        
        // 2. (สำคัญ) แปลง 'xlsx' เป็น 'excel' ให้ตรงกับ URL ของ Django
        const exportFormat = (format === 'xlsx') ? 'excel' : format;

        // 3. สร้าง objectสำหรับ query params
        const queryParams = {};
        if (status !== null) {
            queryParams.verified_status = status;
        }

        const response = await api.get(`/api/export/${exportFormat}/`, { 
            responseType: 'blob',
            params: queryParams // 👈 4. ส่ง params ที่สร้างไว้
        });

        // สร้างชื่อไฟล์เองแทนการอ่านจาก header
        const statusText = filteredVerified.value === null ? 'ทั้งหมด' : 
                          filteredVerified.value === 0 ? 'ยังไม่รายงานตัว' :
                          filteredVerified.value === 1 ? 'รายงานตัวแล้ว' : 'อยู่ในห้องพิธี';
        
        const today = new Date();
        const dateStr = today.getFullYear().toString() + 
                       (today.getMonth() + 1).toString().padStart(2, '0') + 
                       today.getDate().toString().padStart(2, '0');
        
        const filename = `รายชื่อ${statusText}_${dateStr}.${format}`;
        
        console.log('Generated filename:', filename);
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename); 
        document.body.appendChild(link);
        link.click();
        link.remove();
    } catch (error) {
        console.error('Export error:', error);
        if (error.response) {
            console.error('Response status:', error.response.status);
            console.error('Response data:', error.response.data);
            alert(`Export failed: ${error.response.data?.error || error.response.statusText}`);
        } else if (error.request) {
            console.error('Request error:', error.request);
            alert('Export failed: Network error');
        } else {
            console.error('Error:', error.message);
            alert(`Export failed: ${error.message}`);
        }
    }
};

// อัพโหลด
const file = ref(null);
const progress = ref(0);
const processing = ref(false);
const processingInterval = ref(null);
const uploadInProgress = ref(false);
const uploadStartTime = ref(null);
const uploadStats = ref(null);

const handleFileSelect = (event) => {
    file.value = event.target.files[0];
    uploadStats.value = null; // รีเซ็ตสถิติเมื่อเลือกไฟล์ใหม่
};

const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
};

const getFileExtension = (filename) => {
    return filename.split('.').pop().toUpperCase();
};

const handleFileUpload = async () => {
    if (!file.value) {
        alert('กรุณาเลือกไฟล์ก่อน');
        return;
    }

    // จำกัดขนาดไฟล์ไม่เกิน 15MB
    const maxSize = 15 * 1024 * 1024; // 15MB
    if (file.value.size > maxSize) {
        alert('ไฟล์มีขนาดเกิน 15MB');
        return;
    }

    uploadInProgress.value = true;
    progress.value = 0;
    processing.value = false;
    uploadStartTime.value = Date.now();
    uploadStats.value = null;

    const formData = new FormData();
    formData.append('file', file.value);

    try {
        const response = await api.post(`/api/import/`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            onUploadProgress: (progressEvent) => {
                const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                progress.value = Math.min(percent * 0.8, 79); // จำกัดไม่ให้เกิน 79%
            }
        });

        // เริ่มการจำลองการประมวลผลที่ server
        processing.value = true;
        processingInterval.value = setInterval(() => {
            if (progress.value < 99) {
                progress.value += 1;
            } else {
                clearInterval(processingInterval.value);
            }
        }, 50);

        await fetchPersons(); // รอให้ server ทำงานเสร็จ

        clearInterval(processingInterval.value);
        progress.value = 100;

        // คำนวณเวลาที่ใช้
        const uploadTime = ((Date.now() - uploadStartTime.value) / 1000).toFixed(2);
        
        // เก็บสถิติจาก response
        uploadStats.value = {
            ...response.data.stats,
            uploadTime: uploadTime,
            fileName: file.value.name,
            fileSize: formatFileSize(file.value.size),
            fileType: getFileExtension(file.value.name)
        };

    } catch (error) {
        clearInterval(processingInterval.value);
        toast.error('อัปโหลดล้มเหลว', error.response?.data?.error || 'เกิดข้อผิดพลาด');
    } finally {
        uploadInProgress.value = false;
        processing.value = false;
    }
};

// ฟังก์ชันนี้จะถูกเรียกเมื่อกดปุ่ม "ปิด"
const closeDialog = () => {
    file.value = null;
    progress.value = 0;
    uploadInProgress.value = false;
    processing.value = false;
    uploadStats.value = null;
    UploadDialog.value = false;
};

const saveProduct = async () => {
    submitted.value = true;
    if (product?.value?.name?.trim()) {
        try {
            const payload = { ...product.value };
            payload.verified1 = payload.verified;
            delete payload.verified;
            if (payload.id) {
                await api.put(`api/person/${payload.id}/`, payload);
            } else {
                await api.post('api/person/', payload);
            }
            await fetchPersons();
            productDialog.value = false;
        } catch (error) {
            console.error('Error saving data:', error);
            toast.error('เกิดข้อผิดพลาด', error.response?.data?.error || 'บันทึกข้อมูลไม่สำเร็จ');
        }
    } else {
        toast.warn('ข้อมูลไม่ครบ', 'กรุณากรอกชื่อ');
    }
};

const deleteProduct = async () => {
    if (!product.value || !product.value.id) {
        toast.warn('ไม่พบข้อมูล', 'ไม่สามารถลบข้อมูลที่ไม่ถูกต้อง');
        return;
    }

    const deletingId = product.value.id;

    try {
        await api.delete(`/api/person/${deletingId}/`);
        persons.value = persons.value.filter((val) => val.id !== deletingId);
        deleteProductDialog.value = false;
        toast.success('สำเร็จ', 'ลบข้อมูลเรียบร้อย');
    } catch (error) {
        console.error('Error deleting data:', error);

        if (error.response?.status === 404) {
            toast.warn('ไม่พบข้อมูล', 'ข้อมูลถูกลบไปแล้ว');
        } else {
            toast.error('เกิดข้อผิดพลาด', 'ลบข้อมูลไม่สำเร็จ');
        }
    }
};

async function deleteSelectedpersons() {
    if (!selectedpersons.value || selectedpersons.value.length === 0) {
        toast.success('ไม่มีข้อมูล', 'กรุณาเลือกรายการที่จะลบ');
        return;
    }

    const ids = selectedpersons.value.map((person) => person.id).filter((id) => id != null);

    try {
        await api.delete(`/api/person/delete/`, {
            data: { ids },
            headers: {
                'Content-Type': 'application/json'
            }
        });
        persons.value = persons.value.filter((val) => !ids.includes(val.id));
        selectedpersons.value = null;
        deletepersonsDialog.value = false;
        toast.success('สำเร็จ', 'ลบรายการเรียบร้อย');
    } catch (error) {
        console.error('Error deleting data:', error);
        toast.error('เกิดข้อผิดพลาด', error.response?.data?.error || 'ลบรายการไม่สำเร็จ');
    }
}

function confirmDeleteSelected() {
    deletepersonsDialog.value = true;
}

function confirmDeleteProduct(prod) {
    product.value = { ...prod };
    deleteProductDialog.value = true;
}

function confirmUpload() {
    UploadDialog.value = true;
}

function choseExport() {
    ExportDialog.value = true;
}

function openNew() {
    product.value = {};
    submitted.value = false;
    productDialog.value = true;
}

function hideDialog() {
    productDialog.value = false;
    submitted.value = false;
}

function editProduct(prod) {
    const editedProduct = { ...prod };
    editedProduct.verified = getLatestVerified(prod);
    product.value = editedProduct;
    productDialog.value = true;
}

async function updateSelectedVerified(status, field = 'verified1') {
    try {
        const ids = selectedpersons.value.map((p) => p.id);

        await api.put(`/api/person/`, {
            ids,
            verified: status,
            verified_field: field
        });

        persons.value = persons.value.map((p) => (ids.includes(p.id) ? { ...p, [field]: status } : p));
        selectedpersons.value = [];
        await fetchPersons();
        toast.success('สำเร็จ', `เปลี่ยนสถานะเป็น ${status} เรียบร้อย`);
    } catch (error) {
        toast.error('เกิดข้อผิดพลาด', error.response?.data?.error || 'ไม่สามารถเปลี่ยนสถานะได้');
    }
}

const menu1 = ref(null);
const menu2 = ref(null);

function toggleMenu1(event) {
    menu1.value.toggle(event);
}

function toggleMenu2(event) {
    menu2.value.toggle(event);
}

// กรองคนรายงานตัว
const applyVerifiedFilter = (value) => {
    filteredVerified.value = value;
};

const filteredPersons = computed(() => {
    if (filteredVerified.value === null) {
        return persons.value; // แสดงทั้งหมด
    }
    return persons.value.filter((person) => getLatestVerified(person) === filteredVerified.value);
});

const verifiedMenuItems = [
    {
        label: 'ยังไม่รายงานตัว',
        icon: 'rivet-icons:close-circle-solid',
        color: 'text-red-500',
        command: () => updateSelectedVerified(0, 'verified1')
    },
    {
        label: 'รายงานตัวแล้ว',
        icon: 'rivet-icons:check-circle-solid',
        color: 'text-green-500',
        command: () => updateSelectedVerified(1, 'verified1')
    },
    {
        label: 'อยู่ในห้องพิธี',
        icon: 'tdesign:certificate-filled',
        color: 'text-yellow-300',
        command: () => updateSelectedVerified(2, 'verified1')
    }
];

const items = ref([
    {
        label: 'ทั้งหมด',
        icon: 'material-symbols:border-all',
        color: 'text-blue-500',
        command: () => {
            applyVerifiedFilter(null);
        }
    },
    {
        label: 'รายงานตัวแล้ว',
        icon: 'rivet-icons:check-circle-solid',
        color: 'text-green-500',
        command: () => {
            applyVerifiedFilter(1);
        }
    },
    {
        label: 'ยังไม่รายงานตัว',
        icon: 'rivet-icons:close-circle-solid',
        color: 'text-red-500',
        command: () => {
            applyVerifiedFilter(0);
        }
    },
    {
        label: 'อยู่ในห้องพิธี',
        icon: 'tdesign:certificate-filled',
        color: 'text-yellow-300',
        command: () => {
            applyVerifiedFilter(2);
        }
    }
]);

function getLatestVerified(data) {
    const updatedAts = {
        1: data.verified_updated_at1,
        2: data.verified_updated_at2,
        3: data.verified_updated_at3
    };

    // หา key (1, 2, หรือ 3) ของเวลาที่ใหม่ที่สุด
    const latest = Object.entries(updatedAts)
        // Filter out null or undefined timestamps before sorting
        .filter(([, timestamp]) => timestamp)
        .sort((a, b) => new Date(b[1]) - new Date(a[1]))[0]?.[0];

    // ถ้าหา latest ไม่เจอ (อาจจะเพราะทุกค่าเป็น null) ให้คืนค่า verified1 หรือ 0 เป็นค่าเริ่มต้น
    if (!latest) {
        return data.verified1 !== undefined ? data.verified1 : 0;
    }

    return data[`verified${latest}`];
}

const multiSortMeta = ref([
    { field: 'degree_level', order: 1 },  // เรียงจาก ป.เอก > ป.โท > ป.ตรี
    { field: 'seat', order: 1 }  // จากนั้นเรียงตามเลขที่นั่ง
]);

const tableData = computed(() => {
    if (!filteredPersons.value) return [];

    return filteredPersons.value.map((person) => {
        // ใช้ตัวเลขแทน string เพื่อให้เรียงลำดับได้ถูกต้อง
        // 1 = ป.เอก, 2 = ป.โท, 3 = ป.ตรี
        let degree_level = 3; // ค่าเริ่มต้นเป็น ป.ตรี
        let degree_label = 'ป.ตรี';
        
        if (person.degree?.includes('ดุษฎีบัณฑิต')) {
            degree_level = 1;
            degree_label = 'ป.เอก';
        } else if (person.degree?.includes('มหาบัณฑิต')) {
            degree_level = 2;
            degree_label = 'ป.โท';
        }

        return {
            ...person,
            degree_level: degree_level,
            degree_label: degree_label,
            seat: parseInt(person.seat) || 0  // แปลงเป็นตัวเลขสำหรับการเรียง
        };
    });
});

const getExportUrl = (baseUrl) => {
    // ดึงค่าสถานะที่เลือกอยู่ ถ้าไม่มีให้เป็น 'all'
    const status = filteredVerified.value || 'all';
    return `${baseUrl}?verified_status=${status}`;
};
</script>

<template>
    <div class="page-wrapper">
        <div class="card">
            <div class="relative">
                <Toolbar class="mb-6">
                    <template #start>
                        <div class="flex items-center gap-2">
                            <Button v-if="auth.status !== 'Staff'" v-tooltip.top="'เพิ่มรายชื่อ'" severity="secondary" class="mr-2" @click="openNew" rounded raised>
                                <Icon icon="material-symbols:add-2-rounded" />
                            </Button>
                            <Button v-if="auth.status !== 'Staff'" v-tooltip.top="'ลบรายการที่เลือก'" severity="secondary" class="mr-2" @click="confirmDeleteSelected" :disabled="!selectedpersons || !selectedpersons.length" rounded raised>
                                <Icon icon="mdi:trash-can-outline" />
                            </Button>
                            <Button v-if="auth.status !== 'Staff'" v-tooltip.top="'รีเซ็ตข้อมูล'" severity="secondary" class="mr-2" @click="confirmResetdatabase" rounded raised>
                                <Icon icon="lucide:database-backup" />
                            </Button>
                            <Button v-if="auth.status !== 'Staff'" v-tooltip.top="'เปลี่ยนสถานะ'" severity="secondary" @click="toggleMenu1" :disabled="!selectedpersons || selectedpersons.length === 0" rounded raised>
                                <Icon icon="mdi:tag" />
                            </Button>
                            <Menu ref="menu1" :model="verifiedMenuItems" :popup="true">
                                <template #item="{ item }">
                                    <div class="flex items-center gap-2 px-2 py-1">
                                        <Icon :icon="item.icon" :class="item.color" />
                                        <span>{{ item.label }}</span>
                                    </div>
                                </template>
                            </Menu>
                        </div>
                    </template>

                    <template #end>
                        <Button v-if="auth.status !== 'Staff'" :disabled="uploadInProgress" severity="secondary" class="mr-2" @click="confirmUpload" rounded raised> <Icon icon="lets-icons:import" />อัปโหลดไฟล์ </Button>
                        <Button severity="secondary" class="mr-2" @click="choseExport" rounded raised> <Icon icon="lets-icons:export" />โหลดไฟล์ </Button>
                    </template>
                </Toolbar>
            </div>

            <DataTable
                ref="dt"
                v-model:selection="selectedpersons"
                :value="tableData"
                dataKey="id"
                :paginator="true"
                :rows="10"
                :filters="filters"
                paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
                :rowsPerPageOptions="[5, 10, 25, 50]"
                currentPageReportTemplate="จาก   {first} ถึง {last} ของทั้งหมด {totalRecords} คน"
                scrollable
                scrollHeight="600"
                :loading="loading"
                sortMode="multiple"
                v-model:multiSortMeta="multiSortMeta"
            >
                <template #header>
                    <div class="flex flex-wrap items-center justify-between gap-2">
                        <div class="flex">
                            <h4>จัดการรายชื่อบัณฑิต</h4>
                            <span v-if="selectedpersons.length > 0" class="ml-5 text-white/70">[ จำนวนที่เลือก {{ selectedpersons.length }} คน ]</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <Button v-tooltip.top="'เช็คสถานะ'" severity="secondary" @click="toggleMenu2" rounded raised>
                                <Icon icon="mdi:tag" />
                                <span v-if="filteredVerified === null">ทั้งหมด</span>
                                <Icon v-else-if="filteredVerified === 1" icon="rivet-icons:check-circle-solid" class="text-green-500"></Icon>
                                <Icon v-else-if="filteredVerified === 0" icon="rivet-icons:close-circle-solid" class="text-red-500"></Icon>
                                <Icon v-else-if="filteredVerified === 2" icon="tdesign:certificate-filled" class="text-yellow-300"></Icon>
                            </Button>
                            <Menu ref="menu2" :model="items" :popup="true">
                                <template #item="{ item }">
                                    <div class="flex items-center gap-2 px-2 py-1">
                                        <Icon :icon="item.icon" :class="item.color" />
                                        <span>{{ item.label }}</span>
                                    </div>
                                </template>
                            </Menu>
                            <IconField>
                                <InputIcon>
                                    <i class="pi pi-search" />
                                </InputIcon>
                                <InputText v-model="filters['global'].value" placeholder="ค้นหาข้อมูลบัณฑิต" />
                            </IconField>
                        </div>
                    </div>
                </template>

                <Column v-if="auth.status !== 'Staff'" selectionMode="multiple" style="width: 3rem" :exportable="false"></Column>
                <Column field="degree_level" header="วุฒิ" sortable style="min-width: 5rem">
                    <template #body="slotProps">
                        {{ slotProps.data.degree_label }}
                    </template>
                </Column>
                <Column field="id" header="เลขที่บัณฑิต" sortable style="min-width: 5rem"></Column>
                <Column field="nisit" header="รหัสนักศึกษา" sortable style="min-width: 10rem"></Column>
                <!-- <Column header="Image">
                    <template #body="slotProps">
                        <img :src="`https://primefaces.org/cdn/primevue/images/product/${slotProps.data.image}`" :alt="slotProps.data.image" class="rounded" style="width: 64px" />
                    </template>
                </Column> -->
                <Column field="name" header="ชื่อ - สกุล" sortable style="min-width: 12rem"></Column>
                <Column field="degree" header="ชื่อหลักสูตร" sortable style="min-width: 10rem"></Column>
                <!-- <Column field="rating" header="Reviews" sortable style="min-width: 12rem">
                    <template #body="slotProps">
                        <Rating :modelValue="slotProps.data.rating" :readonly="true" />
                    </template>
                </Column> -->
                <Column field="seat" header="เลขที่นั่ง" sortable style="min-width: 8rem"></Column>
                <Column field="verified" header="รายงานตัว" dataType="boolean" bodyClass="text-center" style="min-width: 8rem">
                    <template #body="{ data }">
                        <template v-if="getLatestVerified(data) === 1">
                            <Icon class="text-green-500 icon" icon="rivet-icons:check-circle-solid" />
                        </template>
                        <template v-else-if="getLatestVerified(data) === 2">
                            <Icon class="text-yellow-300 icon" icon="tdesign:certificate-filled" />
                        </template>
                        <template v-else>
                            <Icon class="text-red-500 icon" icon="rivet-icons:close-circle-solid" />
                        </template>
                    </template>
                    <template #filter="{ filterModel }">
                        <label for="verified-filter" class="font-bold"> Verified </label>
                        <Checkbox v-model="filterModel.value" :indeterminate="filterModel.value === null" binary inputId="verified-filter" />
                    </template>
                </Column>
                <Column v-if="auth.status !== 'Staff'" :exportable="false" frozen alignFrozen="right" style="min-width: 120px; max-width: 140px; text-align: center">
                    <template #body="slotProps">
                        <div class="flex">
                            <div class="flex justify-center gap-2">
                                <Button icon="pi pi-pencil" outlined rounded class="p-1 mr-2" @click="editProduct(slotProps.data)" />
                            </div>
                            <div class="flex justify-center gap-2">
                                <Button icon="pi pi-trash" outlined rounded severity="danger" class="p-1" @click="confirmDeleteProduct(slotProps.data)" />
                            </div>
                        </div>
                    </template>
                </Column>
            </DataTable>
        </div>

        <Dialog v-model:visible="productDialog" :style="{ width: '850px' }" header="รายละเอียดบัณฑิต" :modal="true" class="graduate-dialog">
            <div class="grid grid-cols-2 gap-x-6 gap-y-5">
                <!-- คอลัมน์ซ้าย -->
                <div class="space-y-5">
                    <div>
                        <label for="id" class="block mb-2 text-sm font-semibold text-surface-700 dark:text-surface-300">ลำดับ</label>
                        <InputText id="id" v-model.trim="product.id" fluid />
                    </div>
                    <div>
                        <label for="nisit" class="block mb-2 text-sm font-semibold text-surface-700 dark:text-surface-300">รหัสนักศึกษา</label>
                        <InputText id="nisit" v-model.trim="product.nisit" fluid />
                    </div>
                    <div>
                        <label for="name" class="block mb-2 text-sm font-semibold text-surface-700 dark:text-surface-300">
                            ชื่อ - สกุล <span class="text-red-500">*</span>
                        </label>
                        <InputText id="name" v-model.trim="product.name" required="true" autofocus :invalid="submitted && !product.name" fluid />
                        <small v-if="submitted && !product.name" class="text-red-500">กรุณากรอกชื่อ - สกุล</small>
                    </div>
                    <div>
                        <label for="seat" class="block mb-2 text-sm font-semibold text-surface-700 dark:text-surface-300">ที่นั่ง</label>
                        <InputText id="seat" v-model.trim="product.seat" fluid />
                    </div>
                </div>
                <!-- คอลัมน์ขวา -->
                <div class="space-y-5">
                    <div>
                        <label for="degree" class="block mb-2 text-sm font-semibold text-surface-700 dark:text-surface-300">
                            ชื่อปริญญา <span class="text-red-500">*</span>
                        </label>
                        <InputText id="degree" v-model.trim="product.degree" required="true" :invalid="submitted && !product.degree" fluid />
                        <small v-if="submitted && !product.degree" class="text-red-500">กรุณากรอกชื่อปริญญา</small>
                    </div>
                    <div>
                        <label for="rfid" class="block mb-2 text-sm font-semibold text-surface-700 dark:text-surface-300">รหัส RFID</label>
                        <InputText id="rfid" v-model.trim="product.rfid" fluid placeholder="ระบุรหัส RFID (ถ้ามี)" />
                    </div>
                    <div>
                        <span class="block mb-3 text-sm font-semibold text-surface-700 dark:text-surface-300">สถานะรายงานตัว</span>
                        <div class="flex justify-between gap-3">
                            <div class="flex items-center justify-center flex-1 gap-2 p-3 transition-all border-2 rounded-lg cursor-pointer hover:shadow-md" 
                                 :class="product.verified === 0 ? 'border-red-500 bg-red-50 dark:bg-red-900/20' : 'border-surface-300 dark:border-surface-700'"
                                 @click="product.verified = 0">
                                <RadioButton id="verified0" v-model="product.verified" name="verified" :value="0" />
                                <label for="verified0" class="flex flex-col items-center gap-1 cursor-pointer">
                                    <Icon icon="rivet-icons:close-circle-solid" class="text-2xl text-red-500" />
                                    <span class="text-xs font-medium">ยังไม่รายงาน</span>
                                </label>
                            </div>
                            <div class="flex items-center justify-center flex-1 gap-2 p-3 transition-all border-2 rounded-lg cursor-pointer hover:shadow-md"
                                 :class="product.verified === 1 ? 'border-green-500 bg-green-50 dark:bg-green-900/20' : 'border-surface-300 dark:border-surface-700'"
                                 @click="product.verified = 1">
                                <RadioButton id="verified1" v-model="product.verified" name="verified" :value="1" />
                                <label for="verified1" class="flex flex-col items-center gap-1 cursor-pointer">
                                    <Icon icon="rivet-icons:check-circle-solid" class="text-2xl text-green-500" />
                                    <span class="text-xs font-medium">รายงานแล้ว</span>
                                </label>
                            </div>
                            <div class="flex items-center justify-center flex-1 gap-2 p-3 transition-all border-2 rounded-lg cursor-pointer hover:shadow-md"
                                 :class="product.verified === 2 ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20' : 'border-surface-300 dark:border-surface-700'"
                                 @click="product.verified = 2">
                                <RadioButton id="verified2" v-model="product.verified" name="verified" :value="2" />
                                <label for="verified2" class="flex flex-col items-center gap-1 cursor-pointer">
                                    <Icon icon="tdesign:certificate-filled" class="text-2xl text-yellow-500" />
                                    <span class="text-xs font-medium">ในห้องพิธี</span>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <template #footer>
                <div class="flex justify-end gap-2">
                    <Button label="ยกเลิก" icon="pi pi-times" @click="hideDialog" severity="secondary" text />
                    <Button label="บันทึก" icon="pi pi-check" @click="saveProduct" />
                </div>
            </template>
        </Dialog>

        <Dialog v-model:visible="UploadDialog" :modal="true" :closable="!uploadInProgress" :style="{ width: '600px' }" class="upload-dialog">
            <template #header>
                <div class="flex items-center gap-3">
                    <Icon icon="material-symbols:cloud-upload" class="text-3xl text-primary-500" />
                    <span class="text-xl font-semibold">{{ progress >= 100 ? 'สรุปผลการอัปโหลด' : 'อัปโหลดไฟล์' }}</span>
                </div>
            </template>

            <div class="flex flex-col gap-6 py-4">
                <!-- ส่วนแสดงไฟล์ที่เลือก -->
                <div v-if="file && !uploadStats" class="p-4 border-2 border-dashed rounded-xl bg-surface-50 dark:bg-surface-800">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <Icon 
                                :icon="file.name.endsWith('.xlsx') ? 'vscode-icons:file-type-excel' : 'catppuccin:csv'" 
                                class="text-4xl" 
                            />
                            <div>
                                <p class="font-semibold text-surface-900 dark:text-surface-0">{{ file.name }}</p>
                                <p class="text-sm text-surface-600 dark:text-surface-400">{{ formatFileSize(file.size) }}</p>
                            </div>
                        </div>
                        <Tag severity="info" class="px-3 py-1">{{ getFileExtension(file.name) }}</Tag>
                    </div>
                </div>

                <!-- ปุ่มเลือกไฟล์ -->
                <div v-if="!file && !uploadInProgress" class="flex flex-col items-center gap-3 py-8">
                    <Icon icon="material-symbols:upload-file" class="text-6xl text-surface-400" />
                    <p class="text-sm text-surface-600 dark:text-surface-400">เลือกไฟล์ Excel (.xlsx) หรือ CSV (.csv)</p>
                    <small class="text-xs text-surface-500">ขนาดไฟล์ไม่เกิน 15 MB</small>
                    <input type="file" accept=".xlsx,.csv" @change="handleFileSelect" ref="fileInput" hidden />
                    <Button @click="$refs.fileInput.click()" severity="secondary" size="large">
                        <Icon icon="material-symbols:folder-open" class="mr-2" />
                        เลือกไฟล์
                    </Button>
                </div>

                <!-- Progress Bar -->
                <div v-if="uploadInProgress || (progress > 0 && progress < 100)" class="flex flex-col gap-3">
                    <div class="flex items-center justify-between text-sm">
                        <span class="font-medium text-surface-700 dark:text-surface-300">
                            {{ progress < 80 ? 'กำลังอัปโหลด...' : 'กำลังประมวลผล...' }}
                        </span>
                        <span class="font-bold text-primary-600">{{ Math.round(progress) }}%</span>
                    </div>
                    <ProgressBar :value="progress" class="h-3" />
                </div>

                <!-- แสดงสถิติหลังอัปโหลดเสร็จ -->
                <div v-if="uploadStats" class="flex flex-col gap-4">
                    <!-- ข้อมูลไฟล์ -->
                    <div class="p-3 border rounded-lg bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
                        <div class="flex items-center gap-2 mb-2">
                            <Icon icon="line-md:confirm-circle" class="text-xl text-green-600" />
                            <h3 class="text-xl font-semibold text-green-800 dark:text-green-200">อัปโหลดสำเร็จ!</h3>
                        </div>
                        <div class="grid grid-cols-4 gap-2 text-base text-center">
                            <div>
                                <span class="text-surface-600 dark:text-surface-400">ชื่อไฟล์:</span>
                                <p class="font-medium text-surface-900 dark:text-surface-0 truncate">{{ uploadStats.fileName }}</p>
                            </div>
                            <div>
                                <span class="text-surface-600 dark:text-surface-400">ประเภท:</span>
                                <p class="font-medium text-surface-900 dark:text-surface-0">{{ uploadStats.fileType }}</p>
                            </div>
                            <div>
                                <span class="text-surface-600 dark:text-surface-400">ขนาด:</span>
                                <p class="font-medium text-surface-900 dark:text-surface-0">{{ uploadStats.fileSize }}</p>
                            </div>
                            <div>   
                                <span class="text-surface-600 dark:text-surface-400">เวลา:</span>
                                <p class="font-medium text-surface-900 dark:text-surface-0">{{ uploadStats.uploadTime }}s</p>
                            </div>
                        </div>
                    </div>

                    <!-- สถิติข้อมูล และระดับปริญญา -->
                    <div class="grid grid-cols-2 gap-3">
                        <div class="grid grid-cols-1 gap-2">
                            <div class="p-3 text-center border rounded-lg bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
                                <Icon icon="material-symbols:database" class="mb-1 text-2xl text-blue-600" />
                                <p class="text-3xl font-bold text-blue-900 dark:text-blue-100">{{ uploadStats.imported_count }}</p>
                                <p class="text-lg text-blue-700 dark:text-blue-300">รายการที่นำเข้า</p>
                                <p class="mt-1 text-base text-surface-600 dark:text-surface-400">
                                    ใหม่: {{ uploadStats.new_count }} | อัปเดต: {{ uploadStats.updated_count }}
                                </p>
                            </div>
                            <!-- คอลัมน์กลาง: มีรหัส RFID -->
                            <div class="p-3 text-center border rounded-lg bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800">
                                <Icon icon="flowbite:tag-solid" class="mb-1 text-2xl text-purple-600" />
                                <p class="text-3xl font-bold text-purple-900 dark:text-purple-100">{{ uploadStats.rfid_count }}</p>
                                <p class="text-lg text-purple-700 dark:text-purple-300">มีรหัส RFID</p>
                                <p class="mt-1 text-base text-surface-600 dark:text-surface-400">
                                    จากทั้งหมด {{ uploadStats.total_count }} คน
                                </p>
                            </div>
                        </div>
                        
                        <div class="flex flex-col justify-between gap-2">
                            <!-- ป.ตรี -->
                            <div class="flex items-center gap-3 p-3 border rounded-lg bg-cyan-50 dark:bg-cyan-900/20 border-cyan-200 dark:border-cyan-800 flex-1">
                                <Icon icon="fluent:hat-graduation-16-filled" class="text-2xl text-cyan-600 flex-shrink-0" />
                                <div class="flex-1">
                                    <p class="text-xl font-bold text-cyan-900 dark:text-cyan-100">{{ uploadStats.bachelor_count }} คน</p>
                                    <p class="text-sm text-cyan-700 dark:text-cyan-300">ปริญญาตรี</p>
                                </div>
                            </div>
                            
                            <!-- ป.โท -->
                            <div class="flex items-center gap-3 p-3 border rounded-lg bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800 flex-1">
                                <Icon icon="fluent:hat-graduation-16-filled" class="text-2xl text-orange-600 flex-shrink-0" />
                                <div class="flex-1">
                                    <p class="text-xl font-bold text-orange-900 dark:text-orange-100">{{ uploadStats.master_count }} คน</p>
                                    <p class="text-sm text-orange-700 dark:text-orange-300">ปริญญาโท</p>
                                </div>
                            </div>
                            
                            <!-- ป.เอก -->
                            <div class="flex items-center gap-3 p-3 border rounded-lg bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 flex-1">
                                <Icon icon="fluent:hat-graduation-16-filled" class="text-2xl text-red-600 flex-shrink-0" />
                                <div class="flex-1">
                                    <p class="text-xl font-bold text-red-900 dark:text-red-100">{{ uploadStats.doctor_count }} คน</p>
                                    <p class="text-sm text-red-700 dark:text-red-300">ปริญญาเอก</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <template #footer>
                <div class="flex justify-end gap-2">
                    <Button 
                        v-if="progress < 100" 
                        label="ยกเลิก" 
                        severity="secondary" 
                        @click="closeDialog" 
                        :disabled="uploadInProgress" 
                        text
                    />
                    <Button 
                        v-if="progress < 100" 
                        label="อัปโหลด" 
                        icon="pi pi-upload" 
                        @click="handleFileUpload" 
                        :loading="uploadInProgress" 
                        :disabled="!file || uploadInProgress" 
                    />
                    <Button 
                        v-if="progress >= 100" 
                        label="ปิด" 
                        icon="pi pi-check" 
                        @click="closeDialog" 
                        severity="success" 
                    />
                </div>
            </template>
        </Dialog>

        <!-- Toast Notification -->
        <Toast position="top-center" group="crud">
            <template #message="slotProps">
                <div class="flex items-center gap-3">
                    <Icon :icon="slotProps.message.severity === 'success' ? 'line-md:confirm-circle-twotone' : 'line-md:close-circle-twotone'" class="text-2xl" />
                    <div>
                        <p class="font-bold">{{ slotProps.message.summary }}</p>
                        <p class="text-sm">{{ slotProps.message.detail }}</p>
                    </div>
                </div>
            </template>
        </Toast>

        <Dialog v-model:visible="ExportDialog" header="ยืนยันการโหลดไฟล์" :modal="true">
            <div class="flex items-center justify-center gap-4 mb-5">  
                <div class="inline-flex items-center flex-wrap gap-2 text-base"> 
                    <span>คุณต้องการโหลดไฟล์</span>
                    <span class="font-bold"> <span v-if="filteredVerified === null" class="text-blue-500">
                            <Tag severity="info" class="px-2 py-1 rounded-xl">
                                <Icon icon="material-symbols:border-all" class="mr-1" />
                                ทั้งหมด</Tag>
                        </span>
                        <span v-else-if="filteredVerified === 1" class="text-green-500">
                            <Tag severity="success" class="px-2 py-1 rounded-xl">
                                <Icon icon="rivet-icons:check-circle-solid" class="mr-1" />
                                รายงานตัวแล้ว</Tag>
                        </span>
                        <span v-else-if="filteredVerified === 0" class="text-red-500">
                            <Tag severity="danger" class="px-2 py-1 rounded-xl">
                                <Icon icon="rivet-icons:close-circle-solid" class="mr-1" />
                                ยังไม่รายงานตัว</Tag>
                        </span>
                        <span v-else class="text-yellow-500">
                            <Tag severity="warn" class="px-2 py-1 rounded-xl">
                                <Icon icon="tdesign:certificate-filled" class="mr-1" />
                                อยู่ในห้องพิธี</Tag>
                        </span>
                    </span> 
                    <span>ใช่หรือไม่ ?</span>
                </div>
            </div>
            
            <div class="flex items-center justify-center">
                <Button severity="secondary" class="mr-2" @click="exportData('xlsx')" rounded raised>
                    <Icon icon="vscode-icons:file-type-excel"></Icon>
                    <span class="ml-2">โหลดไฟล์เป็น Excel</span>
                </Button>
                <Button severity="secondary" class="mr-2" @click="exportData('csv')" rounded raised>
                    <Icon icon="catppuccin:csv"></Icon>
                    <span class="ml-2">โหลดไฟล์เป็น CSV</span>
                </Button>
                <Button severity="secondary" class="mr-2" @click="exportPDF" rounded raised>
                    <Icon icon="vscode-icons:file-type-pdf2" />
                    <span class="ml-2">โหลดไฟล์เป็น PDF</span>
                </Button>
            </div>
        </Dialog>

        <!-- Dialog ยืนยันขั้นที่ 1 -->
        <Dialog v-model:visible="confirmResetDialog1" header="ยืนยันการรีเซ็ต" :modal="true" :style="{ width: '500px' }">
            <div class="flex items-center gap-4 p-4">
                <Icon icon="bi:exclamation-triangle-fill" class="text-yellow-300" />
                <div>
                    <h3 class="mb-2 text-lg font-bold">คุณแน่ใจที่จะรีเซ็ตฐานข้อมูลทั้งหมด?</h3>
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

        <Dialog v-model:visible="deleteProductDialog" header="ยืนยันการลบ" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span v-if="product"
                    >คุณแน่ใจหรือไม่ที่จะลบลำดับที่ <b>{{ product.id }}</b> <b>{{ product.name }}</b>
                    ?
                </span>
            </div>
            <template #footer>
                <Button label="ยกเลิก" icon="pi pi-times" text @click="deleteProductDialog = false" severity="danger" />
                <Button label="ยืนยัน" icon="pi pi-check" text @click="deleteProduct" />
            </template>
        </Dialog>

        <Dialog v-model:visible="deletepersonsDialog" header="การยืนยัน" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span v-if="product">แน่ใจว่าจะลบที่เลือกไว้ ?</span>
            </div>
            <template #footer>
                <Button label="No" icon="pi pi-times" text @click="deletepersonsDialog = false" severity="danger" />
                <Button label="Yes" icon="pi pi-check" text @click="deleteSelectedpersons" />
            </template>
        </Dialog>
    </div>
</template>

<style scoped>
.iconify {
    width: 18px;
    height: 18px;
}
</style>
