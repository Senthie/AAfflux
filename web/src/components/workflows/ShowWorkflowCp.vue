<!--
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-12 11:49:16
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-20 16:40:28
 * @FilePath: /web/src/components/workflows/ShowWorkflowCp.vue
 * @Description: 展示当前的工作空间的工作流
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
-->
<script setup lang="ts">
import { v1_delete_workflow } from 'src/apis/workflow_api'
import { useWorkspaceStore } from 'src/stores/workspace-store'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
const router = useRouter()
const workspace_store = useWorkspaceStore()

const delete_workflow_id = ref('')
const delete_confirm = ref(false)
const oepe_delete_dialog = (workflow_id: string) => {
    delete_workflow_id.value = workflow_id
    delete_confirm.value = true
}
const handle_delete_workflow = async () => {
    const res = await v1_delete_workflow(delete_workflow_id.value)
    if (res.code) {
        // TOOD 全局刷新不友好，后期需要改为局部刷新
        location.reload()
    }
}

const to_wordflow = (id: string) => {
    void router.push(`/workflow/${id}`)
}
</script>
<template>
    <div>
        <q-dialog v-model="delete_confirm" persistent>
            <q-card>
                <q-card-section class="row items-center">
                    <span class="q-ml-sm">你即将删除该工作流，请确认</span>
                </q-card-section>

                <q-card-actions align="right">
                    <q-btn flat label="Cancel" color="primary" v-close-popup />
                    <q-btn
                        flat
                        label="确认"
                        color="negative"
                        v-close-popup
                        @click="handle_delete_workflow"
                    />
                </q-card-actions>
            </q-card>
        </q-dialog>
    </div>
    <div>
        <q-list bordered separator>
            <template
                v-for="workflows in workspace_store.workflows"
                :key="workflows.id"
            >
                <q-item>
                    <q-item-section dark="null">
                        <div class="row">
                            <div class="col-1">
                                {{ workflows.name }}
                            </div>
                            <div class="col-2">
                                {{ workflows.description }}
                            </div>

                            <div class="col-2">
                                <q-btn
                                    color="primary"
                                    label="查看"
                                    @click="to_wordflow(workflows.id)"
                                />
                                <q-btn
                                    color="negative"
                                    label="删除"
                                    @click="oepe_delete_dialog(workflows.id)"
                                />
                            </div>
                        </div>
                    </q-item-section>
                </q-item>
            </template>
        </q-list>
    </div>
</template>
<style lang="scss" scoped></style>
