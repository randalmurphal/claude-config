#!/usr/bin/env python3
import json
from collections import defaultdict

# Track parent relationships
messages_by_uuid = {}
children = defaultdict(list)

with open('/home/randy/.claude/projects/-home-randy-repos-claude-mcp/55653782-179a-4cf2-b63f-1ba698038628.jsonl') as f:
    for line in f:
        if not line.strip():
            continue
        
        entry = json.loads(line)
        entry_type = entry.get('type')
        
        if entry_type in ['user', 'assistant']:
            uuid = entry.get('uuid')
            parent = entry.get('parentUuid')
            is_sidechain = entry.get('isSidechain', False)
            
            messages_by_uuid[uuid] = {
                'type': entry_type,
                'parent': parent,
                'sidechain': is_sidechain,
                'timestamp': entry.get('timestamp')
            }
            
            if parent:
                children[parent].append(uuid)

# Find branching points (messages with multiple children)
print("BRANCHING ANALYSIS")
print("=" * 80)

branches = {parent: kids for parent, kids in children.items() if len(kids) > 1}

if branches:
    print(f"\nFound {len(branches)} branching points:")
    for parent, kids in list(branches.items())[:5]:
        print(f"\nParent: {parent}")
        print(f"  Type: {messages_by_uuid[parent]['type']}")
        print(f"  Timestamp: {messages_by_uuid[parent]['timestamp']}")
        print(f"  Children ({len(kids)}):")
        for kid in kids:
            info = messages_by_uuid[kid]
            print(f"    - {kid} ({info['type']}, sidechain={info['sidechain']})")
else:
    print("\nNo branching points found in this session")

# Check for sidechains
sidechains = [uuid for uuid, info in messages_by_uuid.items() if info['sidechain']]
print(f"\n\nSIDECHAIN MESSAGES: {len(sidechains)}")
if sidechains:
    for uuid in sidechains[:5]:
        info = messages_by_uuid[uuid]
        print(f"  - {uuid} ({info['type']}, parent={info['parent']})")

# Show message chain structure
print(f"\n\nTOTAL MESSAGES: {len(messages_by_uuid)}")
print(f"Messages with parents: {sum(1 for m in messages_by_uuid.values() if m['parent'])}")
print(f"Root messages (no parent): {sum(1 for m in messages_by_uuid.values() if not m['parent'])}")

# Check last few messages for recent activity
print("\n\nLAST 5 MESSAGES:")
sorted_msgs = sorted(messages_by_uuid.items(), key=lambda x: x[1]['timestamp'])[-5:]
for uuid, info in sorted_msgs:
    print(f"{info['timestamp']}: {info['type']} (sidechain={info['sidechain']})")
