<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const isOpen = ref(true); // เปิด dialog ทันที
const router = useRouter();

const redirectToLogin = () => {
    router.push('/auth/login'); // เปลี่ยนไปหน้า login
};
</script>

<template>
    <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-gray-500 bg-opacity-50">
        <div class="w-auto p-6 text-center rounded-lg shadow-lg card">
            <h2 class="mb-4 text-xl font-semibold">กรุณาล็อกอินเพื่อดำเนินการต่อ</h2>
            <Button @click="redirectToLogin" class="px-4 py-2 rounded hover:bg-blue-700">ไปที่หน้าเข้าสู่ระบบ</Button>
        </div>
    </div>
</template>

<style scoped></style>
