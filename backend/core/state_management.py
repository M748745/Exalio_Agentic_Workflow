"""
State Management System (CRITICAL)
Complete workflow state, context, and memory management

Features:
- Workflow Variables (global store accessible by all nodes)
- Session State (per-user/per-session storage)
- Context Passing (variable scoping and passing between nodes)
- Memory Store (long-term agent memory with persistence)
- Cache Management (temporary data caching)
- Variable Inspector (debug and monitoring)

This is the foundation for stateful workflows and conversational AI.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging
import threading
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class Variable:
    """Single variable in the state store"""
    name: str
    value: Any
    scope: str  # 'workflow', 'session', 'global'
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    ttl_seconds: Optional[int] = None  # Time to live


@dataclass
class MemoryEntry:
    """Entry in long-term memory store"""
    key: str
    value: Any
    category: str  # 'user_preference', 'conversation', 'knowledge', etc.
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    importance: float = 1.0  # 0-1 score for memory importance
    metadata: Dict[str, Any] = field(default_factory=dict)


class StateManager:
    """
    Centralized state management for workflows
    Handles variables, sessions, context, and memory
    """

    def __init__(self, persistence_dir: Optional[Path] = None):
        self.persistence_dir = persistence_dir
        if persistence_dir:
            persistence_dir.mkdir(parents=True, exist_ok=True)

        # Variable stores (in-memory with optional persistence)
        self._workflow_vars: Dict[str, Dict[str, Variable]] = defaultdict(dict)  # workflow_id -> variables
        self._session_vars: Dict[str, Dict[str, Variable]] = defaultdict(dict)  # session_id -> variables
        self._global_vars: Dict[str, Variable] = {}

        # Memory store (long-term)
        self._memory: Dict[str, MemoryEntry] = {}

        # Cache (temporary, short-lived)
        self._cache: Dict[str, Any] = {}
        self._cache_expiry: Dict[str, datetime] = {}

        # Context stack for hierarchical scoping
        self._context_stack: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # Thread safety
        self._lock = threading.RLock()

        logger.info("State Manager initialized")

    # ========================================================================
    # VARIABLE MANAGEMENT
    # ========================================================================

    def set_variable(
        self,
        name: str,
        value: Any,
        scope: str = 'workflow',
        workflow_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
        **metadata
    ) -> Variable:
        """
        Set a variable in the appropriate scope

        Args:
            name: Variable name
            value: Variable value (any JSON-serializable type)
            scope: 'workflow', 'session', or 'global'
            workflow_id: Required for workflow scope
            session_id: Required for session scope
            ttl_seconds: Optional time-to-live
            **metadata: Additional metadata

        Returns:
            Variable object
        """
        with self._lock:
            now = datetime.utcnow()

            # Create variable object
            var = Variable(
                name=name,
                value=value,
                scope=scope,
                created_at=now,
                updated_at=now,
                metadata=metadata,
                ttl_seconds=ttl_seconds
            )

            # Store in appropriate scope
            if scope == 'global':
                self._global_vars[name] = var

            elif scope == 'workflow':
                if not workflow_id:
                    raise ValueError("workflow_id required for workflow scope")
                self._workflow_vars[workflow_id][name] = var

            elif scope == 'session':
                if not session_id:
                    raise ValueError("session_id required for session scope")
                self._session_vars[session_id][name] = var

            else:
                raise ValueError(f"Unknown scope: {scope}")

            logger.debug(f"Set variable: {name}={value} (scope={scope})")
            return var

    def get_variable(
        self,
        name: str,
        scope: Optional[str] = None,
        workflow_id: Optional[str] = None,
        session_id: Optional[str] = None,
        default: Any = None
    ) -> Any:
        """
        Get variable value

        Scope resolution order (if scope not specified):
        1. Session scope (if session_id provided)
        2. Workflow scope (if workflow_id provided)
        3. Global scope

        Args:
            name: Variable name
            scope: Optional specific scope to check
            workflow_id: Workflow ID for scope resolution
            session_id: Session ID for scope resolution
            default: Default value if not found

        Returns:
            Variable value or default
        """
        with self._lock:
            # Check TTL and clean expired variables
            self._clean_expired_variables()

            # Specific scope requested
            if scope:
                var = self._get_from_scope(name, scope, workflow_id, session_id)
                return var.value if var else default

            # Scope resolution order
            # 1. Session scope
            if session_id:
                var = self._get_from_scope(name, 'session', workflow_id, session_id)
                if var:
                    return var.value

            # 2. Workflow scope
            if workflow_id:
                var = self._get_from_scope(name, 'workflow', workflow_id, session_id)
                if var:
                    return var.value

            # 3. Global scope
            var = self._get_from_scope(name, 'global', workflow_id, session_id)
            if var:
                return var.value

            return default

    def _get_from_scope(
        self,
        name: str,
        scope: str,
        workflow_id: Optional[str],
        session_id: Optional[str]
    ) -> Optional[Variable]:
        """Get variable from specific scope"""
        if scope == 'global':
            return self._global_vars.get(name)
        elif scope == 'workflow' and workflow_id:
            return self._workflow_vars.get(workflow_id, {}).get(name)
        elif scope == 'session' and session_id:
            return self._session_vars.get(session_id, {}).get(name)
        return None

    def delete_variable(
        self,
        name: str,
        scope: str = 'workflow',
        workflow_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """Delete a variable"""
        with self._lock:
            if scope == 'global':
                if name in self._global_vars:
                    del self._global_vars[name]
                    return True

            elif scope == 'workflow' and workflow_id:
                if name in self._workflow_vars.get(workflow_id, {}):
                    del self._workflow_vars[workflow_id][name]
                    return True

            elif scope == 'session' and session_id:
                if name in self._session_vars.get(session_id, {}):
                    del self._session_vars[session_id][name]
                    return True

            return False

    def list_variables(
        self,
        scope: Optional[str] = None,
        workflow_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Variable]:
        """List all variables in scope(s)"""
        with self._lock:
            self._clean_expired_variables()

            variables = {}

            if scope == 'global' or scope is None:
                variables.update(self._global_vars)

            if (scope == 'workflow' or scope is None) and workflow_id:
                variables.update(self._workflow_vars.get(workflow_id, {}))

            if (scope == 'session' or scope is None) and session_id:
                variables.update(self._session_vars.get(session_id, {}))

            return variables

    def _clean_expired_variables(self):
        """Remove variables that have exceeded their TTL"""
        now = datetime.utcnow()

        def clean_dict(var_dict):
            expired = []
            for name, var in var_dict.items():
                if var.ttl_seconds:
                    age = (now - var.created_at).total_seconds()
                    if age > var.ttl_seconds:
                        expired.append(name)
            for name in expired:
                del var_dict[name]

        # Clean global
        clean_dict(self._global_vars)

        # Clean workflow scopes
        for workflow_vars in self._workflow_vars.values():
            clean_dict(workflow_vars)

        # Clean session scopes
        for session_vars in self._session_vars.values():
            clean_dict(session_vars)

    # ========================================================================
    # CONTEXT MANAGEMENT
    # ========================================================================

    def push_context(
        self,
        workflow_id: str,
        context: Dict[str, Any]
    ):
        """
        Push new context onto stack
        Used for nested scopes or sub-workflows
        """
        with self._lock:
            self._context_stack[workflow_id].append(context)

    def pop_context(
        self,
        workflow_id: str
    ) -> Optional[Dict[str, Any]]:
        """Pop context from stack"""
        with self._lock:
            if self._context_stack[workflow_id]:
                return self._context_stack[workflow_id].pop()
            return None

    def get_context(
        self,
        workflow_id: str
    ) -> Dict[str, Any]:
        """Get current context (top of stack)"""
        with self._lock:
            if self._context_stack[workflow_id]:
                return self._context_stack[workflow_id][-1]
            return {}

    def merge_context(
        self,
        workflow_id: str,
        updates: Dict[str, Any]
    ):
        """Merge updates into current context"""
        with self._lock:
            if self._context_stack[workflow_id]:
                self._context_stack[workflow_id][-1].update(updates)
            else:
                self._context_stack[workflow_id].append(updates)

    # ========================================================================
    # MEMORY MANAGEMENT (Long-term)
    # ========================================================================

    def store_memory(
        self,
        key: str,
        value: Any,
        category: str = 'general',
        importance: float = 1.0,
        **metadata
    ) -> MemoryEntry:
        """
        Store in long-term memory

        Args:
            key: Unique memory key
            value: Memory value
            category: Memory category for organization
            importance: Importance score (0-1)
            **metadata: Additional metadata

        Returns:
            MemoryEntry object
        """
        with self._lock:
            now = datetime.utcnow()

            entry = MemoryEntry(
                key=key,
                value=value,
                category=category,
                created_at=now,
                accessed_at=now,
                access_count=0,
                importance=importance,
                metadata=metadata
            )

            self._memory[key] = entry

            # Persist if enabled
            if self.persistence_dir:
                self._persist_memory(key, entry)

            return entry

    def recall_memory(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """Recall from long-term memory"""
        with self._lock:
            if key in self._memory:
                entry = self._memory[key]
                entry.accessed_at = datetime.utcnow()
                entry.access_count += 1
                return entry.value
            return default

    def search_memory(
        self,
        category: Optional[str] = None,
        min_importance: float = 0.0,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """Search memory by criteria"""
        with self._lock:
            results = list(self._memory.values())

            # Filter by category
            if category:
                results = [m for m in results if m.category == category]

            # Filter by importance
            results = [m for m in results if m.importance >= min_importance]

            # Sort by importance and recency
            results.sort(
                key=lambda m: (m.importance, m.accessed_at),
                reverse=True
            )

            return results[:limit]

    def forget_memory(self, key: str) -> bool:
        """Remove from long-term memory"""
        with self._lock:
            if key in self._memory:
                del self._memory[key]

                # Remove from persistence
                if self.persistence_dir:
                    memory_file = self.persistence_dir / f"memory_{key}.json"
                    if memory_file.exists():
                        memory_file.unlink()

                return True
            return False

    def _persist_memory(self, key: str, entry: MemoryEntry):
        """Persist memory entry to disk"""
        if not self.persistence_dir:
            return

        memory_file = self.persistence_dir / f"memory_{key}.json"

        data = {
            'key': entry.key,
            'value': entry.value,
            'category': entry.category,
            'created_at': entry.created_at.isoformat(),
            'accessed_at': entry.accessed_at.isoformat(),
            'access_count': entry.access_count,
            'importance': entry.importance,
            'metadata': entry.metadata
        }

        with open(memory_file, 'w') as f:
            json.dump(data, f, indent=2)

    # ========================================================================
    # CACHE MANAGEMENT (Short-term)
    # ========================================================================

    def cache_set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 3600
    ):
        """Set cache value with TTL"""
        with self._lock:
            self._cache[key] = value
            self._cache_expiry[key] = datetime.utcnow() + timedelta(seconds=ttl_seconds)

    def cache_get(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """Get cache value"""
        with self._lock:
            # Clean expired first
            self._clean_expired_cache()

            return self._cache.get(key, default)

    def cache_delete(self, key: str) -> bool:
        """Delete cache entry"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._cache_expiry:
                    del self._cache_expiry[key]
                return True
            return False

    def cache_clear(self):
        """Clear all cache"""
        with self._lock:
            self._cache.clear()
            self._cache_expiry.clear()

    def _clean_expired_cache(self):
        """Remove expired cache entries"""
        now = datetime.utcnow()
        expired = [
            key for key, expiry in self._cache_expiry.items()
            if now > expiry
        ]
        for key in expired:
            del self._cache[key]
            del self._cache_expiry[key]

    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================

    def create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        **metadata
    ) -> Dict[str, Any]:
        """Create new session"""
        with self._lock:
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'created_at': datetime.utcnow().isoformat(),
                'metadata': metadata
            }

            # Store as global variable
            self.set_variable(
                f'session_{session_id}',
                session_data,
                scope='global'
            )

            return session_data

    def end_session(
        self,
        session_id: str,
        persist: bool = False
    ):
        """End session and cleanup"""
        with self._lock:
            # Optionally persist session data
            if persist and session_id in self._session_vars:
                session_key = f'session_{session_id}_archive'
                self.store_memory(
                    session_key,
                    dict(self._session_vars[session_id]),
                    category='session_archive'
                )

            # Clear session variables
            if session_id in self._session_vars:
                del self._session_vars[session_id]

            # Clear session metadata
            self.delete_variable(f'session_{session_id}', scope='global')

    # ========================================================================
    # INSPECTION & DEBUGGING
    # ========================================================================

    def inspect_state(
        self,
        workflow_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get complete state snapshot for debugging"""
        with self._lock:
            self._clean_expired_variables()
            self._clean_expired_cache()

            snapshot = {
                'timestamp': datetime.utcnow().isoformat(),
                'global_variables': {
                    name: {'value': var.value, 'created_at': var.created_at.isoformat()}
                    for name, var in self._global_vars.items()
                },
                'cache_size': len(self._cache),
                'memory_size': len(self._memory),
            }

            if workflow_id:
                snapshot['workflow_variables'] = {
                    name: {'value': var.value, 'created_at': var.created_at.isoformat()}
                    for name, var in self._workflow_vars.get(workflow_id, {}).items()
                }
                snapshot['workflow_context'] = self.get_context(workflow_id)

            if session_id:
                snapshot['session_variables'] = {
                    name: {'value': var.value, 'created_at': var.created_at.isoformat()}
                    for name, var in self._session_vars.get(session_id, {}).items()
                }

            return snapshot

    def get_stats(self) -> Dict[str, Any]:
        """Get state management statistics"""
        with self._lock:
            return {
                'global_variables': len(self._global_vars),
                'workflow_scopes': len(self._workflow_vars),
                'session_scopes': len(self._session_vars),
                'total_workflow_variables': sum(len(v) for v in self._workflow_vars.values()),
                'total_session_variables': sum(len(v) for v in self._session_vars.values()),
                'cache_entries': len(self._cache),
                'memory_entries': len(self._memory),
                'active_contexts': sum(len(c) for c in self._context_stack.values())
            }


# Global state manager instance
state_manager = StateManager()
