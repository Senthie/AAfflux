/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-03-02 17:01:49
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-03-02 17:04:37
 * @FilePath: /web/src/interfaces/IFile.ts
 * @Description:
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */
export interface IFileUploadResponse {
    file_id: string
    filename: string
    content_type: string
    size_bytes: number
    storage_type: string
    workspace_id: string
    uploaded_by: string
    created_at: string
}
