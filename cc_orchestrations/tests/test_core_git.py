"""Unit tests for cc_orchestrations.core.git.

Tests git utilities for orchestration workflows.
"""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from cc_orchestrations.core.git import (
    get_conduct_commits,
    git_commit,
    git_has_changes,
    git_log_since,
    git_show_commit,
    git_stage_all,
)


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repository."""
    repo = tmp_path / 'repo'
    repo.mkdir()

    subprocess.run(['git', 'init'], cwd=repo, capture_output=True, check=True)
    subprocess.run(
        ['git', 'config', 'user.email', 'test@test.com'],
        cwd=repo,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ['git', 'config', 'user.name', 'Test User'],
        cwd=repo,
        capture_output=True,
        check=True,
    )

    # Create initial commit
    (repo / 'README.md').write_text('# Test Repo')
    subprocess.run(
        ['git', 'add', '.'], cwd=repo, capture_output=True, check=True
    )
    subprocess.run(
        ['git', 'commit', '-m', 'Initial commit'],
        cwd=repo,
        capture_output=True,
        check=True,
    )

    return repo


class TestGitHasChanges:
    """Tests for git_has_changes function."""

    def test_no_changes(self, git_repo: Path):
        """Test when there are no changes."""
        assert git_has_changes(git_repo) is False

    def test_unstaged_changes(self, git_repo: Path):
        """Test with unstaged changes."""
        (git_repo / 'new_file.txt').write_text('new content')
        assert git_has_changes(git_repo) is True

    def test_staged_changes(self, git_repo: Path):
        """Test with staged changes."""
        (git_repo / 'new_file.txt').write_text('new content')
        subprocess.run(
            ['git', 'add', 'new_file.txt'],
            cwd=git_repo,
            capture_output=True,
            check=True,
        )
        assert git_has_changes(git_repo) is True

    def test_modified_file(self, git_repo: Path):
        """Test with modified existing file."""
        (git_repo / 'README.md').write_text('# Modified')
        assert git_has_changes(git_repo) is True

    def test_not_a_git_repo(self, tmp_path: Path):
        """Test with non-git directory."""
        # Should return False (not raise)
        result = git_has_changes(tmp_path)
        assert result is False


class TestGitStageAll:
    """Tests for git_stage_all function."""

    def test_stage_new_file(self, git_repo: Path):
        """Test staging a new file."""
        (git_repo / 'new_file.txt').write_text('content')

        result = git_stage_all(git_repo)

        assert result is True

        # Verify file is staged
        status = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=git_repo,
            capture_output=True,
            text=True,
            check=True,
        )
        assert 'A  new_file.txt' in status.stdout

    def test_stage_multiple_files(self, git_repo: Path):
        """Test staging multiple files."""
        (git_repo / 'file1.txt').write_text('content1')
        (git_repo / 'file2.txt').write_text('content2')

        result = git_stage_all(git_repo)

        assert result is True

    def test_stage_nothing(self, git_repo: Path):
        """Test staging when nothing to stage."""
        result = git_stage_all(git_repo)
        assert result is True  # Should succeed even with nothing to stage


class TestGitCommit:
    """Tests for git_commit function."""

    def test_commit_with_changes(self, git_repo: Path):
        """Test creating a commit with changes."""
        (git_repo / 'new_file.txt').write_text('content')

        commit_hash = git_commit(
            git_repo,
            phase='skeleton',
            component='my_component.py',
        )

        assert commit_hash is not None
        assert len(commit_hash) == 7  # Short hash

        # Verify commit message
        log = subprocess.run(
            ['git', 'log', '-1', '--format=%s'],
            cwd=git_repo,
            capture_output=True,
            text=True,
            check=True,
        )
        assert '[conduct] skeleton: my_component.py' in log.stdout

    def test_commit_no_changes(self, git_repo: Path):
        """Test commit when nothing to commit."""
        commit_hash = git_commit(git_repo, phase='test')
        assert commit_hash is None

    def test_commit_with_message(self, git_repo: Path):
        """Test commit with custom message."""
        (git_repo / 'file.txt').write_text('content')

        commit_hash = git_commit(
            git_repo,
            phase='validation',
            message='All tests pass',
        )

        assert commit_hash is not None

        log = subprocess.run(
            ['git', 'log', '-1', '--format=%s'],
            cwd=git_repo,
            capture_output=True,
            text=True,
            check=True,
        )
        assert '[conduct] validation: All tests pass' in log.stdout

    def test_commit_draft_mode(self, git_repo: Path):
        """Test commit in draft mode."""
        (git_repo / 'draft.txt').write_text('draft content')

        commit_hash = git_commit(
            git_repo,
            phase='skeleton',
            component='draft.py',
            draft_mode=True,
        )

        assert commit_hash is not None

        log = subprocess.run(
            ['git', 'log', '-1', '--format=%s'],
            cwd=git_repo,
            capture_output=True,
            text=True,
            check=True,
        )
        assert '[DRAFT] [conduct] skeleton: draft.py' in log.stdout

    def test_commit_phase_only(self, git_repo: Path):
        """Test commit with phase only (no component or message)."""
        (git_repo / 'file.txt').write_text('content')

        commit_hash = git_commit(git_repo, phase='complete')

        assert commit_hash is not None

        log = subprocess.run(
            ['git', 'log', '-1', '--format=%s'],
            cwd=git_repo,
            capture_output=True,
            text=True,
            check=True,
        )
        assert '[conduct] complete: complete' in log.stdout


class TestGitLogSince:
    """Tests for git_log_since function."""

    def test_get_recent_commits(self, git_repo: Path):
        """Test getting recent commits."""
        # Create some commits
        for i in range(3):
            (git_repo / f'file{i}.txt').write_text(f'content{i}')
            subprocess.run(
                ['git', 'add', '.'], cwd=git_repo, capture_output=True
            )
            subprocess.run(
                ['git', 'commit', '-m', f'Commit {i}'],
                cwd=git_repo,
                capture_output=True,
            )

        commits = git_log_since(git_repo)

        assert len(commits) >= 3
        assert any('Commit 0' in c for c in commits)
        assert any('Commit 2' in c for c in commits)

    def test_get_commits_since(self, git_repo: Path):
        """Test getting commits since a specific commit."""
        # Get initial commit hash
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=git_repo,
            capture_output=True,
            text=True,
            check=True,
        )
        initial_hash = result.stdout.strip()

        # Create more commits
        for i in range(2):
            (git_repo / f'file{i}.txt').write_text(f'content{i}')
            subprocess.run(
                ['git', 'add', '.'], cwd=git_repo, capture_output=True
            )
            subprocess.run(
                ['git', 'commit', '-m', f'New commit {i}'],
                cwd=git_repo,
                capture_output=True,
            )

        commits = git_log_since(git_repo, since_commit=initial_hash)

        assert len(commits) == 2
        assert all('New commit' in c for c in commits)

    def test_custom_format(self, git_repo: Path):
        """Test with custom format string."""
        commits = git_log_since(git_repo, format_str='%h')

        # Should just be short hashes
        assert all(len(c) == 7 for c in commits)


class TestGitShowCommit:
    """Tests for git_show_commit function."""

    def test_show_commit(self, git_repo: Path):
        """Test getting commit details."""
        # Create a commit
        (git_repo / 'feature.py').write_text('def feature(): pass')
        subprocess.run(['git', 'add', '.'], cwd=git_repo, capture_output=True)
        subprocess.run(
            ['git', 'commit', '-m', 'Add feature'],
            cwd=git_repo,
            capture_output=True,
        )

        # Get commit hash
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=git_repo,
            capture_output=True,
            text=True,
            check=True,
        )
        commit_hash = result.stdout.strip()

        details = git_show_commit(git_repo, commit_hash)

        assert 'message' in details
        assert 'files' in details
        assert 'diff' in details
        assert 'Add feature' in details['message']
        assert 'feature.py' in details['files']

    def test_show_invalid_commit(self, git_repo: Path):
        """Test with invalid commit hash."""
        details = git_show_commit(git_repo, 'invalid123')

        # Should return empty dict without raising
        assert details['message'] == ''


class TestGetConductCommits:
    """Tests for get_conduct_commits function."""

    def test_parse_conduct_commits(self, git_repo: Path):
        """Test parsing [conduct] commits."""
        # Create conduct-style commits
        (git_repo / 'skeleton.py').write_text('# skeleton')
        subprocess.run(['git', 'add', '.'], cwd=git_repo, capture_output=True)
        subprocess.run(
            ['git', 'commit', '-m', '[conduct] skeleton: component_a.py'],
            cwd=git_repo,
            capture_output=True,
        )

        (git_repo / 'impl.py').write_text('# impl')
        subprocess.run(['git', 'add', '.'], cwd=git_repo, capture_output=True)
        subprocess.run(
            ['git', 'commit', '-m', '[conduct] implementation: component_a.py'],
            cwd=git_repo,
            capture_output=True,
        )

        commits = get_conduct_commits(git_repo)

        assert len(commits) >= 2
        phases = [c['phase'] for c in commits]
        assert 'skeleton' in phases
        assert 'implementation' in phases

    def test_parse_draft_commits(self, git_repo: Path):
        """Test parsing [DRAFT] [conduct] commits."""
        (git_repo / 'draft.py').write_text('# draft')
        subprocess.run(['git', 'add', '.'], cwd=git_repo, capture_output=True)
        subprocess.run(
            ['git', 'commit', '-m', '[DRAFT] [conduct] skeleton: draft.py'],
            cwd=git_repo,
            capture_output=True,
        )

        commits = get_conduct_commits(git_repo)

        draft_commits = [c for c in commits if c['draft']]
        assert len(draft_commits) >= 1
        assert draft_commits[0]['phase'] == 'skeleton'
        assert draft_commits[0]['component'] == 'draft.py'

    def test_ignores_non_conduct_commits(self, git_repo: Path):
        """Test that non-conduct commits are ignored."""
        (git_repo / 'regular.py').write_text('# regular')
        subprocess.run(['git', 'add', '.'], cwd=git_repo, capture_output=True)
        subprocess.run(
            ['git', 'commit', '-m', 'Regular commit'],
            cwd=git_repo,
            capture_output=True,
        )

        commits = get_conduct_commits(git_repo)

        assert all('conduct' in c['message'] for c in commits)


class TestMockedGitOperations:
    """Tests using mocks for edge cases."""

    def test_git_has_changes_handles_error(self, tmp_path: Path):
        """Test git_has_changes handles subprocess errors."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'git')

            result = git_has_changes(tmp_path)

            assert result is False

    def test_git_stage_all_handles_error(self, tmp_path: Path):
        """Test git_stage_all handles errors."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'git')

            result = git_stage_all(tmp_path)

            assert result is False

    def test_git_log_handles_error(self, tmp_path: Path):
        """Test git_log_since handles errors."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'git')

            result = git_log_since(tmp_path)

            assert result == []
