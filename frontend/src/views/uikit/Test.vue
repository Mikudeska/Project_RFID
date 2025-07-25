<script setup>
import { Icon } from '@iconify/vue';
import { useToast } from 'primevue/usetoast';
import { ref, onUnmounted, computed } from 'vue';
import { useOnline } from '@vueuse/core';

const online = useOnline();
const wifistatus = computed(() => (online.value ? 'svg-spinners:wifi-fade' : 'material-symbols:wifi-off-rounded'));
const clazz = computed(() => (online.value ? 'text-primary' : 'text-red'));
const text = computed(() => (online.value ? 'Online' : 'Offline'));
const toast = useToast();
const visible = ref(false);
const progress = ref(0);
const interval = ref();

const upload = () => {
    if (!visible.value) {
        toast.add({ severity: 'custom', summary: 'Uploading your files.', group: 'headless', styleClass: 'backdrop-blur-lg rounded-2xl' });
        visible.value = true;
        progress.value = 0;

        if (interval.value) {
            clearInterval(interval.value);
        }

        interval.value = setInterval(() => {
            if (progress.value <= 100) {
                progress.value = progress.value + 20;
            }

            if (progress.value >= 100) {
                progress.value = 100;
                clearInterval(interval.value);
            }
        }, 1000);
    }
};
</script>

<template>
    <div class="grid grid-cols-[repeat(3,1fr)] grid-rows-[repeat(3,1fr)] gap-y-[10px] gap-x-[10px]">
        <div class="flex flex-col items-start gap-2 card row-1 row-2 col-1 col-2">
            <FileUpload ref="fileupload" mode="basic" name="demo[]" url="/api/upload" accept="image/*" :maxFileSize="1000000" @upload="onUpload" />
            <Button label="Upload" @click="upload" severity="secondary" />
            <Toast position="top-center" group="headless" @close="visible = false">
                <template #container="{ message, closeCallback }">
                    <section class="flex flex-col w-full gap-4 p-4 rounded-xl">
                        <div class="flex items-center gap-5">
                            <Icon icon="subway:upload-1"></Icon>
                            <span class="text-base font-bold">{{ message.summary }}</span>
                        </div>
                        <div class="flex flex-col gap-2">
                            <ProgressBar :value="progress" :showValue="false" :style="{ height: '4px' }"></ProgressBar>
                            <label class="text-sm font-bold">{{ progress }}% uploaded</label>
                        </div>
                        <div class="flex justify-end gap-4 mb-4">
                            <Button label="Another Upload?" size="small" @click="closeCallback"></Button>
                            <Button label="Cancel" size="small" @click="closeCallback"></Button>
                        </div>
                    </section>
                </template>
            </Toast>
        </div>
        <div class="card row-1 row-2 col-2 col-3">
            <div class="flex items-center gap-2 text-5xl">
                Status: <b class="flex items-center gap-2 text-5xl" :class="clazz"><Icon :icon="wifistatus" />{{ text }}</b>
            </div>
        </div>
        <div class="card row-1 row-2 col-3 col-4">
            <Badge value="3" severity="danger" />
        </div>
        <div class="card row-2 row-3 col-1 col-2">4</div>
        <div class="card row-2 row-3 col-2 col-3">5</div>
        <div class="card row-2 row-3 col-3 col-4">6</div>
        <div class="card row-3 row-4 col-1 col-2">7</div>
        <div class="card row-3 row-4 col-2 col-3">8</div>
        <div class="card row-3 row-4 col-3 col-4">9</div>
    </div>
</template>

<style scoped></style>
