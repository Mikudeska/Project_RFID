<script setup>
import { onMounted, onBeforeUnmount } from 'vue';
import { useWebSocketStore } from '@/stores/websocket';

const wsStore = useWebSocketStore();

onMounted(() => {
    wsStore.connect();
});

onBeforeUnmount(() => {
    wsStore.disconnect();
});
</script>

<template>
    <router-view />
</template>
