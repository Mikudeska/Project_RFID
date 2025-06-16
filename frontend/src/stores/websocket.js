import { defineStore } from 'pinia';
import { ref } from 'vue';

const useWebSocket = import.meta.env.VITE_USE_WEBSOCKET === 'true';

export const useWebSocketStore = defineStore('websocket', () => {
    const socket = ref(null);

    function connect() {
        if (!useWebSocket) {
            console.log('🛑 WebSocket disabled by .env');
            return;
        }

        if (socket.value) return;

        socket.value = new WebSocket('ws://localhost:8000/ws/crud01/');

        socket.value.onopen = () => {
            console.log('🌐 WebSocket connected');
        };

        socket.value.onmessage = (event) => {
            const data = JSON.parse(event.data);
            window.dispatchEvent(new CustomEvent('ws-message', { detail: data }));
        };

        socket.value.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        socket.value.onclose = () => {
            console.log('WebSocket closed');
            socket.value = null;
        };
    }

    function disconnect() {
        if (socket.value) {
            socket.value.close();
            socket.value = null;
        }
    }

    return { socket, connect, disconnect };
});
