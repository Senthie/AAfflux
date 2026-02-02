<!--
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-30 17:51:25
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-02-02 15:37:09
 * @FilePath: /web/src/components/workflows/EditableTitleCp.vue
 * @Description: 标题或者其他文字的修改
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
-->
<template>
    <div
        ref="titleEl"
        class="editable-title"
        :contenteditable="isEditing"
        @click="makeEditable"
        @blur="saveContent"
        @keydown.enter.prevent="saveAndBlur"
    >
        {{ title }}
    </div>
</template>

<script lang="ts" setup>
import { nextTick, ref } from 'vue'
import { debounce } from 'src/utils/debounce'

const title = defineModel({ default: '' })

const titleEl = ref<HTMLElement | null>(null)
const isEditing = ref(false)
const originalTitle = ref('')

const makeEditable = () => {
    if (!isEditing.value) {
        isEditing.value = true
        originalTitle.value = title.value

        // 聚焦并选择所有文本
        void nextTick(() => {
            if (titleEl.value != null) {
                titleEl.value.focus()
                selectAllText(titleEl.value)
            }
        })
    }
}

// 防抖的保存函数
const debouncedSave = debounce((newTitle: string) => {
    if (newTitle && newTitle !== originalTitle.value) {
        title.value = newTitle
    }
}, 300) // 300ms 防抖延迟

const saveContent = () => {
    if (isEditing.value && titleEl.value != null) {
        const newTitle = titleEl.value.textContent?.trim() || ''
        if (newTitle) {
            debouncedSave(newTitle)
        } else {
            titleEl.value.textContent = originalTitle.value
        }
        isEditing.value = false
    }
}

/**
 * 按回车键保存并失去焦点
 */
const saveAndBlur = (event: KeyboardEvent): void => {
    ;(event.target as HTMLElement).blur()
}

/**
 * 选择元素内的所有文本
 */
const selectAllText = (element: HTMLElement): void => {
    const selection = window.getSelection()
    const range = document.createRange()

    if (selection) {
        range.selectNodeContents(element)
        selection.removeAllRanges()
        selection.addRange(range)
    }
}
</script>

<style scoped>
.editable-title {
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 4px;
    transition: all 0.2s;
    min-height: 1.5em; /* 保持高度 */
    outline: none;
}

.editable-title:hover {
    background-color: rgba(0, 0, 0, 0.04);
}

.editable-title[contenteditable='true'] {
    background-color: white;
    border: 1px solid #027be3;
    box-shadow: 0 0 0 1px #027be3;
    cursor: text;
}
</style>
