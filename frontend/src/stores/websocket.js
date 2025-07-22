import { defineStore } from 'pinia';
import { ref } from 'vue';

const useWebSocket = import.meta.env.VITE_USE_WEBSOCKET === 'true';
const wsBase = import.meta.env.VITE_API_WS_BASE;

export const useWebSocketStore = defineStore('websocket', () => {
    const socket = ref(null);
    const isConnected = ref(false);
    const viewerCount = ref(0);
    const handlers = [];

    function connect() {
        if (!useWebSocket) {
            console.log('🛑 WebSocket disabled by .env');
            return;
        }

        if (socket.value) return;

        socket.value = new WebSocket(wsBase);

        socket.value.onopen = () => {
            console.log('🌐 WebSocket connected');
            isConnected.value = true;
        };

        socket.value.onmessage = (event) => {
            const data = JSON.parse(event.data);

            // ✅ แยกกรณี viewer count
            if (data.type === 'viewer_count') {
                viewerCount.value = data.count;
            }

            handlers.forEach((fn) => fn(data));

            // ✅ ไม่กระทบระบบเดิม (ยังส่ง customEvent เหมือนเดิม)
            window.dispatchEvent(new CustomEvent('ws-message', { detail: data }));
        };

        socket.value.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        socket.value.onclose = () => {
            console.log('WebSocket closed');
            isConnected.value = false;
            socket.value = null;
        };
    }

    function disconnect() {
        if (socket.value) {
            socket.value.close();
            socket.value = null;
            isConnected.value = false;
        }
    }

    function registerHandler(fn) {
        if (typeof fn === 'function') {
            handlers.push(fn);
        }
    }

    return {
        socket,
        connect,
        disconnect,
        isConnected,
        viewerCount,
        registerHandler
    };
});
