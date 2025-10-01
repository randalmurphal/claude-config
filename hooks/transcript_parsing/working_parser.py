#!/usr/bin/env python3
"""
Working transcript parser - validated approach.
"""
import json
import sys

def parse_message_content(content):
    """Extract text from message content (handles both string and array)."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # Tool results - skip for analysis
        return ""
    return ""

def parse_transcript(jsonl_path):
    """Parse JSONL, extract clean conversation."""
    messages = []

    with open(jsonl_path) as f:
        for line in f:
            if not line.strip():
                continue

            entry = json.loads(line)
            entry_type = entry.get('type')

            if entry_type not in ['user', 'assistant']:
                continue

            if entry_type == 'user':
                text = parse_message_content(entry.get('message', {}).get('content', ''))
                if not text:  # Skip tool results
                    continue

                messages.append({
                    'role': 'user',
                    'text': text,
                    'timestamp': entry.get('timestamp'),
                    'uuid': entry.get('uuid')
                })

            elif entry_type == 'assistant':
                content_blocks = entry.get('message', {}).get('content', [])

                text_parts = []
                tool_uses = []
                thinking = None

                for block in content_blocks:
                    if block.get('type') == 'text':
                        text_parts.append(block.get('text', ''))
                    elif block.get('type') == 'tool_use':
                        tool_uses.append({
                            'name': block.get('name'),
                            'input': block.get('input', {})
                        })
                    elif block.get('type') == 'thinking':
                        thinking = block.get('thinking', '')

                messages.append({
                    'role': 'assistant',
                    'text': '\n'.join(text_parts),
                    'tools': tool_uses,
                    'thinking': thinking,
                    'timestamp': entry.get('timestamp'),
                    'uuid': entry.get('uuid')
                })

    return messages

def detect_corrections(messages):
    """Find correction patterns."""
    corrections = []

    CORRECTION_KW = [
        'no', "don't", 'wrong', 'incorrect', 'fix', 'instead',
        'actually', 'not', "shouldn't", "can't", 'stop'
    ]

    FRUSTRATION_KW = ['i told you', 'again', 'like i said', 'remember', 'third time']

    for i, msg in enumerate(messages):
        if msg['role'] != 'user':
            continue

        text_lower = msg['text'].lower()

        # Check for correction
        if any(kw in text_lower for kw in CORRECTION_KW):
            # Get previous assistant actions (within 3 messages)
            prev_actions = []
            for j in range(max(0, i-3), i):
                if messages[j]['role'] == 'assistant':
                    prev_actions.append({
                        'text': messages[j]['text'][:200],
                        'tools': [t['name'] for t in messages[j]['tools']],
                        'index': j
                    })

            # Frustration score
            frustration = 0.5
            if any(kw in text_lower for kw in FRUSTRATION_KW):
                frustration = 0.9

            corrections.append({
                'user_text': msg['text'],
                'prev_actions': prev_actions,
                'frustration': frustration,
                'timestamp': msg['timestamp'],
                'index': i
            })

    return corrections

def cluster_corrections(corrections):
    """Group similar corrections."""
    # Simple clustering by keyword overlap
    clusters = {}

    for corr in corrections:
        words = set(corr['user_text'].lower().split())

        # Find existing cluster
        found = False
        for cluster_key in clusters:
            cluster_words = set(cluster_key.split('_'))
            # If 40%+ word overlap, same cluster
            overlap = len(words & cluster_words) / max(len(words), len(cluster_words))
            if overlap > 0.4:
                clusters[cluster_key].append(corr)
                found = True
                break

        if not found:
            # New cluster
            key = '_'.join(sorted(words)[:3])  # First 3 words as key
            clusters[key] = [corr]

    # Return only repeated patterns (2+)
    repeated = {k: v for k, v in clusters.items() if len(v) >= 2}
    return repeated

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: working_parser.py <transcript.jsonl>")
        sys.exit(1)

    transcript_path = sys.argv[1]

    print("Parsing transcript...")
    messages = parse_transcript(transcript_path)
    print(f"✓ Extracted {len(messages)} messages")
    print(f"  {sum(1 for m in messages if m['role'] == 'user')} user")
    print(f"  {sum(1 for m in messages if m['role'] == 'assistant')} assistant")

    print("\nDetecting corrections...")
    corrections = detect_corrections(messages)
    print(f"✓ Found {len(corrections)} corrections")

    if corrections:
        print("\nSample corrections:")
        for i, corr in enumerate(corrections[:3], 1):
            print(f"\n{i}. {corr['user_text'][:80]}...")
            print(f"   Frustration: {corr['frustration']}")
            if corr['prev_actions']:
                print(f"   After: {corr['prev_actions'][0]['tools']}")

    print("\nClustering repeated patterns...")
    clusters = cluster_corrections(corrections)
    print(f"✓ Found {len(clusters)} repeated patterns")

    if clusters:
        print("\nRepeated patterns:")
        for pattern, instances in list(clusters.items())[:3]:
            print(f"\n• Pattern (appears {len(instances)}x):")
            for inst in instances[:2]:
                print(f"  - {inst['user_text'][:60]}...")

    # Save results
    output = {
        'messages': messages,
        'corrections': corrections,
        'clusters': {k: v for k, v in clusters.items()}
    }

    with open('/tmp/parsed_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ Saved to /tmp/parsed_results.json")
