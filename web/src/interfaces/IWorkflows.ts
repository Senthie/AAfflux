/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-10 16:06:42
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-26 14:27:19
 * @FilePath: /web/src/interfaces/IWorkflows.ts
 * @Description:
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */
/* eslint-disable @typescript-eslint/no-explicit-any */

import type { PluginConfigRecord } from './IPlugin'

/**
 * Request schema for creating a workflow.
 */
export interface IWorkflowCreateRequest {
    /**
     * Workflow name
     * @minimum 1
     * @maximum 255
     */
    name: string

    /**
     * Workflow description
     */
    description?: string

    /**
     * Input parameter schema
     * @default {}
     */
    input_schema: Record<string, any>

    /**
     * Output result schema
     * @default {}
     */
    output_schema: Record<string, any>
}
export interface INode {
    // Response schema for a node.
    id: string
    plugin_id: string
    type: string
    config: PluginConfigRecord
    ui: Record<string, any>
}

// Response schema for a connection.
export interface IConnection {
    id: string
    source_node_id: string
    target_node_id: string
}
export interface IGraph {
    nodes: INode[]
    connections: IConnection[]
}

export interface IWorkflowResponse {
    /** Response schema for a workflow. */
    id: string
    name: string
    description?: string
    workspace_id: string

    input_schema: Record<string, any>
    output_schema: Record<string, any>

    created_at: string // 或者使用 Date 类型，根据您的序列化方式决定
    updated_at: string // 或者使用 Date 类型
    created_by: string
    is_deleted: boolean
    graph: IGraph
}
