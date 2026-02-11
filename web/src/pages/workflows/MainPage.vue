<!--
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-14 15:07:09
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-02-11 11:32:59
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
import type { INodeRectInputData } from 'src/utils/nodeReact'
import { NodeRect } from 'src/utils/nodeReact'
import { Platform } from 'leafer-ui'
import { useRoute, useRouter } from 'vue-router'
import { Notify } from 'quasar'
import { v1_get_workflow } from 'src/apis/workflow_api'
import { useWorkflowStore } from 'src/stores/workflow-store'
import type { INode } from 'src/interfaces/IWorkflows'
import { PluginUtil } from 'src/utils/PluginUtil'
import { v4 as uuid4 } from 'uuid'
import MouseCoordinateDisplay from 'src/components/workflows/MouseCoordinateDisplay.vue'
import EditNodeFormCp from 'src/components/workflows/EditNodeFormCp.vue'

import emitter from 'src/boot/mitt'
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

const app = ref<App | null>(null)
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
    try {
        const page_req: IPageReq = {
            total: page_res.value.total,
            size: page_res.value.size,
            current: page_res.value.current,
            orders: [],
            maxLimit: 0,
        }
        const res = await v1_plugins_list(page_req)
        page_res.value.records = res.data.records
    } catch (error) {
        console.error('Error fetching plugins:', error)
        Notify.create({
            type: 'negative',
            message: '获取插件列表失败',
        })
    }
}

// 记录右键页面时候的xy的位置
const click_xy = reactive({
    x: 0,
    y: 0,
})
const onContextMenu = (e: MouseEvent) => {
    try {
        // 阻止浏览器默认菜单
        e.preventDefault()
        if (app.value && app.value.leafer) {
            // 转换事件为 rect 坐标 = app.value.leafer.getPagePoint
            const worldPoint = app.value.leafer.getPagePoint({
                x: e.clientX,
                y: e.clientY,
            })
            click_xy.x = worldPoint.x
            click_xy.y = worldPoint.y
            console.log('worldPoint:', worldPoint)
        } else {
            click_xy.x = e.x
            click_xy.y = e.y
        }

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
    } catch (error) {
        console.error('Error in context menu:', error)
    }
}

const onConnectorMenu = (
    e: MouseEvent,
    connectorData: {
        connector: unknown
        from: NodeRect | null
        to: NodeRect | null
    }
) => {
    try {
        // 阻止浏览器默认菜单
        e.preventDefault()

        // 显示连线右键菜单
        ContextMenu.showContextMenu({
            x: e.x,
            y: e.y,
            items: [
                {
                    label: '删除连线',
                    onClick: () => {
                        if (
                            connectorData.connector &&
                            connectorData.from &&
                            connectorData.to
                        ) {
                            // 从画布中移除连线
                            const connector = connectorData.connector as {
                                remove: () => void
                            }
                            connector.remove()

                            // 从 store 中删除连接记录
                            const fromNodeId = connectorData.from.id
                            const toNodeId = connectorData.to.id

                            if (fromNodeId && toNodeId) {
                                workflow_store.del_connection_by_nodes(
                                    fromNodeId,
                                    toNodeId
                                )

                                Notify.create({
                                    type: 'positive',
                                    message: `连线已删除: ${fromNodeId} -> ${toNodeId}`,
                                })
                            }
                        }
                    },
                },
            ],
        })
    } catch (error) {
        console.error('Error in connector menu:', error)
    }
}

const onNodeMenu = (e: MouseEvent, node: IUI) => {
    try {
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
                        console.log(node)
                        if (node && typeof node.remove === 'function') {
                            workflow_store.del_node_by_id(node.id as string)
                            node.remove()
                        }
                    },
                },
            ],
        })
    } catch (error) {
        console.error('Error in node menu:', error)
    }
}

const get_workflow_by_workflow_id = async (workflow_id: string) => {
    try {
        console.log('workflow_store:', workflow_store)
        console.log('workflow_store.set_workflow:', workflow_store.set_workflow)

        const res = await v1_get_workflow(workflow_id)
        if (res.code === 200) {
            if (typeof workflow_store.set_workflow === 'function') {
                workflow_store.set_workflow(res.data)
            } else {
                console.error(
                    'set_workflow is not a function:',
                    typeof workflow_store.set_workflow
                )
                throw new Error('Store not properly initialized')
            }
        } else {
            void router.push('/main')
        }
    } catch (error) {
        console.error('Error fetching workflow:', error)
        Notify.create({
            type: 'negative',
            message: '获取工作流失败',
        })
        void router.push('/main')
    }
}

