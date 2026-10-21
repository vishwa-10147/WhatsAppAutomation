with open('backend/app/api/routes/workflows.py', 'rb') as f:
    content = f.read()
    idx = content.find(b'for w in workflows')
    # Print each character
    for i, b in enumerate(content[idx:idx+80]):
        ch = chr(b) if 32 <= b < 127 else f'\\x{b:02x}'
        print(f'{i}: {ch}')