import urllib.request
import urllib.parse

content = open('standalone_prototype.html', 'r', encoding='utf-8').read()
data = urllib.parse.urlencode({
    'content': content,
    'title': 'Quantique 5G O-RAN Code',
    'syntax': 'html',
    'expiry_days': 30
}).encode('utf-8')

req = urllib.request.Request('https://dpaste.org/api/', data=data, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as res:
        url = res.read().decode('utf-8').strip().strip('"')
        print('dpaste url:', url)
        raw_url = url + '/raw'
        print('raw url:', raw_url)
        gpt_req = urllib.request.Request(raw_url, headers={'User-Agent': 'Mozilla/5.0 (compatible; GPTBot/1.0; +https://openai.com/gptbot)'})
        with urllib.request.urlopen(gpt_req) as gres:
            print('GPTBot status on dpaste raw:', gres.status, 'size:', len(gres.read()))
except Exception as e:
    print('dpaste error:', e)
