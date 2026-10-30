# Needs you

Decisions, logins, reviews, and keys only a human can provide. The skill writes the `question` column. You write the `answer` column. The next run acts on any row with an answer and no `closed` date, then stamps it.

Keep answers to one line where you can. If the answer is "never" or "not now," say that; the row closes and the blocked candidate is dropped or deferred.

| id | opened | blocks | question | answer | closed |
|---|---|---|---|---|---|
| NY-1 | 2026-10-30 | all GSC panels | Connect Search Console for skiff.solutionscay.com (seo MCP server failed to connect this run)? Options: fix the seo MCP server, paste a 28-day page export, or not now. | | |
| NY-2 | 2026-10-30 | repair: support page | Cloudflare Email Obfuscation rewrites the support@ mailto on /support/ to /cdn-cgi/l/email-protection, which returns 404 to crawlers. Options: turn off Scrape Shield > Email Address Obfuscation in Cloudflare (recommended), or let the next run wrap the address in <!--email_off--> comments. | | |
| NY-3 | 2026-10-30 | repair: gallery | /gallery/ has one inbound link (home). Add it to the shared footer so it has two? This changes the footer on every page. | | |
