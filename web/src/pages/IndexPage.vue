<!--
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2025-11-26 10:24:58
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-12 11:36:58
 * @FilePath: /web/src/pages/IndexPage.vue
 * @Description: 用户登陆后的主页
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
-->
<script setup lang="ts">
import { onMounted } from 'vue'
import CreateWorkflowCp from 'src/components/workflows/CreateWorkflowCp.vue'
import { useWorkspaceStore } from 'src/stores/workspace-store'
const workspace_store = useWorkspaceStore()

onMounted(() => {
    void workspace_store.handle_get_workspaces()
})
</script>
<template>
    <q-page class="row justify-evenly">
        <div>{{ workspace_store.workspace }}</div>
        <div>
            <CreateWorkflowCp />
        </div>
    </q-page>
</template>
