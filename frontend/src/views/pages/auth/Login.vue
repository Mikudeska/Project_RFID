<script setup>
import FloatingConfigurator from '@/components/FloatingConfigurator.vue';
import router from '@/router';
import { ref } from 'vue';
import api from '@/plugins/axios';

import bg1 from '@/assets/image/background/bg1.jpg';
import bg2 from '@/assets/image/background/bg2.jpg';
import { createLocalToast } from '@/components/utils/toastUtils';
import { useAuthStore } from '@/stores/auth';
const auth = useAuthStore();

const toast = createLocalToast();

const backgrounds = [bg1, bg2];
const imageSrc = ref(backgrounds[Math.floor(Math.random() * backgrounds.length)]);

const isFading = ref(false);
const checked = ref(false);

const username = ref('');
const password = ref('');
const errorMsg = ref('');
const isLoading = ref(false);

async function handleLogin() {
    isLoading.value = true;
    errorMsg.value = '';

    try {
        // 1) ขอ CSRF ก่อน
        await api.get('api/get-csrf-token/');

        // 2) Login
        await api.post('api/login/', {
            username: username.value,
            password: password.value
        });

        // 3) ดึง profile
        const res = await api.get('api/profile/');
        auth.setUser(res.data);
        console.log('Profile:', res.data);

        router.push('/');
    } catch (err) {
        console.error(err);
        errorMsg.value = 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง';
    } finally {
        isLoading.value = false;
    }
}
</script>

<template>
    <div v-if="!isFading" class="login-page">
        <FloatingConfigurator />
        <div class="fixed inset-0 bg-center bg-cover -z-10" :style="{ backgroundImage: 'url(' + imageSrc + ')', filter: 'blur(8px)' }"></div>

        <div class="flex items-center justify-center w-screen h-screen overflow-hidden">
            <div class="flex flex-col items-center justify-center">
                <div style="border-radius: 56px; padding: 0.3rem; background: linear-gradient(180deg, var(--primary-color) 10%, rgba(33, 150, 243, 0) 30%)">
                    <div class="w-full px-8 py-16 bg-surface-0 dark:bg-surface-900 sm:px-20" style="border-radius: 53px">
                        <div>
                            <Button v-tooltip.top="'กลับหน้าแรก'" @click="router.push('/')" rounded text>
                                <Icon icon="icon-park-solid:back" class="text-2xl" />
                            </Button>
                        </div>
                        <div class="mb-8 text-center">
                            <svg viewBox="0 0 100 30" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <image href="https://ssru.ac.th/datafiles/loadimg/SSRU_LOGO1.png" x="40" y="0" height="30" width="20" />
                            </svg>
                        </div>

                        <div>
                            <label for="username" class="block mb-2 text-xl font-medium">ชื่อผู้ใช้งาน</label>
                            <InputText id="username" type="text" placeholder="ใส่ชื่อผู้ใช้งานที่ตั้งไว้" class="w-full md:w-[30rem] mb-4" v-model="username" />
                            <!-- ข้อความ error สีแดงใต้ช่อง username -->
                            <p v-if="errorMsg" class="mb-4 text-red-600">{{ errorMsg }}</p>

                            <label for="password" class="block mb-2 text-xl font-medium">รหัสผ่าน</label>
                            <Password id="password" v-model="password" placeholder="ใส่รหัสผ่านที่ตั้งไว้" :toggleMask="true" class="mb-4" fluid :feedback="false" />

                            <div class="flex items-center justify-between gap-8 mt-2 mb-8">
                                <div class="flex items-center">
                                    <Checkbox v-model="checked" id="rememberme" binary class="mr-2" />
                                    <label for="rememberme">จดจำฉัน</label>
                                </div>
                                <span class="ml-2 font-medium text-right no-underline cursor-pointer text-primary">ลืมรหัสผ่าน?</span>
                            </div>

                            <Button class="w-full relative overflow-hidden min-h-[42px]" @click="handleLogin" :disabled="isLoading">
                                <span :class="isLoading ? 'opacity-0' : 'opacity-100'">เข้าสู่ระบบ</span>
                                <Icon v-if="isLoading" icon="line-md:loading-loop" class="absolute text-xl -translate-x-1/2 -translate-y-1/2 left-1/2 top-1/2" />
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
