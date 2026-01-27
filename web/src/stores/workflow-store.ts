/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-12 11:07:19
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-27 11:30:45
 * @FilePath: /web/src/stores/workflow-store.ts
 * @Description: 用户当前打开的 workflow
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */
import type { IUI } from 'leafer-ui'
import { defineStore } from 'pinia'
import type {
    IConnection,
    INode,
    IWorkflowResponse,
} from 'src/interfaces/IWorkflows'
import { ref } from 'vue'
export const useWorkflowStore = defineStore('workflowStore', () => {
    const workflow = ref<IWorkflowResponse>({
        graph: {
            nodes: [],
            connections: [],
        },
        id: '',
        name: '',
        workspace_id: '',
        input_schema: {},
        output_schema: {},
        created_at: '',
        updated_at: '',
        created_by: '',
        is_deleted: false,
    })

    const app_nodeRects = ref(new Map<string, IUI>())
    const app_connections = ref(new Map<string, IUI>())

    function get_node(): INode[] {
        return workflow.value.graph.nodes
    }

    // 添加 node 节点
    function add_node(node: INode) {
        workflow.value.graph.nodes.push(node)
        console.log(workflow.value)
    }

    function get_node_by_id(id: string): INode | undefined {
        return workflow.value.graph.nodes.find((node) => node.id === id)
    }

    // 删除节点通过id
    function del_node_by_id(id: string) {
        // 获取index
        const index = workflow.value.graph.nodes.findIndex(
            (node) => node.id === id
        )
        if (index !== -1) {
            // 删除节点
            workflow.value.graph.nodes.splice(index, 1)
        }
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    function update_node_config(id: string, config: Record<string, any>) {
        const node = get_node_by_id(id)
        if (node) {
            node.config = config
        }
    }

    function set_workflow(workflow_data: IWorkflowResponse) {
        workflow.value = workflow_data
    }

    function get_connections(): IConnection[] {
        return workflow.value.graph.connections
    }

    function add_connection(source_node_id: string, target_node_id: string) {
        const connection = {
            id: `${source_node_id}_to_${target_node_id}`,
            source_node_id: source_node_id,
            target_node_id: target_node_id,
        } as IConnection
        workflow.value.graph.connections.push(connection)
    }

    // 删除连接
    function del_connection_by_id(connection_id: string) {
        const index = workflow.value.graph.connections.findIndex(
            (connection) => connection.id === connection_id
        )
        if (index !== -1) {
            workflow.value.graph.connections.splice(index, 1)
        }
    }

    // 根据源节点和目标节点删除连接
    function del_connection_by_nodes(
        source_node_id: string,
        target_node_id: string
    ) {
        const index = workflow.value.graph.connections.findIndex(
            (connection) =>
                connection.source_node_id === source_node_id &&
                connection.target_node_id === target_node_id
        )
        if (index !== -1) {
            workflow.value.graph.connections.splice(index, 1)
        }
    }

    return {
        workflow,
        app_nodeRects,
        app_connections,
        add_node,
        get_node,
        get_node_by_id,
        del_node_by_id,
        update_node_config,
        get_connections,
        add_connection,
        del_connection_by_id,
        del_connection_by_nodes,
        set_workflow,
    }
})
