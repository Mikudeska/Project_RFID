<script setup>
import { computed, ref, nextTick, onMounted, onBeforeUnmount } from 'vue';
import { Icon } from '@iconify/vue';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE;

const displayTime = ref(new Date());
setInterval(() => {
    displayTime.value = new Date();
}, 1000);
const displayTimeString = computed(() => {
    return displayTime.value.toLocaleString('th-TH', {
        timeStyle: 'medium'
    });
});
const displayDateString = computed(() => {
    return displayTime.value.toLocaleString('th-TH', {
        dateStyle: 'full'
    });
});

const features = ref([
    { title: 'จำนวนบัญฑิตทั้งหมด', description: '0' },
    { title: 'จำนวนบัญฑิตที่ต้องมารายงานตัวทั้งหมด', description: '0' },
    { title: 'จำนวนบัญฑิตที่มารายงานตัว', description: '0' },
    { title: 'อยู่ในห้องพิธี', description: '0' }
]);

function handleWsMessage(event) {
    const msg = event.detail;

    if (msg.action === 'stats') {
        // อัพเดต features ตามข้อมูลใหม่
        const d = msg.data;
        features.value = [
            { title: 'จำนวนบัญฑิตทั้งหมด', description: d.total },
            { title: 'ยังไม่รายงานตัว', description: d.checked_in },
            { title: 'รายงานตัวแล้ว', description: d.in_checkin_room },
            { title: 'อยู่ในห้องพิธี', description: d.in_graduation_room }
        ];
    } else if (msg.action === 'comment') {
        comments.value.push({
            comment: msg.data.comment,
            time: msg.data.time
        });
        nextTick().then(() => {
            scrollToBottom();
        });
    }
}

async function fetchStats() {
    try {
        const res = await axios.get(`${API_BASE}/api/stats/`);
        const d = res.data;
        features.value = [
            { title: 'จำนวนบัญฑิตทั้งหมด', description: d.total },
            { title: 'ยังไม่รายงานตัว', description: d.checked_in },
            { title: 'รายงานตัวแล้ว', description: d.in_checkin_room },
            { title: 'อยู่ในห้องพิธี', description: d.in_graduation_room }
        ];
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

onMounted(async () => {
    await fetchStats();
    window.addEventListener('ws-message', handleWsMessage);
});

onBeforeUnmount(() => {
    window.removeEventListener('ws-message', handleWsMessage);
});
// ตัวแปรคอมเมนต์
const newComment = ref('');
const commentsContainer = ref(null);
const comments = ref([]);

const addComment = async () => {
    if (newComment.value.trim()) {
        try {
            await axios.post(`${API_BASE}/api/logs/new/`, {
                action: 'comment',
                model: 'Comment',
                details: newComment.value
            });

            newComment.value = '';
        } catch (err) {
            console.error('❌ Error posting comment:', err);
        }
    }
};

const scrollToBottom = () => {
    if (commentsContainer.value) {
        commentsContainer.value.scrollTo({
            top: commentsContainer.value.scrollHeight,
            behavior: 'smooth' // เพิ่ม effect การเลื่อนแบบ smooth
        });
    }
};
const loadComments = async () => {
    const res = await axios.get(`${API_BASE}/api/logs/`);
    const logs = res.data.results; // ดึง array จาก 'results'

    comments.value = logs
        .filter((log) => log.action === 'comment')
        .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp)) // เรียงจากเก่าไปใหม่
        .map((log) => ({
            comment: log.details,
            time: log.timestamp
        }));
};

onMounted(async () => {
    await loadComments();
    nextTick().then(() => {
        scrollToBottom();
    });

    // ✅ ดัก WebSocket
    window.addEventListener('ws-message', handleWsMessage);
});
</script>

<template>
    <div class="flex flex-col">
        <!-- ส่วนแสดงวันที่และเวลา -->
        <div class="card flex flex-row md:flex-row items-center justify-between mb-[2rem] gap-2 divide-x-4 divide-indigo-600">
            <div class="flex-1 text-center text-1xl sm:text-2xl md:text-3xl xl:text-5xl">{{ displayDateString }}</div>
            <div class="flex items-center justify-center flex-1 gap-2 text-2xl sm:text-5xl md:text-7xl">
                <Icon icon="material-symbols:alarm-outline-rounded"></Icon>
                <span>{{ displayTimeString }}</span>
            </div>
        </div>
        <div class="grid grid-cols-12 md:flex-row gap-[2rem]">
            <!-- ส่วนแสดงจำนวน -->
            <div class="col-span-12 md:col-span-8">
                <div class="grid grid-cols-12 gap-[2rem] h-full">
                    <div
                        class="flex flex-col col-span-12 duration-150 rounded-s-md hover:-translate-y-2 hover:shadow-2xl card xl:col-span-6"
                        v-for="(feat, index) in features"
                        :key="feat"
                        :class="[
                            index % 4 === 0
                                ? 'border-b-8 border-blue-500 rounded-b-xl'
                                : index % 4 === 1
                                ? 'border-b-8 border-red-500 rounded-b-xl'
                                : index % 4 === 2
                                ? 'border-b-8 border-green-500 rounded-b-xl'
                                : 'border-b-8 border-yellow-300 rounded-b-xl'
                        ]"
                    >
                        <h2 class="pb-2 text-xl text-center border-b-2 border-indigo-600 xl:text-4xl">
                            {{ feat.title }}
                        </h2>
                        <span class="flex items-center justify-around flex-grow pt-4 text-4xl xl:text-8xl"> {{ feat.description }} </span>
                    </div>
                </div>
            </div>
            <!-- ส่วนแสดงคอมเมนต์ -->
            <div class="col-span-12 md:col-span-4">
                <div class="card h-[calc(100vh-100px)] max-h-[calc(100vh-230px)] xl:max-h-[calc(100vh-310px)] overflow-auto" ref="commentsContainer">
                    <div class="pb-2 text-4xl">กล่องข้อความ</div>
                    <div v-for="(comment, index) in comments" :key="index" class="pt-2 mb-4 border-t-2 border-indigo-600">
                        <p class="w-full mb-2 text-lg text-center">
                            {{
                                new Date(comment.time).toLocaleString('th-TH', {
                                    dateStyle: 'short'
                                })
                            }}
                            {{
                                new Date(comment.time).toLocaleString('th-TH', {
                                    timeStyle: 'short'
                                })
                            }}
                        </p>
                        <p class="flex-col w-full px-2 text-2xl break-words">
                            {{ comment.comment }}
                        </p>
                    </div>
                    <div class="">
                        <div class="grid grid-cols-12 gap-2 pt-4 md:flex-row">
                            <InputText type="text" v-model="newComment" placeholder="พิมพ์คอมเมนต์ของคุณ.... " class="flex flex-col col-span-12 px-2 border rounded-md resize-none xl:col-span-10 text-1xl" />
                            <Button label="ส่ง" @click="addComment" class="flex flex-col col-span-12 text-xl xl:col-span-2" Rounded />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped></style>
