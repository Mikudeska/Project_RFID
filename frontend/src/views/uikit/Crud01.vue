<script setup>
import { FilterMatchMode } from '@primevue/core/api';
import { onMounted, onBeforeUnmount, ref, computed } from 'vue';
import api from '@/plugins/axios';
import { Icon } from '@iconify/vue';
import { createLocalToast } from '@/components/utils/toastUtils';

const toast = createLocalToast();

function formatId(id) {
    return id.toString().padStart(4, '0');
}

// ฟังก์ชันเพิ่ม formatted_id ให้กับข้อมูล
function addFormattedId(person) {
    return {
        ...person,
        formatted_id: formatId(person.id)
    };
}

const persons = ref([]);

async function fetchPersons() {
    loading.value = true;
    try {
        const response = await api.get(`/api/person/`);
        const data = Array.isArray(response.data) ? response.data : response.data.results ?? [];
        persons.value = data.map(addFormattedId);
    } catch (error) {
        console.error('Error fetching persons:', error);
    } finally {
        loading.value = false;
    }
}
onMounted(fetchPersons);

function handleWsMessage(event) {
    const msg = event.detail;
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
    }
}

onMounted(() => {
    window.addEventListener('ws-message', handleWsMessage);
});

onBeforeUnmount(() => {
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
const selectedpersons = ref();
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
        const response = await api.get(`/api/export-pdf/`, {
            responseType: 'blob',
            timeout: 30000
        });

        if (response.data.size < 1024) {
            throw new Error('ไฟล์ PDF ว่างเปล่า');
        }

        // อ่านชื่อไฟล์จาก header
        const disposition = response.headers['content-disposition'];
        let filename = 'รายชื่อ.pdf';

        if (disposition) {
            // วิธีที่ 1: แยกด้วย regex
            const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
            if (matches && matches[1]) {
                filename = matches[1].replace(/['"]/g, '');
            }

            // วิธีที่ 2: สำหรับ UTF-8 filename (ทางเลือกเสริม)
            const utf8Filename = disposition.match(/filename\*=UTF-8''(.*)/)?.[1];
            if (utf8Filename) {
                filename = decodeURIComponent(utf8Filename);
            }
        }

        // สร้างลิงก์ดาวน์โหลด
        const blob = new Blob([response.data], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();

        // ล้างทรัพยากร
        setTimeout(() => {
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        }, 100);
    } catch (error) {
        console.error('PDF Export Error:', error);
        alert('การส่งออก PDF ล้มเหลว: ' + error.message);
    }
};

// Export ข้อมูล
const exportData = async (format) => {
    try {
        const response = await api.get(`/api/export/${format}/`, { responseType: 'blob' });

        // สร้างลิงก์ดาวน์โหลด
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `persons${format}.${format}`);
        document.body.appendChild(link);
        link.click();
        link.remove();
    } catch (error) {
        console.error('Export error:', error);
    }
};

// อัพโหลด
const file = ref(null);
const progress = ref(0);
const processing = ref(false);
const processingInterval = ref(null);
const uploadInProgress = ref(false);

const handleFileSelect = (event) => {
    file.value = event.target.files[0];
};

const handleFileUpload = async () => {
    if (!file.value) {
        alert('กรุณาเลือกไฟล์ก่อน');
        return;
    }

    uploadInProgress.value = true;
    progress.value = 0;
    processing.value = false;

    const formData = new FormData();
    formData.append('file', file.value);

    try {
        await api.post(`/api/import/`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            onUploadProgress: (progressEvent) => {
                const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                progress.value = Math.min(percent * 0.8, 95); // จำกัดไม่ให้เกิน %
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
    UploadDialog.value = false;
};

const saveProduct = async () => {
    submitted.value = true;

    // ตรวจสอบว่ามีชื่อหรือไม่ (name.trim)
    if (product?.value?.name?.trim()) {
        try {
            if (product.value.id) {
                await api.put(`api/person/${product.value.id}/`, product.value);
            } else {
                await api.post('api/person/', product.value);
            }
            // ดึงข้อมูลใหม่หลังบันทึก เพื่ออัพเดตตารางหรือรายการ
            await fetchPersons();
            // ปิด dialog
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
    product.value = { ...prod };
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

        // อัปเดตแสดงผลเฉพาะ field ที่ถูกเปลี่ยน
        persons.value = persons.value.map((p) => (ids.includes(p.id) ? { ...p, [field]: status } : p));

        selectedpersons.value = null;
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
    return persons.value.filter((person) => person.verified1 === filteredVerified.value);
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
        label: 'รีเซ็ต',
        icon: 'grommet-icons:power-reset',
        color: 'text-green-500',
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
    const latest = Object.entries(updatedAts).sort((a, b) => new Date(b[1]) - new Date(a[1]))[0]?.[0];
    return data[`verified${latest}`];
}
</script>

<template>
    <div class="page-wrapper">
        <div class="card">
            <Toolbar class="mb-6">
                <template #start>
                    <Button v-tooltip.top="'เพิ่มรายชื่อ'" severity="secondary" class="mr-2" @click="openNew" rounded raised>
                        <Icon icon="material-symbols:add-2-rounded" />
                    </Button>
                    <Button v-tooltip.top="'ลบรายการที่เลือก'" severity="secondary" class="mr-2" @click="confirmDeleteSelected" :disabled="!selectedpersons || !selectedpersons.length" rounded raised>
                        <Icon icon="mdi:trash-can-outline" />
                    </Button>
                    <Button v-tooltip.top="'รีเซ็ตข้อมูล'" severity="secondary" class="mr-2" @click="confirmResetdatabase" rounded raised>
                        <Icon icon="lucide:database-backup" />
                    </Button>
                    <Button v-tooltip.top="'เปลี่ยนสถานะ'" severity="secondary" @click="toggleMenu1" :disabled="!selectedpersons || selectedpersons.length === 0" rounded raised>
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
                </template>

                <template #end>
                    <Button :disabled="uploadInProgress" severity="secondary" class="mr-2" @click="confirmUpload" rounded raised> <Icon icon="lets-icons:import" />อัปโหลดไฟล์</Button>
                    <Button severity="secondary" class="mr-2" @click="choseExport" rounded raised> <Icon icon="lets-icons:export" />โหลดไฟล์ </Button>
                </template>
            </Toolbar>
            <DataTable
                ref="dt"
                v-model:selection="selectedpersons"
                :value="filteredPersons"
                dataKey="id"
                :paginator="true"
                :rows="10"
                :filters="filters"
                paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
                :rowsPerPageOptions="[5, 10, 25, 50]"
                currentPageReportTemplate="จาก   {first} ถึง {last} ของทั้งหมด {totalRecords} คน"
                scrollable
                scrollHeight="600"
                :sortField="'formatted_id'"
                :sortOrder="1"
                :loading="loading"
            >
                <template #header>
                    <div class="flex flex-wrap items-center justify-between gap-2">
                        <div>
                            <h4 class="m-0">จัดการรายชื่อบัญฑิต</h4>
                        </div>
                        <div class="flex items-center gap-2">
                            <Button v-tooltip.top="'เช็คสถานะ'" severity="secondary" @click="toggleMenu2" rounded raised>
                                <Icon icon="mdi:tag" />
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
                                <InputText v-model="filters['global'].value" placeholder="ค้นหาข้อมูลบัญฑิต" />
                            </IconField>
                        </div>
                    </div>
                </template>

                <Column selectionMode="multiple" style="width: 3rem" :exportable="false"></Column>
                <Column field="formatted_id" header="ลำดับที่" sortable style="min-width: 6rem"></Column>
                <Column field="nisit" header="รหัสนิสิต" sortable style="min-width: 10rem"></Column>
                <!-- <Column header="Image">
                    <template #body="slotProps">
                        <img :src="`https://primefaces.org/cdn/primevue/images/product/${slotProps.data.image}`" :alt="slotProps.data.image" class="rounded" style="width: 64px" />
                    </template>
                </Column> -->
                <Column field="name" header="ชื่อ-นามสกุล" sortable style="min-width: 12rem"></Column>
                <Column field="degree" header="ชื่อปริญญา" sortable style="min-width: 10rem"></Column>
                <!-- <Column field="rating" header="Reviews" sortable style="min-width: 12rem">
                    <template #body="slotProps">
                        <Rating :modelValue="slotProps.data.rating" :readonly="true" />
                    </template>
                </Column> -->
                <Column field="seat" header="เลขที่นั่ง" sortable style="min-width: 8rem"></Column>
                <Column field="verified" :body="(data) => getLatestVerified(data)" header="รายงานตัว" dataType="boolean" bodyClass="text-center" style="min-width: 8rem">
                    <template #body="{ data }">
                        <Icon
                            class="icon"
                            :icon="data.verified === 1 ? 'rivet-icons:check-circle-solid' : data.verified === 0 ? 'rivet-icons:close-circle-solid' : 'tdesign:certificate-filled'"
                            :class="{
                                'text-green-500': data.verified === 1,
                                'text-red-500': data.verified === 0,
                                'text-yellow-300': data.verified === 2
                            }"
                        />
                    </template>
                    <template #filter="{ filterModel }">
                        <label for="verified-filter" class="font-bold"> Verified </label>
                        <Checkbox v-model="filterModel.value" :indeterminate="filterModel.value === null" binary inputId="verified-filter" />
                    </template>
                </Column>
                <Column :exportable="false" frozen alignFrozen="right" style="min-width: 120px; max-width: 140px; text-align: center">
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

        <Dialog v-model:visible="productDialog" :style="{ width: '450px' }" header="รายละเอียดบัญฑิต" :modal="true">
            <div class="flex flex-col gap-6">
                <div>
                    <label for="formatted_id" class="block mb-3 font-bold">ลำดับ</label>
                    <InputText id="formatted_id" v-model.trim="product.formatted_id" autofocus :invalid="submitted && !product.formatted_id" fluid :disabled="true" />
                </div>
                <div>
                    <label for="nisit" class="block mb-3 font-bold">รหัสนิสิต</label>
                    <InputText id="nisit" v-model.trim="product.nisit" autofocus :invalid="submitted && !product.nisit" fluid :disabled="true" />
                </div>
                <div>
                    <label for="name" class="block mb-3 font-bold">ชื่อ-นามสกุล</label>
                    <InputText id="name" v-model.trim="product.name" required="true" autofocus :invalid="submitted && !product.name" fluid />
                    <small v-if="submitted && !product.name" class="text-red-500">จำเป็นต้องใส่</small>
                </div>
                <div>
                    <label for="degree" class="block mb-3 font-bold">ชื่อปริญญา</label>
                    <InputText id="degree" v-model.trim="product.degree" required="true" autofocus :invalid="submitted && !product.degree" fluid />
                    <small v-if="submitted && !product.degree" class="text-red-500">จำเป็นต้องใส่</small>
                </div>
                <div>
                    <label for="seat" class="block mb-3 font-bold">ที่นั่ง</label>
                    <InputText id="seat" v-model.trim="product.seat" autofocus :invalid="submitted && !product.degree" fluid :disabled="true" />
                </div>
                <div>
                    <span class="block mb-4 font-bold">สถานะรายงานตัว</span>
                    <div class="grid grid-cols-12 gap-4">
                        <div class="flex items-center col-span-4 gap-2">
                            <RadioButton id="verified1" v-model="product.verified1" name="verified" :value="1" />
                            <label for="verified1">
                                <Icon icon="rivet-icons:check-circle-solid" class="text-green-500" />
                            </label>
                        </div>
                        <div class="flex items-center col-span-4 gap-2">
                            <RadioButton id="verified0" v-model="product.verified1" name="verified" :value="0" />
                            <label for="verified0">
                                <Icon icon="rivet-icons:close-circle-solid" class="text-red-500" />
                            </label>
                        </div>
                        <div class="flex items-center col-span-4 gap-2">
                            <RadioButton id="verified2" v-model="product.verified1" name="verified" :value="2" />
                            <label for="verified2">
                                <Icon icon="tdesign:certificate-filled" class="text-yellow-300" />
                            </label>
                        </div>
                    </div>
                </div>
                <div>
                    <label for="rfid" class="block mb-3 font-bold">รหัส RFID</label>
                    <InputText id="rfid" v-model.trim="product.rfid" required="true" autofocus :invalid="submitted && !product.rfid" fluid />
                </div>
                <!--

                <div class="grid grid-cols-12 gap-4">
                    <div class="col-span-6">
                        <label for="price" class="block mb-3 font-bold">Price</label>
                        <InputNumber id="price" v-model="product.price" mode="currency" currency="USD" locale="en-US" fluid />
                    </div>
                    <div class="col-span-6">
                        <label for="quantity" class="block mb-3 font-bold">Quantity</label>
                        <InputNumber id="quantity" v-model="product.quantity" integeronly fluid />
                    </div>
                </div> -->
            </div>

            <template #footer>
                <Button label="Cancel" icon="pi pi-times" text @click="hideDialog" severity="danger" />
                <Button label="Save" icon="pi pi-check" text @click="saveProduct" />
            </template>
        </Dialog>

        <Dialog v-model:visible="UploadDialog" header="อัปโหลดไฟล์" :modal="true" :closable="false">
            <div class="flex flex-col items-center gap-4">
                <div v-if="file" class="py-2">
                    <div class="flex items-center gap-3">
                        <Icon icon="clarity:file-line" class="text-primary-700" style="width: 36px; height: 36px" />
                        <Tag severity="success" class="px-4 py-2 rounded-xl max-w-[400px] overflow-hidden text-ellipsis whitespace-nowrap">
                            <span class="text-3xl font-bold break-all">{{ file.name }}</span>
                        </Tag>
                    </div>
                </div>

                <!-- ปุ่มเลือกไฟล์ -->
                <div v-if="!uploadInProgress && !processing && !progress">
                    <input type="file" accept=".xlsx,.csv" @change="handleFileSelect" ref="fileInput" hidden />
                    <Button @click="$refs.fileInput.click()">
                        <Icon icon="lets-icons:import" />
                        {{ file ? 'เปลี่ยนไฟล์' : 'เลือกไฟล์' }}
                    </Button>
                </div>

                <!-- ข้อความเมื่อเสร็จ -->
                <p v-if="progress >= 100" class="text-sm text-center text-green-600">✔️ อัปโหลดและประมวลผลเสร็จสมบูรณ์</p>

                <!-- Progress Bar -->
                <template v-if="uploadInProgress">
                    <ProgressBar v-if="uploadInProgress" :value="progress" :showValue="false" class="w-full" style="height: 4px" />
                    <p v-if="uploadInProgress" class="mt-2 text-sm text-center text-sold">
                        {{ progress < 80 ? 'กำลังอัปโหลดไฟล์...' : 'กำลังประมวลผลข้อมูล...' }}
                    </p>
                </template>
            </div>

            <template #footer>
                <!-- ปุ่มก่อนอัปโหลดเสร็จ -->
                <template v-if="progress < 100">
                    <Button label="ยกเลิก" icon="pi pi-times" @click="closeDialog" severity="danger" />
                    <Button label="ยืนยัน" icon="pi pi-check" @click="handleFileUpload" :loading="uploadInProgress" :disabled="!file || uploadInProgress" />
                </template>

                <!-- ปุ่มหลังอัปโหลดเสร็จ -->
                <template v-else>
                    <Button label="ปิด" @click="closeDialog" severity="success" />
                </template>
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

        <Dialog v-model:visible="ExportDialog" header="โหลดไฟล์" :modal="true">
            <div class="flex items-center justify-center">
                <Button severity="secondary" class="mr-2" @click="exportData('xlsx')" rounded raised>
                    <Icon icon="vscode-icons:file-type-excel"></Icon>
                    <span>โหลดไฟล์เป็น Excel</span>
                </Button>
                <Button severity="secondary" class="mr-2" @click="exportData('csv')" rounded raised>
                    <Icon icon="catppuccin:csv"></Icon>
                    <span>โหลดไฟล์เป็น CSV</span>
                </Button>
                <Button severity="secondary" class="mr-2" @click="exportPDF" rounded raised>
                    <Icon icon="vscode-icons:file-type-pdf2" />
                    <span>โหลดไฟล์เป็น PDF</span>
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
                    >คุณแน่ใจหรือไม่ที่จะลบลำดับที่ <b>{{ product.formatted_id }}</b> <b>{{ product.name }}</b>
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
