<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Icon } from '@iconify/vue';
import { useToast } from 'primevue/usetoast';
import Dialog from 'primevue/dialog';
import InputNumber from 'primevue/inputnumber';
import Button from 'primevue/button';

const router = useRouter();
const toast = useToast();

// ตัวแปรสำหรับการออกแบบ
const seatLayout = ref({
    rows: 70,
    seatsPerRow: 70,
    seatsPerSideA: 35,
    seatsPerSideB: 35
});

const pillars = ref([]);
const selectedPillar = ref(null);
const isAddingPillar = ref(false);
const newPillar = ref({
    row: 1,
    side: 'left',
    index: 0,
    length: 1
});

// ตัวเลือก layout templates
const layoutTemplates = [
    {
        name: 'แบบมาตรฐาน (35x35)',
        rows: 70,
        seatsPerRow: 70,
        seatsPerSideA: 35,
        seatsPerSideB: 35
    },
    {
        name: 'กำหนดเอง',
        rows: 0,
        seatsPerRow: 0,
        seatsPerSideA: 0,
        seatsPerSideB: 0,
        isCustom: true
    }
];

// ตัวแปรสำหรับการกำหนดเอง
const showCustomLayout = ref(false);
const showAddPillarDropdown = ref(false);
const customLayout = ref({
    rows: 70,
    seatsPerRow: 70,
    seatsPerSideA: 35,
    seatsPerSideB: 35
});

// ฟังก์ชันเปลี่ยน template
function changeTemplate(template) {
    console.log('changeTemplate called with:', template);
    console.log('template.isCustom:', template.isCustom);
    console.log('showCustomLayout.value:', showCustomLayout.value);

    if (template.isCustom) {
        // แสดงฟอร์มกำหนดเอง
        console.log('Opening custom layout dialog...');
        showCustomLayout.value = true;
        customLayout.value = { ...seatLayout.value }; // คัดลอกค่าปัจจุบัน
        console.log('showCustomLayout.value after set:', showCustomLayout.value);
    } else {
        // ใช้ template ที่เลือก
        seatLayout.value = { ...template };
        pillars.value = []; // ล้างเสาเก่า
        showCustomLayout.value = false;
        toast.add({
            severity: 'success',
            summary: 'เปลี่ยน Layout',
            detail: `เปลี่ยนเป็น ${template.name}`,
            life: 3000
        });
    }
}

// ฟังก์ชันยืนยันการกำหนดเอง
function confirmCustomLayout() {
    // ตรวจสอบความถูกต้อง
    if (customLayout.value.rows < 1 || customLayout.value.rows > 1000) {
        toast.add({
            severity: 'error',
            summary: 'ข้อผิดพลาด',
            detail: 'จำนวนแถวต้องอยู่ระหว่าง 1-1000',
            life: 3000
        });
        return;
    }

    if (customLayout.value.seatsPerSideA < 1 || customLayout.value.seatsPerSideB < 1) {
        toast.add({
            severity: 'error',
            summary: 'ข้อผิดพลาด',
            detail: 'จำนวนที่นั่งต่อฝั่งต้องมากกว่า 0',
            life: 3000
        });
        return;
    }

    // ใช้การตั้งค่าที่กำหนดเอง (ไม่ต้องตรวจสอบ seatsPerRow)
    seatLayout.value = {
        rows: customLayout.value.rows,
        seatsPerSideA: customLayout.value.seatsPerSideA,
        seatsPerSideB: customLayout.value.seatsPerSideB,
        // seatsPerRow จะถูกคำนวณใน SeatPractice ตามข้อมูลจริง
        seatsPerRow: customLayout.value.seatsPerSideA + customLayout.value.seatsPerSideB
    };
    pillars.value = []; // ล้างเสาเก่า
    showCustomLayout.value = false;

    toast.add({
        severity: 'success',
        summary: 'กำหนด Layout เอง',
        detail: `${customLayout.value.rows} แถว × แถวตั้งไม่จำกัด (ซ้าย ${customLayout.value.seatsPerSideA} + ขวา ${customLayout.value.seatsPerSideB})`,
        life: 3000
    });
}