// 连线状态管理
const isDraggingConnection = ref(false)
const draggingNode = ref<NodeRect>(null as unknown as NodeRect)
const create_app = () => {
    //TOOD 当 view设置为window的时候，后退的页面会失去所有点击事件
    app.value = new App({
        view: window,
        editor: {},
        wheel: { preventDefault: true }, // 阻止浏览器默认滚动页面事件
        touch: { preventDefault: true }, // 阻止移动端默认触摸屏滑动页面事件
        pointer: { preventDefaultMenu: true }, // 阻止浏览器默认菜单事件，改为 true
    })
    //  点阵图
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const dot = new DotMatrix(app.value as any, {
        dotColor: '#D2D4D7',
        gridGap: 45,
        gridType: 'dots', // 'dots' | 'lines'
        maxSize: 10,
        minSize: 0.1,
    })
    dot.enableDotMatrix(true)
    // 监听 leafer-ui 的右键事件
    app.value.on('pointer.menu', (e: { origin: MouseEvent }) => {
        try {
            if (app.value?.editor.single) {
                const { element } = app.value.editor
                onNodeMenu(e.origin, element as IUI)
            } else {
                onContextMenu(e.origin)
            }
        } catch (error) {
            console.error('Error in pointer.menu handler:', error)
        }
    })

    // 全局鼠标事件处理，用于连线功能
    app.value.on('pointer.move', (e: IPointerEvent) => {
        try {
            if (isDraggingConnection.value && draggingNode && app.value) {
                // 禁用编辑器选择功能
                if (app.value.editor) {
                    app.value.editor.cancel()
                }
                draggingNode.value.updateDragLineExternal(e)
            }
        } catch (error) {
            console.error('Error in pointer.move handler:', error)
        }
    })

    app.value.on('pointer.up', (e: IPointerEvent) => {
        try {
            if (isDraggingConnection.value && draggingNode) {
                draggingNode.value.endDragConnectionExternal(e)
                isDraggingConnection.value = false
                draggingNode.value = null as unknown as NodeRect
            }
        } catch (error) {
            console.error('Error in pointer.up handler:', error)
        }
    })
}

const load_ui = async () => {
    if (!app.value) return

    const nodes = workflow_store.get_node()
    const nodeMap = new Map<string, NodeRect>()

    // 首先创建所有节点
    for (const node of nodes) {
        const node_ui = new NodeRect({ id: node.id, ...node.ui })
        // 使用全局设置函数为新节点添加监听器
        const setupFunctions = (
            window as { setupNodeListeners?: NodeListeners }
        ).setupNodeListeners
        if (setupFunctions) {
            setupFunctions.setupNodeDragListeners(node_ui)
            setupFunctions.setupConnectionListeners(node_ui)
        }
        app.value.tree.add(node_ui)
        nodeMap.set(node.id, node_ui)
    }

    // 然后创建所有连线
    const connections = workflow_store.get_connections()
    for (const connection of connections) {
        const sourceNode = nodeMap.get(connection.source_node_id)
        const targetNode = nodeMap.get(connection.target_node_id)

        if (sourceNode && targetNode) {
            try {
                // 动态导入 Connector
                const { Connector } = await import('leafer-connector')

                // 创建连接线：从源节点的 out 连接到目标节点的 in
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                const connector = new Connector(app.value as any, {
                    from: sourceNode.out,
                    to: targetNode.in,
                    stroke: '#32cd79',
                })

                // 为连线添加右键菜单事件
                connector.on('pointer.menu', (e: IPointerEvent) => {
                    // 阻止事件冒泡
                    if (e.stopDefault) e.stopDefault()
                    if (e.stop) e.stop()

                    // 将 leafer 事件转换为 MouseEvent
                    const mouseEvent = new MouseEvent('contextmenu', {
                        clientX: e.x,
                        clientY: e.y,
                        bubbles: true,
                        cancelable: true,
                    })
                    onConnectorMenu(mouseEvent, {
                        connector,
                        from: sourceNode,
                        to: targetNode,
                    })
                })

                app.value.tree.add(connector)
                console.log(
                    `连接已创建: ${connection.source_node_id} -> ${connection.target_node_id}`
                )
            } catch (error) {
                console.error('创建连接失败:', error)
            }
        } else {
            console.warn(
                `无法找到连接的节点: ${connection.source_node_id} -> ${connection.target_node_id}`
            )
        }
    }
}

const update_nodeRect_by_id = (data: {
    node_id: string
    ui_config: INodeRectInputData
}) => {
    if (!app.value) return
    const node_rect = app.value.findId(data.node_id) as NodeRect
    node_rect.updateNode(data.ui_config)
}

