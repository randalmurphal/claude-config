#!/usr/bin/env python3
"""
ascii-fix: Fix alignment in ASCII art diagrams within markdown files.

Fixes:
  - Box border width consistency (all rows match the widest)
  - Content padding within boxes (right edge aligned)
  - Markdown table column alignment
  - Trailing whitespace removal

Creates a .bak backup by default before modifying files.
"""

import argparse
import difflib
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════════
# Data types
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class Box:
    """A detected box region in ASCII art."""

    start: int  # line index of top border (within the code block's inner lines)
    end: int  # line index of bottom border
    col: int  # column of left edge
    width: int  # width of top border (left corner to right corner inclusive)
    style: str  # 'unicode' or 'ascii'


@dataclass
class Stats:
    """Counts of fixes applied."""

    boxes_fixed: int = 0
    tables_fixed: int = 0
    whitespace_lines: int = 0

    @property
    def total(self):
        return self.boxes_fixed + self.tables_fixed + self.whitespace_lines


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(
        prog="ascii-fix",
        description="Fix alignment in ASCII art diagrams within markdown files",
    )
    parser.add_argument("files", nargs="+", metavar="FILE")
    parser.add_argument(
        "--no-backup", action="store_true", help="Skip .bak backup creation"
    )
    parser.add_argument(
        "--diff", action="store_true", help="Print unified diff, don't modify"
    )
    parser.add_argument(
        "--check", action="store_true", help="Exit 1 if changes needed, don't modify"
    )
    args = parser.parse_args()

    exit_code = 0
    for filepath in args.files:
        path = Path(filepath)
        if not path.exists():
            print(f"error: {filepath} not found", file=sys.stderr)
            exit_code = 1
            continue

        original = path.read_text()
        fixed, stats = fix_content(original)

        if original == fixed:
            print(f"{filepath}: no changes needed")
            continue

        if args.check:
            print(f"{filepath}: {stats.total} fixes needed")
            exit_code = 1
            continue

        if args.diff:
            _show_diff(original, fixed, filepath)
            continue

        if not args.no_backup:
            bak = path.with_suffix(path.suffix + ".bak")
            shutil.copy2(path, bak)
            print(f"  backup: {bak}")

        path.write_text(fixed)
        parts = []
        if stats.boxes_fixed:
            parts.append(f"{stats.boxes_fixed} boxes")
        if stats.tables_fixed:
            parts.append(f"{stats.tables_fixed} tables")
        if stats.whitespace_lines:
            parts.append(f"{stats.whitespace_lines} lines trimmed")
        print(f"{filepath}: fixed ({', '.join(parts)})")

    sys.exit(exit_code)


# ═══════════════════════════════════════════════════════════════════════════
# Content pipeline
# ═══════════════════════════════════════════════════════════════════════════


def fix_content(content: str) -> tuple[str, Stats]:
    """Apply all alignment fixes to markdown content."""
    stats = Stats()
    lines = content.split("\n")

    # Phase 1: trailing whitespace
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if stripped != line:
            stats.whitespace_lines += 1
            lines[i] = stripped

    # Phase 2: process sections (code blocks get box fixes, rest gets table fixes)
    result = []
    for is_code, section in _iter_sections(lines):
        if is_code:
            fixed, n = _fix_code_block(section)
            stats.boxes_fixed += n
            result.extend(fixed)
        else:
            fixed, n = _fix_tables_in_section(section)
            stats.tables_fixed += n
            result.extend(fixed)

    return "\n".join(result), stats


