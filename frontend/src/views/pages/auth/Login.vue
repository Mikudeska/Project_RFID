<script setup>
import FloatingConfigurator from '@/components/FloatingConfigurator.vue';
import router from '@/router';
import { ref } from 'vue';

import bg1 from '@/assets/image/background/bg1.jpg'
import bg2 from '@/assets/image/background/bg2.jpg'

const backgrounds = [bg1, bg2]
function getRandomIndex(max) {
  return Math.floor(Math.random() * max)
}
const imageSrc = ref(backgrounds[getRandomIndex(backgrounds.length)])

const email = ref('');
const password = ref('');
const checked = ref(false);

function goToDashboard (){
    router.push('/')
}
</script>

<template>
    <div class="login-page">
        <FloatingConfigurator />
        <!-- Background -->
        <div class="fixed inset-0 bg-cover bg-center -z-10"
             :style="{ backgroundImage: 'url(' + imageSrc + ')', filter: 'blur(8px)' }"></div>

        <!-- Content -->
        <div class="flex items-center justify-center h-screen w-screen overflow-hidden">
            <div class="flex flex-col items-center justify-center">
                <div style="border-radius: 56px; padding: 0.3rem; background: linear-gradient(180deg, var(--primary-color) 10%, rgba(33, 150, 243, 0) 30%)">
                    <div class="w-full px-8 py-16 bg-surface-0 dark:bg-surface-900 sm:px-20" style="border-radius: 53px">
                        <div>
                            <Button v-tooltip.top="'กลับหน้าแรก'" @click="goToDashboard" rounded text>
                                <Icon icon="icon-park-solid:back" class="text-2xl" />
                            </Button>
                        </div>
                        <div class="mb-8 text-center">
                            <svg viewBox="0 0 100 30" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <image href="https://ssru.ac.th/datafiles/loadimg/SSRU_LOGO1.png" x="40" y="0" height="30" width="20" />
                            </svg>
                        </div>

                        <div>
                            <label for="email1" class="block mb-2 text-xl font-medium text-surface-900 dark:text-surface-0">ชื่อผู้ใช้งาน</label>
                            <InputText id="email1" type="text" placeholder="ใส่ชื่อผู้ใช้งานที่ตั้งไว้" class="w-full md:w-[30rem] mb-8" v-model="email" />

                            <label for="password1" class="block mb-2 text-xl font-medium text-surface-900 dark:text-surface-0">รหัสผ่าน</label>
                            <Password id="password1" v-model="password" placeholder="ใส่รหัสผ่านที่ตั้งไว้" :toggleMask="true" class="mb-4" fluid :feedback="false" />

                            <div class="flex items-center justify-between gap-8 mt-2 mb-8">
                                <div class="flex items-center">
                                    <Checkbox v-model="checked" id="rememberme1" binary class="mr-2" />
                                    <label for="rememberme1">จดจำฉัน</label>
                                </div>
                                <span class="ml-2 font-medium text-right no-underline cursor-pointer text-primary">ลืมรหัสผ่าน?</span>
                            </div>
                            <Button label="เข้าสู่ระบบ" class="w-full" as="router-link" to="/" />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.login-page {
    height: 100vh;
    width: 100vw;
    overflow: hidden; /* ✅ ไม่มีการเลื่อนเฉพาะหน้า login */
}

.pi-eye {
    transform: scale(1.6);
    margin-right: 1rem;
}

.pi-eye-slash {
    transform: scale(1.6);
    margin-right: 1rem;
}
</style>