<script setup>
import { Icon } from '@iconify/vue';
import { useToast } from 'primevue/usetoast';
import { ref, onUnmounted, computed } from 'vue';
import { useOnline } from '@vueuse/core';
import { io } from 'socket.io-client';

const testMessage = ref(null);

const API_BASE = import.meta.env.VITE_API_BASE; // เช่น http://localhost:8000
const WS_BASE = API_BASE.replace(/^http/, 'ws');
const socket = io(`${WS_BASE}/ws/person/`);

socket.on('connect', () => {
    console.log('✅ WebSocket เชื่อมต่อแล้ว');
});

socket.on('disconnect', () => {
    console.log('❌ WebSocket หลุดการเชื่อมต่อ');
});

socket.on('message', (event) => {
    console.log('📡 ได้รับข้อความ:', event);
    testMessage.value = JSON.stringify(event, null, 2); // แสดงผลใน UI
});

// ปุ่มทดสอบการส่งข้อความไปยัง socket server
function sendTestMessage() {
    socket.emit('message', { text: 'hello from frontend!' });
}

const online = useOnline();
const clazz = computed(() => (online.value ? 'text-primary' : 'text-red'));
const text = computed(() => (online.value ? 'Online' : 'Offline'));
const toast = useToast();
const visible = ref(false);
const progress = ref(0);
const interval = ref();

onUnmounted(() => {
    if (interval.value) {
        clearInterval(interval.value);
    }
});

const upload = () => {
    if (!visible.value) {
        toast.add({ severity: 'custom', summary: 'Uploading your files.', group: 'headless', styleClass: 'backdrop-blur-lg rounded-2xl' });
        visible.value = true;
        progress.value = 0;

        if (interval.value) {
            clearInterval(interval.value);
        }

        interval.value = setInterval(() => {
            if (progress.value <= 100) {
                progress.value = progress.value + 20;
            }

            if (progress.value >= 100) {
                progress.value = 100;
                clearInterval(interval.value);
            }
        }, 1000);
    }
};
</script>

<template>
    <div class="grid grid-cols-[repeat(3,1fr)] grid-rows-[repeat(3,1fr)] gap-y-[10px] gap-x-[10px]">
        <div class="flex flex-col items-start gap-2 card row-1 row-2 col-1 col-2">
            <FileUpload ref="fileupload" mode="basic" name="demo[]" url="/api/upload" accept="image/*" :maxFileSize="1000000" @upload="onUpload" />
            <Button label="Upload" @click="upload" severity="secondary" />
            <Toast position="top-center" group="headless" @close="visible = false">
                <template #container="{ message, closeCallback }">
                    <section class="flex flex-col w-full gap-4 p-4 rounded-xl">
                        <div class="flex items-center gap-5">
                            <Icon icon="subway:upload-1"></Icon>
                            <span class="text-base font-bold">{{ message.summary }}</span>
                        </div>
                        <div class="flex flex-col gap-2">
                            <ProgressBar :value="progress" :showValue="false" :style="{ height: '4px' }"></ProgressBar>
                            <label class="text-sm font-bold">{{ progress }}% uploaded</label>
                        </div>
                        <div class="flex justify-end gap-4 mb-4">
                            <Button label="Another Upload?" size="small" @click="closeCallback"></Button>
                            <Button label="Cancel" size="small" @click="closeCallback"></Button>
                        </div>
                    </section>
                </template>
            </Toast>
        </div>
        <div class="card row-1 row-2 col-2 col-3">
            <div class="text-5xl">
                Status: <b :class="clazz">{{ text }}</b>
            </div>
        </div>
        <div class="card row-1 row-2 col-3 col-4">
            <div class="p-4 space-y-4 card">
                <h2 class="text-xl font-bold text-green-600">🔌 ทดสอบการเชื่อมต่อ WebSocket</h2>

                <Button @click="sendTestMessage" class="px-4 py-2 text-white bg-blue-500 shadow rounded-xl" rounded> 📤 ส่งข้อความทดสอบ </Button>

                <div v-if="testMessage" class="p-3 mt-4 text-sm text-black whitespace-pre-wrap bg-gray-100 rounded">
                    <strong>📥 ข้อมูลที่ได้รับ:</strong>
                    <pre>{{ testMessage }}</pre>
                </div>
            </div>
        </div>
        <div class="card row-2 row-3 col-1 col-2">4</div>
        <div class="card row-2 row-3 col-2 col-3">5</div>
        <div class="card row-2 row-3 col-3 col-4">6</div>
        <div class="card row-3 row-4 col-1 col-2">7</div>
        <div class="card row-3 row-4 col-2 col-3">8</div>
        <div class="card row-3 row-4 col-3 col-4">9</div>
    </div>
</template>

<style scoped></style>