def _iter_sections(lines):
    """Split lines into (is_code_block, section_lines) chunks.

    Code blocks are fenced with ``` or ~~~. The fence lines are included
    in the code block section.
    """
    sections = []
    current = []
    in_code = False
    fence_char = None

    for line in lines:
        if not in_code:
            m = re.match(r"^(\s*)(```|~~~)", line)
            if m:
                # Entering a code block
                if current:
                    sections.append((False, current))
                current = [line]
                in_code = True
                fence_char = m.group(2)
            else:
                current.append(line)
        else:
            current.append(line)
            # Check for closing fence (same char, at least as many)
            if re.match(r"^\s*" + re.escape(fence_char) + r"\s*$", line):
                sections.append((True, current))
                current = []
                in_code = False
                fence_char = None

    if current:
        sections.append((in_code, current))

    return sections


# ═══════════════════════════════════════════════════════════════════════════
# Box detection
# ═══════════════════════════════════════════════════════════════════════════


def _detect_boxes(lines: list[str]) -> list[Box]:
    """Find all box structures in a list of lines."""
    boxes = []
    # Track which (line, col) positions are already claimed by a box
    used: set[tuple[int, int]] = set()

    for i, line in enumerate(lines):
        # Unicode box tops: ┌─...─┐ (with optional ┬ junctions)
        for m in re.finditer(r"┌[─┬]+┐", line):
            col = m.start()
            if (i, col) in used:
                continue
            box = _scan_box(lines, i, col, m.end() - m.start(), "unicode")
            if box and box.end - box.start >= 1:
                boxes.append(box)
                for j in range(box.start, box.end + 1):
                    used.add((j, col))

        # ASCII box tops: +--...--+ (with optional + junctions)
        for m in re.finditer(r"\+[-+]+\+", line):
            col = m.start()
            if (i, col) in used:
                continue
            box = _scan_box(lines, i, col, m.end() - m.start(), "ascii")
            if box and box.end - box.start >= 1:
                boxes.append(box)
                for j in range(box.start, box.end + 1):
                    used.add((j, col))

    return boxes


def _scan_box(
    lines: list[str], start: int, col: int, width: int, style: str
) -> Box | None:
    """Scan downward from a top border to find the complete box.

    Validates both left AND right edges on every line to avoid extending
    through content that merely happens to have a box char at the left column.
    """
    if style == "unicode":
        body_left = set("│├└")
        body_right = set("│┤┘")
        border_left = set("├└")
        border_right = set("┤┘")
    else:
        body_left = set("|+")
        body_right = set("|+")
        border_left = set("+")
        border_right = set("+")

    expected_right = col + width - 1
    last_bottom = None

    for j in range(start + 1, min(start + 300, len(lines))):
        line = lines[j]
        if col >= len(line):
            break

        left_char = line[col]
        if left_char not in body_left:
            break

        # Verify right edge exists near expected position (±3 tolerance)
        right_found = False
        for offset in range(0, 4):
            for pos in [expected_right + offset, expected_right - offset]:
                if col < pos < len(line) and line[pos] in body_right:
                    right_found = True
                    break
            if right_found:
                break

        if not right_found:
            break  # no matching right edge — this line isn't part of the box

        if style == "unicode":
            if left_char == "└":
                last_bottom = j
                break  # definitive bottom for unicode
            # │ and ├ → keep scanning
        else:
            # ASCII: + could be divider or bottom, keep scanning
            if left_char == "+":
                last_bottom = j
            # | → keep scanning

    if last_bottom is not None:
        return Box(start, last_bottom, col, width, style)
    return None


# ═══════════════════════════════════════════════════════════════════════════
# Box normalization
# ═══════════════════════════════════════════════════════════════════════════


