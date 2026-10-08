#!/usr/bin/env python3

import argparse
import re
import time
from pathlib import Path
from urllib.parse import urlparse, unquote
import unicodedata

import requests
from playwright.sync_api import sync_playwright

# constants
TIMEOUT_MINUTES = 2

def file_fingerprint(filename: str) -> str:
    p = Path(filename)

    stem = unicodedata.normalize("NFKC", p.stem)
    suffix = unicodedata.normalize("NFKC", p.suffix).lower()

    # Remove trailing " (2)", " (3)", etc.
    stem = re.sub(r"\s*\(\d+\)\s*$", "", stem)

    # Ignore punctuation/spacing differences.
    stem = re.sub(r"[^a-zA-Z0-9]+", "", stem).lower()

    return stem + suffix

def safe_name(s: str) -> str:
    s = re.sub(r"[^\w\s.-]", "", s).strip()
    s = re.sub(r"\s+", " ", s)
    return s[:180] or "attachment"


def filename_from_response(url, response, fallback):
    cd = response.headers.get("content-disposition", "")
    m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)', cd)
    if m:
        return safe_name(unquote(m.group(1)))

    path = urlparse(response.url).path
    name = Path(path).name
    if "." in name:
        return safe_name(unquote(name))

    return safe_name(fallback)


def download(url, outdir, fallback_name):
    outdir.mkdir(parents=True, exist_ok=True)

    r = requests.get(url, timeout=(TIMEOUT_MINUTES * 60), allow_redirects=True)
    r.raise_for_status()

    name = filename_from_response(url, r, fallback_name)

    desired_key = file_fingerprint(name)

    existing_keys = {
        file_fingerprint(p.name)
        for p in outdir.iterdir()
        if p.is_file()
    }

    print(f"  Checking duplicate key: {desired_key} against {existing_keys}")
    if desired_key in existing_keys:
        print(f"Skipped existing duplicate: {name}")
        return

    path = outdir / name
    path.write_bytes(r.content)
    print(f"Downloaded: {path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("meeting_url")
    parser.add_argument("-o", "--outdir", default="legistar_downloads")
    args = parser.parse_args()

    base_outdir = Path(args.outdir)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(args.meeting_url, wait_until="domcontentloaded", timeout=(TIMEOUT_MINUTES * 60 * 1000))
        page.wait_for_timeout(3000)

        # Collect file-id links from the meeting items table.
        links = page.locator("a").evaluate_all("""
            els => els.map(a => ({
                text: a.innerText.trim(),
                href: a.href
            })).filter(x =>
                /^\\d{2}-\\d{4}$/.test(x.text)
            )
        """)

        print(f"Found {len(links)} file-id links")

        for item in links:
            file_id = safe_name(item["text"])
            detail_url = item["href"]
            print(f"Checking {file_id}: {detail_url}")

            detail = browser.new_page()
            try:
                detail.goto(detail_url, wait_until="domcontentloaded", timeout=(TIMEOUT_MINUTES * 60 * 1000))
            except Exception as e:
                print(f"  ERROR opening {file_id}: {type(e).__name__}; skipping.")
                detail.close()
                continue
            time.sleep(1)

            # Find attachment-ish links. Legistar often uses View.ashx or AttachmentViewer.
            attachments = detail.locator("a").evaluate_all("""
                els => els.map(a => ({
                    text: a.innerText.trim(),
                    href: a.href
                })).filter(x =>
                    x.href &&
                    (
                        x.href.includes("View.ashx") ||
                        x.href.includes("AttachmentViewer") ||
                        x.href.includes("FileOpen")
                    )
                )
            """)

            # Remove non-attachment export/details links.
            cleaned = []
            seen = set()
            for a in attachments:
                text = a["text"] or "attachment"
                href = a["href"]
                if href in seen:
                    continue
                if text in ["Legislation Text", "Legislation Details", "Legislation Details (With Text)"]:
                    continue
                seen.add(href)
                cleaned.append(a)

            print(f"  Found {len(cleaned)} attachments")

            item_outdir = base_outdir / file_id
            for a in cleaned:
                try:
                    download(a["href"], item_outdir, a["text"])
                except Exception as e:
                    print(f"  ERROR downloading {a['text']}: {e}")
            detail.close()

        browser.close()


if __name__ == "__main__":
    main()

