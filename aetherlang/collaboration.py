"""
AetherLang Collaborative Sessions

Real-time collaboration system for multi-user flow editing:
- Session management with unique IDs
- Real-time code synchronization
- Shared execution state
- User presence tracking
- Session permissions (owner, editor, viewer)
"""

import time
import uuid
import asyncio
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum


class UserRole(Enum):
    """User roles in a collaborative session"""
    OWNER = "owner"  # Full control, can delete session
    EDITOR = "editor"  # Can edit code and execute
    VIEWER = "viewer"  # Read-only access


@dataclass
class User:
    """User in a collaborative session"""
    user_id: str
    name: str
    role: UserRole
    color: str  # Hex color for cursor/selection
    cursor_position: Optional[Dict[str, int]] = None  # {line, column}
    selection: Optional[Dict[str, Any]] = None  # {start, end}
    last_seen: float = field(default_factory=time.time)
    is_online: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "role": self.role.value,
            "color": self.color,
            "cursor_position": self.cursor_position,
            "selection": self.selection,
            "last_seen": self.last_seen,
            "is_online": self.is_online
        }


@dataclass
class CodeChange:
    """A single code change event"""
    change_id: str
    user_id: str
    timestamp: float
    change_type: str  # "insert", "delete", "replace"
    position: Dict[str, int]  # {line, column}
    old_text: Optional[str] = None
    new_text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CollaborativeSession:
    """A collaborative editing session"""
    session_id: str
    flow_name: str
    code: str
    query: str

    created_at: float
    last_modified: float
    owner_id: str

    users: Dict[str, User] = field(default_factory=dict)
    change_history: List[CodeChange] = field(default_factory=list)
    execution_results: List[Dict[str, Any]] = field(default_factory=list)

    # Session settings
    max_users: int = 10
    allow_anonymous: bool = False
    require_approval: bool = False

    # Execution state
    is_executing: bool = False
    current_executor: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "flow_name": self.flow_name,
            "code": self.code,
            "query": self.query,
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "owner_id": self.owner_id,
            "users": {uid: user.to_dict() for uid, user in self.users.items()},
            "change_count": len(self.change_history),
            "execution_count": len(self.execution_results),
            "max_users": self.max_users,
            "allow_anonymous": self.allow_anonymous,
            "require_approval": self.require_approval,
            "is_executing": self.is_executing,
            "current_executor": self.current_executor,
            "user_count": len(self.users)
        }


