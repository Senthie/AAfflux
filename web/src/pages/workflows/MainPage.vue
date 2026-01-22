<!--
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-14 15:07:09
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-22 17:31:48
 * @FilePath: /web/src/pages/workflows/MainPage.vue
 * @Description: 工作流的主要页面
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
-->
<script setup lang="ts">
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import type { IUI, IPointerEvent } from 'leafer-ui'
import { App } from 'leafer-ui'
import { DotMatrix } from 'leafer-x-dotwuxian'
// import { useWindowSize } from '@vueuse/core'
// const { width, height } = useWindowSize()
import { Connector } from 'leafer-connector'
import ContextMenu from '@imengyu/vue3-context-menu'
import '@leafer-in/editor' // 导入图形编辑器插件
import '@leafer-in/viewport' // 导入视口插件 (可选)
import '@leafer-in/find' // 导入查找元素插件
import type { IPageReq, IPageRes } from 'src/interfaces/Ipage'
import type { PluginConfigRecord, PluginResponse } from 'src/interfaces/IPlugin'
import { v1_plugins_list } from 'src/apis/plugin_api'
import { NodeRect } from 'src/utils/nodeReact'
import { Platform } from 'leafer-ui'
import { useRoute, useRouter } from 'vue-router'
import { Notify } from 'quasar'
import { v1_get_workflow } from 'src/apis/workflow_api'
import { useWorkflowStore } from 'src/stores/workflow-store'
import type { INodeRes } from 'src/interfaces/IWorkflows'
import { PluginUtil } from 'src/utils/PluginUtil'

const workflow_store = useWorkflowStore()

const route = useRoute()
const router = useRouter()
// 定义接口
interface NodeListeners {
    setupConnectionListeners: (node: NodeRect) => void
    setupNodeDragListeners: (node: NodeRect) => void
}

// 允许跨域图片渲染，但不支持导出画板内容（浏览器的限制）。
Platform.image.crossOrigin = 'anonymous'

let app: App = null as unknown as App
const add_node_dialog_visiable = ref(false)
const page_res = ref<IPageRes<PluginResponse>>({
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

// 记录右键页面时候的xy的位置
const click_xy = reactive({
    x: 0,
    y: 0,
})
const onContextMenu = (e: MouseEvent) => {
    // 阻止浏览器默认菜单
    e.preventDefault()
    click_xy.x = e.x
    click_xy.y = e.y

    // 显示自定义右键菜单
    ContextMenu.showContextMenu({
        x: e.x,
        y: e.y,
        items: [
            {
                label: '添加节点',
                onClick: () => {
                    add_node_dialog_visiable.value =
                        !add_node_dialog_visiable.value
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

const get_workflow_by_workflow_id = async (workflow_id: string) => {
    const res = await v1_get_workflow(workflow_id)
    if (res.code === 200) {
        workflow_store.set_workflow(res.data)
    } else {
        void router.push('/main')
    }
}
onMounted(async () => {
    // 获取传参
    const workflowId = Array.isArray(route.params.id)
        ? route.params.id[0]
        : route.params.id
    if (workflowId) {
        await get_workflow_by_workflow_id(workflowId)
    } else {
        Notify.create({
            type: 'negative',
            message: '无法获取工作流',
        })
        void router.push('/main')
    }

    app = new App({
        view: window,
        editor: {},
        wheel: { preventDefault: true }, // 阻止浏览器默认滚动页面事件
        touch: { preventDefault: true }, // 阻止移动端默认触摸屏滑动页面事件
        pointer: { preventDefaultMenu: true }, // 阻止浏览器默认菜单事件，改为 true
    })

    // 连线状态管理
    let isDraggingConnection = false
    let draggingNode: NodeRect | null = null

    // 监听 leafer-ui 的右键事件
    app.on('pointer.menu', (e: { origin: MouseEvent }) => {
        if (app?.editor.single) {
            const { element } = app.editor
            onNodeMenu(e.origin, element as IUI)
        } else {
            onContextMenu(e.origin)
        }
    })

    // 全局鼠标事件处理，用于连线功能
    app.on('pointer.move', (e: IPointerEvent) => {
        if (isDraggingConnection && draggingNode) {
            // 禁用编辑器选择功能
            if (app.editor) {
                app.editor.cancel()
            }
            draggingNode.updateDragLineExternal(e)
        }
    })

    app.on('pointer.up', (e: IPointerEvent) => {
        if (isDraggingConnection && draggingNode) {
            draggingNode.endDragConnectionExternal(e)
            isDraggingConnection = false
            draggingNode = null
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

    // 将设置函数暴露给 createNodeRect 使用
    ;(window as { setupNodeListeners?: NodeListeners }).setupNodeListeners = {
        setupConnectionListeners: (node: NodeRect) => {
            node.on('drag.connection.start', () => {
                console.log('连线拖拽开始')
                isDraggingConnection = true
                draggingNode = node

                // 禁用编辑器的选择功能
                if (app.editor) {
                    app.editor.cancel()
                }
            })

            node.on('connection.created', (data: unknown) => {
                console.log('新连接已创建:', data)
                // 这里可以添加连接创建后的处理逻辑
            })
        },
        setupNodeDragListeners: (node: NodeRect) => {
            node.on('drag.end', () => {
                // 拖动结束时更新所有连接线
                const allConnectors = app.tree.children.filter(
                    (child) => child instanceof Connector
                )
                allConnectors.forEach((connector) => {
                    if (connector.update) {
                        connector.update()
                    }
                })
            })
        },
    }

    // 获取插件
    await handle_get_plugins()
})

const createNodeRect = (plugin: PluginResponse) => {
    // TOOD 这样创建 rect 并不严谨 应该通过 NODE表
    // 继续去查询节点的名字是否存在重复
    const ui = {
        title: `${plugin.name}`,
        icon: plugin.icon,
        x: click_xy.x,
        y: click_xy.y,
        editable: true,
    }
    const config: PluginConfigRecord =
        PluginUtil.createPluginConfigRecord(plugin)

    const node: INodeRes = {
        id: '',
        plugin_id: '',
        workflow_id: '',
        type: '',
        config: config,
        ui: ui,
        is_deleted: false,
    }
    const node_ui = new NodeRect(ui)

    // 使用全局设置函数为新节点添加监听器
    const setupFunctions = (window as { setupNodeListeners?: NodeListeners })
        .setupNodeListeners
    if (setupFunctions) {
        setupFunctions.setupNodeDragListeners(node_ui)
        setupFunctions.setupConnectionListeners(node_ui)
    }

    app.tree.add(node_ui)
    workflow_store.add_node(node)
    console.log(workflow_store.workflow)
    add_node_dialog_visiable.value = false
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
            <q-dialog v-model="add_node_dialog_visiable">
                <q-card style="min-width: 350px">
                    <q-card-section>
                        <div class="text-h6">创建节点</div>
                    </q-card-section>

                    <q-card-section class="q-pt-none">
                        <template
                            v-for="(plugin, index) in page_res.records"
                            :key="index"
                        >
                            <q-btn
                                :label="plugin.name"
                                color="primary"
                                @click="createNodeRect(plugin)"
                            />
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
