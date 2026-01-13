/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-10 16:06:42
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-12 10:48:23
 * @FilePath: /web/src/interfaces/IWorkflows.ts
 * @Description:
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */
/* eslint-disable @typescript-eslint/no-explicit-any */
import type { UUID } from 'crypto'

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

export interface IWorkflowResponse {
    /** Response schema for a workflow. */
    id: UUID
    name: string
    description?: string
    workspace_id: UUID

    input_schema: Record<string, any>

    output_schema: Record<string, any>
    created_at: string // 或者使用 Date 类型，根据您的序列化方式决定
    updated_at: string // 或者使用 Date 类型
    created_by: UUID
    is_deleted: boolean
}
