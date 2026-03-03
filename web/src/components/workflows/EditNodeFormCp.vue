<script lang="ts" setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import FormFieldCp from './FormFieldCp.vue'
import emitter from 'src/boot/mitt'
import { useWorkflowStore } from 'src/stores/workflow-store'
import type { INode } from 'src/interfaces/IWorkflows'
import type { IPluginBase } from 'src/interfaces/IPlugin'
import { v1_plugins_id } from 'src/apis/plugin_api'
import EditableTitleCp from './EditableTitleCp.vue'
import { debounce } from 'src/utils/debounce'
import { v1_file_upload } from 'src/apis/file_api'

const workflow_store = useWorkflowStore()
const node_id = ref<string>('')
const dialog_visiable = ref<boolean>(false)
const errors = ref<Record<string, string>>({})
const isSaving = ref<boolean>(false) // 保存状态指示器

const node = ref<INode>({
    id: '',
    plugin_id: '',
    type: '',
    config: {},
    ui: {},
})

const plugin = ref<IPluginBase>({
    name: '',
    displya_name: '',
    desc: '',
    version: '',
    author: '',
    icon: '',
    category: '',
    plugin_type: '',
    manifest: {
        internal: [],
        parameters: [],
    },
    source_url: '',
    documentation_url: '',
})

const handleOpenDialog = async (data: {
    visiable: boolean
    node_id: string
}) => {
    dialog_visiable.value = true
    node_id.value = data.node_id
    const _node = workflow_store.get_node_by_id(data.node_id)
    console.log('_node:', _node)
    if (_node) {
        node.value = _node
        const res = await v1_plugins_id(_node.plugin_id)
        plugin.value = res.data
    }
}
// 处理字段验证
const handleFieldValidation = (
    key: string,
    isValid: boolean,
    error?: string
) => {
    if (isValid) {
        delete errors.value[key]
    } else if (error) {
        errors.value[key] = error
    }
}

// 处理字段值变化，自动同步到store - 添加防抖
const debouncedFieldChange = debounce(async (key: string, value: unknown) => {
    // TODO: 只通过file_data的名字去检测是否上传文件，不方便扩展
    if (key === 'file_data') {
        const res = await v1_file_upload(
            workflow_store.workflow.workspace_id,
            value as File
        )
        if (res.code === 200) {
            key = 'file_id'
            value = res.data.file_id
        }
    }
    // 更新本地node配置
    ;(node.value.config as Record<string, unknown>)[key] = value

    // 同步到workflow store
    workflow_store.update_node_config(node.value.id, node.value.config)
}, 800) // 800ms 防抖延迟，比FormFieldCp稍长一些

const handleFieldChange = (key: string, value: unknown) => {
    // 立即更新本地显示
    ;(node.value.config as Record<string, unknown>)[key] = value

    // 防抖更新到store
    debouncedFieldChange(key, value)
}

// 设置 di
onMounted(() => {
    const dialogHandler = async (data: {
        visiable: boolean
        node_id: string
    }) => {
        try {
            await handleOpenDialog(data)
        } catch (err) {
            console.error(err)
        }
    }

    // 监听字段值更新事件
    const fieldUpdateHandler = (data: {
        fieldKey: string
        value: unknown
        nodeId?: string
    }) => {
        // 只处理当前节点的字段更新
        if (data.nodeId === node.value.id || !data.nodeId) {
            handleFieldChange(data.fieldKey, data.value)
        }
    }

    // 监听字段验证事件
    const fieldValidateHandler = (data: {
        fieldKey: string
        isValid: boolean
        error?: string
        nodeId?: string
    }) => {
        // 只处理当前节点的字段验证
        if (data.nodeId === node.value.id || !data.nodeId) {
            handleFieldValidation(data.fieldKey, data.isValid, data.error)
        }
    }

    // 注册事件监听器
    // eslint-disable-next-line @typescript-eslint/no-misused-promises
    emitter.on('noderect:edit.dialog.open', dialogHandler)
    emitter.on('formfield:value.update', fieldUpdateHandler)
    emitter.on('formfield:validate', fieldValidateHandler)
})

onUnmounted(() => {
    // 移除所有事件监听
    emitter.off('noderect:edit.dialog.open')
    emitter.off('formfield:value.update')
    emitter.off('formfield:validate')
})

// 防抖的节点更新函数
const debouncedNodeUpdate = debounce(() => {
    node.value.ui.title = node.value.config.title
    workflow_store.update()
    emitter.emit('noderect:edit.ui.update', {
        node_id: node.value.id,
        ui_config: node.value.ui,
    })
    // 更新 node rect
}, 300) // 1秒防抖延迟

// 处理对话框关闭
const handleDialogClose = async () => {
    try {
        isSaving.value = true // 显示保存状态

        // 立即执行所有待处理的防抖更新
        // 1. 立即执行字段变化的防抖更新
        if (debouncedFieldChange.flush) {
            debouncedFieldChange.flush()
        }

        // 2. 立即执行节点更新的防抖更新
        if (debouncedNodeUpdate.flush) {
            debouncedNodeUpdate.flush()
        }

        // 3. 确保 workflow store 立即更新
        workflow_store.updateImmediate()

        // 4. 等待一小段时间确保所有更新完成
        await new Promise((resolve) => setTimeout(resolve, 200))

        // 5. 关闭对话框
        dialog_visiable.value = false
    } catch (error) {
        console.error('Error closing dialog:', error)
        // 即使出错也要关闭对话框
        dialog_visiable.value = false
    } finally {
        isSaving.value = false // 隐藏保存状态
    }
}

watch(
    node,
    () => {
        debouncedNodeUpdate()
    },
    { deep: true }
)
</script>
<template>
    <div>
        <q-dialog v-model="dialog_visiable" persistent>
            <q-card style="min-width: 350px">
                <q-card-section>
                    <div class="row items-center justify-between">
                        <div class="col">
                            <EditableTitleCp
                                class="text-h4"
                                v-model="node.config.title as string"
                            >
                            </EditableTitleCp>
                            <EditableTitleCp
                                v-model="node.config.desc as string"
                            >
                            </EditableTitleCp>
                        </div>
                        <div class="col-auto">
                            <q-btn
                                icon="close"
                                flat
                                round
                                dense
                                v-close-popup
                                @click="handleDialogClose"
                            />
                        </div>
                    </div>
                </q-card-section>

                <q-card-section class="q-pt-none">
                    <!-- 参数配置部分 -->
                    <div>
                        <h6 style="margin-top: 1%; margin-bottom: 1%">
                            <span>参数配置</span>
                        </h6>

                        <div class="fields-grid">
                            <template
                                v-for="field in plugin.manifest.parameters"
                                :key="field.key"
                            >
                                <FormFieldCp
                                    :field="field"
                                    v-model="node.config[field.key]"
                                    :error="errors[field.key] || undefined"
                                    :node-id="node.id"
                                />
                            </template>
                        </div>
                    </div>
                </q-card-section>

                <q-card-actions align="right" class="text-primary">
                    <q-btn
                        flat
                        label="完成"
                        color="primary"
                        :loading="isSaving"
                        :disable="isSaving"
                        @click="handleDialogClose"
                    />
                </q-card-actions>
            </q-card>
        </q-dialog>
    </div>
</template>
<style lang="sass" scoped></style>
