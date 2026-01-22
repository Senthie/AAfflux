/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-12 11:07:19
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-22 12:20:34
 * @FilePath: /web/src/stores/workflow-store.ts
 * @Description: 用户当前打开的 workflow
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */
import { defineStore } from 'pinia'
import type { INodeRes, IWorkflowDetailRes } from 'src/interfaces/IWorkflows'
import { ref } from 'vue'
export const useWorkflowStore = defineStore('workspaceStore', () => {
    const workflow = ref<IWorkflowDetailRes>({
        nodes: [],
        connections: [],
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

    // 添加 node 节点
    function add_node(node: INodeRes) {
        workflow.value.nodes.push(node)
    }

    function get_node_by_id(id: string): INodeRes | undefined {
        return workflow.value.nodes.find((node) => node.id === id)
    }

    // 删除节点通过id
    function del_node_by_id(id: string) {
        // 获取index
        const index = workflow.value.nodes.findIndex((node) => node.id === id)
        if (index !== -1) {
            // 删除节点
            workflow.value.nodes.splice(index, 1)
        }
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    function update_node_config(id: string, config: Record<string, any>) {
        const node = get_node_by_id(id)
        if (node) {
            node.config = config
        }
    }

    function set_workflow(workflow_data: IWorkflowDetailRes) {
        workflow.value = workflow_data
    }

    function add_connection(source_node_id: string, target_node_id: string) {
        const connection = {
            id: `conn_${Date.now()}`,
            workflow_id: workflow.value.id,
            source_node_id: source_node_id,
            target_node_id: target_node_id,
            source_output: 'output',
            target_input: 'input',
        }
        workflow.value.connections.push(connection)
    }

    return {
        workflow,
        add_node,
        get_node_by_id,
        del_node_by_id,
        update_node_config,
        add_connection,
        set_workflow,
    }
})
