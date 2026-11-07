#!/usr/bin/env python3
"""JunLin｜AI 個人網站產生器
用法：python3 build.py
讀取 content/pages、content/posts 的 .md，輸出完整靜態網站到 docs/（GitHub Pages 發佈這個資料夾）。
新增文章：在 content/posts 放一個 .md（照現有檔案的開頭格式），重新執行 build.py。
"""
import html, json, os, re, shutil, urllib.parse
from pathlib import Path
import markdown

ROOT = Path(__file__).parent
SRC = ROOT / "content"
OUT = ROOT / "docs"
SITE = "https://1123junlin.com"
NAME = "JunLin｜AI"
PERSON = "賴俊燐"
EMAIL = "oth.1123junlin@gmail.com"
DESC = "分享 AI 應用，協助個人與企業善用科技提升效率、打造品牌，推動數位轉型"
SOCIAL = [
    ("Instagram", "https://www.instagram.com/lailai.rex/"),
    ("Facebook", "https://www.facebook.com/lai.ting.hao.857999/"),
    ("LinkedIn", "https://www.linkedin.com/in/jun-lin-lai-8775a9169/"),
    ("Threads", "https://www.threads.com/@lailai.rex"),
    ("X", "https://x.com/rexlai1123"),
    ("ORCID", "https://orcid.org/0009-0005-0464-6276"),
]
NAV = [("關於我", "/about/"), ("服務", "/services/"), ("作品", "/portfolio/"),
       ("活動足跡", "/activities/"), ("訪談", "/interview/"), ("文章", "/blog/"),
       ("常見問題", "/faq/"), ("聯絡", "/#contact")]
PAGE_ORDER = ["about", "services", "portfolio", "activities", "interview", "faq"]
PORTRAIT = "/images/2026/07/20260711-ljl.png"

# ---------- 讀取 ----------
def parse(path):
    raw = path.read_text(encoding="utf-8")
    meta, body = {}, raw
    if raw.startswith("---"):
        _, fm, body = raw.split("---", 2)
        for line in fm.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    return meta, body.strip()

posts = []
for p in sorted((SRC / "posts").glob("*.md")):
    m, b = parse(p)
    d = m["date"][:10]
    y, mo, da = d.split("-")
    m["path"] = f"/{y}/{mo}/{da}/{m['slug']}/"
    m["d"] = d
    m["file"] = p.name
    m["body"] = b
    posts.append(m)
posts.sort(key=lambda x: x["date"], reverse=True)

pages = {}
for p in (SRC / "pages").glob("*.md"):
    m, b = parse(p)
    m["file"] = p.name
    m["body"] = b
    m["path"] = "/" if p.stem == "index" else f"/{p.stem}/"
    pages[p.stem] = m

LINKMAP = {x["file"]: x["path"] for x in posts}
LINKMAP.update({x["file"]: x["path"] for x in pages.values()})

# ---------- Markdown → HTML ----------
YT = re.compile(r'<p><a href="https://www\.youtube\.com/(watch\?v=|shorts/)([\w-]+)">([^<]*)</a></p>')

def yt_embed(m):
    short = m.group(1) == "shorts/"
    vid, title = m.group(2), html.escape(html.unescape(m.group(3)), quote=True)
    cls = "video short" if short else "video"
    return (f'<div class="{cls}"><iframe src="https://www.youtube-nocookie.com/embed/{vid}" '
            f'title="{title}" loading="lazy" allow="accelerometer; encrypted-media; gyroscope; picture-in-picture; web-share" '
            f'allowfullscreen></iframe></div>')

YT_ITEM = re.compile(r'<li><a href="https://www\.youtube\.com/(watch\?v=|shorts/)([\w-]+)">([^<]*)</a></li>')
YT_LIST = re.compile(r'<ul>\s*(?:<li><a href="https://www\.youtube\.com/(?:watch\?v=|shorts/)[\w-]+">[^<]*</a></li>\s*)+</ul>')

def yt_grid(m):
    items = []
    for it in YT_ITEM.finditer(m.group(0)):
        frame = yt_embed(it).replace('<div class="video short">', '<div class="video short">', 1)
        items.append(f'<figure>{frame}<figcaption>{it.group(3)}</figcaption></figure>')
    return f'<div class="video-grid">{"".join(items)}</div>'

