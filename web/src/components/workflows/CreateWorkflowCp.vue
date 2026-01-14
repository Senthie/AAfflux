<!--
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-09 16:54:11
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-14 11:58:10
 * @FilePath: /web/src/components/workflows/CreateWorkflowCp.vue
 * @Description: 创建工作流
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
-->
<script setup lang="ts">
import { v1_create_workflow } from 'src/apis/workflow_api'
import type { IWorkflowCreateRequest } from 'src/interfaces/IWorkflows'
import { useWorkspaceStore } from 'src/stores/workspace-store'
import { reactive, ref } from 'vue'

const workspace_store = useWorkspaceStore()
const dialog_visible = ref(false)

const create_workflow_data = reactive<IWorkflowCreateRequest>({
    name: '',
    description: '',
    input_schema: {},
    output_schema: {},
})

const handle_create_workflow = async () => {
    await v1_create_workflow(create_workflow_data, workspace_store.workspace.id)
    // TOOD 全局刷新不友好，后期需要改为局部刷新
    location.reload()
}
</script>
<template>
    <div>
        <q-btn
            color="white"
            text-color="black"
            label="Create Workflow"
            @click="dialog_visible = true"
        />
    </div>
    <q-dialog v-model="dialog_visible">
        <q-card>
            <q-card-section>
                <div class="text-h6">Create Workflow</div>
            </q-card-section>

            <q-card-section class="q-pt-none">
                <q-input
                    filled
                    v-model="create_workflow_data.name"
                    label="name"
                />
                <q-input
                    filled
                    v-model="create_workflow_data.description"
                    label="desc"
                />
            </q-card-section>

            <q-card-actions align="right">
                <q-btn
                    flat
                    label="OK"
                    color="primary"
                    v-close-popup
                    v-on:click="handle_create_workflow"
                />
            </q-card-actions>
        </q-card>
    </q-dialog>
</template>

<style lang="scss" scoped></style>
