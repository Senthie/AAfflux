<template>
    <router-view />
</template>

<script setup lang="ts">
import 'src/utils/proxyData' // 重写 proxyData，全局只需引入一次
</script>
