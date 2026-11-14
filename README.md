# Malaysia Dividend Hub — live Bursa lookup

No historical dividend JSON database. The browser fetches the Cloudflare Worker API every time the user clicks **Fetch live dividends**. The Worker requests Yahoo Finance chart dividend events online. Holdings and Worker URL are saved only in the user's own browser localStorage (no server-side storage). This is **not official Bursa filing data** and may fail due to provider restrictions.

## 1. Deploy the Worker (free Cloudflare account required)

1. Go to https://dash.cloudflare.com/ → Workers & Pages → Create → Worker.
2. Name it `malaysia-dividend-live` (or any available name).
3. Edit the Worker code and paste **all contents** of `worker/index.js`; save and deploy.
4. Copy the `https://...workers.dev` URL. Test `/api/dividends?ticker=1155` in your browser. The Worker must return JSON; if the upstream provider blocks requests, choose a licensed financial API provider instead. The Worker does not guarantee Yahoo availability.

Alternatively use Wrangler CLI from the `worker/` directory: `npx wrangler deploy` (after authenticating).

## 2. Deploy GitHub Pages

Copy `site/index.html` and `.github/workflows/main.yml` into your existing `pyhor/malaysia-dividend-hub` repository, replacing previous files. Keep GitHub Pages source = **GitHub Actions**. The workflow publishes `site/` directly, without Python or requirements.txt. Remove old scheduled database build workflows to avoid conflict.

## 3. Use

Visit https://pyhor.github.io/malaysia-dividend-hub/; paste your Worker URL and click **Use this API**. Enter Bursa ticker and share count. Click **Fetch live dividends**. Click **Copy live Apple Calendar URL**, then Apple Calendar → File → New Calendar Subscription. This URL exposes ticker symbols, not share counts; the calendar notes therefore show sen/share but **not personal RM estimates**. Anyone who knows the URL can see the selected ticker symbols.

## Limitations

- Live market-data source supplies ex-dates and dividend amounts, not guaranteed announcement or payment dates. Rates/yields are not invented.
- Calendar refresh depends on Apple Calendar's subscription schedule; provider errors may temporarily prevent updates.
- EPF and ASM do **not** have a reliable live source integrated here. They are intentionally excluded from the live feed until official data ingestion is implemented.
- Only numeric Bursa tickers (4–5 digits) supported, e.g. `1155`, `1295`. No stock-name search in this version.
- Data is fetched on demand; no historical dividends are stored in GitHub or Worker. Local browser **holdings** are stored for convenience, not dividend data.
- This is an independently hosted API; GitHub Pages alone cannot proxy external financial data or reliably bypass CORS.
