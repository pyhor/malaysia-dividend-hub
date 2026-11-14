# Malaysia Dividend Hub — Bursa Malaysia only

A GitHub Pages dividend tracker for **Bursa Malaysia stocks, EPF Conventional/Shariah, ASM 1, ASM 2 Wawasan and ASM 3**, with an Apple Calendar subscription.

## Deploy to `pyhor/malaysia-dividend-hub`

1. Upload **the contents of this ZIP's `dividend-hub` folder** to the **root** of your existing GitHub repository on branch `main`. Keep the folders `data/`, `scripts/`, `site/` and `.github/workflows/`.
2. Delete the old `.github/workflows/publish.yml` if present. Keep **only** `.github/workflows/main.yml` to avoid duplicate deployments.
3. Under **Settings → Pages**, set Source to **GitHub Actions**.
4. Open **Actions → Publish Malaysia Dividend Hub → Run workflow**.
5. After a successful deploy, visit `https://pyhor.github.io/malaysia-dividend-hub/` and subscribe to `https://pyhor.github.io/malaysia-dividend-hub/dividends.ics`.

The workflow runs on pushes to main, new/edited GitHub issues, and daily (approximately 09:17 Malaysia time). It uses Python standard library only; **no `requirements.txt` or pip install needed**.

## Add stocks

- On the website choose **Bursa Malaysia stock**, enter e.g. `1155.KL` or `Maybank`, and enter shares owned. Holdings stay in browser localStorage.
- The project initially tracks a few common stocks listed in `data/stocks.json`.
- For a new stock, the website shows **Request tracking**. Click it, submit the prefilled public GitHub issue titled `Track stock: 1234.KL`. GitHub Actions reads the issue titles and automatically includes those tickers in future builds. No dividend dates/rates are entered by users. **Issues are public, so do not put private holdings in an issue.**
- The name-to-code dictionary is limited to common companies. For other stocks use the Bursa numeric ticker code; it cannot reliably identify arbitrary company names offline.

## Data and limitations

- Stock ex-dividend dates and dividend amounts are retrieved from the Yahoo Finance chart dividend-event endpoint at build time, covering up to 5 years. This is **third-party market data, not official Bursa announcements**, and can be unavailable, delayed or incomplete. The source link appears in records and event Notes. No payment or announcement date is invented when unavailable.
- `data/verified_events.json` is a curated database for official EPF/ASM announcements. Only records with verified source dates/rates should be added. At present it includes two EPF 2025 records; **ASM data is not automatically scraped yet**. ASM funds are supported in the portfolio UI but will have no records until curated official records are supplied.
- This is a **public, shared subscription feed**, not a personalized subscription. The **Download my personal calendar** option adds estimates to Notes but is a static snapshot. A private, automatically updating personalized subscription needs authenticated hosting/backend.
- The website calculates an **illustrative** payout based on today's entered shares/units. Historical entitlement, ex-date eligibility, EPF daily balances and actual payments may differ. A stock's dividend amount in sen is **not** the dividend yield percentage.
- If a stock fetch fails, the build still succeeds and may show no stock records. Check GitHub Actions logs and issuer/Bursa announcements.

## Files

- `site/index.html`: frontend website
- `scripts/build.py`: fetch dividend events, produce `site/records.json` and `site/dividends.ics`
- `data/stocks.json`: initial tracked Bursa symbols
- `data/verified_events.json`: manually curated official fund records
- `.github/workflows/main.yml`: scheduled and issue-triggered Pages deployment
