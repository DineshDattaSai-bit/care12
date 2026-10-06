import urllib.request
import os

filepath = 'standalone_prototype.html'
filesize = os.path.getsize(filepath)
print(f'File size: {filesize} bytes')

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
with open(filepath, 'rb') as f:
    file_bytes = f.read()

body = bytearray()
body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="reqtype"\r\n\r\nfileupload\r\n'.encode('utf-8'))
body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="fileToUpload"; filename="Quantique_5G_Prototype.html"\r\nContent-Type: text/html\r\n\r\n'.encode('utf-8'))
body.extend(file_bytes)
body.extend(f'\r\n--{boundary}--\r\n'.encode('utf-8'))

req = urllib.request.Request('https://catbox.moe/user/api.php', data=bytes(body), headers={
    'Content-Type': f'multipart/form-data; boundary={boundary}',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
})

try:
    with urllib.request.urlopen(req, timeout=30) as res:
        catbox_url = res.read().decode('utf-8').strip()
        print('Catbox Upload URL:', catbox_url)
        # Test with GPTBot user agent
        gpt_req = urllib.request.Request(catbox_url, headers={'User-Agent': 'Mozilla/5.0 (compatible; GPTBot/1.0; +https://openai.com/gptbot)'})
        with urllib.request.urlopen(gpt_req, timeout=10) as gpt_res:
            print('GPTBot fetch status:', gpt_res.status, 'Content-Length:', len(gpt_res.read()))
except Exception as e:
    print('Catbox error:', e)
