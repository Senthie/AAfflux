<!--
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-14 15:07:09
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-19 17:02:53
 * @FilePath: /web/src/pages/workflows/MainPage.vue
 * @Description:
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
-->
<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import type { IUI } from 'leafer-ui'
import { App, Rect } from 'leafer-ui'
import { DotMatrix } from 'leafer-x-dotwuxian'
// import { useWindowSize } from '@vueuse/core'
// const { width, height } = useWindowSize()
import { Connector } from 'leafer-connector'
import ContextMenu from '@imengyu/vue3-context-menu'
import '@leafer-in/editor' // 导入图形编辑器插件
import '@leafer-in/viewport' // 导入视口插件 (可选)
import '@leafer-in/find' // 导入查找元素插件
import type { IPageReq, IPageRes } from 'src/interfaces/Ipage'
import type { IPluginBase } from 'src/interfaces/IPlugin'
import { v1_plugins_list } from 'src/apis/plugin_api'
import { NodeRect } from 'src/utils/nodeReact'

let app: App = null as unknown as App
const add_node_visiable = ref(false)
const page_res = ref<IPageRes<IPluginBase>>({
    total: 0,
    size: 10,
    current: 1,
    orders: [],
    maxLimit: 100,
    records: [],
})

const handle_get_plugins = async () => {
    const page_req: IPageReq = {
        total: page_res.value.total,
        size: page_res.value.size,
        current: page_res.value.current,
        orders: [],
        maxLimit: 0,
    }
    const res = await v1_plugins_list(page_req)
    page_res.value.records = res.data.records
}

const onContextMenu = (e: MouseEvent) => {
    // 阻止浏览器默认菜单
    e.preventDefault()

    // 显示自定义右键菜单
    ContextMenu.showContextMenu({
        x: e.x,
        y: e.y,
        items: [
            {
                label: '添加节点',
                onClick: () => {
                    add_node_visiable.value = !add_node_visiable.value
                    // createRect(e.x, e.y)
                },
            },
            {
                label: '视图',
                children: [
                    {
                        label: '适应画布',
                        onClick: () => {
                            console.log('适应画布')
                        },
                    },
                    {
                        label: '重置缩放',
                        onClick: () => {
                            console.log('重置缩放')
                        },
                    },
                ],
            },
        ],
    })
}

const onNodeMenu = (e: MouseEvent, node: IUI) => {
    // 阻止浏览器默认菜单
    e.preventDefault()

    // 显示自定义右键菜单
    ContextMenu.showContextMenu({
        x: e.x,
        y: e.y,
        items: [
            {
                label: '复制',
                onClick: () => {
                    console.log('复制')
                },
            },
            {
                label: '粘贴',
                onClick: () => {
                    console.log('粘贴')
                },
            },
            {
                label: '删除',
                onClick: () => {
                    node.remove()
                },
            },
        ],
    })
}
onMounted(() => {
    app = new App({
        view: window,
        editor: {},
        wheel: { preventDefault: true }, // 阻止浏览器默认滚动页面事件
        touch: { preventDefault: true }, // 阻止移动端默认触摸屏滑动页面事件
        pointer: { preventDefaultMenu: true }, // 阻止浏览器默认菜单事件，改为 true
    })

    // 监听 leafer-ui 的右键事件
    app.on('pointer.menu', (e: { origin: MouseEvent }) => {
        if (app?.editor.single) {
            const { element } = app.editor
            onNodeMenu(e.origin, element as IUI)
        } else {
            onContextMenu(e.origin)
        }
    })
    const dot = new DotMatrix(app, {
        dotColor: '#D2D4D7',
        gridGap: 45,
        gridType: 'dots', // 'dots' | 'lines'
        maxSize: 10,
        minSize: 0.1,
    })
    dot.enableDotMatrix(true)
    const a = new NodeRect({
        title: 'a',
        x: 100,
        y: 100,
        editable: true,
    })
    const b = new NodeRect({
        title: 'b',
        x: 520,
        y: 280,
        editable: true,
    })
    const c = new NodeRect({
        title: 'c',
        icon: 'https://n8niostorageaccount.blob.core.windows.net/n8nio-strapi-blobs-prod/assets/Docu_Seal_b9ab4f1bfb.svg',
        x: 520,
        y: 580,
        editable: true,
    })
    const edge = new Connector(app, { from: a, to: b, stroke: '#32cd79' })
    const edge2 = new Connector(app, { from: c, to: b, stroke: '#32cd79' })
    app.tree.add([a, b, c, edge, edge2])

    // 获取插件
    void handle_get_plugins()
})

const createRect = (x: number, y: number) => {
    let num = 0
    // TOOD 这样创建 rect 并不严谨 应该通过 NODE表
    // 继续去查询节点的名字是否存在重复
    const rect = new Rect({
        name: `rect${num}`,
        x: x,
        y: y,
        editable: true,
        width: 200,
        height: 100,
        fill: '#1E90FF',
        draggable: true,
        cornerRadius: 20,
    })
    do {
        num += 1
        rect.name = `rect${num}`
    } while (num <= 3)

    app.tree.add(rect)
}

onBeforeUnmount(() => {
    // leafer-editor 不同版本销毁方法名可能不同，这里尽量兜底
    app?.destroy?.()
    app = null as unknown as App
})
</script>

<template>
    <div>
        <template>
            <q-dialog v-model="add_node_visiable">
                <q-card style="min-width: 350px">
                    <q-card-section>
                        <div class="text-h6">创建节点</div>
                    </q-card-section>

                    <q-card-section class="q-pt-none">
                        <template
                            v-for="(plugin, index) in page_res.records"
                            :key="index"
                        >
                            <q-btn :label="plugin.name" color="primary" />
                        </template>
                    </q-card-section>

                    <q-card-actions align="right" class="text-primary">
                    </q-card-actions>
                </q-card>
            </q-dialog>
        </template>
    </div>
</template>

<style lang="sass" scoped></style>
