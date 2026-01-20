<!--
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2025-11-26 10:24:58
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-20 17:01:31
 * @FilePath: /web/src/pages/IndexPage.vue
 * @Description: 用户登陆后的主页，项目首页
 * // TOOD 从其他页面返回后，页面无反应
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
-->
<script setup lang="ts">
import { onMounted } from 'vue'
import CreateWorkflowCp from 'src/components/workflows/CreateWorkflowCp.vue'
import ShowWorkflowCp from 'src/components/workflows/ShowWorkflowCp.vue'
import { useWorkspaceStore } from 'src/stores/workspace-store'
const workspace_store = useWorkspaceStore()

onMounted(async () => {
    await workspace_store.handle_get_workspaces()
})
</script>
<template>
    <q-page class="row justify-evenly">
        <div class="row">
            <div class="col-12">
                <div>{{ workspace_store.workspace }}</div>
                <div>
                    <CreateWorkflowCp />
                </div>
            </div>
            <div class="col-12">
                <div><ShowWorkflowCp /></div>
            </div>
        </div>
    </q-page>
</template>