def _fix_code_block(lines: list[str]) -> tuple[list[str], int]:
    """Fix boxes inside a fenced code block.

    Uses multi-pass processing with simultaneous line modification:
    1. Each pass detects boxes, selects the innermost level, and fixes them
    2. Inner box fixes cascade outward (fixing an inner box may correct
       the outer box's body width, eliminating the outer misalignment)
    3. Repeats until no more changes (max 4 passes to prevent loops)

    Within each pass, all fixes on a given line are computed from the
    original line positions and assembled simultaneously. This preserves
    gaps between side-by-side boxes.

    lines[0] is the opening fence, lines[-1] is the closing fence.
    """
    if len(lines) < 3:
        return lines, 0

    fence_top = lines[0]
    fence_bot = lines[-1]
    inner = list(lines[1:-1])

    total_fixed = 0

    for _ in range(4):
        boxes = _detect_boxes(inner)
        if not boxes:
            break

        # Select innermost boxes (those with no children).
        # Fixing these first corrects cascading misalignments before
        # we process their parent boxes.
        processable = _get_innermost(boxes)

        # Compute target width for each box.
        # The border width (from the top border) is the anchor, but if
        # any body line has content that can't fit within the border
        # width (even after stripping trailing whitespace), the border
        # expands to accommodate. This prevents cascading expansion
        # where fixing an inner box shifts content and causes the outer
        # box to grow unnecessarily.
        targets: dict[int, int] = {}
        for idx, box in enumerate(processable):
            targets[idx] = _compute_target(inner, box)

        fixed_count = _apply_fixes(inner, processable, targets)
        if fixed_count == 0:
            break
        total_fixed += fixed_count

    return [fence_top] + inner + [fence_bot], total_fixed


def _get_innermost(boxes: list[Box]) -> list[Box]:
    """Select boxes that contain no other boxes (leaf nodes).

    These are the innermost boxes and should be fixed first so that
    cascading misalignments are corrected from the inside out.
    """
    innermost = []
    for i, box in enumerate(boxes):
        has_child = False
        for j, other in enumerate(boxes):
            if i != j and _is_nested(other, box):
                has_child = True
                break
        if not has_child:
            innermost.append(box)
    return innermost


def _compute_target(lines: list[str], box: Box) -> int:
    """Compute the target width for a box.

    Uses the border width as the anchor. Only expands beyond the border
    if actual content (ignoring trailing whitespace) requires more space.
    This prevents cascading expansion: inner box fixes that add whitespace
    to outer box lines won't cause the outer box to grow.
    """
    border_width = box.width
    right_chars = _right_edge_chars(box.style)

    # Find the minimum width needed to contain all body content
    content_min = 0
    for i in range(box.start + 1, box.end):
        if _is_border_start(lines[i], box.col, box.style):
            continue
        right_pos = _find_right_edge(lines[i], box.col, box.width, right_chars)
        if right_pos is None:
            continue
        inner_content = lines[i][box.col + 1 : right_pos].rstrip()
        content_min = max(content_min, len(inner_content) + 2)

    return max(border_width, content_min)


def _is_nested(inner: Box, outer: Box) -> bool:
    """Check if inner box is geometrically contained within outer box."""
    return (
        inner.col > outer.col
        and inner.start >= outer.start
        and inner.end <= outer.end
        and inner.col + inner.width <= outer.col + outer.width
    )


