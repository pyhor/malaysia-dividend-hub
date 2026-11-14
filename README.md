# Dividend Hub Malaysia (unofficial)

Static responsive GitHub Pages website to track holdings in EPF Conventional/Shariah, ASM 1, ASM 2 Wawasan, ASM 3, and custom stocks. Includes a public Apple Calendar subscription and a private local-only .ics export.

## Deploy
1. Create a **public** repository `malaysia-dividend-hub` on GitHub with `main` branch.
2. Upload **all contents**, including hidden `.github/workflows/publish.yml`, `site/index.html`, `scripts/build.py`, and `data/verified_events.json`.
3. Settings → Pages → Source: **GitHub Actions**.
4. Actions → **Publish Malaysia Dividend Hub** → Run workflow → main.
5. Visit `https://YOUR-USERNAME.github.io/malaysia-dividend-hub/` and subscribe to `https://YOUR-USERNAME.github.io/malaysia-dividend-hub/dividends.ics` in Mac Calendar (File → New Calendar Subscription → iCloud).

## Adding verified dividend records to the public feed
Edit `data/verified_events.json` and commit to `main`. Each record supports `asset`, `year`, `announcement_date`, `crediting_date`, `percent`, `sen`, `crediting_label`, `source`. Unknown dates should be `null` or omitted. **Never invent dates**. The workflow republishes on every push and daily, but **does not scrape or discover new announcements automatically**. The daily rebuild alone will not add new rates or dates. Historical years can be added only when official source evidence is available.

## Personal data and calculations
Holdings and manually entered dividend records live in browser `localStorage` only; they do not sync across devices or appear in the public feed. Export/import JSON for backup. The personal .ics download is a **snapshot**, not a live subscription. To provide truly automatic *personalized* calendar updates across devices, you need authentication, server-side storage and a private authenticated calendar feed, which static GitHub Pages cannot provide securely.

For stocks, dividend in sen/share × shares / 100 is illustrative and does not account for eligibility, currency, taxes, corporate actions, or multiple distributions. For ASM, unit-based calculations are illustrative; for EPF, balance × rate is not the actual dividend computation. No market data API is integrated, and there is no claim of real-time coverage. Check KWSP, ASNB, and company announcements.

## Test locally
`python scripts/build.py` then open `site/index.html`. The public `.ics` is generated at `site/dividends.ics`.
