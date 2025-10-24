import { defineStore } from 'pinia';
import { ref } from 'vue';
import { WS_BASE_URL, isDevelopment } from '@/config';

// ใน development mode ปิด WebSocket โดยอัตโนมัติ (เพราะไม่มี Redis)
const useWebSocket = isDevelopment 
    ? import.meta.env.VITE_USE_WEBSOCKET === 'true'  // ต้องตั้งค่าเป็น true จริงๆ ถึงจะเปิด
    : import.meta.env.VITE_USE_WEBSOCKET !== 'false'; // production: เปิดโดยอัตโนมัติ

const wsBase = WS_BASE_URL;

export const useWebSocketStore = defineStore('websocket', () => {
    const socket = ref(null);
    const isConnected = ref(false);
    const viewerCount = ref(0);
    const connectionAttempts = ref(0);
    const maxRetries = 3;

    // ✨ เปลี่ยนจาก Array ธรรมดาเป็น Map เพื่อให้ลบ handler ออกได้ง่าย
    const handlers = new Map();
    let handlerId = 0;
    let reconnectTimeout = null;

    function connect() {
        if (!useWebSocket) {
            console.log('🔌 WebSocket disabled in development mode (USE_CHANNEL=false)');
            return;
        }

        if (socket.value) return;

        try {
            socket.value = new WebSocket(wsBase);

            socket.value.onopen = () => {
                console.log('✅ WebSocket connected');
                isConnected.value = true;
                connectionAttempts.value = 0;
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

            socket.value.onerror = (error) => {
                console.warn('⚠️ WebSocket error (กำลังทำงานในโหมดไม่มี WebSocket):', error.type);
                // ไม่ throw error แต่ทำงานต่อไปได้
            };

            socket.value.onclose = () => {
                console.log('🔌 WebSocket closed');
                isConnected.value = false;
                socket.value = null;

                // ลองเชื่อมต่อใหม่อัตโนมัติ (แต่จำกัดจำนวนครั้ง)
                if (useWebSocket && connectionAttempts.value < maxRetries) {
                    connectionAttempts.value++;
                    console.log(`🔄 Attempting to reconnect... (${connectionAttempts.value}/${maxRetries})`);
                    reconnectTimeout = setTimeout(connect, 5000);
                } else if (connectionAttempts.value >= maxRetries) {
                    console.log('❌ WebSocket disabled after max retries. App will work without real-time updates.');
                }
            };
        } catch (error) {
            console.warn('⚠️ Failed to create WebSocket connection:', error.message);
            console.log('ℹ️ App will work without real-time updates.');
        }
    }

    function disconnect() {
        // ยกเลิก reconnect timeout ถ้ามี
        if (reconnectTimeout) {
            clearTimeout(reconnectTimeout);
            reconnectTimeout = null;
        }
        
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

    return { socket, connect, disconnect, isConnected, viewerCount, registerHandler, connectionAttempts };
});
