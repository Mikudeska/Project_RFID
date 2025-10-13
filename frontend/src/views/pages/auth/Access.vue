<script setup>
import FloatingConfigurator from '@/components/FloatingConfigurator.vue';
</script>

<template>
    <FloatingConfigurator />
    <div class="relative flex items-center justify-center w-full min-h-screen px-4 overflow-hidden bg-surface-0 dark:bg-surface-900">
        <div class="flex flex-col items-center justify-center">
            <div style="border-radius: 56px; padding: 0.3rem; background: linear-gradient(180deg, rgba(249, 115, 22, 0.4) 10%, rgba(249, 115, 22, 0) 35%)">
                <div class="flex flex-col items-center w-full px-8 py-16 bg-surface-0 sm:px-20 dark:bg-surface-900" style="border-radius: 53px">
                    <div class="flex flex-col items-center gap-6 text-center">
                        <div class="flex items-center justify-center w-16 h-16 bg-orange-100 rounded-full shadow-lg shadow-orange-500/20 dark:bg-orange-900/50">
                            <i class="text-3xl text-orange-500 pi pi-lock"></i>
                        </div>

                        <h1 class="text-4xl font-bold tracking-tight text-surface-900 lg:text-5xl dark:text-surface-0">ไม่มีสิทธิ์เข้าถึง</h1>
                        <p class="max-w-md text-lg text-surface-600 dark:text-surface-300">คุณไม่มีสิทธิ์ที่จำเป็นในการเข้าถึงหน้านี้ กรุณาติดต่อผู้ดูแลระบบเพื่อขอความช่วยเหลือ</p>

                        <img src="/demo/images/access/asset-access.svg" alt="Access denied" class="w-3/4 max-w-sm mb-4 animated-asset" />

                        <Button as="router-link" to="/" label="กลับไปหน้าหลัก" severity="warn" class="transition-transform duration-300 hover:scale-105" />
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
/* พื้นหลังแบบไล่ระดับสีที่นุ่มนวล */
body {
    background-color: var(--surface-0);
}

.dark body {
    background-color: var(--surface-900);
}

/* อนิเมชันลอยขึ้นลงสำหรับรูปภาพ */
@keyframes float {
    0% {
        transform: translateY(0px);
    }
    50% {
        transform: translateY(-20px);
    }
    100% {
        transform: translateY(0px);
    }
}

.animated-asset {
    animation: float 6s ease-in-out infinite;
}
</style>