def _apply_fixes(
    lines: list[str], boxes: list[Box], targets: dict[int, int]
) -> int:
    """Apply all box fixes simultaneously, preserving inter-box spacing.

    For each line, finds all boxes that touch it, computes their fixed
    segments from the original line positions, then assembles the new
    line in one pass. Gaps between boxes come from the original line,
    so side-by-side spacing is always preserved.
    """
    boxes_changed: set[int] = set()

    for line_idx in range(len(lines)):
        # Find all boxes that include this line
        affecting: list[tuple[int, Box]] = []
        for box_idx, box in enumerate(boxes):
            if box.start <= line_idx <= box.end:
                affecting.append((box_idx, box))

        if not affecting:
            continue

        # Sort by column position (left to right)
        affecting.sort(key=lambda x: x[1].col)

        # Build new line from segments: each box contributes a fixed segment,
        # and the gaps between boxes come directly from the original line.
        old_line = lines[line_idx]
        segments: list[str] = []
        last_end = 0

        for box_idx, box in affecting:
            target = targets[box_idx]
            right_chars = _right_edge_chars(box.style)

            # Find current right edge using the box's detected width
            right_pos = _find_right_edge(
                old_line, box.col, box.width, right_chars
            )
            if right_pos is None:
                continue

            # Skip if this box overlaps with a previously processed box.
            # This handles false-positive detections (e.g., ASCII arrows
            # like +--+---+--> that match the box regex) and nested boxes
            # that weren't filtered because their edges slightly exceed
            # the parent's detected border width.
            if box.col < last_end:
                continue

            # Preserve gap from last segment end to this box's left edge
            segments.append(old_line[last_end : box.col])

            # Build the fixed segment for this box on this line
            fixed_seg = _build_segment(
                old_line, box.col, right_pos, target, box.style
            )
            original_seg = old_line[box.col : right_pos + 1]

            if fixed_seg != original_seg:
                boxes_changed.add(box_idx)

            segments.append(fixed_seg)
            last_end = right_pos + 1

        # Trailing content after the last box
        segments.append(old_line[last_end:])

        new_line = "".join(segments)
        if new_line != old_line:
            lines[line_idx] = new_line

    return len(boxes_changed)


def _build_segment(
    line: str, col: int, right_pos: int, target_width: int, style: str
) -> str:
    """Build a fixed segment for one box on one line.

    Takes the original line, the current left/right edge positions,
    and the target width. Returns the fixed segment (left edge +
    inner content + right edge).
    """
    left_char = line[col]
    inner = line[col + 1 : right_pos]
    right_char = line[right_pos]

    inner_target = target_width - 2
    current_inner = len(inner)

    if current_inner == inner_target:
        return line[col : right_pos + 1]

    is_border = _is_border_start(line, col, style)
    fill = "─" if style == "unicode" else "-"

    if is_border:
        diff = inner_target - current_inner
        if diff > 0:
            inner = inner + fill * diff
        elif diff < 0:
            # Remove fill chars from end, preserving junctions
            inner_list = list(inner)
            to_remove = -diff
            removed = 0
            for p in range(len(inner_list) - 1, -1, -1):
                if inner_list[p] == fill and removed < to_remove:
                    inner_list.pop(p)
                    removed += 1
            inner = "".join(inner_list)
            if len(inner) > inner_target:
                inner = inner[:inner_target]
    else:
        diff = inner_target - current_inner
        if diff > 0:
            inner = inner + " " * diff
        elif diff < 0:
            stripped = inner.rstrip()
            if len(stripped) <= inner_target:
                inner = stripped + " " * (inner_target - len(stripped))
            else:
                inner = inner[:inner_target]

    return left_char + inner + right_char


def _measure_row(line: str, col: int, approx_width: int, style: str) -> int:
    """Measure the actual width of a box row (left edge to right edge inclusive).

    Returns 0 if no right edge is found within tolerance, indicating this line
    should be skipped during normalization.
    """
    if col >= len(line):
        return 0

    right_chars = _right_edge_chars(style)
    expected = col + approx_width - 1

    # Tight search: only ±5 from expected position
    for offset in range(0, 6):
        for pos in [expected + offset, expected - offset]:
            if col < pos < len(line) and line[pos] in right_chars:
                return pos - col + 1

    # No right edge found nearby — skip this line
    return 0


def _right_edge_chars(style: str) -> set[str]:
    """Characters that can be a box's right edge."""
    if style == "unicode":
        return set("┐┘┤│")
    return set("|+")


def _is_border_start(line: str, col: int, style: str) -> bool:
    """Check if position col starts a horizontal border line."""
    if col >= len(line):
        return False
    char = line[col]
    next_char = line[col + 1] if col + 1 < len(line) else ""
    if style == "unicode":
        return char in "┌└├" and next_char in "─┬┴┼"
    return char == "+" and next_char in "-+"


