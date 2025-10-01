#!/usr/bin/env python3
import json

session_file = '/home/randy/.claude/projects/-home-randy-repos-claude-mcp/55653782-179a-4cf2-b63f-1ba698038628.jsonl'

# Find the branching point and its children
target_parent = '912ed541-911e-49f3-9f99-498d91173ebe'
target_children = ['b0f4c02a-4bd4-4ebf-b241-9a2c5189a204', '4ecae0b8-b237-4de2-ad59-4b5d333dddc5']

messages = {}

with open(session_file) as f:
    for line in f:
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry.get('uuid') in [target_parent] + target_children:
            messages[entry['uuid']] = entry

print("=" * 80)
print("PARENT MESSAGE:")
print("=" * 80)
parent = messages[target_parent]
print(f"UUID: {parent['uuid']}")
print(f"Type: {parent['type']}")
print(f"Timestamp: {parent['timestamp']}")
if parent['type'] == 'assistant':
    content = parent.get('message', {}).get('content', [])
    for block in content:
        if block.get('type') == 'text':
            text = block.get('text', '')[:200]
            print(f"Text: {text}...")

print("\n" + "=" * 80)
print("CHILD 1:")
print("=" * 80)
child1 = messages[target_children[0]]
print(f"UUID: {child1['uuid']}")
print(f"Type: {child1['type']}")
print(f"Timestamp: {child1['timestamp']}")
print(f"Is Sidechain: {child1.get('isSidechain', False)}")
if child1['type'] == 'user':
    msg = child1.get('message', {})
    content = msg.get('content', '')
    if isinstance(content, str):
        print(f"Content: {content}")

print("\n" + "=" * 80)
print("CHILD 2:")
print("=" * 80)
child2 = messages[target_children[1]]
print(f"UUID: {child2['uuid']}")
print(f"Type: {child2['type']}")
print(f"Timestamp: {child2['timestamp']}")
print(f"Is Sidechain: {child2.get('isSidechain', False)}")
if child2['type'] == 'user':
    msg = child2.get('message', {})
    content = msg.get('content', '')
    if isinstance(content, str):
        print(f"Content: {content}")

# Now trace forward from each child to see where they go
print("\n" + "=" * 80)
print("TRACING BRANCHES FORWARD:")
print("=" * 80)

# Build full message map
all_messages = {}
with open(session_file) as f:
    for line in f:
        if not line.strip():
            continue
        entry = json.loads(line)
        if 'uuid' in entry:  # Skip entries without UUIDs
            all_messages[entry['uuid']] = entry

def trace_branch(start_uuid, depth=5):
    """Trace conversation branch forward."""
    messages_in_branch = []

    # Find all children of this start point
    current = start_uuid
    for _ in range(depth):
        # Find next message with this as parent
        next_msg = None
        for uuid, msg in all_messages.items():
            if msg.get('parentUuid') == current:
                next_msg = (uuid, msg)
                break

        if not next_msg:
            break

        uuid, msg = next_msg
        current = uuid

        msg_type = msg['type']
        is_sidechain = msg.get('isSidechain', False)

        if msg_type == 'user':
            content = msg.get('message', {}).get('content', '')
            if isinstance(content, str):
                text = content[:80]
            else:
                text = "[tool result]"
        elif msg_type == 'assistant':
            blocks = msg.get('message', {}).get('content', [])
            text_blocks = [b.get('text', '') for b in blocks if b.get('type') == 'text']
            text = ' '.join(text_blocks)[:80] if text_blocks else "[no text]"
        else:
            text = f"[{msg_type}]"

        messages_in_branch.append({
            'uuid': uuid,
            'type': msg_type,
            'sidechain': is_sidechain,
            'text': text
        })

    return messages_in_branch

print("\nBRANCH 1 (from first child):")
branch1 = trace_branch(target_children[0])
for i, msg in enumerate(branch1, 1):
    print(f"  {i}. [{msg['type']}] (sidechain={msg['sidechain']}): {msg['text']}")

print("\nBRANCH 2 (from second child):")
branch2 = trace_branch(target_children[1])
for i, msg in enumerate(branch2, 1):
    print(f"  {i}. [{msg['type']}] (sidechain={msg['sidechain']}): {msg['text']}")