// ฟังก์ชันยกเลิกการกำหนดเอง
function cancelCustomLayout() {
    showCustomLayout.value = false;
    customLayout.value = { ...seatLayout.value }; // รีเซ็ตเป็นค่าปัจจุบัน
}

// ฟังก์ชัน auto-calculate จำนวนที่นั่งต่อแถว
function autoCalculateSeatsPerRow() {
    customLayout.value.seatsPerRow = customLayout.value.seatsPerSideA + customLayout.value.seatsPerSideB;
}

// ฟังก์ชันเพิ่มเสา
function addPillar() {
    const pillar = {
        id: Date.now(),
        row: newPillar.value.row - 1, // แปลงเป็น 0-based
        side: newPillar.value.side,
        index: newPillar.value.index,
        length: newPillar.value.length
    };

    // ตรวจสอบว่าซ้อนทับกันหรือไม่
    if (checkPillarOverlap(pillar)) {
        toast.add({
            severity: 'error',
            summary: 'ไม่สามารถเพิ่มเสาได้',
            detail: 'เสาซ้อนทับกับเสาอื่น',
            life: 3000
        });
        return;
    }

    pillars.value.push(pillar);
    showAddPillarDropdown.value = false;
    resetNewPillar();

    toast.add({
        severity: 'success',
        summary: 'เพิ่มเสาเรียบร้อย',
        detail: `แถว ${pillar.row + 1}, ฝั่ง ${pillar.side === 'left' ? 'ซ้าย' : 'ขวา'}`,
        life: 3000
    });
}

// ฟังก์ชันลบเสา
function removePillar(pillarId) {
    const index = pillars.value.findIndex((p) => p.id === pillarId);
    if (index !== -1) {
        pillars.value.splice(index, 1);
        toast.add({
            severity: 'info',
            summary: 'ลบเสาเรียบร้อย',
            detail: 'เสาถูกลบออกจากแผนที่',
            life: 3000
        });
    }
}

// ฟังก์ชันสลับเสา (เพิ่ม/ลบ) โดยการคลิก
function togglePillar(row, side, index) {
    // หาเสาที่มีอยู่แล้วในตำแหน่งนี้
    const existingPillar = pillars.value.find((p) => p.row === row && p.side === side && p.index === index);

    if (existingPillar) {
        // ถ้ามีเสาอยู่แล้ว ให้ลบ
        removePillar(existingPillar.id);
    } else {
        // ถ้าไม่มีเสา ให้เพิ่ม
        const pillar = {
            id: Date.now(),
            row: row,
            side: side,
            index: index,
            length: 1
        };

        // ตรวจสอบว่าซ้อนทับกันหรือไม่
        if (checkPillarOverlap(pillar)) {
            toast.add({
                severity: 'error',
                summary: 'ไม่สามารถเพิ่มเสาได้',
                detail: 'เสาซ้อนทับกับเสาอื่น',
                life: 3000
            });
            return;
        }

        pillars.value.push(pillar);
        toast.add({
            severity: 'success',
            summary: 'เพิ่มเสาเรียบร้อย',
            detail: `แถว ${row + 1}, ฝั่ง ${side === 'left' ? 'ซ้าย' : 'ขวา'}, ตำแหน่ง ${index + 1}`,
            life: 3000
        });
    }
}

// ฟังก์ชันตรวจสอบเสาซ้อนทับ
function checkPillarOverlap(newPillar) {
    return pillars.value.some((pillar) => {
        if (pillar.row !== newPillar.row) return false;
        if (pillar.side !== newPillar.side) return false;

        const pillarStart = pillar.index;
        const pillarEnd = pillar.index + pillar.length;
        const newStart = newPillar.index;
        const newEnd = newPillar.index + newPillar.length;

        return !(newEnd <= pillarStart || newStart >= pillarEnd);
    });
}

// ฟังก์ชันรีเซ็ตเสาใหม่
function resetNewPillar() {
    newPillar.value = {
        row: 1,
        side: 'left',
        index: 0,
        length: 1
    };
}

