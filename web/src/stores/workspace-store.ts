/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-12 11:07:19
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-13 16:05:39
 * @FilePath: /web/src/stores/workspace-store.ts
 * @Description: 当前的Workspace 的资源类
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */
import { defineStore } from 'pinia'
import { v1_workflow_list } from 'src/apis/workflow_api'
import { v1_get_workspaces } from 'src/apis/workscpace_api'
import type { IPageReq, IPageRes } from 'src/interfaces/Ipage'
import type { IWorkflowResponse } from 'src/interfaces/IWorkflows'
import type { IWorkspaceResponse } from 'src/interfaces/IWorkspace'

export const useWorkspaceStore = defineStore('workspaceStore', {
    // 为了完整类型推理，推荐使用箭头函数
    state: () => {
        return {
            // 所有这些属性都将自动推断出它们的类型S
            workspace: {} as IWorkspaceResponse,
            workspace_ids: [] as IWorkspaceResponse[],
            page_workflows: {
                records: [],
                total: 0,
                size: 10,
                current: 1,
                orders: [],
                maxLimit: 100,
            } as IPageRes<IWorkflowResponse>,
        }
    },
    getters: {
        page(state): IPageReq {
            return {
                total: state.page_workflows.total,
                size: state.page_workflows.size,
                current: state.page_workflows.current,
                orders: state.page_workflows.orders,
                maxLimit: state.page_workflows.maxLimit,
            }
        },
        workflows(state): IWorkflowResponse[] {
            return state.page_workflows.records
        },
    },
    actions: {
        setWorkspace(workspace: IWorkspaceResponse) {
            this.workspace = workspace
        },
        setWorkspaceIds(workspace_ids: IWorkspaceResponse[]) {
            this.workspace_ids = workspace_ids
        },
        async handle_get_workspaces() {
            const res = await v1_get_workspaces()
            this.workspace_ids = res.data
            for (const wp of this.workspace_ids) {
                // 设置主页的 workspace
                // TOOD 用名字并不是一个明智的选择，因为名字不是唯一的标识
                if (wp.name === 'Personal') this.workspace = wp
                break
            }
            void this.handle_get_workflows_by_workspace_id(null)
        },

        async handle_get_workflows_by_workspace_id(
            workspace_id: string | null
        ) {
            if (workspace_id === null) {
                workspace_id = this.workspace.id
            }
            const res = await v1_workflow_list(
                {
                    total: this.page_workflows.total,
                    size: this.page_workflows.size,
                    current: this.page_workflows.current,
                    orders: this.page_workflows.orders,
                    maxLimit: this.page_workflows.maxLimit,
                },
                workspace_id
            )
            this.page_workflows = res.data
        },
    },
})
