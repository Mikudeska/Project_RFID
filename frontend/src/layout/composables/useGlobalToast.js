import { inject } from 'vue';
import { useToast } from 'primevue/usetoast';

// ฟังก์ชันสร้าง toast แบบใช้งานภายใน component
export function createLocalToast() {
  const toast = useToast();
  return {
    success: (msg, detail) => toast.add({ severity: 'success', summary: msg, detail, life: 3000 }),
    error: (msg, detail) => toast.add({ severity: 'error', summary: msg, detail, life: 3000 }),
    info: (msg, detail) => toast.add({ severity: 'info', summary: msg, detail, life: 3000 }),
    warn: (msg, detail) => toast.add({ severity: 'warn', summary: msg, detail, life: 3000 }),
  };
}

// ฟังก์ชันสำหรับดึง toast ที่ provide ไว้จาก component ตัวบนสุด (global)
export function useGlobalToast() {
  return inject('globalToast');
}
