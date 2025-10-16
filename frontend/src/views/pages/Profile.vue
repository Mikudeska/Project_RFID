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

const passwordFieldType = ref('password');
const confirmPasswordFieldType = ref('password');

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
    <div class="p-5 rounded-lg shadow-sm card md:p-8">
        <Toast />
        <div class="">
            <h3 class="mb-6 text-lg font-semibold">ข้อมูลส่วนตัว</h3>
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
            <input type="text" name="fakeusernameremembered" autocomplete="username" class="hidden" />
            <input type="password" name="fakepasswordremembered" autocomplete="new-password" class="hidden" />

            <h3 class="mb-6 text-lg font-semibold">เปลี่ยนรหัสผ่าน</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-5">
                <div class="flex flex-col gap-2">
                    <label for="new_password_custom" class="block mb-2 font-medium">รหัสผ่านใหม่</label>
                    <Password id="new_password_custom" :type="passwordFieldType" v-model="passwordFields.new_password" placeholder="กรอกรหัสผ่านใหม่" :toggleMask="true" class="mb-4" fluid :feedback="false" autocomplete="new-password" />
                    <small v-if="passwordError" class="mt-1 text-red-500">
                        {{ passwordError }}
                    </small>
                </div>
                <div class="flex flex-col gap-2">
                    <label for="confirm_password_custom" class="block mb-2 font-medium">ยืนยันรหัสผ่านใหม่</label>
                    <Password
                        id="confirm_password_custom"
                        :type="confirmPasswordFieldType"
                        v-model="passwordFields.confirm_password"
                        placeholder="ยืนยันรหัสผ่านอีกครั้ง"
                        :toggleMask="true"
                        class="mb-4"
                        fluid
                        :feedback="false"
                        autocomplete="new-password"
                    />
                </div>
            </div>
            <div class="flex mt-6">
                <Button label="เปลี่ยนรหัสผ่าน" icon="pi pi-key" @click="changePassword" severity="secondary" />
            </div>
        </div>
    </div>
</template>

<style scoped></style>
