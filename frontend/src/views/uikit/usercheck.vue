<script setup>
import { onMounted } from 'vue';
import { useWebSocketStore } from '@/stores/websocket';
import { storeToRefs } from 'pinia';

const wsStore = useWebSocketStore();
const { clientInfoList } = storeToRefs(wsStore);

onMounted(() => {
    wsStore.connect();
});
</script>

<template>
    <div class="card">
        <h2 class="mb-2 text-lg font-bold">🧾 ข้อมูลผู้เชื่อมต่อ</h2>

        <DataTable :value="clientInfoList" :paginator="true" :rows="5" responsiveLayout="scroll" stripedRows class="p-datatable-sm">
            <Column field="id" header="🆔 ID" />
            <Column field="ip" header="🧾 IP" />
            <Column field="origin" header="🌍 Origin" />
            <Column field="user_agent" header="🖥️ User-Agent" />
            <Column field="location" header="📍 Location" />
            <Column field="time" header="🕒 Time" />
        </DataTable>
    </div>
</template>
