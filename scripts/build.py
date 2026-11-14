import json
from pathlib import Path
from datetime import date, timedelta, datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
SITE.mkdir(exist_ok=True)

def esc(s):
    return str(s).replace('\\', '\\\\').replace('\n', '\\n').replace(',', '\\,').replace(';', '\\;')

def event(uid, d, title, notes, source):
    start = date.fromisoformat(d)
    end = start + timedelta(days=1)
    return ['BEGIN:VEVENT', f'UID:{uid}@dividend-hub', f'DTSTAMP:{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}',
            f'DTSTART;VALUE=DATE:{start:%Y%m%d}', f'DTEND;VALUE=DATE:{end:%Y%m%d}',
            f'SUMMARY:{esc(title)}', f'DESCRIPTION:{esc(notes)}', f'URL:{source}', 'END:VEVENT']

items = json.loads((ROOT / 'data' / 'verified_events.json').read_text(encoding='utf-8'))
lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Dividend Hub Malaysia//EN',
         'CALSCALE:GREGORIAN', 'METHOD:PUBLISH', 'X-WR-CALNAME:Malaysia Dividends (Verified)']
for i, r in enumerate(items):
    asset = r['asset']; year = r['year']; pct = r.get('percent'); sen = r.get('sen')
    pct_text = f'{pct}%' if pct is not None else 'Not published'
    sen_text = f'{sen} sen/unit or share' if sen is not None else 'Not applicable / not published'
    notes = (f'Fund/stock: {asset}\nDividend year: {year}\nDividend percentage: {pct_text}'
             f'\nDividend sen: {sen_text}\nExample amount: not calculated (depends on holdings and eligibility)'
             f'\nOfficial source: {r["source"]}')
    if r.get('announcement_date'):
        lines += event(f'{i}-{year}-announcement', r['announcement_date'],
                       f'{asset} {year} dividend announced: {pct_text if pct is not None else sen_text}', notes, r['source'])
    if r.get('crediting_date'):
        lines += event(f'{i}-{year}-crediting', r['crediting_date'],
                       f'{asset} {year}: {r.get("crediting_label", "Dividend crediting")}', notes, r['source'])
lines.append('END:VCALENDAR')
(SITE / 'dividends.ics').write_bytes(('\r\n'.join(lines)+'\r\n').encode('utf-8'))
print(f'Generated {len(items)} verified records, {sum(x == "BEGIN:VEVENT" for x in lines)} calendar events')
