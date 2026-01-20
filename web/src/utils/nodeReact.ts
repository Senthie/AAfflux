/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-19 15:49:12
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-20 11:58:50
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
import type { IGroupInputData, IGroupData, IUI } from '@leafer-ui/interface'
import { Rect, Text, Ellipse } from 'leafer-ui'

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
    declare public __: INodeRectData

    @dataType('') declare public title: string // 增加自定义属性

    @dataType('')
    declare public desc: string // 增加自定义属性

    @dataType('')
    declare public icon: string // 增加自定义属性

    public in: IUI = null as unknown as IUI
    public out: IUI = null as unknown as IUI

    constructor(data: INodeRectInputData) {
        super(data)

        this.create_rect()
        this.create_title()
    }

    create_rect(): void {
        // TOOD 计算更真实的尺寸
        //  设置 stroke 后 rect的实际尺寸应该是 101 而不是 100
        const rect = new Rect({
            width: 100,
            height: 100,
            fill: [
                {
                    type: 'solid',
                    color: '#FFFFFF',
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
            stroke: {
                type: 'solid',
                color: '#32cd79',
                style: {
                    strokeWidth: 1,
                    strokeAlign: 'center',
                },
            },
            cornerRadius: 20,
        })
        this.in = new Ellipse({
            width: 10,
            height: 10,
            x: -5,
            y: 45,
            fill: '#ffffffff',
            stroke: {
                type: 'solid',
                color: '#32cd79',
                style: {
                    strokeWidth: 1,
                    strokeAlign: 'center',
                },
            },
        })
        this.out = this.in.clone({ x: 95 })
        this.add(rect)
        this.add(this.in)
        this.add(this.out)
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
