/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-19 15:49:12
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-19 17:04:35
 * @FilePath: /web/src/utils/nodeReact.ts
 * @Description: 创建一个 node 的节点类型
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */
// #自定义元素 [继承 Group]
import {
    registerUI,
    dataProcessor,
    Group,
    GroupData,
    dataType,
} from '@leafer-ui/core' // 引入跨平台核心包
import type { IGroupInputData, IGroupData } from '@leafer-ui/interface'
import { Rect, Text } from 'leafer-ui'
import { Platform } from 'leafer-ui'
// 允许跨域图片渲染，但不支持导出画板内容（浏览器的限制）。
Platform.image.crossOrigin = null
// 定义数据
export interface INodeRectInputData extends IGroupInputData {
    title?: string
    desc?: string
    icon?: string
}

export interface INodeRectData extends IGroupData {
    title?: string
    desc?: string
    icon?: string
}

export class NodeRectData extends GroupData implements INodeRectData {}

// 定义类

@registerUI()
export class NodeRect extends Group {
    public override get __tag() {
        return 'NodeRect'
    }

    @dataProcessor(NodeRectData)
    public declare __: INodeRectData

    @dataType('') public declare title: string // 增加自定义属性

    @dataType('')
    public declare desc: string // 增加自定义属性

    @dataType('')
    public declare icon: string // 增加自定义属性

    constructor(data: INodeRectInputData) {
        super(data)
        this.create_rect()
        this.create_title()
    }

    create_rect(): void {
        const rect = new Rect({
            width: 100,
            height: 100,
            fill: [
                {
                    type: 'solid',
                    color: '#bfffdcff',
                },
                {
                    type: 'image', // 图案填充
                    url: `${this.icon}`,
                    offset: { x: 15, y: 15 },
                    mode: 'normal',
                    size: 70,
                    opacity: 1,
                },
            ],
            cornerRadius: 20,
        })
        this.add(rect)
    }

    create_title(): void {
        const text = new Text({
            x: 0,
            y: 102,
            fill: '#000000ff',
            text: `${this.title}`,
        })
        // 获取 text的长度
        text.x = this.x_center_position(text.boxBounds.width, 100)
        this.add(text)
    }

    x_center_position(width: number, canvas_w: number) {
        const x = canvas_w / 2 - width / 2
        return x
    }
}
