"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-10 17:44:58
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-16 10:33:07
FilePath: : AAfflux: api: app: api: v1: teams.py
Description:团队管理 API 端点
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.middleware.auth import get_current_user
from app.models.auth.user import User
from app.schemas.team import (
    TeamCreate,
    TeamResponse,
    TeamMemberResponse,
    TeamMemberCreate,
    TeamMemberUpdate,
    TeamInvitationCreate,
    TeamInvitationResponse,
    TeamInvitationAccept,
)
from app.services.team_service import TeamService

router = APIRouter(prefix='/teams', tags=['Team Management'])

# 依赖注入定义
DbSession = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_team_service(session: DbSession) -> TeamService:
    """获取团队服务实例"""
    return TeamService(session)


TeamServiceDep = Annotated[TeamService, Depends(get_team_service)]


@router.post(
    '',
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
    summary='创建团队',
)
async def create_team(
    data: TeamCreate,
    current_user: CurrentUser,
    service: TeamServiceDep,
) -> TeamResponse:
    """创建新团队"""
    team = await service.create_team(data, current_user.id)
    return TeamResponse.model_validate(team)


@router.get(
    '/{team_id}',
    response_model=TeamResponse,
    summary='获取团队信息',
)
async def get_team(
    team_id: UUID,
    service: TeamServiceDep,
) -> TeamResponse:
    """获取指定团队信息"""
    # 这里需要在 TeamService 中添加 get_team 方法
    # team = await service.get_team(team_id)
    # if not team:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail='Team not found'
    #     )
    # return TeamResponse.model_validate(team)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail='Method not implemented yet'
    )


@router.get(
    '/{team_id}/members',
    response_model=list[TeamMemberResponse],
    summary='获取团队成员列表',
)
async def get_team_members(
    team_id: UUID,
    service: TeamServiceDep,
) -> list[TeamMemberResponse]:
    """获取团队成员列表"""
    members = await service.get_team_members(team_id)
    return [TeamMemberResponse.model_validate(member) for member in members]


@router.post(
    '/{team_id}/members',
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary='添加团队成员',
)
async def add_team_member(
    team_id: UUID,
    data: TeamMemberCreate,
    service: TeamServiceDep,
) -> TeamMemberResponse:
    """添加团队成员"""
    try:
        member = await service.add_member(team_id, data.user_id, data.role)
        return TeamMemberResponse.model_validate(member)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e


@router.put(
    '/{team_id}/members/{user_id}',
    response_model=TeamMemberResponse,
    summary='更新成员角色',
)
async def update_team_member(
    team_id: UUID,
    user_id: UUID,
    data: TeamMemberUpdate,
    service: TeamServiceDep,
) -> TeamMemberResponse:
    """更新团队成员角色"""
    member = await service.update_member_role(team_id, user_id, data.role)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Team member not found'
        )
    return TeamMemberResponse.model_validate(member)


@router.delete(
    '/{team_id}/members/{user_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='移除团队成员',
)
async def remove_team_member(
    team_id: UUID,
    user_id: UUID,
    service: TeamServiceDep,
) -> None:
    """移除团队成员"""
    success = await service.remove_member(team_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Team member not found'
        )


@router.post(
    '/{team_id}/invitations',
    response_model=TeamInvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary='发送团队邀请',
)
async def send_team_invitation(
    team_id: UUID,
    data: TeamInvitationCreate,
    current_user: CurrentUser,
    service: TeamServiceDep,
) -> TeamInvitationResponse:
    """发送团队邀请"""
    invitation = await service.send_invitation(
        team_id, data.email, data.role, current_user.id
    )
    return TeamInvitationResponse.model_validate(invitation)


@router.post(
    '/invitations/accept',
    response_model=TeamMemberResponse,
    summary='接受团队邀请',
)
async def accept_team_invitation(
    data: TeamInvitationAccept,
    current_user: CurrentUser,
    service: TeamServiceDep,
) -> TeamMemberResponse:
    """接受团队邀请"""
    member = await service.accept_invitation(data.token, current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid or expired invitation token'
        )
    return TeamMemberResponse.model_validate(member)