def md(text):
    h = markdown.markdown(text, extensions=["tables", "sane_lists"])
    h = re.sub(r'<!--.*?-->', '', h, flags=re.S)
    def fix(m):
        href = m.group(1)
        if href.endswith(".md"):
            return f'href="{LINKMAP.get(os.path.basename(href), href)}"'
        return m.group(0)
    h = re.sub(r'href="([^"]+)"', fix, h)
    h = YT_LIST.sub(yt_grid, h)
    h = YT.sub(yt_embed, h)
    h = re.sub(r'href="(https?://(?!1123junlin\.com)[^"]+)"', r'href="\1" target="_blank" rel="noopener"', h)
    h = h.replace("<img ", '<img loading="lazy" decoding="async" ')
    return h

def first_img(text):
    m = re.search(r'!\[[^\]]*\]\((/images/[^)\s]+)\)', text)
    return m.group(1) if m else None

def esc(s):
    return html.escape(s, quote=True)

def zh_date(d):
    y, m, dd = d.split("-")
    return f"{y}年{int(m)}月{int(dd)}日"

# ---------- 版型 ----------
def layout(title, desc, body, path, ld=None, image=None, og_type="website"):
    full = f"{title}｜{NAME}" if title != NAME else NAME
    img = SITE + (image or PORTRAIT)
    nav = "".join(
        f'<li><a href="{u}"{" aria-current=page" if u != "/#contact" and (path == u or (u == "/blog/" and re.match(r"^/\d{4}/", path))) else ""}>{n}</a></li>'
        for n, u in NAV)
    lds = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld or []))
    year = posts[0]["d"][:4] if posts else "2026"
    return f"""<!doctype html>
<html lang="zh-Hant-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(full)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:image" content="{img}">
<meta property="og:locale" content="zh_TW">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&family=Noto+Serif+TC:wght@500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/style.css">
{lds}
</head>
<body>
<a class="skip" href="#main">跳到主要內容</a>
<header class="site-head"><div class="wrap">
<a class="brand" href="/">JunLin<span>｜AI</span></a>
<nav class="nav-desk" aria-label="主選單"><ul>{nav}</ul></nav>
<details class="nav"><summary class="nav-toggle">選單</summary><ul>{nav}</ul></details>
</div></header>
<main id="main">
{body}
</main>
<footer class="site-foot"><div class="wrap">
<div><strong>{PERSON}（JunLin）</strong><br>白袍人生學院特助兼 AI 應用師<br><a href="mailto:{EMAIL}">{EMAIL}</a></div>
<ul>{"".join(f'<li><a href="{u}" target="_blank" rel="noopener">{n}</a></li>' for n, u in SOCIAL)}</ul>
<div>© {year} {PERSON}</div>
</div></footer>
</body>
</html>
"""

PERSON_LD = {
    "@context": "https://schema.org", "@type": "Person", "@id": SITE + "/#person",
    "name": PERSON, "alternateName": ["JunLin", "Jun-Lin Lai"], "url": SITE + "/about/",
    "image": SITE + PORTRAIT, "email": "mailto:" + EMAIL, "jobTitle": "特助兼AI應用師",
    "worksFor": {"@type": "Organization", "name": "白袍人生學院", "url": "https://course.ent33ent.com/"},
    "knowsAbout": ["AI應用規劃", "生成式AI", "工作流程自動化", "課程規劃與執行", "網站維護", "SEO", "AIEO", "數位轉型"],
    "knowsLanguage": "zh-TW", "sameAs": [u for _, u in SOCIAL],
}

def write(path, content):
    f = OUT / path.strip("/") / "index.html" if not path.endswith(".html") else OUT / path.strip("/")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(content, encoding="utf-8")

# ---------- 首頁 ----------
def post_card(p):
    img = p.get("featured_image", "").replace("https://1123junlin.com/wp-content/uploads/", "/images/") or first_img(p["body"])
    ph = (f'<div class="ph"><img src="{img}" alt="" loading="lazy" decoding="async"></div>' if img
          else f'<div class="ph noimg">{esc(p.get("category",""))}</div>')
    return f'<a class="card" href="{p["path"]}">{ph}<span class="d">{zh_date(p["d"])}</span><h3>{esc(p["title"])}</h3></a>'

