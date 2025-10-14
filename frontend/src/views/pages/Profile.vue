<script setup>
import { ref, onMounted } from 'vue';
import { Icon } from '@iconify/vue';
import { useAuthStore } from '@/stores/auth';
import { storeToRefs } from 'pinia';
import { createLocalToast } from '@/components/utils/toastUtils';

// --- Setup ---
const toast = createLocalToast();
const auth = useAuthStore();
const { user } = storeToRefs(auth);

// --- State for Profile Editing ---
const isEditing = ref(false);
const editableUser = ref({});

// --- State for Password Change ---
const passwordFields = ref({
    new_password: '',
    confirm_password: ''
});
const passwordError = ref('');

// --- V V V ส่วนที่เพิ่มเข้ามาสำหรับ CSS Method V V V ---
// State สำหรับสลับ type ของ input ระหว่าง 'password' กับ 'text'
const passwordFieldType = ref('password');
const confirmPasswordFieldType = ref('password');

// ฟังก์ชันสำหรับสลับการมองเห็นรหัสผ่าน
const togglePasswordVisibility = () => {
    passwordFieldType.value = passwordFieldType.value === 'password' ? 'text' : 'password';
};
const toggleConfirmPasswordVisibility = () => {
    confirmPasswordFieldType.value = confirmPasswordFieldType.value === 'password' ? 'text' : 'password';
};
// --- ^ ^ ^ สิ้นสุดส่วนที่เพิ่มเข้ามา ^ ^ ^ ---

// --- Functions ---
const startEditing = () => {
    editableUser.value = { ...user.value };
    isEditing.value = true;
};

const cancelEditing = () => {
    isEditing.value = false;
};

const saveProfile = async () => {
    try {
        await auth.updateUserProfile(editableUser.value);
        toast.success('บันทึกสำเร็จ', 'ข้อมูลโปรไฟล์ของคุณถูกอัปเดตเรียบร้อยแล้ว');
        isEditing.value = false;
    } catch (error) {
        toast.error('บันทึกไม่สำเร็จ', 'เกิดข้อผิดพลาดในการบันทึกข้อมูล');
    }
};

const changePassword = async () => {
    passwordError.value = '';

    if (!passwordFields.value.new_password || !passwordFields.value.confirm_password) {
        passwordError.value = 'กรุณากรอกรหัสผ่านทั้งสองช่อง';
        return;
    }

    if (passwordFields.value.new_password !== passwordFields.value.confirm_password) {
        passwordError.value = 'รหัสผ่านไม่ตรงกัน';
        return;
    }

    try {
        await auth.changeUserPassword(passwordFields.value.new_password);
        toast.success('เปลี่ยนรหัสผ่านสำเร็จ', 'คุณสามารถใช้รหัสผ่านใหม่ในการเข้าสู่ระบบครั้งถัดไป');

        passwordFields.value.new_password = '';
        passwordFields.value.confirm_password = '';
    } catch (error) {
        toast.error('เกิดข้อผิดพลาด', 'ไม่สามารถเปลี่ยนรหัสผ่านได้');
    }
};

onMounted(() => {
    editableUser.value = { ...user.value };
});
</script>

