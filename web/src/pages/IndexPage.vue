<!--
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2025-11-26 10:24:58
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-07 15:31:11
 * @FilePath: /web/src/pages/IndexPage.vue
 * @Description: 用户登陆后的主页
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
-->
<script setup lang="ts">
import { ref } from 'vue'
import type { Todo, Meta } from 'components/models'

const todos = ref<Todo[]>([
    {
        id: 1,
        content: 'ct1',
    },
    {
        id: 2,
        content: 'ct2',
    },
    {
        id: 3,
        content: 'ct3',
    },
    {
        id: 4,
        content: 'ct4',
    },
    {
        id: 5,
        content: 'ct5',
    },
])
</script>
<template>
    <q-page class="row justify-evenly">
        <div></div>
    </q-page>
</template>