def home():
    pillars = [
        ("分享", "Share", "透過演講、授課、訪談，分享創業觀點與 AI 應用。", "/images/2026/07/service-01.png"),
        ("建構", "Build", "依需求開發 AI 與自動化流程，提升團隊效率。", "/images/2026/07/service-02-3.png"),
        ("優化", "Optimize", "從網站架構、內容規劃，優化搜尋能見度與使用者體驗。", "/images/2026/07/service-03.png"),
        ("轉型", "Transform", "協助企業導入 AI，建立數位工作模式。", "/images/2026/07/service-04-1-1.png"),
    ]
    timeline = [
        ("2026.10.18", "台灣醫用雷射光電學會秋季年會", "以非醫師身分參與，記錄 AI 時代的數位護城河", "/2026/10/21/taiwan-medical-laser-photonics-society-2026/"),
        ("2026.09.12", "TEDxRenaiRoad 2026", "以工作人員身分參與第三屆大會", "/2026/09/12/tedx-renairoad-2026-volunteer-reflection/"),
        ("2026.09.05", "來日方腸醫學研討會", "從篝火計畫 09 聚走到台南的跨界學習", "/2026/09/06/campfire-09-colorectal-health-2026/"),
        ("2026.07.03", "AllPlayer Studio", "訪談華書基金會執行長", "/interview/"),
        ("2026.06.27", "白袍人生學院 2026 高峰年會", "共學共好的醫師社群年會", "/2026/06/27/dr-hao-summit-2026/"),
        ("2026.06.26", "AI 課程教學", "強化服務業人才韌性計畫：AI 新品需求預測與上市策略", "/activities/"),
        ("2026.05.09", "大專生涯發展協會", "2026 志工大會", "/activities/"),
    ]
    interviews = [
        ("#022", "HOOTERS TAIWAN二代&老撈麻辣鍋共同創辦人-劉昶志"),
        ("#021", "長穩社福慈善基金會執行長 – Sigrid"),
        ("#020", "嗜甜咖啡烘焙所負責人-林哲正"),
    ]
    routes = [
        ("想邀請演講、課程或訪談", "AI 應用講座、課程規劃與節目訪談，來信附上主題、對象、時間與形式。", "看服務項目", "/services/"),
        ("想把 AI 導入工作流程", "從日常行政到團隊流程，找出能交給 AI 與自動化的環節。", "看作品", "/portfolio/"),
        ("想讓網站被搜尋與 AI 讀懂", "網站架構、內容規劃與結構化資料，提升 SEO 與 AIEO。", "看常見問題", "/faq/"),
    ]
    body = f"""
<section class="hero"><div class="wrap">
  <div>
    <p class="hero-name">賴俊燐　JunLin</p>
    <h1>把 AI 落地，<br>變成真正能用的工具</h1>
    <p class="lead">現職白袍人生學院特助兼 AI 應用師，曾任財團法人工業技術研究院課程規劃管理師。專注於 AI 應用規劃、課程執行、網站維護與行政流程優化。</p>
    <ul class="creds">
      <li>白袍人生學院　特助兼 AI 應用師</li>
      <li>前 工研院　課程規劃管理師</li>
      <li>AllPlayer Studio　品牌主持</li>
    </ul>
    <div class="btns"><a class="btn btn-main" href="#contact">聯絡合作</a><a class="btn btn-ghost" href="/about/">認識 JunLin</a></div>
  </div>
  <div class="hero-visual">
    <p class="tate" aria-hidden="true">交流合作，說不定會有些火花</p>
    <figure><img src="{PORTRAIT}" alt="賴俊燐（JunLin）個人照" fetchpriority="high"></figure>
  </div>
</div></section>

<section class="sec"><div class="wrap">
  <div class="sec-head"><div><h2>四大服務</h2><p>從分享觀念到實際落地，陪個人與企業走完 AI 導入的每一步。</p></div><a class="more" href="/services/">服務項目</a></div>
  <div class="pillars">{"".join(f'<div class="pillar"><img src="{i}" alt="" loading="lazy"><h3>{t}</h3><p class="en">{e}</p><p>{d}</p></div>' for t,e,d,i in pillars)}</div>
</div></section>

<section class="sec tint"><div class="wrap">
  <div class="sec-head"><div><h2>精選影片</h2><p>2026 明志科大「強化服務業人才韌性計畫」課程紀錄</p></div></div>
  <div class="video"><iframe src="https://www.youtube-nocookie.com/embed/kMBMhw4O6xs" title="2026 明志科大強化服務業人才韌性計畫課程紀錄" loading="lazy" allow="accelerometer; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div>
</div></section>

<section class="sec"><div class="wrap">
  <div class="sec-head"><div><h2>活動足跡</h2><p>參與、主持與服務過的課程和活動。</p></div><a class="more" href="/activities/">全部活動</a></div>
  <ol class="timeline">{"".join(f'<li><time>{d}</time><div><h3><a href="{u}">{esc(t)}</a></h3><p>{esc(s)}</p></div></li>' for d,t,s,u in timeline)}</ol>
</div></section>

<section class="sec"><div class="wrap">
  <div class="sec-head"><div><h2>最新文章</h2><p>課程心得、活動記錄與 AI 應用的觀察。</p></div><a class="more" href="/blog/">全部文章</a></div>
  <div class="cards">{"".join(post_card(p) for p in posts[:6])}</div>
</div></section>

<section class="sec tint"><div class="wrap">
  <div class="sec-head"><div><h2>訪談節目</h2><p>AllPlayer Studio 品牌主持，與各領域經營者對談。</p></div><a class="more" href="/interview/">全部訪談</a></div>
  <ul class="plain">{"".join(f'<li><a href="/interview/"><span class="d">SalesWhat {n}</span><span class="t">{esc(t)}</span></a></li>' for n,t in interviews)}</ul>
</div></section>

<section class="sec"><div class="wrap">
  <div class="sec-head"><div><h2>從這裡開始</h2><p>依你的需求，找到合適的合作方式。</p></div></div>
  <div class="routes">{"".join(f'<a class="route" href="{u}"><h3>{t}</h3><p>{d}</p><span class="go">{g}</span></a>' for t,d,g,u in routes)}</div>
</div></section>

<section class="sec tint" id="contact"><div class="wrap contact">
  <div class="sec-head"><div><h2>聯絡我</h2><p>如果您想上節目接受訪談、討論 AI 應用開發、邀約講座課程，歡迎來信。</p></div></div>
  <a class="mail" href="mailto:{EMAIL}">{EMAIL}</a>
  <ul class="social">{"".join(f'<li><a href="{u}" target="_blank" rel="noopener">{n}</a></li>' for n,u in SOCIAL)}</ul>
</div></section>
"""
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": NAME, "url": SITE + "/",
           "description": DESC, "inLanguage": "zh-TW", "author": {"@id": SITE + "/#person"}}, PERSON_LD]
    write("/", layout(NAME, DESC, body, "/", ld))