<template>
    <div class="card p-5 md:p-8 rounded-lg shadow-sm">
        <Toast />
        <div class="flex justify-between items-center mb-6">
            <h1 class="text-2xl font-bold">แก้ไขโปรไฟล์</h1>
        </div>

        <div class="mt-8">
            <h3 class="text-lg font-semibold mb-6">ข้อมูลส่วนตัว</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-5">
                <div class="flex flex-col gap-2">
                    <label for="first_name" class="font-medium">ชื่อจริง</label>
                    <IconField>
                        <InputIcon>
                            <Icon icon="solar:user-bold-duotone" />
                        </InputIcon>
                        <InputText id="first_name" v-model.trim="editableUser.first_name" :disabled="!isEditing" />
                    </IconField>
                </div>

                <div class="flex flex-col gap-2">
                    <label for="last_name" class="font-medium">นามสกุล</label>
                    <IconField>
                        <InputIcon>
                            <Icon icon="solar:user-bold-duotone" />
                        </InputIcon>
                        <InputText id="last_name" v-model.trim="editableUser.last_name" :disabled="!isEditing" />
                    </IconField>
                </div>

                <div class="flex flex-col gap-2">
                    <label for="nickname" class="font-medium">ชื่อเล่น</label>
                    <IconField>
                        <InputIcon>
                            <Icon icon="solar:sticker-smile-circle-bold-duotone" />
                        </InputIcon>
                        <InputText id="nickname" v-model.trim="editableUser.nickname" :disabled="!isEditing" />
                    </IconField>
                </div>

                <div class="flex flex-col gap-2">
                    <label for="username" class="font-medium">ชื่อผู้ใช้ (Username)</label>
                    <IconField>
                        <InputIcon>
                            <Icon icon="solar:user-id-bold-duotone" />
                        </InputIcon>
                        <InputText id="username" v-model="editableUser.username" disabled />
                    </IconField>
                </div>
                <div class="">
                    <div>
                        <template v-if="!isEditing">
                            <Button label="แก้ไขโปรไฟล์" icon="pi pi-user-edit" @click="startEditing" />
                        </template>
                        <template v-else>
                            <Button label="ยกเลิก" icon="pi pi-times" @click="cancelEditing" severity="danger" text class="mr-2" />
                            <Button label="บันทึก" icon="pi pi-check" @click="saveProfile" />
                        </template>
                    </div>
                </div>
            </div>
        </div>

        <Divider class="my-8" />

        <div>
            <h3 class="text-lg font-semibold mb-6">เปลี่ยนรหัสผ่าน</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-5">
                <div class="flex flex-col gap-2">
                    <label for="new_password_custom" class="font-medium">รหัสผ่านใหม่</label>
                    <div class="password-wrapper">
                        <InputText id="new_password_custom" :type="passwordFieldType" v-model="passwordFields.new_password" placeholder="กรอกรหัสผ่านใหม่" class="w-full password-input" />
                        <Icon :icon="passwordFieldType === 'password' ? 'solar:eye-closed-bold' : 'solar:eye-bold'" class="password-icon" @click="togglePasswordVisibility" />
                    </div>
                    <small v-if="passwordError" class="text-red-500 mt-1">
                        {{ passwordError }}
                    </small>
                </div>

                <div class="flex flex-col gap-2">
                    <label for="confirm_password_custom" class="font-medium">ยืนยันรหัสผ่านใหม่</label>
                    <div class="password-wrapper">
                        <InputText id="confirm_password_custom" :type="confirmPasswordFieldType" v-model="passwordFields.confirm_password" placeholder="ยืนยันรหัสผ่านอีกครั้ง" class="w-full password-input" />
                        <Icon :icon="confirmPasswordFieldType === 'password' ? 'solar:eye-closed-bold' : 'solar:eye-bold'" class="password-icon" @click="toggleConfirmPasswordVisibility" />
                    </div>
                </div>
            </div>
            <div class="mt-6 flex">
                <Button label="เปลี่ยนรหัสผ่าน" icon="pi pi-key" @click="changePassword" severity="secondary" />
            </div>
        </div>
    </div>
</template>

<style scoped>
/* สไตล์สำหรับ Wrapper ของ Input และ Icon */
.password-wrapper {
    position: relative;
    width: 100%;
}

/* สไตล์สำหรับ Icon ที่เราสร้างขึ้นเอง */
.password-icon {
    position: absolute;
    top: 50%;
    right: 1rem; /* ระยะห่างจากขอบขวา */
    transform: translateY(-50%); /* จัดให้อยู่กึ่งกลางแนวตั้งพอดี */
    cursor: pointer;
    color: #f7f7f7; /* สีไอคอน */
    font-size: 1.25rem;
}

/* เพิ่ม Padding ด้านขวาให้ Input เพื่อไม่ให้ตัวหนังสือทับไอคอน */
.p-inputtext.password-input {
    padding-right: 3rem !important;
}
</style>