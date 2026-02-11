<!--
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-27 15:00:00
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-02-11 11:24:18
 * @FilePath: /web/src/components/workflows/MouseCoordinateDisplay.vue
 * @Description: 鼠标坐标显示组件
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
-->
<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'

// 定义 props
interface Props {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    app?: any
}

const props = withDefaults(defineProps<Props>(), {
    app: null,
})

// 鼠标坐标状态
const canvasX = ref(0)
const canvasY = ref(0)

// 鼠标移动事件处理函数
const handleMouseMove = (event: MouseEvent) => {
    // 如果有 app 实例，计算画布坐标
    if (props.app && props.app.leafer) {
        try {
            const worldPoint = props.app.leafer.getPagePoint({
                x: event.clientX,
                y: event.clientY,
            })
            canvasX.value = Math.round(worldPoint.x)
            canvasY.value = Math.round(worldPoint.y)
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (error) {
            // 如果转换失败，使用屏幕坐标
            canvasX.value = event.clientX
            canvasY.value = event.clientY
        }
    } else {
        // 没有 app 实例时，使用屏幕坐标
        canvasX.value = event.clientX
        canvasY.value = event.clientY
    }
}

// 组件挂载时添加事件监听
onMounted(() => {
    document.addEventListener('mousemove', handleMouseMove)
})

// 组件卸载时移除事件监听
onBeforeUnmount(() => {
    document.removeEventListener('mousemove', handleMouseMove)
})
</script>

<template>
    <div class="mouse-coordinate-display">
        X: {{ canvasX }} Y: {{ canvasY }}
    </div>
</template>

<style lang="sass" scoped>
.mouse-coordinate-display
  position: fixed
  top: 20px
  right: 20px
  background: transparent
  color: #333
  font-family: 'Courier New', monospace
  font-size: 14px
  font-weight: 600
  z-index: 1000
  pointer-events: none
  text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.8)
</style>
