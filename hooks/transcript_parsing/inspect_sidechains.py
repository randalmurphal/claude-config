#!/usr/bin/env python3
import json

session_file = '/home/randy/.claude/projects/-home-randy-repos-claude-mcp/55653782-179a-4cf2-b63f-1ba698038628.jsonl'

# Find all sidechain messages
sidechains = []
all_messages = {}

with open(session_file) as f:
    for line in f:
        if not line.strip():
            continue
        entry = json.loads(line)

        if 'uuid' not in entry:
            continue

        all_messages[entry['uuid']] = entry

        if entry.get('isSidechain', False):
            sidechains.append(entry)

print(f"Found {len(sidechains)} sidechain messages")
print("\n" + "=" * 80)

# Find sidechain roots (sidechains with no parent or parent not in sidechains)
sidechain_uuids = {s['uuid'] for s in sidechains}
sidechain_roots = []

for sc in sidechains:
    parent = sc.get('parentUuid')
    if not parent:  # No parent = root
        sidechain_roots.append(sc)
    elif parent not in sidechain_uuids:  # Parent is NOT a sidechain = branch point
        sidechain_roots.append(sc)

print(f"Found {len(sidechain_roots)} sidechain roots (entry points)")
print("=" * 80)

for i, root in enumerate(sidechain_roots[:5], 1):
    print(f"\nSIDECHAIN ROOT {i}:")
    print(f"  UUID: {root['uuid']}")
    print(f"  Type: {root['type']}")
    print(f"  Timestamp: {root['timestamp']}")
    print(f"  Parent UUID: {root.get('parentUuid', 'None')}")

    if root['type'] == 'user':
        msg = root.get('message', {})
        content = msg.get('content', '')
        if isinstance(content, str):
            print(f"  User content: {content[:100]}")
    elif root['type'] == 'assistant':
        blocks = root.get('message', {}).get('content', [])
        text_blocks = [b.get('text', '') for b in blocks if b.get('type') == 'text']
        if text_blocks:
            text = ' '.join(text_blocks)[:100]
            print(f"  Assistant text: {text}")

    # Trace this sidechain forward a bit
    print("  Chain length: ", end='')
    current = root['uuid']
    chain_length = 1
    for _ in range(20):
        next_uuid = None
        for uuid, msg in all_messages.items():
            if msg.get('parentUuid') == current and msg.get('isSidechain', False):
                next_uuid = uuid
                current = uuid
                chain_length += 1
                break
        if not next_uuid:
            break
    print(chain_length)

    # If parent exists and is NOT sidechain, show what it is
    parent_uuid = root.get('parentUuid')
    if parent_uuid and parent_uuid in all_messages:
        parent = all_messages[parent_uuid]
        if not parent.get('isSidechain', False):
            print("  Branched from main conversation:")
            print(f"    Parent type: {parent['type']}")
            print(f"    Parent time: {parent['timestamp']}")
