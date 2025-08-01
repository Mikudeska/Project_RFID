<script setup>
import { useLayout } from '@/layout/composables/layout';
import AppConfigurator from './AppConfigurator.vue';
import { useOnline } from '@vueuse/core';
import { computed, onMounted, ref, onBeforeUnmount } from 'vue';
import { Icon, loadIcon } from '@iconify/vue';
import { useRouter } from 'vue-router';
import { useWebSocketStore } from '@/stores/websocket';
import { storeToRefs } from 'pinia';
import OverlayPanel from 'primevue/overlaypanel';
import Badge from 'primevue/badge';

const wsStore = useWebSocketStore();
const { isConnected, viewerCount } = storeToRefs(wsStore);

const router = useRouter();
function goToLogin() {
    router.push('/auth/login');
}

onMounted(async () => {
    await loadIcon('material-symbols:wifi-off-rounded');
});

const online = useOnline();
const wifistatus = computed(() => (online.value ? 'svg-spinners:wifi-fade' : 'material-symbols:wifi-off-rounded'));
const clazz = computed(() => (online.value ? 'text-primary' : 'text-red-500'));
const text = computed(() => (online.value ? 'Online' : 'Offline'));

const { toggleMenu, toggleDarkMode, isDarkTheme } = useLayout();

// ✅ Logs จาก WS
const logs = ref([]);
const op = ref(null);

function togglePanel(event) {
    op.value.toggle(event);
}

// ✅ ฟัง WS เฉพาะ upload/comment/reset
function handleWsInbox(event) {
    const msg = event.detail;
    if (['upload', 'comment', 'reset'].includes(msg.action)) {
        logs.value.unshift({
            id: Date.now(),
            user: msg.fields?.user || 'ผู้ใช้',
            action: msg.action,
            timestamp: msg.fields?.timestamp || new Date().toISOString()
        });
        logs.value = logs.value.slice(0, 5); // เก็บแค่ 5 ล่าสุด
    }
}

onMounted(() => {
    wsStore.registerHandler((msg) => {
        if (['upload', 'comment', 'reset'].includes(msg.action)) {
            logs.value.unshift({
                id: Date.now(),
                user: msg.fields?.user || 'ผู้ใช้',
                action: msg.action,
                timestamp: msg.fields?.timestamp || new Date().toISOString()
            });
            logs.value = logs.value.slice(0, 5);
        }
    });
});

onBeforeUnmount(() => {
    window.removeEventListener('ws-message', handleWsInbox);
});

// ✅ format วันที่
function formatDate(datetimeStr) {
    const date = new Date(datetimeStr);
    return date.toLocaleString('th-TH', {
        dateStyle: 'short',
        timeStyle: 'short'
    });
}

const filteredLogs = computed(() => logs.value);
</script>

<template>
    <div class="layout-topbar">
        <div class="layout-topbar-logo-container">
            <button class="layout-menu-button layout-topbar-action" @click="toggleMenu">
                <i class="pi pi-bars"></i>
            </button>
            <router-link to="/" class="layout-topbar-logo">
                <svg viewBox="0 0 300 300" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <image href="https://ssru.ac.th/datafiles/loadimg/SSRU_LOGO1.png" x="0" y="0" height="300" width="300" />
                </svg>
                <span>SSRU_RFID</span>
            </router-link>
        </div>

        <div class="layout-topbar-actions">
            <div class="layout-config-menu">
                <b class="flex items-center gap-2 text-2xl" :class="clazz"><Icon :icon="wifistatus" />{{ text }}</b>
            </div>
            <div class="layout-config-menu">
                <div class="flex items-center gap-2">
                    <Icon
                        :icon="isConnected ? 'material-symbols:person' : 'material-symbols:person-off'"
                        :class="isConnected ? 'text-green-500' : 'text-red-400 line-through'"
                        width="20"
                        height="20"
                    />
                    <span class="text-sm font-semibold">
                        {{ isConnected ? (viewerCount ?? '-') : '-' }}
                    </span>
                </div>
            </div>
            <div class="layout-config-menu">
                <button type="button" class="layout-topbar-action" @click="toggleDarkMode">
                    <i :class="['pi', { 'pi-moon': isDarkTheme, 'pi-sun': !isDarkTheme }]"></i>
                </button>

                <div class="relative">
                    <Button
                        icon="pi pi-palette"
                        v-styleclass="{ selector: '@next', enterFromClass: 'hidden', enterActiveClass: 'animate-scalein', leaveToClass: 'hidden', leaveActiveClass: 'animate-fadeout', hideOnOutsideClick: true }"
                        type="button"
                        rounded
                    />
                    <AppConfigurator />
                </div>

                <!-- Inbox -->
                <div>
                    <div class="relative">
                        <button
                            @click="togglePanel($event)"
                            ref="btn"
                            type="button"
                            class="layout-topbar-action flex items-center justify-center w-10 h-10 rounded-full"
                        >
                            <Icon icon="streamline-plump:inbox-content-solid" class="text-xl" />
                        </button>

                        <Badge
                            v-if="logs.length"
                            severity="warn"
                            class="absolute top-0 right-0 translate-x-1/2 -translate-y-1/2 rounded-full flex items-center justify-center"
                            style="width: 10px; height: 10px; font-size: 10px; padding: 0"
                        />
                    </div>

                    <OverlayPanel ref="op">
                        <ul class="w-72">
                            <li
                                v-for="log in filteredLogs"
                                :key="log.id"
                                class="p-2 text-mg flex justify-between items-center"
                            >
                                <div class="flex-1">{{ log.user }}</div>
                                <div class="flex-1 text-green-800 text-center">{{ log.action }}</div>
                                <div class="flex-1 text-gray-500 text-xs text-right">{{ formatDate(log.timestamp) }}</div>
                            </li>
                            <li v-if="!logs.length" class="p-2 text-center text-gray-400">ไม่มีข้อความล่าสุด</li>
                        </ul>
                    </OverlayPanel>
                </div> 

                <button type="button" class="layout-topbar-action" @click="goToLogin">
                    <i class="pi pi-user"></i>
                    <span>Profile</span>
                </button>
            </div>
        </div>
    </div>
</template>
