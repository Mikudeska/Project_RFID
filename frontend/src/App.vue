<script setup>
import { onMounted, onBeforeUnmount, provide } from 'vue';
import { useWebSocketStore } from '@/stores/websocket';
import { useToast } from 'primevue/usetoast';

const globalToast = useToast();
provide('globalToast', globalToast);

function globalWsHandler(msg) {
    if (msg.action === 'reset' || msg.action === 'upload') {
        globalToast?.add?.({
            severity: 'info',
            summary: msg.action === 'reset' ? 'รีเซ็ตข้อมูล' : 'นำเข้าข้อมูล',
            detail: msg.action === 'reset'
                ? 'ข้อมูลได้ถูกรีเซ็ตเรียบร้อย'
                : 'ข้อมูลได้รับการอัปเดตเรียบร้อย',
            life: 3000
        });
    }
}

const wsStore = useWebSocketStore();

onMounted(() => {
    wsStore.connect();
    wsStore.registerHandler(globalWsHandler);
}); 

onBeforeUnmount(() => {
    wsStore.disconnect();
});
</script>

<template>
    <Toast />
    <router-view />
</template>