// ฟังก์ชันสร้าง layout matrix
function createLayoutMatrix() {
    const matrix = [];
    for (let rowIdx = 0; rowIdx < seatLayout.value.rows; rowIdx++) {
        const layout = Array(seatLayout.value.seatsPerRow).fill('seat');

        // แทรกเสา
        pillars.value
            .filter((p) => p.row === rowIdx)
            .forEach((p) => {
                let insertIdx = p.side === 'left' ? p.index : seatLayout.value.seatsPerSideA + p.index;
                for (let i = 0; i < p.length; i++) {
                    if (insertIdx + i < layout.length) {
                        layout[insertIdx + i] = 'pillar';
                    }
                }
            });

        matrix.push(layout);
    }
    return matrix;
}

// ฟังก์ชันบันทึกการตั้งค่า
function saveLayout() {
    const layoutConfig = {
        seatLayout: seatLayout.value,
        pillars: pillars.value,
        timestamp: new Date().toISOString()
    };

    // บันทึกลง localStorage
    localStorage.setItem('seatLayoutConfig', JSON.stringify(layoutConfig));

    toast.add({
        severity: 'success',
        summary: 'บันทึกเรียบร้อย',
        detail: 'การตั้งค่าแผนที่นั่งถูกบันทึกแล้ว',
        life: 3000
    });
}

// ฟังก์ชันโหลดการตั้งค่า
function loadLayout() {
    const saved = localStorage.getItem('seatLayoutConfig');
    if (saved) {
        const config = JSON.parse(saved);
        seatLayout.value = config.seatLayout;
        pillars.value = config.pillars;
        toast.add({
            severity: 'info',
            summary: 'โหลดการตั้งค่า',
            detail: 'โหลดการตั้งค่าจากการบันทึกล่าสุด',
            life: 3000
        });
    }
}

// ฟังก์ชันส่งไปยังหน้า SeatPractice
function applyToSeatPractice() {
    const layoutConfig = {
        seatLayout: seatLayout.value,
        pillars: pillars.value
    };

    // บันทึกลง localStorage เพื่อให้หน้า SeatPractice อ่านได้
    localStorage.setItem('seatLayoutConfig', JSON.stringify(layoutConfig));

    toast.add({
        severity: 'success',
        summary: 'นำไปใช้',
        detail: 'การตั้งค่าถูกส่งไปยังหน้า SeatPractice',
        life: 3000
    });

    // ไปยังหน้า SeatPractice
    router.push('/uikit/SeatPractice');
}

// ฟังก์ชันล้างการตั้งค่า
function clearLayout() {
    pillars.value = [];
    toast.add({
        severity: 'info',
        summary: 'ล้างการตั้งค่า',
        detail: 'ลบเสาทั้งหมดออกจากแผนที่',
        life: 3000
    });
}

// ฟังก์ชันส่งออกการตั้งค่า
function exportLayout() {
    const layoutConfig = {
        seatLayout: seatLayout.value,
        pillars: pillars.value,
        timestamp: new Date().toISOString()
    };

    const dataStr = JSON.stringify(layoutConfig, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `seat-layout-${new Date().toISOString().split('T')[0]}.json`;
    link.click();

    URL.revokeObjectURL(url);

    toast.add({
        severity: 'success',
        summary: 'ส่งออกเรียบร้อย',
        detail: 'ไฟล์การตั้งค่าถูกดาวน์โหลดแล้ว',
        life: 3000
    });
}

// ฟังก์ชันนำเข้าการตั้งค่า
function importLayout(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const config = JSON.parse(e.target.result);
            seatLayout.value = config.seatLayout;
            pillars.value = config.pillars;

            toast.add({
                severity: 'success',
                summary: 'นำเข้าเรียบร้อย',
                detail: 'การตั้งค่าถูกนำเข้าแล้ว',
                life: 3000
            });
        } catch (error) {
            toast.add({
                severity: 'error',
                summary: 'นำเข้าล้มเหลว',
                detail: 'ไฟล์ไม่ถูกต้อง',
                life: 3000
            });
        }
    };
    reader.readAsText(file);
}

// ตัวแปรสำหรับจำนวนแถวที่แสดงใน preview
const previewRows = ref(30);

