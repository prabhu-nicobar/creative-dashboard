# Putting the dashboard online — a complete walkthrough

**Written for someone who has never used GitHub.** Nothing here assumes any prior
knowledge. Follow it in order. The whole thing takes about twenty minutes the first
time, and about two minutes every week after that.

At the end you will have a web address like
`https://prabhu-nicobar.github.io/creative-dashboard/` that anyone on the team can
open in a browser, on a phone or a laptop, with no login and no software.

---

## What GitHub actually is

GitHub is a place to store files on the internet. It has a feature called **GitHub
Pages** that takes a folder of files and serves them as a website. Because our
dashboard is a single HTML file plus a folder of images, that is all we need. There
is no server, no database, and nothing to maintain.

---

# Part 1 — One-time setup

## Step 1. Make a GitHub account

1. Go to **https://github.com/signup**
2. Enter your email, pick a password, pick a username.
   The username becomes part of your web address, so choose something you're happy
   for the team to see — `prabhu-nicobar` rather than `xyz123`.
3. Verify the email they send you.
4. When it asks about a plan, choose **Free**. Everything we need is free.

## Step 2. Create the repository

A "repository" (everyone says **repo**) is just a project folder.

1. Once logged in, click the **+** icon in the top-right corner → **New repository**.
2. Fill in:
   - **Repository name:** `creative-dashboard`
   - **Description:** `Nicobar Meta creative performance dashboard`
   - **Public** — see the note below.
   - Tick **Add a README file**.
3. Click **Create repository**.

> **A note on Public vs Private.** GitHub Pages only works on a free account if the
> repo is **Public**, which means anyone who finds the address can open it. The page
> is not listed anywhere and the address is not guessable, but it is not secured.
> You told me a password gate isn't essential, so Public is the right call. If that
> ever changes, tell me and I'll move it to Cloudflare Pages, which gives a real
> password gate for free using this same repo.

## Step 3. Upload the files

You should have these from me:

| File | What it is |
|---|---|
| `nicobar-creative-dashboard.html` | The dashboard itself |
| `engine.py`, `narrative.py`, `insights.py`, `export.py` | The analysis pipeline |
| `shell.html`, `app.js` | The design and interface source |
| `fetch_images.py` | Downloads creative previews |
| `DEPLOY.md` | This document |

**Rename the dashboard file to `index.html`.** This matters: GitHub Pages looks for
a file called exactly `index.html` and shows it as the front page. If it's called
anything else, visitors get a blank list of files instead of the dashboard.

Then:

1. On your repo page, click **Add file** → **Upload files**.
2. Drag all the files in.
3. At the bottom, in the box that says *Commit changes*, type
   `First upload of the creative dashboard`.
4. Click **Commit changes**.

"Commit" simply means save. Every save is kept forever with a timestamp, so you can
always go back to an earlier version.

## Step 4. Turn on the website

1. In your repo, click **Settings** (the tab along the top).
2. In the left sidebar, click **Pages**.
3. Under *Build and deployment* → *Source*, choose **Deploy from a branch**.
4. Under *Branch*, choose **main** and folder **/ (root)**. Click **Save**.
5. Wait one to two minutes, then refresh the page. A green box appears at the top
   with your live address:

   ```
   https://YOUR-USERNAME.github.io/creative-dashboard/
   ```

Open it. The dashboard should load.

> **If you get a 404 page:** it's almost always one of two things — the file isn't
> named `index.html`, or Pages hasn't finished building yet. Wait two more minutes
> and refresh before changing anything.

## Step 5. Get the creative images in

Right now every card shows a striped placeholder, because the images aren't in the
repo yet. To fix that, on the computer where you run the weekly refresh:

```bash
pip install requests pillow
python fetch_images.py
```

This reads `creative_urls.json` (produced by the refresh — see Part 2), downloads
each creative once, shrinks it, and saves it into an `images/` folder.

Then upload that `images` folder to GitHub the same way as Step 3: **Add file** →
**Upload files** → drag the whole `images` folder in → **Commit changes**.

Reload the dashboard. The previews appear.

> **Why we download rather than link.** Meta serves creative images from addresses
> that expire after a few days. If the dashboard pointed at those addresses, every
> image would break within a week. Downloading them once means they live in your
> repo permanently and load instantly.

---

# Part 2 — The weekly refresh

Every Saturday you want fresh numbers on the same address. That means regenerating
the files and uploading them again.

## What the refresh has to do, in order

