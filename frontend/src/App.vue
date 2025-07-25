<script setup>
import { onMounted, onBeforeUnmount } from 'vue';
import { useWebSocketStore } from '@/stores/websocket';
import { useGlobalToast } from '@/components/utils/toastUtils';

const toastStore = useGlobalToast();

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
    <Badge />
    <Toast showProgressBar />
    <router-view />
</template>
