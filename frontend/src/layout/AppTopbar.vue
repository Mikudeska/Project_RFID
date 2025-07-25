<script setup>
import { useLayout } from '@/layout/composables/layout';
import AppConfigurator from './AppConfigurator.vue';
import { useOnline } from '@vueuse/core';
import { computed, onMounted, ref } from 'vue';
import { Icon, loadIcon } from '@iconify/vue';
import { useRouter } from 'vue-router';
import { useWebSocketStore } from '@/stores/websocket';
import { storeToRefs } from 'pinia';
import axios from 'axios';
import OverlayPanel from 'primevue/overlaypanel';
import Badge from 'primevue/badge';

const API_BASE = import.meta.env.VITE_API_BASE;

const wsStore = useWebSocketStore();
const { isConnected, viewerCount } = storeToRefs(wsStore);

// เชื่อมต่อทันทีเมื่อ mount
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

// Log
defineProps();
defineEmits();
const logs = ref([]);
const op = ref(null);

function togglePanel(event) {
    op.value.toggle(event);
}

async function fetchLogs() {
    logs.value = [];
    let page = 1;
    let hasNext = true;

    while (hasNext) {
        try {
            const response = await axios.get(`${API_BASE}/api/logs/?page=${page}`);
            const data = response.data;
            logs.value.push(...(data.results ?? []));
            hasNext = !!data.next;
            page++;
        } catch (error) {
            console.error('โหลด logs ล้มเหลวที่หน้า', page, error);
            break;
        }
    }
}

// รูปแบบวันที่
function formatDate(datetimeStr) {
    const date = new Date(datetimeStr);
    return date.toLocaleString('th-TH', {
        dateStyle: 'short',
        timeStyle: 'short'
    });
}

const filteredLogs = computed(() =>
    logs.value
        .filter(log => ['comment', 'import', 'reset'].includes(log.action?.toLowerCase()))
        .slice(0, 5)
);

onMounted(fetchLogs);
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
                <!-- <div class="relative">
                    <button
                        v-styleclass="{ selector: '@next', enterFromClass: 'hidden', enterActiveClass: 'animate-scalein', leaveToClass: 'hidden', leaveActiveClass: 'animate-fadeout', hideOnOutsideClick: true }"
                        type="button"
                        class="layout-topbar-action layout-topbar-action-highlight"
                    >
                        <i class="pi pi-palette"></i>
                    </button>
                    <AppConfigurator />
                </div> -->
                <div>
                    <!-- ปุ่มกล่องข้อความ -->
                    <div class="relative">
                        <button
                            @click="togglePanel($event)"
                            ref="btn"
                            type="button"
                            class="layout-topbar-action"
                        >
                            <Icon icon="streamline-plump:inbox-content-solid" class="mr-2" />
                            <span>Messages</span>
                        </button>

                        <Badge
                            severity="warn"
                            class="absolute top-1.5 right-3 rounded-full flex items-center justify-center"
                            style="width: 10px; height: 10px; font-size: 10px; padding: 0"
                        />
                    </div>
                    <!-- เมนูแจ้งเตือน -->
                    <OverlayPanel ref="op">
                        <ul class="w-72">
                            <li
                                v-for="log in filteredLogs"
                                :key="log.id"
                                class="p-2 text-mg flex justify-between items-center"
                            >
                                <div class="flex-1">{{ log.user || 'ผู้ใช้' }}</div>
                                <div class="flex-1 text-green-800 text-center">{{ log.action || 'ไม่รู้หัวข้อ' }}</div>
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
