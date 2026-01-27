"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:36:55
FilePath: /api/app/utils/rbac.py
Description: RBAC权限控制

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from enum import Enum
from functools import wraps
from typing import Dict, List, Optional, Set


class Role(str, Enum):
    """用户角色枚举"""

    ADMIN = 'admin'  # 管理员 - 完全权限
    MEMBER = 'member'  # 成员 - 创建和读取
    VIEWER = 'viewer'  # 访客 - 只读权限


class Permission(str, Enum):
    """权限操作枚举"""

    CREATE = 'create'
    READ = 'read'
    UPDATE = 'update'
    DELETE = 'delete'


class ResourceType(str, Enum):
    """资源枚举"""

    ORGANIZATION = 'organization'
    TEAM = 'team'
    WORKSPACE = 'workspace'
    WORKFLOW = 'workflow'
    APPLICATION = 'application'
    FILE = 'file'


# 角色权限映射表
ROLE_PERMISSIONS: Dict[Role, List[Permission]] = {
    Role.ADMIN: [Permission.CREATE, Permission.READ, Permission.UPDATE, Permission.DELETE],
    Role.MEMBER: [Permission.CREATE, Permission.READ, Permission.UPDATE],
    Role.VIEWER: [Permission.READ],
}

# 资源层级权限继承规则
RESOURCE_HIERARCHY: Dict[ResourceType, List[ResourceType]] = {
    ResourceType.ORGANIZATION: [ResourceType.TEAM, ResourceType.WORKSPACE],
    ResourceType.TEAM: [ResourceType.WORKSPACE],
    ResourceType.WORKSPACE: [ResourceType.WORKFLOW, ResourceType.APPLICATION, ResourceType.FILE],
}


def has_permission(role: Role, permission: Permission) -> bool:
    """检查角色是否有指定权限

    Args:
        role: 用户角色
        permission: 权限操作

    Returns:
        bool: 是否有权限
    """
    return permission in ROLE_PERMISSIONS.get(role, [])


def get_inherited_permissions(resource_type: ResourceType, role: Role) -> List[Permission]:
    """获取角色在指定资源类型上的基础权限

    Args:
        resource_type: 资源类型
        role: 用户角色

    Returns:
        List[Permission]: 该角色的基础权限列表
    """
    return ROLE_PERMISSIONS.get(role, [])


def _get_parent_resources(resource_type: ResourceType) -> List[ResourceType]:
    """获取指定资源类型的所有上级资源类型

    Args:
        resource_type: 目标资源类型

    Returns:
        List[ResourceType]: 上级资源类型列表
    """
    parent_resources = []

    # 遍历资源层级关系，找到所有指向当前资源的上级资源
    for parent, children in RESOURCE_HIERARCHY.items():
        if resource_type in children:
            parent_resources.append(parent)
            # 递归查找上级的上级
            parent_resources.extend(_get_parent_resources(parent))

    return list(set(parent_resources))  # 去重


def get_effective_permissions(
    resource_type: ResourceType, user_roles: Dict[ResourceType, Role]
) -> List[Permission]:
    """获取用户在指定资源上的有效权限（包括继承权限）

    Args:
        resource_type: 目标资源类型
        user_roles: 用户在各个资源层级的角色 {ResourceType: Role}

    Returns:
        List[Permission]: 有效权限列表
    """
    effective_permissions: Set[Permission] = set()

    # 1. 获取用户在当前资源的直接权限
    current_role = user_roles.get(resource_type)
    if current_role:
        effective_permissions.update(ROLE_PERMISSIONS.get(current_role, []))

    # 2. 获取继承权限
    parent_resources = _get_parent_resources(resource_type)

    for parent_resource in parent_resources:
        parent_role = user_roles.get(parent_resource)
        if parent_role:
            # 上级权限可以继承到下级
            parent_permissions = ROLE_PERMISSIONS.get(parent_role, [])
            effective_permissions.update(parent_permissions)

    return list(effective_permissions)


