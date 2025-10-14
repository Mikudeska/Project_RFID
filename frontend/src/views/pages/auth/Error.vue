<script setup>
import Button from 'primevue/button';
</script>

<template>
    <div class="flex items-center justify-center min-h-screen px-6 py-12 overflow-hidden bg-surface-50 dark:bg-surface-900 lg:px-8">
        <div class="container mx-auto">
            <div class="flex flex-col items-center justify-center gap-12 md:flex-row md:gap-20">
                <div class="w-full max-w-sm md:w-1/2">
                    <img src="@/assets/image/404 error lost in space-bro.svg" alt="Page not found" class="w-full animated-asset" />
                </div>

                <div class="flex flex-col items-center w-full gap-6 text-center md:w-1/2 md:items-start md:text-left">
                    <h1 class="font-extrabold tracking-tighter text-primary-500 dark:text-primary-400" style="font-size: 8rem; line-height: 1">404</h1>
                    <h2 class="text-4xl font-bold tracking-tight text-surface-900 dark:text-surface-0 sm:text-5xl">ไม่พบหน้านี้</h2>
                    <p class="text-xl text-surface-600 dark:text-surface-300">ขออภัยค่ะ ดูเหมือนว่าเราจะหาหน้าที่คุณต้องการไม่เจอ ลองตรวจสอบ URL หรือกลับไปที่หน้าหลักดูนะคะ</p>
                    <Button as="router-link" to="/" label="กลับสู่หน้าหลัก" icon="pi pi-home" size="large" class="mt-4 transition-transform duration-300 hover:scale-105" />
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
/* อนิเมชันลอยขึ้นลงสำหรับรูปภาพ */
@keyframes float {
    0% {
        transform: translateY(0px);
    }
    50% {
        transform: translateY(-25px);
    }
    100% {
        transform: translateY(0px);
    }
}

.animated-asset {
    animation: float 6s ease-in-out infinite;
}
</style>