// ฟังก์ชันสร้าง preview แบบจำลอง
const layoutPreview = computed(() => {
    const matrix = createLayoutMatrix();
    const preview = matrix.slice(0, previewRows.value); // แสดงตาม previewRows

    return preview;
});

// ฟังก์ชันเพิ่มแถวใน preview
function increasePreviewRows() {
    if (previewRows.value < 100) {
        previewRows.value += 5;
    }
}

// ฟังก์ชันลดแถวใน preview
function decreasePreviewRows() {
    if (previewRows.value > 10) {
        previewRows.value -= 5;
    }
}

// ฟังก์ชันนับสถิติ
const statistics = computed(() => {
    const totalSeats = seatLayout.value.rows * seatLayout.value.seatsPerRow;
    const pillarSeats = pillars.value.reduce((sum, p) => sum + p.length, 0);
    const availableSeats = totalSeats - pillarSeats;

    return {
        totalSeats,
        pillarSeats,
        availableSeats,
        pillarCount: pillars.value.length
    };
});

onMounted(() => {
    loadLayout();
});
</script>

<template>
    <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
        <Toast />

        <!-- Header -->
        <div class="bg-white dark:bg-gray-800 shadow-lg">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex items-center justify-between h-16">
                    <div class="flex items-center">
                        <Icon icon="mdi:chair-rolling" class="text-blue-600 dark:text-blue-400 mr-3" width="32" height="32" />
                        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">ออกแบบแผนที่นั่ง</h1>
                    </div>
                    <div class="flex items-center space-x-4">
                        <button @click="router.back()" class="flex items-center px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors">
                            <Icon icon="mdi:arrow-left" class="mr-2" width="20" height="20" />
                            กลับ
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <div class="max-w-8xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <!-- Main Content Grid -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-2 sm:gap-3">
                <!-- Left Sidebar - Controls -->
                <div class="sm:col-span-1 lg:col-span-4 xl:col-span-3 2xl:col-span-4 space-y-2 sm:space-y-3">
                    <!-- Layout Templates -->
                    <div class="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-md shadow-sm border border-gray-200/50 dark:border-gray-700/50 p-2 sm:p-3">
                        <h2 class="text-xs font-semibold text-gray-900 dark:text-white mb-1 sm:mb-2 flex items-center">
                            <div class="p-0.5 bg-blue-100 dark:bg-blue-900/30 rounded mr-1">
                                <Icon icon="mdi:view-grid" class="text-blue-600 dark:text-blue-400" width="8" height="8" />
                            </div>
                            เลือก Layout Template
                        </h2>
                        <div class="space-y-1">
                            <button
                                v-for="template in layoutTemplates"
                                :key="template.name"
                                @click="changeTemplate(template)"
                                class="w-full p-1 sm:p-1.5 text-left border border-gray-200 dark:border-gray-600 rounded hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all duration-200 group"
                                :class="{
                                    'border-blue-500 bg-blue-50 dark:bg-blue-900/30': template.isCustom
                                }"
                            >
                                <div class="flex items-center justify-between">
                                    <div class="text-xs font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                                        {{ template.name }}
                                    </div>
                                    <div v-if="template.isCustom" class="p-0.5 bg-blue-100 dark:bg-blue-900/50 rounded-full">
                                        <Icon icon="mdi:cog" class="text-blue-600 dark:text-blue-400" width="8" height="8" />
                                    </div>
                                </div>
                                <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                    <template v-if="!template.isCustom"> {{ template.rows }} แถว × {{ template.seatsPerRow }} ที่นั่ง </template>
                                    <template v-else>
                                        <span class="text-blue-600 font-medium">กำหนดขนาดเอง</span>
                                        <div class="text-xs text-gray-400">คลิกเพื่อเปิดฟอร์มกำหนดเอง</div>
                                    </template>
                                </div>
                            </button>
                        </div>
                    </div>

                    <!-- Current Layout Info -->
                    <div class="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-md shadow-sm border border-gray-200/50 dark:border-gray-700/50 p-2 sm:p-3">
                        <h2 class="text-xs font-semibold text-gray-900 dark:text-white mb-1 sm:mb-2 flex items-center">
                            <div class="p-0.5 bg-green-100 dark:bg-green-900/30 rounded mr-1">
                                <Icon icon="mdi:information" class="text-green-600 dark:text-green-400" width="8" height="8" />
                            </div>
                            ข้อมูล Layout ปัจจุบัน
                        </h2>

                        <div class="space-y-1">
                            <div class="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded p-1.5">
                                <div class="text-center">
                                    <div class="text-sm font-bold text-blue-600 dark:text-blue-400">{{ seatLayout.seatsPerRow }}</div>
                                    <div class="text-xs text-gray-600 dark:text-gray-400">ที่นั่งต่อแถว</div>
                                </div>
                            </div>

                            <div class="grid grid-cols-2 gap-1">
                                <div class="bg-gray-50 dark:bg-gray-700/50 rounded p-1 text-center">
                                    <div class="text-xs font-bold text-gray-900 dark:text-white">{{ seatLayout.seatsPerSideA }}</div>
                                    <div class="text-xs text-gray-600 dark:text-gray-400">ฝั่งซ้าย</div>
                                </div>
                                <div class="bg-gray-50 dark:bg-gray-700/50 rounded p-1 text-center">
                                    <div class="text-xs font-bold text-gray-900 dark:text-white">{{ seatLayout.seatsPerSideB }}</div>
                                    <div class="text-xs text-gray-600 dark:text-gray-400">ฝั่งขวา</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- เพิ่มเสา -->
                    <div class="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-md shadow-sm border border-gray-200/50 dark:border-gray-700/50 p-2 sm:p-3">
                        <h2 class="text-xs font-semibold text-gray-900 dark:text-white mb-1 sm:mb-2 flex items-center">
                            <div class="p-0.5 bg-purple-100 dark:bg-purple-900/30 rounded mr-1">
                                <Icon icon="mdi:plus" class="text-purple-600 dark:text-purple-400" width="8" height="8" />
                            </div>
                            เพิ่มเสา
                        </h2>

                        <!-- Sub Menu Content -->
                        <div v-if="showAddPillarDropdown" class="space-y-3 mt-2">
                            <div class="grid grid-cols-2 gap-2">
                                <div>
                                    <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">แถว</label>
                                    <input
                                        v-model="newPillar.row"
                                        type="number"
                                        min="1"
                                        :max="seatLayout.rows"
                                        class="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                                    />
                                </div>
                                <div>
                                    <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">ฝั่ง</label>
                                    <select v-model="newPillar.side" class="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white">
                                        <option value="left">ซ้าย</option>
                                        <option value="right">ขวา</option>
                                    </select>
                                </div>
                            </div>
                            <div class="grid grid-cols-2 gap-2">
                                <div>
                                    <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">ตำแหน่ง</label>
                                    <input
                                        v-model="newPillar.index"
                                        type="number"
                                        min="0"
                                        :max="newPillar.side === 'left' ? seatLayout.seatsPerSideA - 1 : seatLayout.seatsPerSideB - 1"
                                        class="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                                    />
                                </div>
                                <div>
                                    <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">ความยาว</label>
                                    <input
                                        v-model="newPillar.length"
                                        type="number"
                                        min="1"
                                        max="10"
                                        class="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                                    />
                                </div>
                            </div>
                            <button
                                @click="addPillar"
                                class="w-full bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 text-white font-semibold py-1.5 px-2 rounded-md transition-all duration-200 flex items-center justify-center text-sm"
                            >
                                <Icon icon="mdi:plus" class="mr-1" width="12" height="12" />
                                เพิ่มเสา
                            </button>
                        </div>

                        <!-- Toggle Button -->
                        <button
                            @click="showAddPillarDropdown = !showAddPillarDropdown"
                            class="w-full bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 text-white font-semibold py-1 sm:py-1.5 px-2 rounded transition-all duration-200 shadow-sm hover:shadow-md flex items-center justify-center text-xs mt-2"
                        >
                            <Icon :icon="showAddPillarDropdown ? 'mdi:minus' : 'mdi:plus'" class="mr-1" width="10" height="10" />
                            {{ showAddPillarDropdown ? 'ซ่อนฟอร์ม' : 'เพิ่มเสา' }}
                            <Icon icon="mdi:chevron-down" class="ml-1 transition-transform duration-200" :class="showAddPillarDropdown ? 'rotate-180' : ''" width="8" height="8" />
                        </button>
                    </div>

                    <!-- รายการเสา -->
                    <div class="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-md shadow-sm border border-gray-200/50 dark:border-gray-700/50 p-2 sm:p-3">
                        <h2 class="text-xs font-semibold text-gray-900 dark:text-white mb-1 sm:mb-2 flex items-center">
                            <div class="p-0.5 bg-orange-100 dark:bg-orange-900/30 rounded mr-1">
                                <Icon icon="mdi:pillar" class="text-orange-600 dark:text-orange-400" width="8" height="8" />
                            </div>
                            รายการเสา ({{ pillars.length }})
                        </h2>
                        <div v-if="pillars.length === 0" class="text-center py-4 text-gray-500 dark:text-gray-400">
                            <Icon icon="mdi:pillar" class="mx-auto mb-2 text-2xl text-gray-300" width="24" height="24" />
                            <p class="text-xs">ยังไม่มีการวางตำแหน่งเสา</p>
                            <p class="text-xs text-gray-400 mt-1">กรุณากดปุ่ม "เพิ่มเสา หรือ กดตรงที่นั่ง" เพื่อเริ่มต้นวางเสา</p>
                        </div>
                        <div v-else class="space-y-2 max-h-48 overflow-y-auto">
                            <div v-for="pillar in pillars" :key="pillar.id" class="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                                <div class="flex items-center space-x-2">
                                    <Icon icon="mdi:pillar" class="text-orange-600" width="16" height="16" />
                                    <div>
                                        <div class="text-sm font-medium text-gray-900 dark:text-white">แถว {{ pillar.row + 1 }}, ฝั่ง {{ pillar.side === 'left' ? 'ซ้าย' : 'ขวา' }}</div>
                                        <div class="text-xs text-gray-600 dark:text-gray-400">ตำแหน่ง {{ pillar.index }}, ยาว {{ pillar.length }} ช่อง</div>
                                    </div>
                                </div>
                                <button @click="removePillar(pillar.id)" class="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">
                                    <Icon icon="mdi:delete" width="16" height="16" />
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Actions -->
                    <div class="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-4">
                        <div class="space-y-3">
                            <button
                                @click="applyToSeatPractice"
                                class="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-semibold py-3 px-4 rounded-lg transition-all duration-200 shadow-md hover:shadow-lg flex items-center justify-center"
                            >
                                <Icon icon="mdi:check-circle" class="mr-2" width="18" height="18" />
                                นำไปใช้
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Main Content Area -->
                <div class="sm:col-span-1 lg:col-span-8 xl:col-span-9 2xl:col-span-8">
                    <!-- Layout Preview -->
                    <!-- Statistics -->
                    <!-- สถิติ - ลบแล้ว -->

                    <!-- Layout Preview -->
                    <div class="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-md shadow-sm border border-gray-200/50 dark:border-gray-700/50 p-2 sm:p-3">
                        <div class="flex items-center justify-between mb-1 sm:mb-2">
                            <h2 class="text-xs font-semibold text-gray-900 dark:text-white flex items-center">
                                <div class="p-0.5 bg-green-100 dark:bg-green-900/30 rounded mr-1">
                                    <Icon icon="mdi:eye" class="text-green-600 dark:text-green-400" width="8" height="8" />
                                </div>
                                ตัวอย่าง Layout ({{ previewRows }} แถวแรก)
                            </h2>
                            <div class="flex items-center gap-1">
                                <button
                                    @click="decreasePreviewRows"
                                    :disabled="previewRows <= 5"
                                    class="p-1 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    <Icon icon="mdi:minus" class="text-gray-600 dark:text-gray-400" width="12" height="12" />
                                </button>
                                <span class="text-xs text-gray-600 dark:text-gray-400 px-2">{{ previewRows }}</span>
                                <button
                                    @click="increasePreviewRows"
                                    :disabled="previewRows >= 100"
                                    class="p-1 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    <Icon icon="mdi:plus" class="text-gray-600 dark:text-gray-400" width="12" height="12" />
                                </button>
                            </div>
                        </div>
                        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-md p-2">
                            <div class="overflow-x-auto">
                                <div class="inline-block min-w-full">
                                    <div v-for="(row, rowIdx) in layoutPreview" :key="rowIdx" class="flex items-center mb-0.5">
                                        <div class="w-12 text-xs font-medium text-gray-600 dark:text-gray-400 mr-1 text-center">แถว A{{ rowIdx + 1 }}</div>
                                        <div class="flex gap-0.5 items-center">
                                            <!-- ฝั่งซ้าย -->
                                            <div class="flex gap-1">
                                                <div
                                                    v-for="(seat, seatIdx) in row.slice(0, seatLayout.seatsPerSideA)"
                                                    :key="`left-${seatIdx}`"
                                                    @click="togglePillar(rowIdx, 'left', seatIdx)"
                                                    :class="[
                                                        'w-3 h-3 sm:w-3.5 sm:h-3.5 lg:w-4 lg:h-4 rounded-sm border transition-all duration-200 cursor-pointer',
                                                        seat === 'pillar' ? 'bg-yellow-400 border-yellow-600 hover:bg-yellow-500' : 'bg-blue-200 border-blue-400 hover:bg-blue-300'
                                                    ]"
                                                    :title="seat === 'pillar' ? `คลิกเพื่อลบเสา (ตำแหน่ง ${seatIdx + 1})` : `คลิกเพื่อเพิ่มเสา (ตำแหน่ง ${seatIdx + 1})`"
                                                ></div>
                                            </div>
                                            <div class="w-12 text-xs font-medium text-gray-600 dark:text-gray-400 mr-1 text-center">แถว A{{ rowIdx + 1 }}</div>
                                            <!-- ช่องว่างตรงกลาง -->
                                            <div class="w-5 h-5 sm:w-5.5 sm:h-5.5 lg:w-10 lg:h-5 bg-green-100 border border-dashed border-green-300 dark:border-green-600 rounded-sm mx-0.5 flex items-center justify-center">
                                                <Icon icon="mdi:walk" class="text-green-500" width="10" height="10" />
                                            </div>

                                            <div class="w-12 text-xs font-medium text-gray-600 dark:text-gray-400 mr-1 text-center">แถว B{{ rowIdx + 1 }}</div>
                                            <!-- ฝั่งขวา -->
                                            <div class="flex gap-1">
                                                <div
                                                    v-for="(seat, seatIdx) in row.slice(seatLayout.seatsPerSideA)"
                                                    :key="`right-${seatIdx}`"
                                                    @click="togglePillar(rowIdx, 'right', seatIdx)"
                                                    :class="[
                                                        'w-3 h-3 sm:w-3.5 sm:h-3.5 lg:w-4 lg:h-4 rounded-sm border transition-all duration-200 cursor-pointer',
                                                        seat === 'pillar' ? 'bg-yellow-400 border-yellow-600 hover:bg-yellow-500' : 'bg-pink-200 border-pink-400 hover:bg-pink-300'
                                                    ]"
                                                    :title="seat === 'pillar' ? `คลิกเพื่อลบเสา (ตำแหน่ง ${seatIdx + 1})` : `คลิกเพื่อเพิ่มเสา (ตำแหน่ง ${seatIdx + 1})`"
                                                ></div>
                                            </div>
                                            <div class="w-12 text-xs font-medium text-gray-600 dark:text-gray-400 mr-1 text-center">แถว B{{ rowIdx + 1 }}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="mt-1 flex flex-wrap items-center gap-1 sm:gap-2 text-xs">
                            <div class="flex items-center">
                                <div class="w-3 h-3 sm:w-3.5 sm:h-3.5 bg-blue-200 border border-blue-400 rounded-sm mr-1"></div>
                                <span class="text-gray-600 dark:text-gray-400">ที่นั่งซ้าย</span>
                            </div>
                            <div class="flex items-center">
                                <div class="w-3 h-3 sm:w-3.5 sm:h-3.5 bg-pink-200 border border-pink-400 rounded-sm mr-1"></div>
                                <span class="text-gray-600 dark:text-gray-400">ที่นั่งขวา</span>
                            </div>
                            <div class="flex items-center">
                                <div class="w-3 h-3 sm:w-3.5 sm:h-3.5 bg-yellow-400 border border-yellow-600 rounded-sm mr-1"></div>
                                <span class="text-gray-600 dark:text-gray-400">เสา</span>
                            </div>
                            <div class="flex items-center">
                                <div class="w-3 h-3 sm:w-3.5 sm:h-3.5 bg-green-100 border border-dashed border-green-300 rounded-sm mr-1 flex items-center justify-center">
                                    <Icon icon="mdi:walk" class="text-green-500" width="8" height="8" />
                                </div>
                                <span class="text-gray-600 dark:text-gray-400">ทางเดิน</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Custom Layout Dialog -->
        <div v-if="showCustomLayout" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click="cancelCustomLayout">
            <div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4" @click.stop>
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-bold text-gray-900 dark:text-white">กำหนด Layout เอง</h2>
                    <button @click="cancelCustomLayout" class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
                        <Icon icon="mdi:close" width="24" height="24" />
                    </button>
                </div>
                <!-- Debug Info - ซ่อนแล้ว -->
                <div class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium mb-2">จำนวนแถว</label>
                            <input v-model.number="customLayout.rows" type="number" min="1" max="200" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-2">จำนวนที่นั่งต่อแถว (คำนวณอัตโนมัติ)</label>
                            <input
                                :value="customLayout.seatsPerSideA + customLayout.seatsPerSideB"
                                type="number"
                                readonly
                                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300"
                            />
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium mb-2">จำนวนที่นั่งฝั่งซ้าย</label>
                            <input
                                v-model.number="customLayout.seatsPerSideA"
                                type="number"
                                min="1"
                                max="100"
                                @input="autoCalculateSeatsPerRow"
                                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-2">จำนวนที่นั่งฝั่งขวา</label>
                            <input
                                v-model.number="customLayout.seatsPerSideB"
                                type="number"
                                min="1"
                                max="100"
                                @input="autoCalculateSeatsPerRow"
                                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                    </div>

                    <div class="card p-4 rounded-lg">
                        <h4 class="text-base font-semibold mb-2">📊 ข้อมูล Layout</h4>
                        <div class="text-base grid grid-cols-2 gap-x-4 gap-y-2">
                            <div>แถว -> {{ customLayout.rows }} แถว</div>
                            <div>ที่นั่งต่อแถว -> {{ customLayout.seatsPerRow }} ที่นั่ง</div>
                            <div>ฝั่งซ้าย -> {{ customLayout.seatsPerSideA }} ที่นั่ง</div>
                            <div>ฝั่งขวา -> {{ customLayout.seatsPerSideB }} ที่นั่ง</div>
                            <div class="mt-2 text-sm flex" :class="customLayout.seatsPerSideA + customLayout.seatsPerSideB === customLayout.seatsPerRow ? 'text-green-600' : 'text-red-600'">
                                <Icon :icon="customLayout.seatsPerSideA + customLayout.seatsPerSideB === customLayout.seatsPerRow ? 'mdi:check-circle' : 'mdi:alert-circle'" class="mr-1" width="16" height="16" />
                                {{ customLayout.seatsPerSideA + customLayout.seatsPerSideB === customLayout.seatsPerRow ? 'ข้อมูลถูกต้อง' : 'จำนวนที่นั่งไม่ตรงกัน' }}
                            </div>
                        </div>
                    </div>

                    <div class="flex justify-end gap-2">
                        <button @click="cancelCustomLayout" class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600">ยกเลิก</button>
                        <button @click="confirmCustomLayout" :disabled="customLayout.seatsPerSideA + customLayout.seatsPerSideB !== customLayout.seatsPerRow" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400">
                            ยืนยัน
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
/* Custom styles if needed */
</style>
