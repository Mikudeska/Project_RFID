import { useToast } from 'primevue/usetoast';

export function useGlobalToast() {
    const toast = useToast();
    return {
        show(config) {
            let toastOptions = {};

            if (typeof config === 'string') {
                // --- 1. พฤติกรรมเดิม: ถ้าเป็น string ---
                if (config === 'reset' || config === 'upload') {
                    toastOptions = {
                        severity: 'info',
                        summary: config === 'reset' ? 'รีเซ็ตข้อมูล' : 'นำเข้าข้อมูล',
                        detail: config === 'reset' ? 'ข้อมูลได้ถูกรีเซ็ตเรียบร้อย' : 'ข้อมูลได้รับการอัปเดตเรียบร้อย',
                        life: 3000
                    };
                } else {
                    // ถ้าเป็น string อื่นๆ ที่ไม่รู้จัก ก็ไม่ต้องทำอะไร
                    return;
                }
            } else if (typeof config === 'object' && config !== null) {
                // --- 2. พฤติกรรมใหม่: ถ้าเป็น Object ---
                toastOptions = config;
            } else {
                // ไม่ใช่ string หรือ object ที่ถูกต้อง
                return;
            }

            toast.add(toastOptions);
        }
    };
}

export function createLocalToast() {
    const toast = useToast();
    return {
        success: (msg, detail) => toast.add({ severity: 'success', summary: msg, detail, life: 3000 }),
        error: (msg, detail) => toast.add({ severity: 'error', summary: msg, detail, life: 3000 }),
        info: (msg, detail) => toast.add({ severity: 'info', summary: msg, detail, life: 3000 }),
        warn: (msg, detail) => toast.add({ severity: 'warn', summary: msg, detail, life: 3000 })
    };
}