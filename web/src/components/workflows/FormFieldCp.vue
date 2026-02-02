<script setup lang="ts">
import type { ManifestItem } from 'src/interfaces/IPlugin'
import { isFileManifestItem } from 'src/interfaces/IPlugin'
import { ref, computed, watch, nextTick } from 'vue'
import emitter from 'src/boot/mitt'

// TODO: 验证 `config` 的参数
// TODO: 设置相应事件

interface Props {
    field: ManifestItem
    modelValue: unknown
    error?: string | undefined
    disabled?: boolean
    nodeId?: string // 添加nodeId用于标识是哪个节点的字段
}

const props = defineProps<Props>()

// 本地值
const localValue = ref(props.modelValue)
const arrayInputValue = ref('')

// 计算属性
const textareaRows = computed(() => {
    if (props.field.type === 'textarea') {
        return Math.min(10, Math.max(3, props.field.rows || 4))
    }
    return 4
})

// 验证字段
const validate = (value: unknown): string | null => {
    // 必填验证
    if (props.field.required) {
        if (value === null || value === undefined || value === '') {
            return `${props.field.label} 是必填项`
        }
    }

    // 字符串类型验证
    if (typeof value === 'string') {
        // 最大长度验证
        if (props.field.maxLength && value.length > props.field.maxLength) {
            return `${props.field.label} 不能超过 ${props.field.maxLength} 个字符`
        }

        // 正则表达式验证
        if (props.field.validation?.regex) {
            try {
                const regex = new RegExp(props.field.validation.regex)
                if (!regex.test(value)) {
                    return (
                        props.field.validation.message ||
                        `${props.field.label} 格式不正确`
                    )
                }
            } catch {
                console.warn('无效的正则表达式:', props.field.validation.regex)
            }
        }
    }

    // 数字类型验证
    if (props.field.type === 'number') {
        const numValue = Number(value)
        if (isNaN(numValue)) {
            return `${props.field.label} 必须是数字`
        }

        if (props.field.min !== undefined && numValue < props.field.min) {
            return `${props.field.label} 不能小于 ${props.field.min}`
        }

        if (props.field.max !== undefined && numValue > props.field.max) {
            return `${props.field.label} 不能大于 ${props.field.max}`
        }
    }

    return null
}

// 获取文件显示文本
const getFileText = () => {
    if (!localValue.value) {
        return props.field.placeholder || '未选择文件'
    }

    if (localValue.value instanceof File) {
        return localValue.value.name
    }

    if (Array.isArray(localValue.value)) {
        return `已选择 ${localValue.value.length} 个文件`
    }

    return localValue.value
}

// 处理文件变化
const handleFileChange = (event: Event) => {
    const input = event.target as HTMLInputElement
    if (input.files && isFileManifestItem(props.field)) {
        if (props.field.multiple) {
            localValue.value = Array.from(input.files)
        } else {
            localValue.value = input.files[0]
        }
        handleInput() // 触发更新
    }
}

// 移除文件
const removeFile = () => {
    localValue.value = null
    handleInput() // 触发更新
}

// 添加数组项
const addArrayItem = () => {
    if (!arrayInputValue.value.trim()) return

    if (!Array.isArray(localValue.value)) {
        localValue.value = []
    }

    ;(localValue.value as unknown[]).push(arrayInputValue.value.trim())
    arrayInputValue.value = ''
    handleInput() // 触发更新
}

// 移除数组项
const removeArrayItem = (index: number) => {
    if (Array.isArray(localValue.value)) {
        ;(localValue.value as unknown[]).splice(index, 1)
        handleInput() // 触发更新
    }
}

// 处理输入
const handleInput = () => {
    // 通过mitt发出更新事件
    const updatePayload: { fieldKey: string; value: unknown; nodeId?: string } =
        {
            fieldKey: props.field.key,
            value: localValue.value,
        }
    if (props.nodeId) {
        updatePayload.nodeId = props.nodeId
    }
    emitter.emit('formfield:value.update', updatePayload)

    // 验证并通过mitt发出验证事件
    const error = validate(localValue.value)
    const validatePayload: {
        fieldKey: string
        isValid: boolean
        error?: string
        nodeId?: string
    } = {
        fieldKey: props.field.key,
        isValid: !error,
    }
    if (error) {
        validatePayload.error = error
    }
    if (props.nodeId) {
        validatePayload.nodeId = props.nodeId
    }
    emitter.emit('formfield:validate', validatePayload)
}

// 处理失去焦点
const handleBlur = () => {
    const error = validate(localValue.value)
    const validatePayload: {
        fieldKey: string
        isValid: boolean
        error?: string
        nodeId?: string
    } = {
        fieldKey: props.field.key,
        isValid: !error,
    }
    if (error) {
        validatePayload.error = error
    }
    if (props.nodeId) {
        validatePayload.nodeId = props.nodeId
    }
    emitter.emit('formfield:validate', validatePayload)
}

// 监听外部值变化
watch(
    () => props.modelValue,
    (newValue) => {
        localValue.value = newValue
    }
)

