import urllib.request
import urllib.parse
import http.cookiejar
import re

cj = http.cookiejar.CookieJar()
o = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

h1 = o.open('http://127.0.0.1:8000/admin/login/?next=/admin/').read().decode()
m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', h1)
csrf = m.group(1)

data = urllib.parse.urlencode({
    'csrfmiddlewaretoken': csrf,
    'username': 'admin',
    'password': 'admin123',
    'next': '/admin/'
}).encode()

req = urllib.request.Request('http://127.0.0.1:8000/admin/login/?next=/admin/', data=data)
o.open(req)  # login

try:
    h2 = o.open('http://127.0.0.1:8000/admin/').read().decode()
    print("SUCCESS", len(h2))
    print(h2[:500])
except Exception as e:
    print("ERROR", e)
