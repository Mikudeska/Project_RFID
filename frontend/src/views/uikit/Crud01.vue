<script setup>
import { FilterMatchMode } from '@primevue/core/api';
import { useToast } from 'primevue/usetoast';
import { onMounted, ref, computed } from 'vue';
import axios from 'axios';
import { Icon } from '@iconify/vue';

const toast = useToast();
const dt = ref();
const persons = ref();
const searchQuery = ref(''); // ตัวแปรสำหรับการค้นหา

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
        await axios.post('http://localhost:8000/api/reset/');
        await fetchPersons();
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

const exportPDF = async () => {
    try {
        const response = await axios.get('http://localhost:8000/api/export-pdf/', {
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
        link.setAttribute('download', 'รายชื่อบัณฑิต.pdf');
        document.body.appendChild(link);
        link.click();
        link.remove();
    } catch (error) {
        console.error('PDF Export Error:', error);
        alert('ส่งออก PDF ไม่สำเร็จ: ' + error.message);
    }
};

// Export ข้อมูล
const exportData = async (format) => {
    try {
        const response = await axios.get(`http://localhost:8000/api/export/${format}/`, { responseType: 'blob' });

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
const visible = ref(false);
const interval = ref(null);
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
    visible.value = true;
    progress.value = 0;

    const formData = new FormData();
    formData.append('file', file.value);

    try {
        await axios.post('http://localhost:8000/api/import/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            onUploadProgress: (progressEvent) => {
                progress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            }
        });

        toast.add({
            severity: 'success',
            summary: 'อัปโหลดสำเร็จ',
            detail: 'นำเข้าข้อมูลเรียบร้อย',
            life: 5000
        });

        await fetchPersons();
    } catch (error) {
        toast.add({
            severity: 'error',
            summary: 'อัปโหลดล้มเหลว',
            detail: error.response?.data?.error || 'เกิดข้อผิดพลาด',
            life: 5000
        });
    } finally {
        uploadInProgress.value = false;
        file.value = null;
        UploadDialog.value = false;
    }
};

const cancelUpload = () => {
    if (interval.value) clearInterval(interval.value);
    visible.value = false;
    progress.value = 0;
    file.value = null;
    uploadInProgress.value = false;
};

// กรองคนรายงานตัว
const applyVerifiedFilter = (value) => {
    filteredVerified.value = value;
};

const filteredPersons = computed(() => {
    if (filteredVerified.value === null) {
        return persons.value; // แสดงทั้งหมด
    }
    return persons.value.filter((person) => person.verified === filteredVerified.value);
});

// เพิ่ม 0 ให้เลขครบ 4 หลัก
function formatId(id) {
    return id.toString().padStart(4, '0');
}

async function fetchPersons() {
    loading.value = true; // เริ่มต้น loading
    try {
        const response = await axios.get('http://127.0.0.1:8000/api/person/');
        persons.value = response.data.map((person) => ({
            ...person,
            formatted_id: formatId(person.id) // ใช้ฟังก์ชันจัดรูปแบบ ID
        }));
    } catch (error) {
        console.error('Error fetching persons:', error);
    } finally {
        loading.value = false; // หยุด loading ไม่ว่าจะสำเร็จหรือล้มเหลว
    }
}
onMounted(fetchPersons);

// เพิ่ม Axios สำหรับ CRUD Operations
const saveProduct = async () => {
    submitted.value = true;
    if (product?.value.name?.trim()) {
        try {
            if (product.value.id) {
                // อัพเดตข้อมูล
                await axios.put(`http://127.0.0.1:8000/api/person/${product.value.id}/`, product.value);
                toast.add({ severity: 'success', summary: 'บันทึกสำเร็จ', detail: 'อัพเดตข้อมูลเรียบร้อย', life: 3000 });
            } else {
                // สร้างข้อมูลใหม่
                await axios.post('http://127.0.0.1:8000/api/person/', product.value);
                toast.add({ severity: 'success', summary: 'บันทึกสำเร็จ', detail: 'สร้างข้อมูลเรียบร้อย', life: 3000 });
            }
            await fetchPersons(); // ดึงข้อมูลใหม่หลังบันทึก
            productDialog.value = false;
        } catch (error) {
            console.error('Error saving data:', error);
            toast.add({ severity: 'error', summary: 'เกิดข้อผิดพลาด', detail: 'บันทึกข้อมูลไม่สำเร็จ', life: 3000 });
        }
    }
};

const deleteProduct = async () => {
    try {
        await axios.delete(`http://127.0.0.1:8000/api/person/${product.value.id}/`);
        persons.value = persons.value.filter((val) => val.id !== product.value.id);
        deleteProductDialog.value = false;
        toast.add({ severity: 'success', summary: 'สำเร็จ', detail: 'ลบข้อมูลเรียบร้อย', life: 3000 });
    } catch (error) {
        console.error('Error deleting data:', error);
        toast.add({ severity: 'error', summary: 'เกิดข้อผิดพลาด', detail: 'ลบข้อมูลไม่สำเร็จ', life: 3000 });
    }
};

// Crud01.vue
async function deleteSelectedpersons() {
    try {
        const ids = selectedpersons.value.map((person) => person.id);
        await axios.delete('http://127.0.0.1:8000/api/person/delete/', {
            data: { ids },
            headers: {
                'Content-Type': 'application/json'
            }
        });

        persons.value = persons.value.filter((val) => !ids.includes(val.id));
        selectedpersons.value = null;
        deletepersonsDialog.value = false;

        toast.add({ severity: 'success', summary: 'สำเร็จ', detail: 'ลบรายการเรียบร้อย', life: 3000 });
    } catch (error) {
        console.error('Error deleting data:', error);
        toast.add({
            severity: 'error',
            summary: 'เกิดข้อผิดพลาด',
            detail: error.response?.data?.error || 'ลบรายการไม่สำเร็จ',
            life: 5000
        });
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

const items = ref([
    {
        label: 'reset',
        icon: 'grommet-icons:power-reset',
        color: 'text-green-500',
        command: () => {
            applyVerifiedFilter(null);
        }
    },
    {
        label: '?',
        icon: 'rivet-icons:exclamation-mark-circle-solid',
        color: 'text-yellow-300',
        command: () => {
            applyVerifiedFilter(2);
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
        label: 'รายงานตัวแล้ว',
        icon: 'rivet-icons:check-circle-solid',
        color: 'text-green-500',
        command: () => {
            applyVerifiedFilter(1);
        }
    }
]);
</script>

<template>
    <div>
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
                </template>

                <template #end>
                    <Button severity="secondary" class="mr-2" @click="confirmUpload" rounded raised> <Icon icon="lets-icons:import" />อัปโหลดไฟล์</Button>
                    <Button severity="secondary" class="mr-2" @click="choseExport" rounded raised> <Icon icon="lets-icons:export" />โหลดไฟล์ </Button>
                </template>
            </Toolbar>

            <DataTable
                ref="dt"
                v-model:selection="selectedpersons"
                :value="filteredPersons"
                dataKey="id"
                :paginator="true"
                :rows="25"
                :filters="filters"
                paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
                :rowsPerPageOptions="[25, 50]"
                currentPageReportTemplate="จาก   {first} ถึง {last} ของทั้งหมด {totalRecords} คน"
                :sortField="'formatted_id'"
                :sortOrder="1"
            >
                <template #header>
                    <div class="flex flex-wrap items-center justify-between gap-2">
                        <div>
                            <h4 class="m-0">จัดการรายชื่อบัญฑิต</h4>
                        </div>
                        <div class="flex items-center gap-2">
                            <SpeedDial :model="items" direction="left" :transitionDelay="40" pt:menuitem="m">
                                <template #button="{ toggleCallback }">
                                    <Button outlined @click="toggleCallback" rounded>
                                        <Icon icon="hugeicons:filter"></Icon>
                                    </Button>
                                </template>
                                <template #item="{ item, toggleCallback }">
                                    <Button class="justify-between gap-2 cursor-pointer text-nowrap" @click="toggleCallback" outlined rounded>
                                        <Icon :icon="item.icon" :class="item.color" />
                                    </Button>
                                </template>
                            </SpeedDial>
                            <IconField>
                                <InputIcon>
                                    <i class="pi pi-search" />
                                </InputIcon>
                                <InputText v-model="filters['global'].value" placeholder="ค้นหาข้อมูลบัญฑิต" />
                            </IconField>
                            <Toast />
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
                <Column field="degree" header="ชื่อปริญญา" sortable style="min-width: 12rem"></Column>
                <!-- <Column field="rating" header="Reviews" sortable style="min-width: 12rem">
                    <template #body="slotProps">
                        <Rating :modelValue="slotProps.data.rating" :readonly="true" />
                    </template>
                </Column> -->
                <Column field="seat" header="เลขที่นั่ง" sortable style="min-width: 6rem"></Column>
                <Column field="verified" header="รายงานตัว" dataType="boolean" bodyClass="text-center" style="min-width: 8rem">
                    <template #body="{ data }">
                        <Icon
                            class="icon"
                            :icon="data.verified === 1 ? 'rivet-icons:check-circle-solid' : data.verified === 0 ? 'rivet-icons:close-circle-solid' : 'rivet-icons:exclamation-mark-circle-solid'"
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
                <Column :exportable="false" style="min-width: 1rem">
                    <template #body="slotProps">
                        <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editProduct(slotProps.data)" />
                        <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmDeleteProduct(slotProps.data)" />
                    </template>
                </Column>
            </DataTable>
        </div>

        <Dialog v-model:visible="productDialog" :style="{ width: '450px' }" header="รายละเอียดบัญฑิต" :modal="true">
            <div class="flex flex-col gap-6">
                <div>
                    <label for="formatted_id" class="block mb-3 font-bold">ลำดับ</label>
                    <InputText id="formatted_id" v-model.trim="product.formatted_id" autofocus :invalid="submitted && !product.formatted_id" fluid disabled="true" />
                </div>
                <div>
                    <label for="nisit" class="block mb-3 font-bold">รหัสนิสิต</label>
                    <InputText id="nisit" v-model.trim="product.nisit" autofocus :invalid="submitted && !product.nisit" fluid disabled="true" />
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
                    <InputText id="seat" v-model.trim="product.seat" autofocus :invalid="submitted && !product.degree" fluid disabled="true" />
                </div>
                <div>
                    <span class="block mb-4 font-bold">สถานะรายงานตัว</span>
                    <div class="grid grid-cols-12 gap-4">
                        <div class="flex items-center col-span-4 gap-2">
                            <RadioButton id="verified1" v-model="product.verified" name="verified" :value="1" />
                            <label for="verified1">
                                <Icon icon="rivet-icons:check-circle-solid" class="text-green-500" />
                            </label>
                        </div>
                        <div class="flex items-center col-span-4 gap-2">
                            <RadioButton id="verified0" v-model="product.verified" name="verified" :value="0" />
                            <label for="verified0">
                                <Icon icon="rivet-icons:close-circle-solid" class="text-red-500" />
                            </label>
                        </div>
                        <div class="flex items-center col-span-4 gap-2">
                            <RadioButton id="verified2" v-model="product.verified" name="verified" :value="2" />
                            <label for="verified2">
                                <Icon icon="rivet-icons:exclamation-mark-circle-solid" class="text-yellow-300" />
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

        <Dialog v-model:visible="UploadDialog" header="อัปโหลดไฟล์" :modal="true" :closable="!uploadInProgress">
            <div class="flex flex-col items-center gap-4">
                <!-- แสดงชื่อไฟล์ -->
                <div class="py-2 border-l-4 border-primary-700 bg-primary-400 card">
                    <div v-if="file" class="flex items-center text-black">
                        <Icon icon="clarity:file-line" class="text-4xl" />
                        <p class="font-bold break-all">{{ file.name }}</p>
                    </div>
                </div>

                <!-- ปุ่มเลือกไฟล์ -->
                <input type="file" accept=".xlsx,.csv" @change="handleFileSelect" ref="fileInput" hidden />
                <Button @click="$refs.fileInput.click()" :disabled="uploadInProgress">
                    <Icon icon="lets-icons:import" />
                    {{ file ? 'เปลี่ยนไฟล์' : 'เลือกไฟล์' }}
                </Button>

                <!-- Progress Bar -->
                <ProgressBar v-if="uploadInProgress" :value="progress" :showValue="false" class="w-full" style="height: 4px" />
            </div>

            <template #footer>
                <Button label="ยกเลิก" icon="pi pi-times" @click="cancelUpload, (UploadDialog = false)" severity="danger" :disabled="uploadInProgress" />
                <Button label="ยืนยัน" icon="pi pi-check" @click="handleFileUpload" :loading="uploadInProgress" :disabled="!file || uploadInProgress" />
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
                    <p class="text-black">การกระทำนี้จะลบข้อมูลทุกรายการและไม่สามารถกู้คืนได้</p>
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
