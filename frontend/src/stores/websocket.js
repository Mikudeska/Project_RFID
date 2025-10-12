import { defineStore } from 'pinia';
import { ref } from 'vue';

const useWebSocket = import.meta.env.VITE_USE_WEBSOCKET === 'true';
const wsBase = import.meta.env.VITE_API_WS_BASE;

export const useWebSocketStore = defineStore('websocket', () => {
    const socket = ref(null);
    const isConnected = ref(false);
    const viewerCount = ref(0);

    // ✨ เปลี่ยนจาก Array ธรรมดาเป็น Map เพื่อให้ลบ handler ออกได้ง่าย
    const handlers = new Map();
    let handlerId = 0;

    function connect() {
        if (!useWebSocket) {
            console.log('WebSocket disabled by .env');
            return;
        }

        if (socket.value) return;
        socket.value = new WebSocket(wsBase);

        socket.value.onopen = () => {
            console.log('WebSocket connected');
            isConnected.value = true;
        };

        socket.value.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'viewer_count') {
                viewerCount.value = data.count;
            }

            // ✨ เรียกใช้ handler ทุกตัวที่ลงทะเบียนไว้
            handlers.forEach((handler) => handler(data));

            // ✅ บรรทัดนี้ยังคงไว้ได้ เผื่อมีส่วนอื่นใช้ แต่เราจะเลิกใช้ใน Crud/ListDoc
            window.dispatchEvent(new CustomEvent('ws-message', { detail: data }));
        };

        socket.value.onerror = (error) => console.error('WebSocket error:', error);
        socket.value.onclose = () => {
            console.log('WebSocket closed');
            isConnected.value = false;
            socket.value = null;
        };
    }

    function disconnect() {
        if (socket.value) {
            socket.value.close();
        }
    }

    // ✨ อัปเกรดฟังก์ชันนี้
    function registerHandler(fn) {
        const id = handlerId++;
        handlers.set(id, fn);

        // ส่งฟังก์ชันสำหรับยกเลิกการลงทะเบียนกลับไป
        return () => handlers.delete(id);
    }

    return { socket, connect, disconnect, isConnected, viewerCount, registerHandler };
});
