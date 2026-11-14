"""Build a static dividend feed. Stock ex-dates come from Yahoo Finance chart events.
No unverified announcement/payment dates are invented.
"""
import json, os, re, urllib.request
from pathlib import Path
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/'site'; SITE.mkdir(exist_ok=True)
REPO=os.getenv('GITHUB_REPOSITORY','pyhor/malaysia-dividend-hub')
HEADERS={'User-Agent':'Mozilla/5.0 (compatible; DividendHub/1.0)','Accept':'application/json'}
def get_json(url):
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=16) as response:return json.load(response)
def normalize(s):
    s=str(s).strip().upper().replace(' ','')
    if s.endswith('.KL'):s=s[:-3]
    if not re.fullmatch(r'\d{4,5}',s):return None
    return s.zfill(4)+'.KL'
def stock_symbols():
    initial=json.loads((ROOT/'data'/'stocks.json').read_text())
    result=set(filter(None,map(normalize,initial)))
    # Public GitHub issues titled "Track stock: 1155.KL" request addition without a token in the browser.
    try:
        for page in range(1,5):
            issues=get_json(f'https://api.github.com/repos/{REPO}/issues?state=all&per_page=100&page={page}')
            for issue in issues:
                if 'pull_request' in issue:continue
                match=re.fullmatch(r'Track stock:\s*(\d{4,5}(?:\.KL)?)\s*',issue.get('title',''),re.I)
                if match:
                    symbol=normalize(match.group(1))
                    if symbol:result.add(symbol)
            if len(issues)<100:break
    except Exception as ex:print('Issue discovery unavailable:',ex)
    return sorted(result)
def fetch_stock(symbol):
    url=f'https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol)}?range=5y&interval=1d&events=div'
    try:
        data=get_json(url)['chart']['result'][0]
        dividends=(data.get('events') or {}).get('dividends') or {}
        found=[]
        for v in dividends.values():
            amount=v.get('amount'); stamp=v.get('date')
            if amount is None or stamp is None:continue
            d=datetime.fromtimestamp(int(stamp),timezone.utc).date().isoformat()
            found.append({'asset':'Stock','ticker':symbol,'year':int(d[:4]),'ex_date':d,
                          'announcement_date':None,'crediting_date':None,'percent':None,
                          'sen':round(float(amount)*100,5),
                          'source':f'https://finance.yahoo.com/quote/{quote(symbol)}/history/',
                          'source_type':'Market data (Yahoo Finance; verify with Bursa/issuer)',
                          'note':'Ex-dividend date and cash dividend amount only; announcement and payment dates are not provided by this source.'})
        print(symbol,len(found),'dividend records')
        return found
    except Exception as ex:
        print('Stock lookup failed',symbol,ex)
        return []
def esc(v):return str(v).replace('\\','\\\\').replace('\n','\\n').replace(',','\\,').replace(';','\\;')
def event(uid,d,title,notes,source):
    start=date.fromisoformat(d); end=start+timedelta(days=1)
    parts=['BEGIN:VEVENT',f'UID:{uid}@malaysia-dividend-hub',f'DTSTAMP:{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}',
           f'DTSTART;VALUE=DATE:{start:%Y%m%d}',f'DTEND;VALUE=DATE:{end:%Y%m%d}',
           f'SUMMARY:{esc(title)}',f'DESCRIPTION:{esc(notes)}']
    if source and source.startswith('https://'):parts.append(f'URL:{source}')
    return parts+['END:VEVENT']
items=json.loads((ROOT/'data'/'verified_events.json').read_text())
symbols=stock_symbols(); stock_records=[]
for sym in symbols:stock_records.extend(fetch_stock(sym))
items.extend(stock_records)
(SITE/'records.json').write_text(json.dumps({'updated_utc':datetime.now(timezone.utc).isoformat(),
    'tracked_tickers':symbols,'records':items},ensure_ascii=False,indent=2)+'\n')
lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Malaysia Dividend Hub//EN','CALSCALE:GREGORIAN','METHOD:PUBLISH','X-WR-CALNAME:Malaysia Dividends']
for i,r in enumerate(items):
    asset=r['ticker'] if r.get('asset')=='Stock' else r['asset']; year=r.get('year','')
    pct=f'{r["percent"]}%' if r.get('percent') is not None else 'Not published'
    sen=f'{r["sen"]} sen per share/unit' if r.get('sen') is not None else 'Not published'
    notes=f'Asset: {asset}\nDividend year: {year}\nDividend rate: {pct}\nDividend amount: {sen}\n'
    notes+='Estimated payout: calculate using your eligible holdings; not included in this public feed.\n'
    notes+=f'Source: {r.get("source", "Not available")}\nSource type: {r.get("source_type", "Official curated record")}\n'
    if r.get('note'):notes+=f'Important: {r["note"]}\n'
    for kind,key in [('Announcement','announcement_date'),('Ex-dividend','ex_date'),('Crediting / payment','crediting_date')]:
        if r.get(key):
            title=f'{asset} {kind} — {pct if r.get("percent") is not None else sen}'
            uid=f'{asset}-{r[key]}-{kind}-{i}'.replace(' ','-')
            lines.extend(event(uid,r[key],title,notes,r.get('source','')))
lines.append('END:VCALENDAR')
(SITE/'dividends.ics').write_bytes(('\r\n'.join(lines)+'\r\n').encode())
print(f'Built {len(items)} records ({len(stock_records)} stock), {lines.count("BEGIN:VEVENT")} calendar events')
