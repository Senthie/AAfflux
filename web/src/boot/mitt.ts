/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-29 16:48:28
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-30 10:31:42
 * @FilePath: /web/src/boot/mitt.ts
 * @Description: 初始化 mitt 事件总线
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */
import mitt from 'mitt'
type Events = {
    'noderect:edit.dialog.open': { visiable: boolean; node_id: string }
    // 可以添加其他事件
}
const emitter = mitt<Events>()
export default emitter