1. **Pull the data from Meta** for four windows: last 7 days, last 14 days, month to
   date, and last 90 days.
   > **Important:** the 90-day pull fails if you ask for all fifteen campaigns at
   > once. It has to be requested in chunks of about five campaigns. This is a Meta
   > limitation, not a bug in our code, and the pipeline already handles it.
2. **Run `export.py`** to score everything and write `payload.json`.
3. **Write `creative_urls.json`** — the creative-id-to-image-address mapping.
4. **Run `fetch_images.py`** to download any creatives that are new this week.
5. **Rebuild `index.html`** from `shell.html`, `app.js` and `payload.json`.
6. **Upload** the changed files to GitHub.

## Setting it up as a recurring Cowork task

1. Open **Claude Cowork** on your desktop.
2. Start a new task and paste the prompt below.
3. Before running it, use the schedule option and set it to **repeat weekly on
   Saturday**, at whatever time suits — early morning means it's ready before anyone
   opens it.

**The prompt to save:**

```
Refresh the Nicobar creative dashboard.

1. Pull ad-level data from the Meta connector for ad account 1346208828785334
   across four windows: last_7d, last_14d, this_month, and last_90d.
   Include these campaigns: NB-008, NB-009, NB-010, NB-011, NB-012, NB-013,
   NB-014, NB-015, NB-016, NB-017, NB-002, NB-019, NB-021, FE-100, FE-104.
   IMPORTANT: request last_90d in chunks of five campaigns — the full-account
   90-day call fails every time.
   Fields: id, name, campaign_id, adset_id, effective_status, created_time,
   creative_id, amount_spent, impressions, reach, frequency, cpm,
   outbound_clicks, outbound_clicks_ctr, omni_landing_page_view,
   omni_add_to_cart, cost_per_omni_add_to_cart, omni_initiated_checkout,
   omni_purchase, omni_purchase_values, purchase_roas.
   Save as l7.json, ads_14d.json, mtd.json, d90.json.

2. Pull image_url and thumbnail_url for every creative_id that appears in those
   files, in batches of about 120, and write creative_urls.json as a flat
   mapping of creative_id to the best available image address (prefer
   image_url, fall back to thumbnail_url).

3. Update the window date labels in export.py to the actual dates covered.

4. Run: python export.py
5. Run: python fetch_images.py
6. Rebuild index.html by injecting payload.json and app.js into shell.html.
7. Tell me which files changed and roughly how many creatives are in each window,
   so I can sanity-check before uploading.
```

## Uploading each week

1. Go to your repo on GitHub.
2. **Add file** → **Upload files**.
3. Drag in `index.html` and the `images` folder.
4. Commit message: `Refresh — 6 September` (whatever the date is).
5. **Commit changes**.

The live site updates within a minute. Anyone who reloads sees the new numbers.

> Dragging a file with the same name replaces the old one. That is exactly what you
> want, and nothing is lost — every previous version is kept in the repo's history.

---

# Part 3 — Things that will come up

**Someone says the page looks broken or old.**
Ask them to hard-refresh: **Ctrl+Shift+R** on Windows, **Cmd+Shift+R** on Mac.
Browsers cache aggressively and will happily show last week's file.

**You want to undo a bad upload.**
On the repo page, click **Commits** (top of the file list), find the last good one,
and use the "..." menu to revert. Nothing is ever permanently lost.

**You want to change something small in the wording.**
Click the file in GitHub, click the pencil icon, edit, and commit. Careful with
`index.html` — it's mostly generated, so anything you hand-edit there gets wiped on
the next refresh. Wording changes belong in `shell.html` or `narrative.py`, which
survive.

**The EuclidFlex fonts.**
The dashboard currently falls back to a system typeface. When you have the `.woff2`
files, put them in a `fonts/` folder, upload it, and tell me — it's a five-line
change and the page will look properly like Nicobar.

**Someone wants it as a PDF for a meeting.**
Open the dashboard, click **Print**, and choose *Save as PDF*. There's a print
stylesheet built in that strips the controls and expands every card.

---

# Quick reference

| I want to… | Do this |
|---|---|
| See the live dashboard | Open your GitHub Pages address |
| Refresh the numbers | Run the Saturday Cowork task, then upload `index.html` |
| Add new creative images | `python fetch_images.py`, then upload `images/` |
| Undo something | Repo → Commits → revert |
| Share it | Send the address — no login needed |
| Print for a meeting | Print button → Save as PDF |
