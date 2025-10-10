import AppLayout from '@/layout/AppLayout.vue';
import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            component: AppLayout,
            children: [
                {
                    path: '/',
                    name: 'dashboard',
                    component: () => import('@/views/Dashboard.vue')
                },
                {
                    path: '/uikit/uc',
                    name: 'uc',
                    component: () => import('@/views/uikit/usercheck.vue')
                },
                {
                    path: '/uikit/test',
                    name: 'test',
                    component: () => import('@/views/uikit/Test.vue')
                },
                {
                    path: '/uikit/Seat',
                    name: 'Seat',
                    component: () => import('@/views/uikit/Seat.vue')
                },
                {
                    path: '/uikit/SeatPractice',
                    name: 'SeatPractice',
                    component: () => import('@/views/uikit/SeatPractice.vue')
                },
                {
                    path: '/uikit/SeatPracticefor4Day',
                    name: 'SeatPractice4Day',
                    component: () => import('@/views/uikit/SeatPractice4Day.vue')
                },
                {
                    path: '/uikit/SeatPracticefor4Daypillar',
                    name: 'SeatPractice4Daypillar',
                    component: () => import('@/views/uikit/SeatPractice4Daypillar.vue')
                },
                {
                    path: '/uikit/theme',
                    name: 'theme',
                    component: () => import('@/views/uikit/Theme.vue')
                },
                {
                    path: '/uikit/logs',
                    name: 'logs',
                    component: () => import('@/views/uikit/Logs.vue')
                },
                {
                    path: '/uikit/crud01',
                    name: 'crud01',
                    component: () => import('@/views/uikit/Crud01.vue')
                },
                {
                    path: '/uikit/List',
                    name: 'input',
                    component: () => import('@/views/uikit/ListDoc.vue')
                },
                {
                    path: '/uikit/Listdegree',
                    name: 'input',
                    component: () => import('@/views/uikit/Listdegree.vue')
                },
                {
                    path: '/uikit/list',
                    name: 'list',
                    component: () => import('@/views/uikit/ListDoc.vue')
                },
                {
                    path: '/pages/empty',
                    name: 'empty',
                    component: () => import('@/views/pages/Empty.vue')
                }
            ]
        },
        {
            path: '/landing',
            name: 'landing',
            component: () => import('@/views/pages/Landing.vue')
        },
        {
            path: '/pages/notfound',
            name: 'notfound',
            component: () => import('@/views/pages/NotFound.vue')
        },

        {
            path: '/auth/login',
            name: 'login',
            component: () => import('@/views/pages/auth/Login.vue')
        },
        {
            path: '/auth/access',
            name: 'accessDenied',
            component: () => import('@/views/pages/auth/Access.vue')
        },
        {
            path: '/auth/error',
            name: 'error',
            component: () => import('@/views/pages/auth/Error.vue')
        }
    ]
});

// การเพิ่ม navigation guard
router.beforeEach((to, from, next) => {
    const authStore = useAuthStore();
    const isAuthenticated = authStore.isAuthenticated;

    // หากผู้ใช้ไม่ได้ล็อกอินและพยายามไปที่หน้าอื่น ๆ จะถูกนำไปหน้า login
    if (!isAuthenticated && to.name !== 'login' && to.name !== 'landing' && to.name !== 'error') {
        next({ name: 'login' });
    } else {
        next();
    }
});

export default router;
