<script setup>
import { onMounted, onBeforeUnmount } from 'vue';
import { useWebSocketStore } from '@/stores/websocket';
import { useGlobalToast } from '@/components/utils/toastUtils';
import { useAuthStore } from '@/stores/auth'; // นำเข้า auth store
import { useRoute } from 'vue-router';
import Dialog from '@/layout/composables/Dialog.vue'; // นำเข้า Dialog component

const toastStore = useGlobalToast();
const authStore = useAuthStore(); // ใช้ auth store
const route = useRoute(); // ดึงเส้นทางปัจจุบัน

function globalWsHandler(msg) {
    toastStore.show(msg.action);
}

const wsStore = useWebSocketStore();

onMounted(() => {
    wsStore.connect();
    wsStore.registerHandler(globalWsHandler);

    // โหลดข้อมูลผู้ใช้
    authStore.loadUser();
});

onBeforeUnmount(() => {
    wsStore.disconnect();
});
</script>

<template>
    <Badge />
    <Toast showProgressBar />

    <!-- แสดง Dialog เมื่อผู้ใช้ไม่ได้ล็อกอิน และไม่ใช่หน้า login -->
    <Dialog v-if="!authStore.isAuthenticated && route.path !== '/auth/login'" />

    <router-view />
</template>
