<script setup>
import { useLayout } from '@/layout/composables/layout';
import AppConfigurator from './AppConfigurator.vue';
import { useOnline } from '@vueuse/core';
import { computed, onMounted } from 'vue';
import { Icon, loadIcon } from '@iconify/vue';
import { useRouter } from 'vue-router';

const router = useRouter();

function goToLogin() {
    router.push('/auth/login');
}

onMounted(async () => {
    await loadIcon('material-symbols:wifi-off-rounded');
});

const online = useOnline();
const wifistatus = computed(() => (online.value ? 'material-symbols:wifi-rounded' : 'material-symbols:wifi-off-rounded'));
const clazz = computed(() => (online.value ? 'text-primary' : 'text-red-500'));
const text = computed(() => (online.value ? 'Online' : 'Offline'));

const { toggleMenu, toggleDarkMode, isDarkTheme } = useLayout();
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
                <button type="button" class="layout-topbar-action" @click="toggleDarkMode">
                    <i :class="['pi', { 'pi-moon': isDarkTheme, 'pi-sun': !isDarkTheme }]"></i>
                </button>
                <div class="relative">
                    <button
                        v-styleclass="{ selector: '@next', enterFromClass: 'hidden', enterActiveClass: 'animate-scalein', leaveToClass: 'hidden', leaveActiveClass: 'animate-fadeout', hideOnOutsideClick: true }"
                        type="button"
                        class="layout-topbar-action layout-topbar-action-highlight"
                    >
                        <i class="pi pi-palette"></i>
                    </button>
                    <AppConfigurator />
                </div>
            </div>

            <button
                class="layout-topbar-menu-button layout-topbar-action"
                v-styleclass="{ selector: '@next', enterFromClass: 'hidden', enterActiveClass: 'animate-scalein', leaveToClass: 'hidden', leaveActiveClass: 'animate-fadeout', hideOnOutsideClick: true }"
            >
                <i class="pi pi-ellipsis-v"></i>
            </button>

            <div class="hidden layout-topbar-menu lg:block">
                <div class="layout-topbar-menu-content">
                    <button type="button" class="layout-topbar-action">
                        <i class="pi pi-calendar"></i>
                        <span>Calendar</span>
                    </button>
                    <button type="button" class="layout-topbar-action">
                        <i class="pi pi-inbox"></i>
                        <span>Messages</span>
                    </button>
                    <button type="button" class="layout-topbar-action" @click="goToLogin">
                        <i class="pi pi-user"></i>
                        <span>Profile</span>
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>
