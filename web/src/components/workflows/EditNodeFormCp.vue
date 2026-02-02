<script lang="ts" setup>
import { onMounted, onUnmounted, ref } from 'vue'
import FormFieldCp from './FormFieldCp.vue'
import emitter from 'src/boot/mitt'
import { useWorkflowStore } from 'src/stores/workflow-store'
import type { INode } from 'src/interfaces/IWorkflows'
import type { IPluginBase } from 'src/interfaces/IPlugin'
import { v1_plugins_id } from 'src/apis/plugin_api'
import EditableTitleCp from './EditableTitleCp.vue'
const workflow_store = useWorkflowStore()
const node_id = ref<string>('')
const dialog_visiable = ref<boolean>(false)
const errors = ref<Record<string, string>>({})

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

// 处理字段值变化，自动同步到store
const handleFieldChange = (key: string, value: unknown) => {
    // 更新本地node配置
    ;(node.value.config as Record<string, unknown>)[key] = value

    // 同步到workflow store
    workflow_store.update_node_config(node.value.id, node.value.config)
}

// 设置di\

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
        console.log('fieldUpdateHandler:', data)
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
</script>
<template>
    <div>
        <q-dialog v-model="dialog_visiable">
            <q-card style="min-width: 350px">
                <q-card-section
                    ><EditableTitleCp
                        v-model="node.config.title as string"
                    ></EditableTitleCp>
                </q-card-section>

                <q-card-section class="q-pt-none">
                    <!-- 参数配置部分 -->
                    <div>
                        <h5>
                            <span>参数配置</span>
                        </h5>

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
                </q-card-actions>
            </q-card>
        </q-dialog>
    </div>
</template>
<style lang="sass" scoped></style>
