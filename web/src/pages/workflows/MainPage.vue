<!--
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-14 15:07:09
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-15 11:37:05
 * @FilePath: /web/src/pages/workflows/MainPage.vue
 * @Description:
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
-->
<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import { App, Rect } from 'leafer-ui'
import { DotMatrix } from 'leafer-x-dotwuxian'
// import { useWindowSize } from '@vueuse/core'
// const { width, height } = useWindowSize()
import { Connector } from 'leafer-connector'

import '@leafer-in/editor' // 导入图形编辑器插件
import '@leafer-in/viewport' // 导入视口插件 (可选)

let app: App | null = null

onMounted(() => {
    app = new App({
        view: window,
        editor: {},
        wheel: { preventDefault: true }, // 阻止浏览器默认滚动页面事件
        touch: { preventDefault: true }, // 阻止移动端默认触摸屏滑动页面事件
        pointer: { preventDefaultMenu: false }, // 阻止浏览器默认菜单事件
    })
    const dot = new DotMatrix(app, {
        dotColor: '#D2D4D7',
        gridGap: 45,
        gridType: 'dots', // 'dots' | 'lines'
        maxSize: 10,
        minSize: 0.1,
    })
    dot.enableDotMatrix(true)
    const a = new Rect({
        x: 100,
        y: 100,
        width: 200,
        height: 160,
        fill: '#32cd79',
        draggable: true,
    })
    const b = new Rect({
        x: 520,
        y: 280,
        width: 220,
        height: 160,
        fill: '#3b82f6',
        draggable: true,
    })
    const c = new Rect({
        x: 520,
        y: 280,
        width: 220,
        height: 160,
        fill: '#	#1E90FF',
        draggable: true,
    })
    const edge = new Connector(app, { from: a, to: b, stroke: '#32cd79' })
    const edge2 = new Connector(app, { from: c, to: b, stroke: '#32cd79' })
    app.tree.add([a, b, c, edge, edge2])
})

onBeforeUnmount(() => {
    // leafer-editor 不同版本销毁方法名可能不同，这里尽量兜底
    app?.destroy?.()
    app = null
})
</script>

<template>
    <div ref="container"></div>
</template>

<style lang="sass" scoped></style>
