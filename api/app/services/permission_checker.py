"""Permission checking service for role-based access control."""

from typing import Optional
from enum import Enum
from uuid import UUID
from sqlmodel import Session, select

from app.models.user import User, Team, TeamMember, Workspace


class Role(str, Enum):
    """User roles in a team."""

    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    GUEST = "GUEST"


class Action(str, Enum):
    """Actions that can be performed on resources."""

    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class PermissionChecker:
    """Service for checking user permissions."""

    def __init__(self, db: Session):
        """
        Initialize PermissionChecker.

        Args:
            db: Database session
        """
        self.db = db

    def check_permission(
        self,
        user: User,
        workspace: Workspace,
        action: Action,
    ) -> bool:
        """
        Check if user has permission to perform action in workspace.

        Args:
            user: User to check permissions for
            workspace: Workspace to check permissions in
            action: Action to perform

        Returns:
            True if user has permission, False otherwise
        """
        # Get user's role in the team
        role = self.get_user_role(user, workspace)

        if not role:
            return False

        # Check permission based on role and action
        return self._has_permission(role, action)

    def get_user_role(self, user: User, workspace: Workspace) -> Optional[Role]:
        """
        Get user's role in workspace's team.

        Args:
            user: User to get role for
            workspace: Workspace to check

        Returns:
            User's role or None if not a member
        """
        # Get team membership
        statement = select(TeamMember).where(
            TeamMember.team_id == workspace.team_id,
            TeamMember.user_id == user.id,
        )
        membership = self.db.exec(statement).first()

        if not membership:
            return None

        try:
            return Role(membership.role)
        except ValueError:
            return None

    def is_team_admin(self, user: User, team: Team) -> bool:
        """
        Check if user is admin of team.

        Args:
            user: User to check
            team: Team to check

        Returns:
            True if user is admin
        """
        statement = select(TeamMember).where(
            TeamMember.team_id == team.id,
            TeamMember.user_id == user.id,
            TeamMember.role == Role.ADMIN.value,
        )
        membership = self.db.exec(statement).first()

        return membership is not None

    def is_workspace_member(self, user: User, workspace: Workspace) -> bool:
        """
        Check if user is member of workspace's team.

        Args:
            user: User to check
            workspace: Workspace to check

        Returns:
            True if user is member
        """
        statement = select(TeamMember).where(
            TeamMember.team_id == workspace.team_id,
            TeamMember.user_id == user.id,
        )
        membership = self.db.exec(statement).first()

        return membership is not None

    def require_permission(
        self,
        user: User,
        workspace: Workspace,
        action: Action,
    ) -> None:
        """
        Require user to have permission, raise exception if not.

        Args:
            user: User to check permissions for
            workspace: Workspace to check permissions in
            action: Action to perform

        Raises:
            PermissionError: If user doesn't have permission
        """
        if not self.check_permission(user, workspace, action):
            raise PermissionError(
                f"User does not have permission to {action.value} in this workspace"
            )

    def _has_permission(self, role: Role, action: Action) -> bool:
        """
        Check if role has permission for action.

        Args:
            role: User role
            action: Action to perform

        Returns:
            True if role has permission
        """
        # Define permission matrix
        permissions = {
            Role.ADMIN: {
                Action.CREATE,
                Action.READ,
                Action.UPDATE,
                Action.DELETE,
            },
            Role.MEMBER: {
                Action.CREATE,
                Action.READ,
                Action.UPDATE,
            },
            Role.GUEST: {
                Action.READ,
            },
        }

        return action in permissions.get(role, set())

    def get_accessible_workspaces(self, user: User) -> list[Workspace]:
        """
        Get all workspaces user has access to.

        Args:
            user: User to get workspaces for

        Returns:
            List of accessible workspaces
        """
        # Get all teams user is member of
        statement = select(TeamMember).where(TeamMember.user_id == user.id)
        memberships = self.db.exec(statement).all()

        if not memberships:
            return []

        team_ids = [m.team_id for m in memberships]

        # Get all workspaces in those teams
        workspaces = []
        for team_id in team_ids:
            statement = select(Workspace).where(Workspace.team_id == team_id)
            team_workspaces = self.db.exec(statement).all()
            workspaces.extend(team_workspaces)

        return workspaces

    def can_access_workspace(self, user: User, workspace_id: UUID) -> bool:
        """
        Check if user can access workspace.

        Args:
            user: User to check
            workspace_id: Workspace ID to check

        Returns:
            True if user can access workspace
        """
        workspace = self.db.get(Workspace, workspace_id)

        if not workspace:
            return False

        return self.is_workspace_member(user, workspace)
