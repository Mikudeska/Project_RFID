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

const isLoading = ref(false)
const isFading = ref(false) // ✅ state สำหรับ fade-out

function handleLogin() {
    if (isLoading.value) return
    isLoading.value = true        // ✅ เปลี่ยนปุ่มเป็นไอคอนหมุนก่อน

    // รอให้เห็นไอคอนหมุนชัดๆ สัก 0.5 วินาทีแล้วค่อย fade-out
    setTimeout(() => {
        isFading.value = true     // ✅ เริ่มทำ fade-out หน้า
        setTimeout(() => {
            router.push('/')      // ✅ เปลี่ยนหน้า หลัง fade-out เสร็จ
        }, 800)                   // เวลาต้องเท่ากับ transition fade-out
    }, 500)
}
</script>

<template>
    <transition name="fade">
        <div v-if="!isFading" class="login-page">
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

                                <!-- ปุ่มเข้าสู่ระบบ -->
                                <Button 
                                    class="w-full relative overflow-hidden min-h-[42px]"
                                    @click="handleLogin"
                                    :disabled="isLoading"
                                >
                                    <!-- ข้อความปกติ -->
                                    <span :class="isLoading ? 'opacity-0' : 'opacity-100'">เข้าสู่ระบบ</span>

                                    <!-- ใช้ icon loading-loop ตอนโหลด -->
                                    <Icon 
                                        v-if="isLoading" 
                                        icon="line-md:loading-loop" 
                                        class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-xl"
                                    />
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </transition>
</template>

<style scoped>
.login-page {
    height: 100vh;
    width: 100vw;
    overflow: hidden;
}

/* ✅ Fade-out effect */
.fade-leave-active {
    transition: opacity 0.8s ease;
}
.fade-leave-to {
    opacity: 0;
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
