import re, os, io, json, time, sys
import requests

UA_OLD = 'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-GB; rv:1.8.1.18) Gecko/20081029 Firefox/2.0.0.18'
UA_NEW = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

SITES = [
    ("Tr-Kalite18", "kalite18.net", "https://www.kalite18.net/",
     r'<article[^>]*class="loop-video[^"]*"[^>]*>\s*<a href="([^"]+)" title="([^"]*)"[^>]*>.{0,900}?<img[^>]*data-src="([^"]+)"',
     "url|title|icon", "%s"),
    ("Tr-Maheir", "maheir.com", "https://maheir.com/",
     r'<a class="clip-link"[^>]*title="([^"]+)"[^>]*href="([^"]+)"[^>]*>\s*<span class="clip">\s*<img src="([^"]+)"',
     "title|url|icon", "%s"),
    ("Tr-Hdabla", "hdabla.net", "https://hdabla.net/",
     r'<a class="clip-link"[^>]*title="([^"]+)"[^>]*href="([^"]+)"[^>]*>\s*<span class="clip">\s*<img src="([^"]+)"',
     "title|url|icon", "%s"),
    ("Tr-Pornoanne", "pornoanne.com", "https://pornoanne.com/",
     r'<a class="clip-link"[^>]*href="([^"]+)"[^>]*>\s*<span class="clip">.{0,1200}?<img[^>]*src="(https?://[^"]+)"[^>]*alt="([^"]*)"',
     "url|icon|title", "%s"),
    ("Tr-Doeda", "doeda.com", "https://www.doeda.com/",
     r'<a class="clip-link"[^>]*title="([^"]+)"[^>]*href="([^"]+)"[^>]*>\s*<span class="clip">\s*<img src="([^"]+)"',
     "title|url|icon", "%s"),
    ("Tr-Evooli", "evooli.com", "https://www.evooli.com/",
     r'<a class="clip-link"[^>]*title="([^"]+)"[^>]*href="([^"]+)"[^>]*>\s*<span class="clip">\s*<img[^>]*data-lazy-src="([^"]+)"',
     "title|url|icon", "%s"),
    ("Tr-7Dak", "7dak.com", "http://7dak.com/",
     r'<article class="videoitem">\s*<a href="([^"]+)"[^>]*><img src="([^"]+)" alt="([^"]*)"',
     "url|icon|title", "http://7dak.com%s"),
    ("Tr-Roxporno", "roxporno.com", "https://roxporno.com/",
     r'<a data-id="\d+" href="([^"]+)" rel="bookmark">.{0,700}?<img[^>]*src="(https?://[^"]+)"[^>]*alt="([^"]*)"',
     "url|icon|title", "%s"),
]

def fetch(session, url, ua, referer=None, timeout=25):
    h = {"User-Agent": ua}
    if referer:
        h["Referer"] = referer
    try:
        r = session.get(url, headers=h, timeout=timeout, allow_redirects=True)
        return r
    except Exception as e:
        return e

def classify(text, marker):
    if not isinstance(text, str):
        return "ERROR"
    low = text.lower()
    if len(text) < 600:
        return "TINY"
    if "erisime_engellenmis" in low or "aidiyet.esb.org.tr" in low:
        return "BTK-BLOCK"
    if "just a moment" in low or "<title>just a moment" in low or "challenge-platform" in low and "cf_chl" in low:
        return "CF-CHALLENGE"
    if marker.search(text):
        return "LIST"
    return "NO-MATCH"

