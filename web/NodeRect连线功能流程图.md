# NodeRect连线功能方法调用流程图

## 1. 初始化阶段

```mermaid
graph TD
    A[MainPage.vue onMounted] --> B[create_app]
    B --> C[设置全局事件监听器]
    C --> D[setupNodeListeners.setupConnectionListeners]
    D --> E[为NodeRect节点绑定连线事件]
    
    E --> F["node.on('drag.connection.start')"]
    E --> G["node.on('connection.created')"]
    E --> H["node.on('connector.context.menu')"]
```

## 2. 连线开始阶段

```mermaid
graph TD
    A[用户点击连接点] --> B[pointer.down事件触发]
    B --> C[NodeRect.setupConnectionEvents]
    C --> D{判断点击的是in还是out}
    
    D -->|in点| E["this.in.on('pointer.down')"]
    D -->|out点| F["this.out.on('pointer.down')"]
    
    E --> G["startDragConnection('in', e)"]
    F --> H["startDragConnection('out', e)"]
    
    G --> I[设置拖拽状态]
    H --> I
    I --> J[创建虚线dragLine]
    J --> K["emit('drag.connection.start')"]
    K --> L[MainPage监听器设置全局状态]
```

## 3. 拖拽过程阶段

```mermaid
graph TD
    A[鼠标移动] --> B["app.on('pointer.move')"]
    B --> C{是否正在拖拽连线?}
    C -->|是| D["draggingNode.updateDragLineExternal"]
    C -->|否| E[忽略事件]
    
    D --> F["NodeRect.updateDragLine"]
    F --> G[更新虚线位置]
    G --> H["dragLine.points更新"]
    
    I[鼠标进入节点] --> J["pointer.enter事件"]
    J --> K[highlightConnectionPoint]
    K --> L[高亮可连接点]
    
    M[鼠标离开节点] --> N["pointer.leave事件"]
    N --> O[unhighlightConnectionPoint]
    O --> P[取消高亮]
```

## 4. 连线完成阶段

```mermaid
graph TD
    A[鼠标释放] --> B["app.on('pointer.up')"]
    B --> C["draggingNode.endDragConnectionExternal"]
    C --> D["NodeRect.endDragConnection"]
    
    D --> E[findTargetNode]
    E --> F{找到目标节点?}
    
    F -->|是| G[checkForCyclicConnection]
    F -->|否| H[cleanupDragState]
    
    G --> I{是否形成循环?}
    I -->|是| J[showConnectionWarning]
    I -->|否| K[createConnection]
    
    J --> H
    K --> L[动态导入Connector]
    L --> M[创建连接线]
    M --> N[setupConnectorContextMenu]
    N --> O["emit('connection.created')"]
    O --> P[MainPage监听器保存到store]
    P --> Q[workflow_store.add_connection]
    Q --> H
```

## 5. 连线删除阶段

```mermaid
graph TD
    A[右键连接线] --> B["connector.on('pointer.menu')"]
    B --> C["emit('connector.context.menu')"]
    C --> D["MainPage.onConnectorMenu"]
    D --> E[显示右键菜单]
    E --> F[用户选择删除]
    F --> G[connector.remove]
    G --> H["workflow_store.del_connection_by_nodes"]
```

## 6. 核心方法调用序列

### 连线创建完整流程

1. **事件绑定**: `setupConnectionEvents()` → 为in/out点绑定pointer.down事件
2. **开始拖拽**: `startDragConnection()` → 设置状态、创建虚线、触发事件
3. **拖拽更新**: `updateDragLine()` → 实时更新虚线位置
4. **结束拖拽**: `endDragConnection()` → 查找目标、检查循环、创建连接
5. **创建连接**: `createConnection()` → 导入Connector、创建连线、设置事件
6. **保存状态**: MainPage监听器 → `workflow_store.add_connection()`

### 关键状态管理

- `isDragging`: 是否正在拖拽
- `dragStartPoint`: 拖拽起始点('in'/'out')
- `dragLine`: 拖拽时的虚线对象
- `isDraggingConnection`: 全局拖拽状态(MainPage)
- `draggingNode`: 当前拖拽的节点(MainPage)

### 循环检测机制

`checkForCyclicConnection()` 方法通过遍历现有连接，检查是否存在反向连接来防止循环。

### 事件传播控制

使用 `e.stopDefault()` 和 `e.stop()` 防止与编辑器的默认行为冲突。