def _find_right_edge(
    line: str, col: int, target_width: int, right_chars: set[str]
) -> int | None:
    """Find the right edge character of a box row.

    Uses tight tolerance (±5 chars) to avoid picking up characters from
    adjacent or nested structures.
    """
    expected = col + target_width - 1

    # Tight search: only ±5 from expected position
    for offset in range(0, 6):
        for pos in [expected + offset, expected - offset]:
            if col < pos < len(line) and line[pos] in right_chars:
                return pos

    # No fallback — if we can't find it nearby, this line doesn't match
    return None


# ═══════════════════════════════════════════════════════════════════════════
# Markdown table alignment
# ═══════════════════════════════════════════════════════════════════════════


def _fix_tables_in_section(lines: list[str]) -> tuple[list[str], int]:
    """Fix markdown table alignment in non-code sections."""
    result = []
    i = 0
    fixed_count = 0

    while i < len(lines):
        if _is_table_row(lines[i]):
            table = []
            while i < len(lines) and _is_table_row(lines[i]):
                table.append(lines[i])
                i += 1

            if len(table) >= 2:
                fixed = _align_table(table)
                if fixed != table:
                    fixed_count += 1
                result.extend(fixed)
            else:
                result.extend(table)
        else:
            result.append(lines[i])
            i += 1

    return result, fixed_count


def _is_table_row(line: str) -> bool:
    """Check if a line looks like a markdown table row."""
    stripped = line.strip()
    return (
        stripped.startswith("|")
        and stripped.endswith("|")
        and stripped.count("|") >= 3
    )


def _align_table(table_lines: list[str]) -> list[str]:
    """Align columns in a markdown table."""
    # Detect leading indent
    m = re.match(r"^(\s*)", table_lines[0])
    indent = m.group(1) if m else ""

    # Parse each row into cells
    rows = []
    for line in table_lines:
        raw = line.strip()
        # Strip outer pipes
        if raw.startswith("|"):
            raw = raw[1:]
        if raw.endswith("|"):
            raw = raw[:-1]
        cells = [c.strip() for c in raw.split("|")]
        rows.append(cells)

    if not rows:
        return table_lines

    num_cols = max(len(r) for r in rows)

    # Calculate column widths (ignore separator rows)
    col_widths = [0] * num_cols
    for row in rows:
        for j, cell in enumerate(row):
            if j < num_cols:
                is_sep = "-" in cell and set(cell) <= set("-: ")
                if not is_sep:
                    col_widths[j] = max(col_widths[j], len(cell))

    # Minimum width for readability
    col_widths = [max(w, 3) for w in col_widths]

    # Rebuild rows
    result = []
    for row in rows:
        parts = []
        for j in range(num_cols):
            cell = row[j] if j < len(row) else ""
            width = col_widths[j]

            is_sep = "-" in cell and set(cell) <= set("-: ")

            if is_sep:
                if cell.startswith(":") and cell.endswith(":"):
                    parts.append(":" + "-" * (width - 2) + ":")
                elif cell.startswith(":"):
                    parts.append(":" + "-" * (width - 1))
                elif cell.endswith(":"):
                    parts.append("-" * (width - 1) + ":")
                else:
                    parts.append("-" * width)
            else:
                parts.append(cell.ljust(width))

        result.append(indent + "| " + " | ".join(parts) + " |")

    return result


# ═══════════════════════════════════════════════════════════════════════════
# Diff output
# ═══════════════════════════════════════════════════════════════════════════


def _show_diff(original: str, fixed: str, filepath: str):
    """Print a unified diff."""
    orig_lines = original.splitlines(keepends=True)
    fix_lines = fixed.splitlines(keepends=True)
    diff = difflib.unified_diff(
        orig_lines,
        fix_lines,
        fromfile=f"{filepath} (original)",
        tofile=f"{filepath} (fixed)",
    )
    sys.stdout.writelines(diff)


if __name__ == "__main__":
    main()
