import { useToast } from 'primevue/usetoast';

export function useGlobalToast() {
    const toast = useToast();
    return {
        show(action) {
            if (action === 'reset' || action === 'upload') {
                toast.add({
                    severity: 'info',
                    summary: action === 'reset' ? 'รีเซ็ตข้อมูล' : 'นำเข้าข้อมูล',
                    detail: action === 'reset' ? 'ข้อมูลได้ถูกรีเซ็ตเรียบร้อย' : 'ข้อมูลได้รับการอัปเดตเรียบร้อย',
                    life: 3000
                });
            }
        }
    };
}

export function createLocalToast() {
    const toast = useToast();
    return {
        success: (msg, detail) => toast.add({ severity: 'success', summary: msg, detail, life: 3000 }),
        error: (msg, detail) => toast.add({ severity: 'error', summary: msg, detail, life: 3000 }),
        info:   (msg, detail) => toast.add({ severity: 'info', summary: msg, detail, life: 3000 }),
        warn:   (msg, detail) => toast.add({ severity: 'warn', summary: msg, detail, life: 3000 })
    };
}

