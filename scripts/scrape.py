"""Refresh a public, temporary dividend calendar snapshot from online pages.
No API key, Cloudflare Worker, or manually maintained dividend database.
"""
import calendar
import json
import re
import sys
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'site'
SOURCE = 'https://www.klsescreener.com/v2/entitlements/dividends'
MONTHS_BACK, MONTHS_AHEAD = 2, 4
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; MalaysiaDividendHub/1.0; personal calendar project)'}


def shift_month(today, offset):
    y, m = divmod(today.year * 12 + today.month - 1 + offset, 12)
    return y, m + 1


def parse_month(html, year, month, url):
    soup = BeautifulSoup(html, 'html.parser')
    for node in soup(['script', 'style', 'noscript']):
        node.decompose()
    # Extract human-visible date-grouped calendar listings. The site can change its
    # markup; failures are detected instead of silently fabricating dividend events.
    lines = [re.sub(r'\s+', ' ', s).strip() for s in soup.get_text('\n').splitlines()]
    lines = [s for s in lines if s]
    results = []
    current = None
    date_re = re.compile(r'^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)(?:day)?\s+(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})', re.I)
    entry_re = re.compile(r'^(\d{4,5})\s+([A-Z][A-Z0-9&.\-]{1,16})\s+MYR\s+([\d.]+)\s+(.+)$')
    # Also handle pages where the table cells are separate lines.
    for i, line in enumerate(lines):
        dm = date_re.match(line)
        if dm:
            try:
                current = date(int(dm.group(3)), datetime.strptime(dm.group(2), '%b').month, int(dm.group(1))).isoformat()
            except ValueError:
                current = None
            continue
        match = entry_re.match(line)
        if not match and re.fullmatch(r'\d{4,5}', line) and i + 3 < len(lines):
            joined = ' '.join(lines[i:i + 4])
            match = entry_re.match(joined)
        if match and current and current[:7] == f'{year}-{month:02d}':
            code, symbol, amount, desc = match.groups()
            try:
                rm = float(amount)
            except ValueError:
                continue
            if rm <= 0 or rm > 100 or not any(w in desc.lower() for w in ('dividend', 'distribution')):
                continue
            results.append({'ticker': code, 'symbol': symbol, 'ex_date': current,
                            'rm_per_share': rm, 'sen_per_share': round(rm * 100, 4),
                            'description': desc[:140], 'source': url,
                            'announcement_date': None, 'payment_date': None})
    return results


def ics_escape(value):
    return str(value).replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')


def write_ics(events):
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Malaysia Dividend Hub//Public Dividend Dates//EN',
             'CALSCALE:GREGORIAN', 'X-WR-CALNAME:Bursa Malaysia Dividend Dates', 'METHOD:PUBLISH']
    now = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    for e in events:
        day = date.fromisoformat(e['ex_date'])
        notes = (f"Ticker: {e['ticker']} ({e['symbol']})\nEx-dividend date: {e['ex_date']}\n"
                 f"Dividend: {e['sen_per_share']} sen/share (RM {e['rm_per_share']:.4f})\n"
                 f"Type: {e['description']}\nAnnouncement/payment dates: Not verified in this feed\n"
                 f"Dividend yield (%): Not provided (requires share price)\nSource: {e['source']}\n"
                 'Eligibility and actual payment depend on the official entitlement notice.')
        lines += ['BEGIN:VEVENT', f"UID:{e['ticker']}-{e['ex_date']}-{e['rm_per_share']:.5f}@malaysia-dividend-hub",
                  f'DTSTAMP:{now}', f"DTSTART;VALUE=DATE:{day:%Y%m%d}",
                  f"DTEND;VALUE=DATE:{day + timedelta(days=1):%Y%m%d}",
                  f"SUMMARY:{ics_escape(e['symbol'] + ' ex-dividend — ' + str(e['sen_per_share']) + ' sen')}",
                  f'DESCRIPTION:{ics_escape(notes)}', f"URL:{e['source']}", 'END:VEVENT']
    lines.append('END:VCALENDAR')
    (OUT / 'dividends.ics').write_text('\r\n'.join(lines) + '\r\n', encoding='utf-8')


def main():
    today = datetime.now(timezone(timedelta(hours=8))).date()
    events = {}
    successes = 0
    failures = []
    for offset in range(-MONTHS_BACK, MONTHS_AHEAD + 1):
        year, month = shift_month(today, offset)
        url = SOURCE + '?' + urlencode({'date_type': 'ex_date', 'month': f'{year}-{month:02d}', 'view': 'list'})
        try:
            response = requests.get(url, headers=HEADERS, timeout=25)
            response.raise_for_status()
            found = parse_month(response.text, year, month, url)
            if found:
                successes += 1
            for event in found:
                key = (event['ticker'], event['ex_date'], event['rm_per_share'], event['description'])
                events[key] = event
            print(f'{year}-{month:02d}: {len(found)} dividend records')
        except requests.RequestException as exc:
            failures.append(f'{year}-{month:02d}: {exc}')
    if not events:
        print('No parseable dividend entries found. Site may block requests or markup may have changed.', file=sys.stderr)
        for msg in failures: print(msg, file=sys.stderr)
        sys.exit(1)  # Do not overwrite a previously published working feed with empty data.
    items = sorted(events.values(), key=lambda e: (e['ex_date'], e['ticker'], e['description']))
    OUT.mkdir(exist_ok=True)
    payload = {'updated_at': datetime.now(timezone.utc).isoformat(), 'source': SOURCE,
               'coverage': f'{MONTHS_BACK} months back / {MONTHS_AHEAD} months ahead',
               'records': items, 'warnings': failures}
    (OUT / 'dividends.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    write_ics(items)
    print(f'Published {len(items)} records from {successes} calendar pages')

if __name__ == '__main__':
    main()
