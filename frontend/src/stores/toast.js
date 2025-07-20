// stores/toast.js
import { defineStore } from 'pinia';
import { useToast } from 'primevue/usetoast';

export const useGlobalToastStore = defineStore('globalToast', {
    state: () => ({
        toast: null
    }),
    actions: {
        init() {
            if (!this.toast) {
                this.toast = useToast();
            }
        },
        show(action) {
            if (!this.toast) return;
            if (action === 'reset' || action === 'upload') {
                this.toast.add({
                    severity: 'info',
                    summary: action === 'reset' ? 'รีเซ็ตข้อมูล' : 'นำเข้าข้อมูล',
                    detail: action === 'reset' ? 'ข้อมูลได้ถูกรีเซ็ตเรียบร้อย' : 'ข้อมูลได้รับการอัปเดตเรียบร้อย',
                    life: 3000
                });
            }
        }
    }
});

export function createLocalToast() {
    const toast = useToast();
    return {
        success: (msg, detail) => toast.add({ severity: 'success', summary: msg, detail, life: 3000 }),
        error: (msg, detail) => toast.add({ severity: 'error', summary: msg, detail, life: 3000 }),
        info: (msg, detail) => toast.add({ severity: 'info', summary: msg, detail, life: 3000 }),
        warn: (msg, detail) => toast.add({ severity: 'warn', summary: msg, detail, life: 3000 })
    };
}