onMounted(async () => {
    try {
        // Check if store is properly initialized
        if (
            !workflow_store ||
            typeof workflow_store.set_workflow !== 'function'
        ) {
            console.error('Workflow store not properly initialized')
            Notify.create({
                type: 'negative',
                message: '应用初始化失败',
            })
            void router.push('/main')
            return
        }

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
            return
        }

        create_app()

        // 将设置函数暴露给 createNodeRect 使用
        ;(window as { setupNodeListeners?: NodeListeners }).setupNodeListeners =
            {
                setupConnectionListeners: (node: NodeRect) => {
                    node.on('drag.connection.start', () => {
                        try {
                            console.log('连线拖拽开始')
                            isDraggingConnection.value = true
                            draggingNode.value = node

                            // 禁用编辑器的选择功能
                            if (app.value?.editor) {
                                app.value.editor.cancel()
                            }
                        } catch (error) {
                            console.error(
                                'Error in drag.connection.start handler:',
                                error
                            )
                        }
                    })

                    node.on(
                        'connection.created',
                        (data: {
                            connector: unknown
                            source: NodeRect
                            target: NodeRect
                        }) => {
                            try {
                                if (data && data.source && data.target) {
                                    // 从连接数据中获取源节点和目标节点的ID
                                    const source_id = data.source.id
                                    const target_id = data.target.id

                                    if (source_id && target_id) {
                                        workflow_store.add_connection(
                                            source_id,
                                            target_id
                                        )
                                        console.log(
                                            `连接已保存到store: ${source_id}_to_${target_id}`
                                        )
                                    }
                                }
                            } catch (error) {
                                console.error(
                                    'Error in connection.created handler:',
                                    error
                                )
                            }
                        }
                    )

                    // 监听连线右键菜单事件
                    node.on(
                        'connector.context.menu',
                        (data: {
                            connector: unknown
                            event: IPointerEvent
                            from: NodeRect | null
                            to: NodeRect | null
                        }) => {
                            try {
                                // 将 leafer 事件转换为 MouseEvent
                                const mouseEvent = new MouseEvent(
                                    'contextmenu',
                                    {
                                        clientX: data.event.x,
                                        clientY: data.event.y,
                                        bubbles: true,
                                        cancelable: true,
                                    }
                                )
                                onConnectorMenu(mouseEvent, {
                                    connector: data.connector,
                                    from: data.from,
                                    to: data.to,
                                })
                            } catch (error) {
                                console.error(
                                    'Error in connector.context.menu handler:',
                                    error
                                )
                            }
                        }
                    )

                    node.on(
                        'noderect:double.tap',
                        (data: { event: IPointerEvent; id: string }) => {
                            emitter.emit('noderect:edit.dialog.open', {
                                visiable: true,
                                node_id: data.id,
                            })
                        }
                    )
                },
                setupNodeDragListeners: (node: NodeRect) => {
                    node.on('drag.end', () => {
                        try {
                            if (!app.value) return
                            // 拖动结束时更新所有连接线
                            const allConnectors =
                                app.value.tree.children.filter(
                                    (child) => child instanceof Connector
                                )
                            allConnectors.forEach((connector) => {
                                if (connector.update) {
                                    connector.update()
                                }
                            })
                        } catch (error) {
                            console.error('Error in drag.end handler:', error)
                        }
                    })
                },
            }
        await load_ui()
        // 获取插件
        await handle_get_plugins()

        // 添加监听事件
        emitter.on('noderect:edit.ui.update', update_nodeRect_by_id)
    } catch (error) {
        console.error('Error in onMounted hook:', error)
        Notify.create({
            type: 'negative',
            message: '页面初始化失败',
        })
    }
})

const createNodeRect = (plugin: PluginResponse) => {
    try {
        if (!app.value) {
            Notify.create({
                type: 'negative',
                message: '应用未初始化',
            })
            return
        }

        // Check if store is available
        if (!workflow_store || typeof workflow_store.add_node !== 'function') {
            console.error('Workflow store not available in createNodeRect')
            Notify.create({
                type: 'negative',
                message: '应用状态异常，无法创建节点',
            })
            return
        }

        // TOOD 这样创建 rect 并不严谨 应该通过 NODE表
        // 继续去查询节点的名字是否存在重复
        const ui = {
            title: `${plugin.name}`,
            icon: plugin.icon,
            x: click_xy.x,
            y: click_xy.y,
        }
        // 创建一个默认的plugin
        const config: PluginConfigRecord =
            PluginUtil.createPluginConfigRecord(plugin)

        config.title = ui.title

        const node: INode = {
            id: uuid4(),
            plugin_id: plugin.id,
            type: plugin.plugin_type,
            config: config,
            ui: ui,
        }
        const node_ui = new NodeRect({ id: node.id, ...node.ui })

        // 使用全局设置函数为新节点添加监听器
        const setupFunctions = (
            window as { setupNodeListeners?: NodeListeners }
        ).setupNodeListeners
        if (setupFunctions) {
            setupFunctions.setupNodeDragListeners(node_ui)
            setupFunctions.setupConnectionListeners(node_ui)
        }

        app.value.tree.add(node_ui)
        workflow_store.add_node(node)
        add_node_dialog_visiable.value = false
    } catch (error) {
        console.error('Error creating node:', error)
        Notify.create({
            type: 'negative',
            message: '创建节点失败',
        })
    }
}

onBeforeUnmount(() => {
    try {
        // leafer-editor 不同版本销毁方法名可能不同，这里尽量兜底
        if (app.value && typeof app.value.destroy === 'function') {
            app.value.destroy()
        }
        app.value = null
    } catch (error) {
        console.error('Error during cleanup:', error)
    }
})
</script>

<template>
    <div>
        <!-- 鼠标坐标显示组件 -->
        <MouseCoordinateDisplay :app="app" />
        <EditNodeFormCp />
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

        <!-- 编辑节点配置 -->

        <div id="leafer-app"></div>
    </div>
</template>

<style lang="sass" scoped></style>
