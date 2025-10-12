// src/layout/composables/layout.js

import { reactive, computed, watch } from 'vue'; // ✨ 1. Import 'watch' เข้ามา

const layoutConfig = reactive({
    preset: 'Aura',
    primary: 'emerald',
    surface: null,
    darkTheme: true, // ✨ 2. กำหนดค่าเริ่มต้นเป็น true (Dark)
    menuMode: 'static'
});

const layoutState = reactive({
    staticMenuDesktopInactive: false,
    overlayMenuActive: false,
    profileSidebarVisible: false,
    configSidebarVisible: false,
    staticMenuMobileActive: false,
    menuHoverActive: false,
    activeMenuItem: null
});

// ✨ 3. เพิ่ม Logic การตรวจสอบและบันทึก Theme ด้วย watch
// ส่วนนี้จะทำงานอัตโนมัติทุกครั้งที่ layoutConfig.darkTheme เปลี่ยน
watch(
    () => layoutConfig.darkTheme,
    (isDark) => {
        if (isDark) {
            document.documentElement.classList.add('app-dark');
            localStorage.setItem('theme', 'dark'); // บันทึกค่าลง localStorage
        } else {
            document.documentElement.classList.remove('app-dark');
            localStorage.setItem('theme', 'light'); // บันทึกค่าลง localStorage
        }
    },
    { immediate: false } // เราจะไม่ให้ run ทันที แต่จะจัดการค่าเริ่มต้นเอง
);

// ✨ 4. เพิ่ม Logic การตั้งค่า Theme เมื่อเริ่มต้นแอป
// ส่วนนี้จะทำงานแค่ครั้งเดียวเมื่อ useLayout() ถูกเรียกใช้ครั้งแรก
const initializeTheme = () => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        // ถ้ามีค่าที่เคยบันทึกไว้, ให้ใช้ค่านั้น
        layoutConfig.darkTheme = savedTheme === 'dark';
    } else {
        // ถ้ายังไม่เคยบันทึก, ให้เช็คการตั้งค่าของ OS
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        layoutConfig.darkTheme = prefersDark;
    }
    // สั่งให้ class บน <html> element อัปเดตตามค่าเริ่มต้น
    if (layoutConfig.darkTheme) {
        document.documentElement.classList.add('app-dark');
    } else {
        document.documentElement.classList.remove('app-dark');
    }
};
initializeTheme(); // เรียกใช้ฟังก์ชันนี้ทันที

export function useLayout() {
    const setActiveMenuItem = (item) => {
        layoutState.activeMenuItem = item.value || item;
    };

    // ✨ 5. ปรับ toggleDarkMode ให้เหลือแค่การสลับค่า state
    // เพราะ watch จะจัดการส่วนที่เหลือ (เพิ่ม class, บันทึก localStorage) ให้เอง
    const toggleDarkMode = () => {
        layoutConfig.darkTheme = !layoutConfig.darkTheme;
    };

    // ฟังก์ชัน executeDarkModeToggle ไม่จำเป็นต้องใช้อีกต่อไป

    const toggleMenu = () => {
        if (layoutConfig.menuMode === 'overlay') {
            layoutState.overlayMenuActive = !layoutState.overlayMenuActive;
        }

        if (window.innerWidth > 991) {
            layoutState.staticMenuDesktopInactive = !layoutState.staticMenuDesktopInactive;
        } else {
            layoutState.staticMenuMobileActive = !layoutState.staticMenuMobileActive;
        }
    };

    const isSidebarActive = computed(() => layoutState.overlayMenuActive || layoutState.staticMenuMobileActive);
    const isDarkTheme = computed(() => layoutConfig.darkTheme);
    const getPrimary = computed(() => layoutConfig.primary);
    const getSurface = computed(() => layoutConfig.surface);

    return {
        layoutConfig,
        layoutState,
        toggleMenu,
        isSidebarActive,
        isDarkTheme,
        getPrimary,
        getSurface,
        setActiveMenuItem,
        toggleDarkMode // ส่งฟังก์ชันที่ปรับปรุงแล้วออกไป
    };
}