# ---------- 一般頁面 ----------
SERVICES = [
    ("分享", "Share", "分享知識，啟發更多可能", "透過演講、授課、訪談，分享創業觀點與 AI 應用。", "/images/2026/07/service-01.png",
     [("明志科大「強化服務業人才韌性計畫」AI 課程", "/activities/"),
      ("AllPlayer Studio 品牌主持，SalesWhat 訪談節目", "/interview/"),
      ("TEDxRenaiRoad 2026 工作人員", "/2026/09/12/tedx-renairoad-2026-volunteer-reflection/")]),
    ("建構", "Build", "落地真正能解決問題的 AI", "依需求開發 AI、自動化流程，提升團隊效率。", "/images/2026/07/service-02-3.png",
     [("短影音人設測驗工具", "/portfolio/"),
      ("Claude 串 GitHub 投票系統", "/portfolio/"),
      ("AI 自動影音剪輯", "/portfolio/")]),
    ("優化", "Optimize", "讓網站作為成長引擎", "從網站架構、內容規劃，優化搜尋能見度與使用者體驗。", "/images/2026/07/service-03.png",
     [("ITI4 企業內部講師孵化器網站建置", "https://iti4.1123junlin.com"),
      ("SEO 與 AIEO：讓搜尋引擎與 AI 讀懂網站", "/faq/"),
      ("AI 時代的數位護城河課程心得", "/2026/08/30/ai-digital-moat-workshop/")]),
    ("轉型", "Transform", "用科技打造數位轉型", "協助企業導入 AI，建立數位工作模式。", "/images/2026/07/service-04-1-1.png",
     [("白袍人生學院：AI 加速行政效率與課程執行", "/about/"),
      ("從科技業看 Dyson CameraJet：AI 從提醒走向執行", "/2026/09/02/dyson-camerajet-ai-toothbrush/"),
      ("Google 我的商家課程心得", "/2026/07/25/google-business-profile-course-review/")]),
]

