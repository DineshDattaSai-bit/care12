import json

log_path = r'C:\Users\Gouri\.gemini\antigravity\brain\1a7dd439-d611-4f1b-8464-9880a06c51b1\.system_generated\logs\transcript_full.jsonl'
with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for i in range(2443, min(2608, len(lines))):
    try:
        obj = json.loads(lines[i])
        for tc in obj.get('tool_calls', []):
            args = tc.get('args', {})
            desc = args.get('Description', '')
            inst = args.get('Instruction', '')
            tf = args.get('TargetFile', '')
            print(f"Step {i}: {tc['name']} - {tf.split('/')[-1].split(chr(92))[-1]} : {desc}")
    except Exception as e:
        pass
