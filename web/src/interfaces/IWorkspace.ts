/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-09 14:36:55
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-09 14:39:27
 * @FilePath: /web/src/interfaces/IWorkspace.ts
 * @Description:
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */
export enum WorkspacePlan {
    FREE = 'free',
    PRO = 'pro',
    ENTERPRISE = 'enterprise',
}

export enum WorkspaceStatus {
    NORMAL = 'normal',
    ARCHIVE = 'archive',
}

export interface IWorkspaceResponse {
    id: number
    name: string
    description: string
    created_at: string
    updated_at: string
    user_id: number
    plan: WorkspacePlan
    status: WorkspaceStatus
}
