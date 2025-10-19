<script setup>
import { onMounted, onBeforeUnmount, watch } from 'vue';
import { useWebSocketStore } from '@/stores/websocket';
import { useGlobalToast } from '@/components/utils/toastUtils';
import { useAuthStore } from '@/stores/auth';
import { useRoute } from 'vue-router';
import Dialog from '@/layout/composables/Dialog.vue';
import { storeToRefs } from 'pinia';

const toastStore = useGlobalToast();
const authStore = useAuthStore();
const route = useRoute();

function globalWsHandler(msg) {
    toastStore.show(msg.action);
}

const wsStore = useWebSocketStore();
const { isConnected } = storeToRefs(wsStore);

onMounted(() => {
    wsStore.connect();
    wsStore.registerHandler(globalWsHandler);

    authStore.loadUser();
});

watch(isConnected, (newValue, oldValue) => {
    if (oldValue === true && newValue === false) {
        toastStore.show({
            severity: 'error',
            summary: 'การเชื่อมต่อหลุด 🛑',
            detail: 'การเชื่อมต่อ WebSocket ขาดหาย กรุณากด F5 หรือรีเฟรชหน้าเพจ',
            sticky: true
        });
    } 
    else if (oldValue === false && newValue === true) {
        toastStore.show({
            severity: 'success',
            summary: 'เชื่อมต่อสำเร็จ ✅',
            detail: 'เชื่อมต่อ WebSocket เรียบร้อย',
            life: 3000 // 1000/1 วินาที
        });
    }
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