def check_resource_permission(
    user_role: Role,
    resource_type: ResourceType,
    permission: Permission,
    parent_permissions: Optional[Dict[ResourceType, Role]] = None,
) -> bool:
    """检查用户是否对指定资源有指定权限

    Args:
        user_role: 用户在当前资源的角色
        resource_type: 资源类型
        permission: 需要检查的权限
        parent_permissions: 用户在上级资源的角色映射 {ResourceType: Role}

    Returns:
        bool: 是否有权限
    """
    # 1. 检查用户在当前资源的直接权限
    if has_permission(user_role, permission):
        return True

    # 2. 检查继承权限
    if parent_permissions:
        parent_resources = _get_parent_resources(resource_type)

        for parent_resource in parent_resources:
            parent_role = parent_permissions.get(parent_resource)
            if parent_role and has_permission(parent_role, permission):
                return True

    return False


def get_user_permissions_for_resource(
    resource_type: ResourceType, resource_id: str, user_roles: Dict[str, Dict[ResourceType, Role]]
) -> List[Permission]:
    """获取用户对特定资源实例的权限

    Args:
        resource_type: 资源类型
        resource_id: 资源实例ID
        user_roles: 用户角色映射 {resource_id: {ResourceType: Role}}

    Returns:
        List[Permission]: 权限列表
    """
    # 获取用户在该资源实例的角色信息
    roles_for_resource = user_roles.get(resource_id, {})

    return get_effective_permissions(resource_type, roles_for_resource)


def is_higher_role(role1: Role, role2: Role) -> bool:
    """比较两个角色的权限级别

    Args:
        role1: 角色1
        role2: 角色2

    Returns:
        bool: role1是否比role2权限更高
    """
    role_hierarchy = {
        Role.VIEWER: 1,
        Role.MEMBER: 2,
        Role.ADMIN: 3,
    }

    return role_hierarchy.get(role1, 0) > role_hierarchy.get(role2, 0)


def get_highest_role(roles: List[Role]) -> Optional[Role]:
    """从角色列表中获取权限最高的角色

    Args:
        roles: 角色列表

    Returns:
        Optional[Role]: 最高权限角色，如果列表为空返回None
    """
    if not roles:
        return None

    role_hierarchy = {
        Role.VIEWER: 1,
        Role.MEMBER: 2,
        Role.ADMIN: 3,
    }

    return max(roles, key=lambda role: role_hierarchy.get(role, 0))


def can_assign_role(assigner_role: Role, target_role: Role) -> bool:
    """检查是否可以分配角色（只能分配不高于自己的角色）

    Args:
        assigner_role: 分配者角色
        target_role: 目标角色

    Returns:
        bool: 是否可以分配
    """
    return not is_higher_role(target_role, assigner_role)


# 权限装饰器
def require_permission(resource_type: ResourceType, permission: Permission):
    """权限检查装饰器

    Args:
        resource_type: 资源类型
        permission: 需要的权限
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 这里需要从请求上下文获取用户信息和权限
            # 实际实现需要结合具体的认证中间件
            # 示例实现：
            # current_user = get_current_user()
            # user_roles = get_user_roles(current_user.id, resource_id)
            # effective_permissions = get_effective_permissions(resource_type, user_roles)
            #
            # if permission not in effective_permissions:
            #     raise HTTPException(status_code=403, detail="Permission denied")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(resource_type: ResourceType, min_role: Role):
    """角色检查装饰器

    Args:
        resource_type: 资源类型
        min_role: 最低要求角色
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 实际实现需要结合具体的认证中间件
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# 工具函数
def get_all_permissions() -> List[Permission]:
    """获取所有权限列表"""
    return list(Permission)


def get_all_roles() -> List[Role]:
    """获取所有角色列表"""
    return list(Role)


def get_all_resource_types() -> List[ResourceType]:
    """获取所有资源类型列表"""
    return list(ResourceType)


def get_child_resources(resource_type: ResourceType) -> List[ResourceType]:
    """获取指定资源类型的所有子资源类型

    Args:
        resource_type: 父资源类型

    Returns:
        List[ResourceType]: 子资源类型列表
    """
    return RESOURCE_HIERARCHY.get(resource_type, [])


def validate_role_assignment(
    resource_type: ResourceType, role: Role, user_roles: Dict[ResourceType, Role]
) -> bool:
    """验证角色分配是否合理

    Args:
        resource_type: 资源类型
        role: 要分配的角色
        user_roles: 用户现有角色

    Returns:
        bool: 是否合理
    """
    # 检查是否在上级资源有足够权限
    parent_resources = _get_parent_resources(resource_type)

    for parent_resource in parent_resources:
        parent_role = user_roles.get(parent_resource)
        if parent_role and is_higher_role(parent_role, role):
            return True

    return False
