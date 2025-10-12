<script setup>
import Button from 'primevue/button';
</script>

<template>
    <div class="flex items-center justify-center min-h-screen px-4 py-12 text-center bg-surface-50 dark:bg-surface-900 sm:px-6 lg:px-8">
        <div class="w-full max-w-md mx-auto">
            <div class="flex flex-col items-center gap-8">
                <div>
                    <h1 class="font-extrabold tracking-tighter text-9xl text-primary-500 dark:text-primary-400">404</h1>
                    <h2 class="mt-2 text-3xl font-bold tracking-tight text-surface-900 dark:text-surface-0 sm:text-4xl">ไม่พบหน้านี้</h2>
                </div>

                <p class="text-lg text-surface-600 dark:text-surface-300">ขออภัยค่ะ ดูเหมือนว่าเราจะหาหน้าที่คุณต้องการไม่เจอ ลองตรวจสอบ URL หรือกลับไปที่หน้าหลักดูนะคะ</p>

                <Button as="router-link" to="/" label="กลับสู่หน้าหลัก" icon="pi pi-home" size="large" />
            </div>
        </div>
    </div>
</template>

<style scoped></style>