// 监听本地值变化并验证
watch(
    localValue,
    (newValue) => {
        void nextTick(() => {
            // 通过mitt发出更新事件
            const updatePayload: {
                fieldKey: string
                value: unknown
                nodeId?: string
            } = {
                fieldKey: props.field.key,
                value: newValue,
            }
            if (props.nodeId) {
                updatePayload.nodeId = props.nodeId
            }
            console.log('发生更新')
            emitter.emit('formfield:value.update', updatePayload)

            // 验证并通过mitt发出验证事件
            const error = validate(newValue)
            const validatePayload: {
                fieldKey: string
                isValid: boolean
                error?: string
                nodeId?: string
            } = {
                fieldKey: props.field.key,
                isValid: !error,
            }
            if (error) {
                validatePayload.error = error
            }
            if (props.nodeId) {
                validatePayload.nodeId = props.nodeId
            }
            emitter.emit('formfield:validate', validatePayload)
        })
    },
    { deep: true }
)
</script>
<template>
    <div
        class="form-field"
        :class="{ 'has-error': !!error, required: field.required }"
    >
        <label :for="field.key" class="field-label">
            {{ field.label }}
            <span v-if="field.required" class="required-asterisk">*</span>
        </label>

        <div>
            <!-- 文本输入框 -->
            <q-input
                outlined
                v-if="field.type === 'textinput'"
                :id="field.key"
                type="text"
                v-model="localValue as string"
                :placeholder="field.placeholder"
                :maxlength="field.maxLength"
                :disabled="disabled"
                class="field-input"
                @blur="handleBlur"
                @input="handleInput"
            />

            <!-- 文本域 -->
            <q-input
                filled
                type="textarea"
                v-else-if="field.type === 'textarea'"
                :id="field.key"
                v-model="localValue as string"
                :placeholder="field.placeholder"
                :maxlength="field.maxLength"
                :disabled="disabled"
                class="field-textarea"
                :rows="textareaRows"
                @blur="handleBlur"
                @input="handleInput"
            />

            <!-- 数字输入框 -->
            <q-input
                v-else-if="field.type === 'number'"
                :id="field.key"
                type="number"
                v-model.number="localValue as number"
                :placeholder="field.placeholder"
                :min="field.min"
                :max="field.max"
                :step="field.step"
                :disabled="disabled"
                class="field-input"
                @blur="handleBlur"
                @input="handleInput"
            />

            <!-- 下拉选择框 -->
            <q-select
                outlined
                v-else-if="field.type === 'select'"
                :id="field.key"
                v-model="localValue"
                :disabled="disabled"
                class="field-select"
                @update:model-value="handleInput"
            >
                <q-item
                    v-if="!field.required"
                    clickable
                    v-close-popup
                    @click="((localValue = ''), handleInput())"
                >
                    <q-item-section>{{
                        field.placeholder || '请选择'
                    }}</q-item-section>
                </q-item>
                <q-item
                    v-for="option in field.options"
                    :key="option.value"
                    clickable
                    v-close-popup
                    @click="((localValue = option.value), handleInput())"
                >
                    >
                    <q-item-section>{{ option.label }}</q-item-section>
                </q-item>
            </q-select>

            <!-- 布尔值开关 -->
            <div v-else-if="field.type === 'boolean'" class="boolean-field">
                <q-toggle
                    :id="field.key"
                    v-model="localValue as boolean"
                    :disabled="disabled"
                    @update:model-value="handleInput"
                />
                <span class="boolean-label">
                    {{ localValue ? '启用' : '禁用' }}
                </span>
            </div>

            <!-- 文件上传 -->
            <div v-else-if="field.type === 'file'" class="file-field">
                <input
                    type="file"
                    :id="field.key"
                    :accept="field.accept"
                    :multiple="field.multiple"
                    :disabled="disabled"
                    @change="handleFileChange"
                    class="file-input"
                />
                <label :for="field.key" class="file-label">
                    <span class="file-icon">📁</span>
                    <span class="file-text">
                        {{ getFileText() }}
                    </span>
                    <span class="file-button">选择文件</span>
                </label>
                <div v-if="localValue" class="file-preview">
                    <button
                        type="button"
                        class="file-remove"
                        @click="removeFile"
                    >
                        ✕
                    </button>
                </div>
            </div>

            <!-- 数组类型（简化版） -->
            <div v-else-if="field.type === 'array'" class="array-field">
                <div
                    class="array-items"
                    v-if="Array.isArray(localValue) && localValue.length > 0"
                >
                    <div
                        v-for="(item, index) in localValue"
                        :key="index"
                        class="array-item"
                    >
                        <span>{{ item }}</span>
                        <button
                            type="button"
                            class="array-remove"
                            @click="removeArrayItem(index)"
                        >
                            ✕
                        </button>
                    </div>
                </div>
                <div class="array-input">
                    <input
                        type="text"
                        v-model="arrayInputValue"
                        :placeholder="field.placeholder || '添加新项'"
                        class="array-text-input"
                        @keyup.enter="addArrayItem"
                    />
                    <button
                        type="button"
                        class="array-add"
                        @click="addArrayItem"
                    >
                        添加
                    </button>
                </div>
            </div>

            <!-- 不支持的类型 -->
            <div v-else>不支持的类型: {{ field }}</div>

            <!-- 字符计数 -->
            <div
                v-if="field.maxLength && typeof localValue === 'string'"
                class="char-count"
            >
                {{ localValue.length }} / {{ field.maxLength }}
            </div>
        </div>

        <!-- 字段描述/提示 -->
        <div v-if="field.placeholder && !error" class="field-hint">
            {{ field.placeholder }}
        </div>

        <!-- 错误信息 -->
        <div v-if="error" class="field-error">
            <span class="error-icon">⚠️</span>
            {{ error }}
        </div>
    </div>
</template>

<style lang="sass" scoped></style>
