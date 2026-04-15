import argparse
import datetime as dt
import html
import json
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def extract_page_meta(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8", errors="ignore")

    title_match = re.search(r"<title>(.*?)</title>", raw, re.IGNORECASE | re.DOTALL)
    desc_match = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
        raw,
        re.IGNORECASE | re.DOTALL,
    )
    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", raw, re.IGNORECASE | re.DOTALL)
    h2_matches = re.findall(r"<h2[^>]*>(.*?)</h2>", raw, re.IGNORECASE | re.DOTALL)
    robots_match = re.search(
        r'<meta[^>]+name=["\\\']robots["\\\'][^>]+content=["\\\'](.*?)["\\\']',
        raw,
        re.IGNORECASE | re.DOTALL,
    )

    rel = "/" if path.name.lower() == "index.html" else f"/{path.name}"
    title = clean_text(title_match.group(1) if title_match else path.stem)
    description = clean_text(desc_match.group(1) if desc_match else "")
    h1 = clean_text(h1_match.group(1) if h1_match else title)
    h2s = [clean_text(item) for item in h2_matches if clean_text(item)]

    return {
        "path": path.name,
        "rel": rel,
        "title": title,
        "description": description,
        "h1": h1,
        "h2": h2s[:6],
        "noindex": "noindex" in (robots_match.group(1).lower() if robots_match else ""),
    }


def site_url_join(base: str, rel: str) -> str:
    return base.rstrip("/") + rel


def current_git_revision() -> str:
    try:
        rev = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
        return rev
    except Exception:
        return "unknown"


def ensure_indexnow_key(root: Path) -> str:
    key_path = root / "indexnow-key.txt"
    if key_path.exists():
        key = key_path.read_text(encoding="utf-8", errors="ignore").strip()
        if key:
            return key
    key = dt.datetime.utcnow().strftime("%Y%m%d") + "geo" + current_git_revision().replace("unknown", "site")
    key = re.sub(r"[^a-zA-Z0-9]", "", key)[:32]
    key_path.write_text(key, encoding="utf-8")
    return key


def generate_sitemap(root: Path, site_url: str, pages: list[dict]) -> None:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for page in pages:
        lines.append("  <url>")
        lines.append(f"    <loc>{site_url_join(site_url, page['rel'])}</loc>")
        lines.append("  </url>")
    lines.append("</urlset>")
    (root / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_robots(root: Path, site_url: str) -> None:
    robots_path = root / "robots.txt"
    desired_lines = [
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {site_url.rstrip('/')}/sitemap.xml",
    ]
    robots_path.write_text("\n".join(desired_lines) + "\n", encoding="utf-8")


def generate_llms(root: Path, site_url: str, brand: str, summary: str, pages: list[dict]) -> None:
    lines = [
        f"# {brand}",
        "",
        f"> {summary}",
        "",
        "## Canonical Website",
        f"- {site_url.rstrip('/')}/",
        "",
        "## Key Pages",
    ]
    for page in pages:
        line = f"- [{page['title']}]({site_url_join(site_url, page['rel'])})"
        if page["description"]:
            line += f" - {page['description']}"
        lines.append(line)

    lines.extend(
        [
            "",
            "## GEO Signals",
            "- Structured data is available on core pages.",
            "- Sitemap is auto-maintained.",
            "- This site is optimized for answer engines and AI assistants.",
            "",
            "## Contact",
            "- Phone/WeChat: 18125834755",
        ]
    )
    (root / "llms.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    full_lines = [
        f"# {brand} Full Content Map",
        "",
        f"Generated from repository revision: {current_git_revision()}",
        "",
    ]
    for idx, page in enumerate(pages, start=1):
        full_lines.append(f"## {idx}. {page['title']}")
        full_lines.append(f"- URL: {site_url_join(site_url, page['rel'])}")
        full_lines.append(f"- H1: {page['h1']}")
        if page["description"]:
            full_lines.append(f"- Description: {page['description']}")
        if page["h2"]:
            full_lines.append(f"- Main Sections: {' | '.join(page['h2'])}")
        full_lines.append("")

    (root / "llms-full.txt").write_text("\n".join(full_lines), encoding="utf-8")


def generate_geo_feed(root: Path, site_url: str, brand: str, pages: list[dict]) -> None:
    payload = {
        "site": brand,
        "domain": urllib.parse.urlparse(site_url).netloc,
        "revision": current_git_revision(),
        "pages": [
            {
                "title": p["title"],
                "url": site_url_join(site_url, p["rel"]),
                "description": p["description"],
                "h1": p["h1"],
                "sections": p["h2"],
            }
            for p in pages
        ],
    }
    (root / "geo-feed.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ping_bing_sitemap(site_url: str) -> None:
    endpoint = "https://www.bing.com/ping?sitemap=" + urllib.parse.quote(site_url.rstrip("/") + "/sitemap.xml", safe="")
    try:
        urllib.request.urlopen(endpoint, timeout=20)
        print("[ping] Bing sitemap ping success")
    except Exception as exc:
        print(f"[ping] Bing sitemap ping failed: {exc}")


def ping_indexnow(site_url: str, key: str, urls: list[str]) -> None:
    host = urllib.parse.urlparse(site_url).netloc
    body = {
        "host": host,
        "key": key,
        "keyLocation": site_url.rstrip("/") + "/indexnow-key.txt",
        "urlList": urls,
    }
    req = urllib.request.Request(
        url="https://api.indexnow.org/indexnow",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=20)
        print("[ping] IndexNow ping success")
    except urllib.error.HTTPError as exc:
        print(f"[ping] IndexNow ping failed: HTTP {exc.code}")
    except Exception as exc:
        print(f"[ping] IndexNow ping failed: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Automate GEO assets for static websites")
    parser.add_argument("--site-url", required=True)
    parser.add_argument("--brand", required=True)
    parser.add_argument("--summary", default="")
    parser.add_argument("--ping", action="store_true")
    args = parser.parse_args()

    root = Path.cwd()
    pages = []
    for html_file in sorted(root.glob("*.html")):
        if html_file.name.lower() in {"404.html"}:
            continue
        page = extract_page_meta(html_file)
        if page["noindex"]:
            continue
        pages.append(page)

    if not pages:
        raise SystemExit("No html pages found at repository root.")

    summary = args.summary.strip() or f"{args.brand} 的核心页面索引与可抓取摘要。"
    site_url = args.site_url.strip().rstrip("/")

    key = ensure_indexnow_key(root)
    generate_sitemap(root, site_url, pages)
    generate_robots(root, site_url)
    generate_llms(root, site_url, args.brand.strip(), summary, pages)
    generate_geo_feed(root, site_url, args.brand.strip(), pages)

    urls = [site_url_join(site_url, p["rel"]) for p in pages]
    if args.ping:
        ping_bing_sitemap(site_url)
        ping_indexnow(site_url, key, urls)

    print(f"Generated GEO assets for {len(pages)} pages.")


if __name__ == "__main__":
    main()
