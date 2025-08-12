document.documentElement.classList.add('app-dark');

import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { Icon } from '@iconify/vue';
import Aura from '@primevue/themes/aura';
import PrimeVue from 'primevue/config';
import ConfirmationService from 'primevue/confirmationservice';
import ToastService from 'primevue/toastservice';
import Toast from 'primevue/toast';
import Tooltip from 'primevue/tooltip';
import JsonExcel from 'vue-json-excel3';
import { definePreset } from '@primevue/themes';
import { createPinia } from 'pinia';
import Badge from 'primevue/badge';
import { useAuthStore } from '@/stores/auth';
import axios from 'axios';

axios.defaults.withCredentials = true;

import '@/assets/styles.scss';
import '@/assets/tailwind.css';

const app = createApp(App);

const MyPreset = definePreset(Aura, {
    semantic: {
        primary: {
            50: '{green.50}',
            100: '{green.100}',
            200: '{green.200}',
            300: '{green.300}',
            400: '{green.400}',
            500: '{green.500}',
            600: '{green.600}',
            700: '{green.700}',
            800: '{green.800}',
            900: '{green.900}',
            950: '{green.950}'
        },
        colorScheme: {
            light: {
                surface: {
                    0: '#ffffff',
                    50: '{zinc.50}',
                    100: '{zinc.100}',
                    200: '{zinc.200}',
                    300: '{zinc.300}',
                    400: '{zinc.400}',
                    500: '{zinc.500}',
                    600: '{zinc.600}',
                    700: '{zinc.700}',
                    800: '{zinc.800}',
                    900: '{zinc.900}',
                    950: '{zinc.950}'
                }
            },
            dark: {
                surface: {
                    0: '#ffffff',
                    50: '{gray.50}',
                    100: '{gray.100}',
                    200: '{gray.200}',
                    300: '{gray.300}',
                    400: '{gray.400}',
                    500: '{gray.500}',
                    600: '{gray.600}',
                    700: '{gray.700}',
                    800: '{gray.800}',
                    900: '{gray.900}',
                    950: '{gray.950}'
                }
            }
        }
    }
});

const pinia = createPinia();
app.use(pinia);

const auth = useAuthStore();
auth.loadUser();
if (auth.user) {
    await auth.fetchUserProfile();
}

app.use(router);
app.use(PrimeVue, {
    theme: {
        preset: MyPreset,
        options: {
            darkModeSelector: '.app-dark'
        }
    }
});
app.use(ToastService);
app.use(ConfirmationService);
app.directive('tooltip', Tooltip);
app.component('Badge', Badge);
app.component('Toast', Toast);
app.component('downloadExcel', JsonExcel);
app.component('Icon', Icon);
app.mount('#app');