def resolve(contents, base, depth=0):
    def absolute(url, base):
        url = url.strip()
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("http://") or url.startswith("https://"):
            return url
        m = re.match(r"(https?://[^/]+)", base or "")
        if url.startswith("/"):
            return (m.group(1) if m else "") + url
        m2 = re.match(r"(https?://.+/)[^/]*$", base or "")
        if m2:
            return m2.group(1) + url
        return (m.group(1) + "/" + url) if m else url

    text = contents.replace("\\/", "/")
    def structured(t):
        for p in [r'''(?:contentUrl|embedUrl)\s*:\s*["']([^"']+?\.(?:mp4|m3u8)[^"']*)''',
                  r'''(?:file|src|source|video_url|videourl|video|url)\s*[:=]\s*['"]([^'"]+?\.m3u8[^'"]*)''',
                  r'''(?:file|src|source|video_url|videourl|video|url)\s*[:=]\s*['"]([^'"]+?\.mp4[^'"]*)''',
                  r'''<source[^>]+src\s*=\s*["']([^"']+?\.(?:mp4|m3u8)[^'"]*)''',
                  r'''<video[^>]+src\s*=\s*["']([^"']+?\.(?:mp4|m3u8)[^'"]*)''']:
            m = re.search(p, t, re.I | re.S)
            if m:
                return m.group(1).replace("\\/", "/")
        return ""
    def any_media(t):
        m = re.search(r'''https?://[^"'\s<>\\]+?\.(?:m3u8|mp4)[^"'\s<>\\]*''', t, re.I | re.S)
        return m.group(0) if m else ""
    def frames(t, b):
        out = []
        for tag in re.findall(r'(?is)<iframe\b[^>]*>', t):
            for attr in ("data-litespeed-src", "data-src", "data-original", "src"):
                m = re.search(r'(?i)(?:^|\s)' + attr + r'\s*=\s*["\']([^"\']+)["\']', tag)
                if m and not m.group(1).lower().startswith(("about:", "data:", "javascript:")):
                    out.append(absolute(m.group(1), b))
                    break
        return out
    m = structured(text)
    if m:
        return absolute(m, base), "structured"
    if depth < 2:
        for f in frames(text, base):
            try:
                r = requests.get(f, headers={"User-Agent": UA_OLD, "Referer": base}, timeout=20)
                got, how = resolve(r.text, f, depth + 1)
                if got:
                    return got, how + " via iframe " + f
            except Exception:
                pass
    m = any_media(text)
    if m:
        return absolute(m, base), "any"
    return "", ""

summary = {}
for title, host, url, pattern, order, urlbuild in SITES:
    key = host
    s = requests.Session()
    info = {"title": title, "url": url}
    # special: 7dak cookie gate
    if host == "7dak.com":
        try:
            r = s.get(url, headers={"User-Agent": UA_OLD}, timeout=20)
            m = re.search(r'document\.cookie="sto-idd=([^";]+)', r.text or "")
            if m:
                s.cookies.set("sto-idd", m.group(1))
                r = s.get(url, headers={"User-Agent": UA_OLD}, timeout=20)
                info["cookie_gate"] = m.group(1)
        except Exception as e:
            r = e
    else:
        r = fetch(s, url, UA_OLD)

    if isinstance(r, Exception):
        info["status"] = "EXC"
        info["error"] = str(r)[:200]
        summary[key] = info
        print(json.dumps(info, ensure_ascii=False), flush=True)
        continue

    text = r.text
    marker = re.compile(pattern, re.I | re.S | re.M)
    info["http"] = r.status_code
    info["size"] = len(text)
    info["final_url"] = r.url
    info["class"] = classify(text, marker)
    matches = marker.findall(text)
    info["items"] = len(matches)
    info["cf_ray"] = r.headers.get("cf-ray", "")
    info["server"] = r.headers.get("server", "")
    if matches:
        names = order.split("|")
        first = dict(zip(names, list(matches[0]) if isinstance(matches[0], tuple) else [matches[0]]))
        vurl = urlbuild % first["url"]
        info["first"] = first.get("title", "")[:80]
        info["video_url"] = vurl
        try:
            vr = s.get(vurl, headers={"User-Agent": UA_OLD, "Referer": url}, timeout=25)
            info["video_http"] = vr.status_code
            info["video_size"] = len(vr.text)
            media, how = resolve(vr.text, vurl)
            info["media"] = media
            info["resolve_via"] = how
            if media:
                try:
                    hr = s.get(media, headers={"User-Agent": UA_OLD, "Referer": vurl, "Range": "bytes=0-4095"}, timeout=25)
                    info["media_http"] = hr.status_code
                    info["media_ct"] = hr.headers.get("content-type", "")
                    info["media_magic"] = hr.content[:8].hex()
                    info["media_len"] = len(hr.content)
                except Exception as e:
                    info["media_error"] = str(e)[:150]
        except Exception as e:
            info["video_error"] = str(e)[:150]
    summary[key] = info
    print(json.dumps(info, ensure_ascii=False), flush=True)

print("SUMMARY_JSON=" + json.dumps(summary, ensure_ascii=False), flush=True)