class CollaborationManager:
    """
    Manages collaborative sessions for AetherLang

    Features:
    - Create/join/leave sessions
    - Real-time code synchronization
    - User presence tracking
    - Role-based permissions
    - Change history
    """

    def __init__(self):
        self.sessions: Dict[str, CollaborativeSession] = {}
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
        self.cleanup_interval = 3600  # Clean up stale sessions every hour
        self._user_colors = [
            "#3B82F6",  # blue
            "#10B981",  # green
            "#F59E0B",  # amber
            "#8B5CF6",  # purple
            "#EF4444",  # red
            "#EC4899",  # pink
            "#14B8A6",  # teal
            "#F97316",  # orange
        ]
        self._next_color_index = 0

    def _get_next_color(self) -> str:
        """Get next user color"""
        color = self._user_colors[self._next_color_index]
        self._next_color_index = (self._next_color_index + 1) % len(self._user_colors)
        return color

    def create_session(
        self,
        flow_name: str,
        code: str,
        query: str,
        owner_id: str,
        owner_name: str,
        max_users: int = 10,
        allow_anonymous: bool = False
    ) -> CollaborativeSession:
        """Create a new collaborative session"""
        session_id = str(uuid.uuid4())

        # Create owner user
        owner = User(
            user_id=owner_id,
            name=owner_name,
            role=UserRole.OWNER,
            color=self._get_next_color()
        )

        session = CollaborativeSession(
            session_id=session_id,
            flow_name=flow_name,
            code=code,
            query=query,
            created_at=time.time(),
            last_modified=time.time(),
            owner_id=owner_id,
            users={owner_id: owner},
            max_users=max_users,
            allow_anonymous=allow_anonymous
        )

        self.sessions[session_id] = session

        # Track user session
        if owner_id not in self.user_sessions:
            self.user_sessions[owner_id] = set()
        self.user_sessions[owner_id].add(session_id)

        return session

    def get_session(self, session_id: str) -> Optional[CollaborativeSession]:
        """Get a session by ID"""
        return self.sessions.get(session_id)

    def join_session(
        self,
        session_id: str,
        user_id: str,
        user_name: str,
        role: UserRole = UserRole.VIEWER
    ) -> bool:
        """Join an existing session"""
        session = self.sessions.get(session_id)
        if not session:
            return False

        # Check if session is full
        if len(session.users) >= session.max_users:
            return False

        # Check if user already in session
        if user_id in session.users:
            session.users[user_id].is_online = True
            session.users[user_id].last_seen = time.time()
            return True

        # Add user to session
        user = User(
            user_id=user_id,
            name=user_name,
            role=role,
            color=self._get_next_color()
        )
        session.users[user_id] = user

        # Track user session
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(session_id)

        return True

    def leave_session(self, session_id: str, user_id: str):
        """Leave a session"""
        session = self.sessions.get(session_id)
        if not session:
            return

        if user_id in session.users:
            session.users[user_id].is_online = False

        # Track user session
        if user_id in self.user_sessions:
            self.user_sessions[user_id].discard(session_id)

    def update_code(
        self,
        session_id: str,
        user_id: str,
        new_code: str,
        change_type: str = "replace",
        position: Optional[Dict[str, int]] = None
    ) -> bool:
        """Update code in a session"""
        session = self.sessions.get(session_id)
        if not session:
            return False

        # Check permissions
        user = session.users.get(user_id)
        if not user:
            return False

        if user.role == UserRole.VIEWER:
            return False

        # Record change
        change = CodeChange(
            change_id=str(uuid.uuid4()),
            user_id=user_id,
            timestamp=time.time(),
            change_type=change_type,
            position=position or {"line": 0, "column": 0},
            old_text=session.code,
            new_text=new_code
        )

        session.change_history.append(change)
        session.code = new_code
        session.last_modified = time.time()

        return True

    def update_query(
        self,
        session_id: str,
        user_id: str,
        new_query: str
    ) -> bool:
        """Update query in a session"""
        session = self.sessions.get(session_id)
        if not session:
            return False

        # Check permissions
        user = session.users.get(user_id)
        if not user:
            return False

        if user.role == UserRole.VIEWER:
            return False

        session.query = new_query
        session.last_modified = time.time()

        return True

    def update_cursor(
        self,
        session_id: str,
        user_id: str,
        line: int,
        column: int
    ):
        """Update user cursor position"""
        session = self.sessions.get(session_id)
        if not session:
            return

        user = session.users.get(user_id)
        if not user:
            return

        user.cursor_position = {"line": line, "column": column}
        user.last_seen = time.time()

    def update_selection(
        self,
        session_id: str,
        user_id: str,
        start_line: int,
        start_column: int,
        end_line: int,
        end_column: int
    ):
        """Update user selection"""
        session = self.sessions.get(session_id)
        if not session:
            return

        user = session.users.get(user_id)
        if not user:
            return

        user.selection = {
            "start": {"line": start_line, "column": start_column},
            "end": {"line": end_line, "column": end_column}
        }
        user.last_seen = time.time()

    def start_execution(
        self,
        session_id: str,
        user_id: str
    ) -> bool:
        """Mark session as executing"""
        session = self.sessions.get(session_id)
        if not session:
            return False

        # Check permissions
        user = session.users.get(user_id)
        if not user:
            return False

        if user.role == UserRole.VIEWER:
            return False

        # Check if already executing
        if session.is_executing:
            return False

        session.is_executing = True
        session.current_executor = user_id

        return True

    def end_execution(
        self,
        session_id: str,
        user_id: str,
        result: Dict[str, Any]
    ):
        """Mark execution as complete"""
        session = self.sessions.get(session_id)
        if not session:
            return

        if session.current_executor != user_id:
            return

        session.is_executing = False
        session.current_executor = None
        session.execution_results.append({
            "timestamp": time.time(),
            "user_id": user_id,
            "result": result
        })

    def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete a session (owner only)"""
        session = self.sessions.get(session_id)
        if not session:
            return False

        # Only owner can delete
        if session.owner_id != user_id:
            return False

        # Remove from all users
        for uid in session.users.keys():
            if uid in self.user_sessions:
                self.user_sessions[uid].discard(session_id)

        del self.sessions[session_id]
        return True

    def list_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all sessions or sessions for a specific user"""
        if user_id:
            session_ids = self.user_sessions.get(user_id, set())
            return [
                self.sessions[sid].to_dict()
                for sid in session_ids
                if sid in self.sessions
            ]
        else:
            return [session.to_dict() for session in self.sessions.values()]

    def get_session_users(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all users in a session"""
        session = self.sessions.get(session_id)
        if not session:
            return []

        return [user.to_dict() for user in session.users.values()]

    def change_user_role(
        self,
        session_id: str,
        owner_id: str,
        target_user_id: str,
        new_role: UserRole
    ) -> bool:
        """Change a user's role (owner only)"""
        session = self.sessions.get(session_id)
        if not session:
            return False

        # Only owner can change roles
        if session.owner_id != owner_id:
            return False

        # Can't change owner's role
        if target_user_id == owner_id:
            return False

        user = session.users.get(target_user_id)
        if not user:
            return False

        user.role = new_role
        return True

    def cleanup_stale_sessions(self, max_age_hours: int = 24):
        """Remove sessions that haven't been modified in max_age_hours"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        to_delete = []
        for session_id, session in self.sessions.items():
            if current_time - session.last_modified > max_age_seconds:
                to_delete.append(session_id)

        for session_id in to_delete:
            session = self.sessions[session_id]
            for user_id in session.users.keys():
                if user_id in self.user_sessions:
                    self.user_sessions[user_id].discard(session_id)
            del self.sessions[session_id]

        return len(to_delete)


# Global collaboration manager
_global_collaboration_manager = CollaborationManager()


def get_collaboration_manager() -> CollaborationManager:
    """Get the global collaboration manager"""
    return _global_collaboration_manager
