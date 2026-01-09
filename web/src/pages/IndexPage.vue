<!--
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2025-11-26 10:24:58
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-09 15:02:56
 * @FilePath: /web/src/pages/IndexPage.vue
 * @Description: 用户登陆后的主页
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
-->
<script setup lang="ts">
import { v1_get_workspaces } from 'src/apis/workscpace_api'
import type { IWorkspaceResponse } from 'src/interfaces/IWorkspace'
import { onMounted, ref } from 'vue'

const workspaces = ref<Array<IWorkspaceResponse>>([])

const handle_get_workspaces = async () => {
    const res = await v1_get_workspaces()
    return res.data
}

onMounted(async () => {
    workspaces.value = await handle_get_workspaces()
})
</script>
<template>
    <q-page class="row justify-evenly">
        <div>{{ workspaces }}</div>
    </q-page>
</template>
