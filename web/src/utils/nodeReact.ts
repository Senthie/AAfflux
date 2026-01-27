/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-19 15:49:12
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-27 12:07:17
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
import type {
    IGroupInputData,
    IGroupData,
    IUI,
    IPointerEvent,
} from '@leafer-ui/interface'
import { Rect, Text, Ellipse, Line } from 'leafer-ui'

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

    // 连线相关状态
    private isDragging = false
    private dragLine: Line | null = null
    private dragStartPoint: 'in' | 'out' | null = null

    constructor(data: INodeRectInputData) {
        super(data)
        this.editable = true
        this.create_rect()
        this.create_title()
        // TOOD Node之间会形成回环，需要添加条件进行控制
        this.setupConnectionEvents()
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

        // 创建连接点，设置为不可编辑以避免与编辑器冲突
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
            editable: false, // 关键：设置连接点不可编辑
            cursor: 'crosshair', // 设置鼠标样式提示
        })

        this.out = this.in.clone({
            x: 95,
            editable: false, // 关键：设置连接点不可编辑
            cursor: 'crosshair', // 设置鼠标样式提示
        })

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

    // 设置连线事件
    private setupConnectionEvents(): void {
        // 为 in 点添加事件监听，使用更高优先级
        this.in.on(
            'pointer.down',
            (e: IPointerEvent) => {
                // 阻止事件冒泡，防止编辑器处理
                if (e.stopDefault) e.stopDefault()
                if (e.stop) e.stop()
                this.startDragConnection('in', e)
            },
            { capture: true }
        )

        // 为 out 点添加事件监听，使用更高优先级
        this.out.on(
            'pointer.down',
            (e: IPointerEvent) => {
                // 阻止事件冒泡，防止编辑器处理
                if (e.stopDefault) e.stopDefault()
                if (e.stop) e.stop()
                this.startDragConnection('out', e)
            },
            { capture: true }
        )

        // 监听鼠标进入节点区域
        this.on('pointer.enter', () => {
            if (this.isDragging && this.dragStartPoint) {
                // 高亮显示可连接的点
                this.highlightConnectionPoint()
            }
        })

        // 监听鼠标离开节点区域
        this.on('pointer.leave', () => {
            if (this.isDragging) {
                // 取消高亮
                this.unhighlightConnectionPoint()
            }
        })
    }

    // 开始拖拽连线
    private startDragConnection(point: 'in' | 'out', e: IPointerEvent): void {
        console.log('开始连线拖拽:', point, 'event:', e)
        this.isDragging = true
        this.dragStartPoint = point

        // 临时禁用节点的编辑功能，避免与连线冲突
        this.editable = false

        // 获取起始点的世界坐标
        const startPoint = point === 'in' ? this.in : this.out
        const startWorldPos = startPoint.getWorldPoint({ x: 5, y: 5 }) // 连接点中心

        // 获取鼠标的世界坐标
        const mouseWorldPos = this.leafer
            ? this.leafer.getWorldPoint({ x: e.x, y: e.y })
            : { x: e.x, y: e.y }

        console.log(
            '起始点世界坐标:',
            startWorldPos,
            '鼠标世界坐标:',
            mouseWorldPos
        )

        // 创建虚线
        this.dragLine = new Line({
            points: [
                startWorldPos.x,
                startWorldPos.y,
                mouseWorldPos.x,
                mouseWorldPos.y,
            ],
            stroke: {
                type: 'solid',
                color: '#32cd79',
                style: {
                    strokeWidth: 2,
                    strokeDashArray: [5, 5], // 虚线样式
                },
            },
            editable: false, // 虚线不可编辑
        })

        // 添加到根节点
        if (this.leafer) {
            this.leafer.add(this.dragLine)
        }

        // 触发全局拖拽开始事件
        this.emit('drag.connection.start', {
            node: this,
            point,
            startPos: startWorldPos,
        })
    }

    // 更新拖拽线条
    private updateDragLine(e: IPointerEvent): void {
        if (this.dragLine && this.dragStartPoint) {
            const startPoint = this.dragStartPoint === 'in' ? this.in : this.out
            const startWorldPos = startPoint.getWorldPoint({ x: 5, y: 5 })

            // 获取鼠标的世界坐标
            const mouseWorldPos = this.leafer
                ? this.leafer.getWorldPoint({ x: e.x, y: e.y })
                : { x: e.x, y: e.y }

            this.dragLine.points = [
                startWorldPos.x,
                startWorldPos.y,
                mouseWorldPos.x,
                mouseWorldPos.y,
            ]
        }
    }

    // 结束拖拽连线
    private endDragConnection(e: IPointerEvent): void {
        if (!this.isDragging || !this.dragLine || !this.dragStartPoint) return

        // 获取鼠标的世界坐标
        const mouseWorldPos = this.leafer
            ? this.leafer.getWorldPoint({ x: e.x, y: e.y })
            : { x: e.x, y: e.y }

        // 检查是否在其他节点上释放
        const targetNode = this.findTargetNode(mouseWorldPos.x, mouseWorldPos.y)

        if (targetNode && targetNode !== this) {
            // 创建连接
            void this.createConnection(targetNode)
        }
        this.editable = true
        // 清理拖拽状态
        this.cleanupDragState()
    }

    // 查找目标节点
    private findTargetNode(x: number, y: number): NodeRect | null {
        if (!this.leafer) return null

        const allNodes = this.leafer.children.filter(
            (child) => child instanceof NodeRect
        )

        for (const node of allNodes) {
            if (node !== this) {
                // 检查点是否在节点的边界内
                const bounds = node.getBounds()
                if (
                    x >= bounds.x &&
                    x <= bounds.x + bounds.width &&
                    y >= bounds.y &&
                    y <= bounds.y + bounds.height
                ) {
                    return node
                }
            }
        }

        return null
    }

    // 检查是否存在循环连接
    private checkForCyclicConnection(targetNode: NodeRect): boolean {
        if (!this.leafer || !this.dragStartPoint) return false

        // 获取所有连接线
        const allConnectors = this.leafer.children.filter(
            (child) => child.constructor.name === 'Connector'
        )

        // 确定当前要创建的连接方向
        const isFromIn = this.dragStartPoint === 'in'

        // 检查是否已经存在任何方向的连接
        for (const connector of allConnectors) {
            const connectorData = connector as unknown as {
                from?: IUI
                to?: IUI
            }
            if (connectorData.from && connectorData.to) {
                // 获取连接线的源节点和目标节点
                const fromNode = this.getNodeFromConnectionPoint(
                    connectorData.from
                )
                const toNode = this.getNodeFromConnectionPoint(connectorData.to)

                if (fromNode && toNode) {
                    // 检查是否存在反向连接（形成循环）
                    if (isFromIn) {
                        // 当前要创建：targetNode -> this
                        // 检查是否存在：this -> targetNode
                        if (fromNode === this && toNode === targetNode) {
                            console.warn(
                                `检测到循环连接，阻止创建连接: ${targetNode.title} -> ${this.title}`
                            )
                            return true
                        }
                    } else {
                        // 当前要创建：this -> targetNode
                        // 检查是否存在：targetNode -> this
                        if (fromNode === targetNode && toNode === this) {
                            console.warn(
                                `检测到循环连接，阻止创建连接: ${this.title} -> ${targetNode.title}`
                            )
                            return true
                        }
                    }
                }
            }
        }

        return false // 不存在循环连接
    }

    // 从连接点获取对应的节点
    private getNodeFromConnectionPoint(
        connectionPoint: IUI | null
    ): NodeRect | null {
        if (!this.leafer || !connectionPoint) return null

        const allNodes = this.leafer.children.filter(
            (child) => child instanceof NodeRect
        )

        for (const node of allNodes) {
            if (node.in === connectionPoint || node.out === connectionPoint) {
                return node
            }
        }

        return null
    }

    // 创建连接
    private async createConnection(targetNode: NodeRect): Promise<void> {
        if (!this.dragStartPoint) return

        // 检查是否会形成循环连接
        if (this.checkForCyclicConnection(targetNode)) {
            console.log('阻止循环连接：节点间已存在反向连接')
            this.showConnectionWarning(
                '不能创建循环连接！节点间已存在反向连接。'
            )
            return
        }

        try {
            // 动态导入 Connector
            const { Connector } = await import('leafer-connector')
            let source_point: IUI
            let target_point: IUI
            let id = `_to_`
            // 根据拖拽起始点确定连接方向
            if (this.dragStartPoint === 'in') {
                // 从 in 拖出，连接到目标节点的 out
                source_point = targetNode.out
                target_point = this.in
                id = `${targetNode.id}_to_${this.id}`
            } else {
                // 从 out 拖出，连接到目标节点的 in
                source_point = this.out
                target_point = targetNode.in
                id = `${this.id}_to_${targetNode.id}`
            }

            if (this.leafer) {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                const connector = new Connector(this.leafer as any, {
                    from: source_point,
                    to: target_point,
                    stroke: '#32cd79',
                })
                connector.id = id

                this.leafer.add(connector)
                const res = {
                    connector,
                    source: this.dragStartPoint === 'in' ? targetNode : this,
                    target: this.dragStartPoint === 'in' ? this : targetNode,
                }
                // 触发自定义事件，通知外部组件有新连接创建
                this.emit('connection.created', res)
            }
        } catch (error) {
            console.error('创建连接失败:', error)
        }
    }
    // 显示连接警告
    private showConnectionWarning(message: string): void {
        console.warn(message)

        // 临时将连接点变红以提示用户
        const warningStroke = {
            type: 'solid' as const,
            color: '#ff4444',
            style: {
                strokeWidth: 2,
                strokeAlign: 'center' as const,
            },
        }

        if (this.dragStartPoint === 'in') {
            this.in.stroke = warningStroke
        } else if (this.dragStartPoint === 'out') {
            this.out.stroke = warningStroke
        }

        // 2秒后恢复原始颜色
        setTimeout(() => {
            this.unhighlightConnectionPoint()
        }, 2000)
    }

    // 高亮连接点
    private highlightConnectionPoint(): void {
        if (this.dragStartPoint === 'in') {
            // 高亮 out 点
            this.out.stroke = {
                type: 'solid',
                color: '#ff6b6b',
                style: { strokeWidth: 2 },
            }
        } else {
            // 高亮 in 点
            this.in.stroke = {
                type: 'solid',
                color: '#ff6b6b',
                style: { strokeWidth: 2 },
            }
        }
    }

    // 取消高亮连接点
    private unhighlightConnectionPoint(): void {
        // 恢复原始样式
        const originalStroke = {
            type: 'solid' as const,
            color: '#32cd79',
            style: {
                strokeWidth: 1,
                strokeAlign: 'center' as const,
            },
        }

        this.in.stroke = originalStroke
        this.out.stroke = originalStroke
    }

    // 清理拖拽状态
    private cleanupDragState(): void {
        if (this.dragLine) {
            this.dragLine.remove()
            this.dragLine = null
        }

        this.isDragging = false
        this.dragStartPoint = null
        this.unhighlightConnectionPoint()
    }

    // 公共方法：供外部调用
    public updateDragLineExternal(e: IPointerEvent): void {
        this.updateDragLine(e)
    }

    public endDragConnectionExternal(e: IPointerEvent): void {
        this.endDragConnection(e)
    }

    public get isCurrentlyDragging(): boolean {
        return this.isDragging
    }

    public get currentDragStartPoint(): 'in' | 'out' | null {
        return this.dragStartPoint
    }
}
