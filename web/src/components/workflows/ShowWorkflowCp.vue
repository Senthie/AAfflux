<!--
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-12 11:49:16
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-13 16:57:36
 * @FilePath: /web/src/components/workflows/ShowWorkflowCp.vue
 * @Description: 展示当前的工作空间的工作流
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
-->
<script setup lang="ts">
import { useWorkspaceStore } from 'src/stores/workspace-store'
const workspace_store = useWorkspaceStore()
</script>
<template>
    <div>
        <q-list bordered separator>
            <template
                v-for="workflows in workspace_store.workflows"
                :key="workflows.id"
            >
                <q-item clickable v-ripple>
                    <q-item-section dark="null">
                        <div class="row">
                            <div class="col-1">
                                {{ workflows.name }}
                            </div>
                            <div class="col-2">
                                {{ workflows.description }}
                            </div>

                            <div class="col-2">
                                <q-btn color="primary" label="编辑" />
                                <q-btn color="negative" label="删除" />
                            </div>
                        </div>
                    </q-item-section>
                </q-item>
            </template>
        </q-list>
    </div>
</template>
<style lang="scss" scoped></style>