def services_page():
    rows = []
    for t, en, tag, d, icon, refs in SERVICES:
        links = "".join(
            f'<li><a href="{u}"{" target=_blank rel=noopener" if u.startswith("http") else ""}>{esc(n)}</a></li>' for n, u in refs)
        rows.append(f"""<section class="svc">
  <div class="svc-mark"><img src="{icon}" alt="" loading="lazy"><p class="svc-name">{t}<span>{en}</span></p></div>
  <div class="svc-body"><h2>{tag}</h2><p>{d}</p></div>
  <div class="svc-refs"><p class="svc-refs-h">做過的事</p><ul>{links}</ul></div>
</section>""")
    body = f"""<div class="wrap">
<header class="page-head"><h1>服務項目</h1>
<p class="page-lead">從分享觀念、動手建構、優化網站到協助轉型，四種合作方式可以單獨進行，也可以一路陪到落地。</p></header>
<div class="svc-list">{"".join(rows)}</div>
<section class="svc-cta">
  <h2>想從哪一項開始？</h2>
  <p>來信簡單說明現況與想解決的問題，我會依實際情況評估可行的合作方式。</p>
  <div class="btns"><a class="btn btn-main" href="mailto:{EMAIL}">寄信討論合作</a><a class="btn btn-ghost" href="/faq/">先看常見問題</a></div>
</section>
</div>"""
    ld = [{"@context": "https://schema.org", "@type": "ProfessionalService", "name": NAME, "url": SITE + "/services/",
           "email": EMAIL, "areaServed": "TW", "founder": {"@id": SITE + "/#person"},
           "hasOfferCatalog": {"@type": "OfferCatalog", "name": "服務項目", "itemListElement": [
               {"@type": "Offer", "itemOffered": {"@type": "Service", "name": f"{t}：{d}"}} for t, _, _, d, _, _ in SERVICES]}}]
    write("/services/", layout("服務", "分享、建構、優化、轉型：AI 應用講座、客製化 AI 與自動化流程、網站 SEO／AIEO 優化、企業 AI 導入。", body, "/services/", ld))

GALLERY = re.compile(r'(?:<p><img [^>]+></p>\s*){2,}')

def gallery(m):
    imgs = re.findall(r'<img [^>]+>', m.group(0))
    return '<div class="gallery">' + "".join(f'<figure>{i}</figure>' for i in imgs) + '</div>'

