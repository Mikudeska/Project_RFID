<script setup>
import { ref } from 'vue';

import AppMenuItem from './AppMenuItem.vue';

const model = ref([
    {
        label: 'Home',
        items: [{ label: 'Dashboard', icon: 'material-symbols:empty-dashboard-outline', to: '/' }]
    },
    {
        label: 'Menu',
        items: [
            {
                label: 'รวมแผนที่นั่ง',
                icon: 'material-symbols:airline-seat-recline-normal',
                items: [
                    {
                        label: 'แผนที่นั่ง 35x35',
                        icon: 'material-symbols:event-seat',
                        items: [
                            { label: 'แผนที่นั่ง', icon: 'material-symbols:airline-seat-recline-normal', to: '/uikit/Seat' },
                            { label: 'แผนที่นั่งวันซ้อม', icon: 'material-symbols:event-seat', to: '/uikit/SeatPractice' }
                        ]
                    },
                    {
                        label: 'แผนที่นั่ง 32x27',
                        icon: 'material-symbols:backup-table',
                        items: [
                            { label: 'แผนที่นั่งวันซ้อมย่อย วันที่1', icon: 'material-symbols:backup-table', to: '/uikit/SeatPracticeDay1' },
                            { label: 'แผนที่นั่งวันซ้อมย่อย วันที่2', icon: 'material-symbols:backup-table', to: '/uikit/SeatPracticeDay2' },
                            { label: 'แผนที่นั่งวันซ้อมย่อย วันที่3', icon: 'material-symbols:backup-table', to: '/uikit/SeatPracticeDay3' },
                            { label: 'แผนที่นั่งวันซ้อมย่อย วันที่4', icon: 'material-symbols:backup-table', to: '/uikit/SeatPracticeDay4' }
                        ]
                    }
                ]
            },
            { label: 'รายชื่อบัณฑิต', icon: 'material-symbols:patient-list-outline', to: '/uikit/crud01' },
            { label: 'รายชื่อที่ผ่านเข้าประตู', icon: 'material-symbols:person-check-outline-rounded', to: '/uikit/List' },
            { label: 'ตารางสรุป', icon: 'material-symbols:person-check-outline-rounded', to: '/uikit/Listdegree' },
            { label: 'ประวัติการทำงาน', icon: 'material-symbols:history-rounded', to: '/uikit/logs' }
            // { label: 'Theme', icon: 'svg-spinners:ring-resize', to: '/uikit/theme' },
            // { label: 'Test', icon: 'svg-spinners:ring-resize', to: '/uikit/test' }
        ]
    }
    // {
    //     label: 'Pages',
    //     icon: 'pi pi-fw pi-briefcase',
    //     to: '/pages',
    //     items: [
    //         {
    //             label: 'Auth',
    //             icon: 'pi pi-fw pi-user',
    //             items: [
    //                 {
    //                     label: 'Login',
    //                     icon: 'pi pi-fw pi-sign-in',
    //                     to: '/auth/login'
    //                 }
    //             ]
    //         }
    //     ]
    // }
]);
</script>

<template>
    <div>
        <ul class="layout-menu">
            <template v-for="(item, i) in model">
                <app-menu-item v-if="!item.separator" :item="item" :index="i" :key="`item-${i}`"></app-menu-item>
                <li v-if="item.separator" class="menu-separator" :key="`separator-${i}`"></li>
            </template>
        </ul>
    </div>
</template>

<style lang="scss" scoped></style>
