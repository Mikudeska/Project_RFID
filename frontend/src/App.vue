<script setup>
import { onMounted, onBeforeUnmount } from 'vue';
import { useWebSocketStore } from '@/stores/websocket';
import { useGlobalToastStore } from '@/stores/toast';

const toastStore = useGlobalToastStore();
toastStore.init();

function globalWsHandler(msg) {
    toastStore.show(msg.action);
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