def page(stem):
    m = pages[stem]
    body_md = re.sub(r'^# .*\n', '', m["body"], count=1)
    wide = " wide" if stem in ("portfolio", "activities") else ""
    body = f"""<div class="wrap{wide}"><header class="page-head"><h1>{esc(m["title"])}</h1></header>
<article class="prose">{GALLERY.sub(gallery, md(body_md)) if stem == "portfolio" else md(body_md)}</article></div>"""
    ld = []
    desc = DESC
    if stem == "about":
        ld = [{"@context": "https://schema.org", "@type": "ProfilePage", "url": SITE + "/about/", "mainEntity": PERSON_LD}]
        desc = "賴俊燐（JunLin），白袍人生學院特助兼AI應用師，協助個人與企業善用AI科技提升效率、打造品牌，推動數位轉型。"
    if stem == "faq":
        qa = re.findall(r'^## (.+?)\n\n(.+?)(?=\n\n## |\Z)', body_md, flags=re.S | re.M)
        ld = [{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q.strip(), "acceptedAnswer": {"@type": "Answer",
             "text": re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', a.strip())}} for q, a in qa]}]
        desc = "關於賴俊燐（JunLin）的背景、服務範圍與合作方式。"
    if stem == "services":
        ld = [{"@context": "https://schema.org", "@type": "ProfessionalService", "name": NAME, "url": SITE + "/services/",
               "email": EMAIL, "areaServed": "TW", "founder": {"@id": SITE + "/#person"}}]
        desc = "分享、建構、優化、轉型：AI 應用講座、客製化 AI 與自動化流程、網站 SEO／AIEO 優化、企業 AI 導入。"
    write(m["path"], layout(m["title"], desc, body, m["path"], ld))

# ---------- 文章 ----------
def post(p):
    feat = p.get("featured_image", "").replace("https://1123junlin.com/wp-content/uploads/", "/images/")
    body = f"""<div class="wrap"><header class="page-head">
<p class="crumb"><a href="/blog/">文章</a></p>
<h1>{esc(p["title"])}</h1>
<p class="meta"><time datetime="{p["date"]}">{zh_date(p["d"])}</time><span class="tag">{esc(p.get("category",""))}</span></p>
</header>
<article class="prose">{md(p["body"])}</article>
<div class="post-foot"><a href="/blog/">回到文章列表</a>　·　作者：<a href="/about/">{PERSON}（JunLin）</a></div></div>"""
    img = feat or first_img(p["body"])
    ld = [{"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"],
           "datePublished": p["date"], "inLanguage": "zh-TW", "url": SITE + p["path"],
           "description": p.get("description", ""), "author": {"@id": SITE + "/#person", "@type": "Person", "name": PERSON},
           "image": SITE + img if img else None, "articleSection": p.get("category", "")}]
    write(p["path"], layout(p["title"], p.get("description", DESC), body, p["path"], ld, img, "article"))

def blog():
    rows, year = [], None
    for p in posts:
        y = p["d"][:4]
        if y != year:
            if year: rows.append("</ul>")
            rows.append(f'<h2 class="year">{y}</h2><ul class="plain">')
            year = y
        rows.append(f'<li><a href="{p["path"]}"><span class="d">{zh_date(p["d"])[5:]}</span>'
                    f'<span class="t"><span class="tag">{esc(p.get("category",""))}</span>{esc(p["title"])}</span></a></li>')
    rows.append("</ul>")
    body = f'<div class="wrap"><header class="page-head"><h1>文章</h1><p class="meta">共 {len(posts)} 篇：活動記錄、知識觀點與生活。</p></header><div style="padding-bottom:80px">{"".join(rows)}</div></div>'
    write("/blog/", layout("文章", "賴俊燐（JunLin）的課程心得、活動記錄與 AI 應用觀察。", body, "/blog/"))

# ---------- 圖片（縮圖壓縮，檔名與路徑不變） ----------
def images():
    from PIL import Image, ImageOps
    src, dst = SRC / "images", OUT / "images"
    for f in src.rglob("*"):
        if not f.is_file() or f.name.startswith("."):
            continue
        t = dst / f.relative_to(src)
        t.parent.mkdir(parents=True, exist_ok=True)
        if t.exists() and t.stat().st_mtime >= f.stat().st_mtime:
            continue
        try:
            im = ImageOps.exif_transpose(Image.open(f))
            if max(im.size) > 1800:
                im.thumbnail((1800, 1800))
            fmt = (im.format or Image.open(f).format or "").upper()
            ext = f.suffix.lower()
            if ext in (".jpg", ".jpeg"):
                im.convert("RGB").save(t, "JPEG", quality=82, optimize=True, progressive=True)
            elif ext == ".png":
                im.save(t, "PNG", optimize=True)
            elif ext == ".webp":
                im.save(t, "WEBP", quality=82)
            else:
                shutil.copy2(f, t)
            if t.stat().st_size > f.stat().st_size:
                shutil.copy2(f, t)
        except Exception:
            shutil.copy2(f, t)

# ---------- 其他 ----------
def extras():
    urls = ["/"] + [pages[s]["path"] for s in PAGE_ORDER] + ["/blog/"] + [p["path"] for p in posts]
    sm = "".join(f"<url><loc>{SITE}{u}</loc></url>" for u in urls)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>', encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    llms = [f"# {NAME}", "", f"> {PERSON}（JunLin）的個人網站。{DESC}。", "",
            "## 頁面"] + [f"- [{pages[s]['title']}]({SITE}{pages[s]['path']})" for s in PAGE_ORDER] + \
           ["", "## 文章"] + [f"- [{p['title']}]({SITE}{p['path']})：{p.get('description','')}" for p in posts]
    (OUT / "llms.txt").write_text("\n".join(llms) + "\n", encoding="utf-8")
    (OUT / "CNAME").write_text("1123junlin.com\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUT / "favicon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="30" fill="#3F7A9B"/><text x="32" y="43" text-anchor="middle" font-family="serif" font-size="30" fill="#fff">俊</text></svg>', encoding="utf-8")
    body = '<div class="wrap"><header class="page-head"><h1>找不到這個頁面</h1><p class="meta">網址可能已經變更。可以從<a href="/">首頁</a>或<a href="/blog/">文章列表</a>找找看。</p></header></div>'
    (OUT / "404.html").write_text(layout("找不到頁面", DESC, body, "/404.html"), encoding="utf-8")
    shutil.copytree(ROOT / "assets", OUT / "assets", dirs_exist_ok=True)

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for f in OUT.iterdir():
        if f.name != "images":
            shutil.rmtree(f) if f.is_dir() else f.unlink()
    home()
    for s in PAGE_ORDER:
        page(s)
    services_page()
    blog()
    for p in posts:
        post(p)
    images()
    extras()
    print(f"完成：首頁、{len(PAGE_ORDER)+1} 個頁面、{len(posts)} 篇文章 → docs/")
