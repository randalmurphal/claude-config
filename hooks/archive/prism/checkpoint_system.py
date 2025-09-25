#!/usr/bin/env python3
"""
Checkpoint System for Agent Response Analyzer
=============================================
Tracks processed transcript entries to prevent reprocessing.
Uses JSON-based persistence for checkpoint state management.
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class TranscriptEntry:
    """Individual transcript entry with unique identification."""

    entry_id: str          # Unique identifier for this entry
    timestamp: float       # When the entry was created
    agent_type: str        # Type of agent that generated this
    content: str           # The actual transcript content
    session_id: str        # Session this entry belongs to
    task_id: Optional[str] = None  # Optional task identifier

    def __post_init__(self):
        """Ensure entry_id is unique if not provided."""
        if not self.entry_id:
            # Generate deterministic hash from content + timestamp + agent_type
            content_hash = hashlib.sha256(
                f"{self.content}{self.timestamp}{self.agent_type}".encode()
            ).hexdigest()[:16]
            self.entry_id = f"{self.agent_type}_{int(self.timestamp)}_{content_hash}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TranscriptEntry':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class CheckpointState:
    """Current checkpoint state tracking processed entries."""

    last_updated: float                    # When checkpoint was last updated
    processed_entries: Set[str]            # Set of processed entry IDs
    session_checkpoints: Dict[str, float]  # Last processed timestamp per session
    total_processed: int                   # Total entries processed
    version: str = "1.0"                   # Checkpoint format version

    def __post_init__(self):
        """Initialize sets and ensure types."""
        if isinstance(self.processed_entries, list):
            self.processed_entries = set(self.processed_entries)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "last_updated": self.last_updated,
            "processed_entries": list(self.processed_entries),  # JSON doesn't support sets
            "session_checkpoints": self.session_checkpoints,
            "total_processed": self.total_processed,
            "version": self.version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CheckpointState':
        """Create from dictionary."""
        return cls(
            last_updated=data.get("last_updated", time.time()),
            processed_entries=set(data.get("processed_entries", [])),
            session_checkpoints=data.get("session_checkpoints", {}),
            total_processed=data.get("total_processed", 0),
            version=data.get("version", "1.0")
        )


class CheckpointManager:
    """Manages checkpoint state persistence and validation."""

    def __init__(self, checkpoint_file: Optional[Path] = None):
        """Initialize checkpoint manager.

        Args:
            checkpoint_file: Path to checkpoint file. Defaults to ~/.claude/analyzer_checkpoint.json
        """
        if checkpoint_file is None:
            checkpoint_file = Path.home() / ".claude" / "analyzer_checkpoint.json"

        self.checkpoint_file = Path(checkpoint_file)
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        self._state: Optional[CheckpointState] = None
        self._load_checkpoint()

    def _load_checkpoint(self) -> None:
        """Load checkpoint state from disk."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    data = json.load(f)
                self._state = CheckpointState.from_dict(data)
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"Warning: Corrupted checkpoint file, creating new: {e}")
                self._state = CheckpointState(
                    last_updated=time.time(),
                    processed_entries=set(),
                    session_checkpoints={},
                    total_processed=0
                )
        else:
            self._state = CheckpointState(
                last_updated=time.time(),
                processed_entries=set(),
                session_checkpoints={},
                total_processed=0
            )

    def save_checkpoint(self) -> bool:
        """Save checkpoint state to disk.

        Returns:
            True if saved successfully, False otherwise
        """
        if not self._state:
            return False

        try:
            self._state.last_updated = time.time()
            with open(self.checkpoint_file, 'w') as f:
                json.dump(self._state.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving checkpoint: {e}")
            return False

    def is_processed(self, entry: TranscriptEntry) -> bool:
        """Check if a transcript entry has already been processed.

        Args:
            entry: The transcript entry to check

        Returns:
            True if already processed, False otherwise
        """
        if not self._state:
            return False

        return entry.entry_id in self._state.processed_entries

    def mark_processed(self, entry: TranscriptEntry) -> None:
        """Mark a transcript entry as processed.

        Args:
            entry: The transcript entry to mark as processed
        """
        if not self._state:
            return

        self._state.processed_entries.add(entry.entry_id)
        self._state.session_checkpoints[entry.session_id] = max(
            self._state.session_checkpoints.get(entry.session_id, 0),
            entry.timestamp
        )
        self._state.total_processed += 1

    def get_session_checkpoint(self, session_id: str) -> float:
        """Get the last processed timestamp for a session.

        Args:
            session_id: The session identifier

        Returns:
            Last processed timestamp for the session (0 if none)
        """
        if not self._state:
            return 0.0

        return self._state.session_checkpoints.get(session_id, 0.0)

    def get_unprocessed_entries(self, entries: List[TranscriptEntry]) -> List[TranscriptEntry]:
        """Filter out already processed entries.

        Args:
            entries: List of transcript entries to filter

        Returns:
            List of unprocessed entries only
        """
        return [entry for entry in entries if not self.is_processed(entry)]

    def validate_entry_uniqueness(self, entries: List[TranscriptEntry]) -> Dict[str, List[str]]:
        """Validate that entries have unique IDs.

        Args:
            entries: List of transcript entries to validate

        Returns:
            Dictionary with 'duplicates' and 'valid' lists of entry IDs
        """
        seen_ids: Set[str] = set()
        duplicates: List[str] = []
        valid: List[str] = []

        for entry in entries:
            if entry.entry_id in seen_ids:
                duplicates.append(entry.entry_id)
            else:
                seen_ids.add(entry.entry_id)
                valid.append(entry.entry_id)

        return {
            "duplicates": duplicates,
            "valid": valid
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get checkpoint statistics.

        Returns:
            Dictionary with checkpoint statistics
        """
        if not self._state:
            return {}

        return {
            "total_processed": self._state.total_processed,
            "unique_sessions": len(self._state.session_checkpoints),
            "last_updated": datetime.fromtimestamp(self._state.last_updated).isoformat(),
            "checkpoint_file": str(self.checkpoint_file),
            "version": self._state.version
        }

    def reset_checkpoint(self) -> bool:
        """Reset checkpoint state (clear all processed entries).

        Returns:
            True if reset successfully, False otherwise
        """
        self._state = CheckpointState(
            last_updated=time.time(),
            processed_entries=set(),
            session_checkpoints={},
            total_processed=0
        )
        return self.save_checkpoint()

    def cleanup_old_entries(self, max_age_days: int = 30) -> int:
        """Remove checkpoint entries older than max_age_days.

        Args:
            max_age_days: Maximum age in days to keep entries

        Returns:
            Number of entries removed
        """
        if not self._state:
            return 0

        cutoff_time = time.time() - (max_age_days * 24 * 3600)
        initial_count = len(self._state.processed_entries)

        # For now, we only track IDs, not timestamps of individual entries
        # This is a simplified cleanup that clears session checkpoints
        old_sessions = [
            session_id for session_id, timestamp
            in self._state.session_checkpoints.items()
            if timestamp < cutoff_time
        ]

        for session_id in old_sessions:
            del self._state.session_checkpoints[session_id]

        # Note: We keep processed_entries since we don't have individual timestamps
        # This ensures we don't reprocess entries even after cleanup

        return len(old_sessions)


class TranscriptProcessor:
    """High-level processor for transcript entries with checkpoint management."""

    def __init__(self, checkpoint_manager: Optional[CheckpointManager] = None):
        """Initialize transcript processor.

        Args:
            checkpoint_manager: Optional checkpoint manager. Creates default if None.
        """
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()

    def process_entries(self, entries: List[TranscriptEntry], processor_func) -> Dict[str, Any]:
        """Process transcript entries with checkpoint tracking.

        Args:
            entries: List of transcript entries to process
            processor_func: Function to process each entry. Should accept TranscriptEntry and return result.

        Returns:
            Dictionary with processing results and statistics
        """
        # Validate entry uniqueness
        validation = self.checkpoint_manager.validate_entry_uniqueness(entries)
        if validation["duplicates"]:
            print(f"Warning: Found {len(validation['duplicates'])} duplicate entry IDs")

        # Filter unprocessed entries
        unprocessed = self.checkpoint_manager.get_unprocessed_entries(entries)

        results = {
            "total_entries": len(entries),
            "already_processed": len(entries) - len(unprocessed),
            "newly_processed": 0,
            "processing_results": [],
            "errors": []
        }

        # Process each unprocessed entry
        for entry in unprocessed:
            try:
                # Call the processor function
                result = processor_func(entry)

                # Mark as processed
                self.checkpoint_manager.mark_processed(entry)

                results["processing_results"].append({
                    "entry_id": entry.entry_id,
                    "result": result,
                    "timestamp": entry.timestamp
                })
                results["newly_processed"] += 1

            except Exception as e:
                results["errors"].append({
                    "entry_id": entry.entry_id,
                    "error": str(e),
                    "timestamp": entry.timestamp
                })

        # Save checkpoint
        self.checkpoint_manager.save_checkpoint()

        return results


# Utility functions for easy access
def create_transcript_entry(agent_type: str, content: str, session_id: str,
                          task_id: Optional[str] = None) -> TranscriptEntry:
    """Create a transcript entry with automatic timestamp and ID generation.

    Args:
        agent_type: Type of agent that generated the content
        content: The transcript content
        session_id: Session identifier
        task_id: Optional task identifier

    Returns:
        New TranscriptEntry instance
    """
    return TranscriptEntry(
        entry_id="",  # Will be auto-generated
        timestamp=time.time(),
        agent_type=agent_type,
        content=content,
        session_id=session_id,
        task_id=task_id
    )


def get_checkpoint_manager() -> CheckpointManager:
    """Get the default checkpoint manager instance."""
    return CheckpointManager()


# Export key classes and functions
__all__ = [
    'TranscriptEntry',
    'CheckpointState',
    'CheckpointManager',
    'TranscriptProcessor',
    'create_transcript_entry',
    'get_checkpoint_manager'
]