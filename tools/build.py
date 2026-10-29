#!/usr/bin/env python3
"""Rebuild the shared parts of every page: the <head>, the top bar, the footer
and sitemap.xml. Page bodies stay hand-written.

    python3 tools/build.py          rewrite the pages and the sitemap
    python3 tools/build.py --check  exit 1 if a page or the sitemap is stale

To add a page, write its <main> into <path>/index.html and add it to PAGES.
A file without <body> is taken as the <main> alone and gets the full frame.
"""
import datetime, hashlib, html, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://skiff.solutionscay.com/"
ANALYTICS = "WBND0Nn9GdlmCPxIRT8H3Q"
PUBLISHER = {"@type": "Organization", "name": "Solutions Cay LLC", "url": "https://solutionscay.com/"}

APP = {
    "@context": "https://schema.org", "@type": "SoftwareApplication", "name": "Skiff",
    "description": "A minimalist desktop workspace for coding agents such as Claude Code, Codex and Gemini CLI.",
    "applicationCategory": "DeveloperApplication", "operatingSystem": "Linux, macOS",
    "license": "https://opensource.org/licenses/MIT", "url": SITE, "downloadUrl": SITE + "download/",
    "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "publisher": PUBLISHER,
}

def article(path, headline, description, published, modified=None):
    return {
        "@context": "https://schema.org", "@type": "TechArticle", "headline": headline,
        "description": description, "datePublished": published, "dateModified": modified or published,
        "author": PUBLISHER, "mainEntityOfPage": SITE + path,
    }

# path: the folder under the site root ("" is the home page).
# og_title and og_desc default to title and desc.
PAGES = [
    dict(path="", title="Skiff: a desktop workspace for Claude Code, Codex and more",
         desc="Run Claude Code, Codex, Gemini CLI and other coding agents side by side on Linux and macOS. Admiral, the built-in coordinator, hands tasks to agents and project Skippers, and sessions keep running when you close the window.",
         ld=APP),
    dict(path="download/", title="Download Skiff", desc="Download Skiff for Linux x86_64 (.deb, .rpm, AppImage) and macOS on Apple Silicon (.dmg). Free and open source under the MIT license.",
         og_desc="Skiff for Linux x86_64 (.deb, .rpm, AppImage) and macOS on Apple Silicon (.dmg).", ld=APP),
    dict(path="gallery/", title="Skiff screenshots and videos",
         desc="Screenshots and videos of Skiff, from the first build to the latest release."),
    dict(path="support/", title="Skiff support",
         desc="Get help with Skiff. Report a bug, ask a question, or suggest a feature."),
    dict(path="claude-code/", title="Run multiple Claude Code sessions on Linux and macOS | Skiff",
         og_title="Run multiple Claude Code sessions on Linux and macOS",
         desc="Skiff is a free, open-source desktop app for Claude Code on Linux and macOS. Run sessions side by side in Git worktrees, see which one waits for approval, and keep them running after you close the window.",
         og_desc="A free, open-source desktop app for Claude Code. Sessions side by side in Git worktrees, approval and finished flags, and sessions that keep running after you close the window."),
    dict(path="codex/", title="Run Codex CLI sessions side by side on Linux and macOS | Skiff",
         og_title="Run Codex CLI sessions side by side on Linux and macOS",
         desc="Skiff is a free, open-source desktop app that runs Codex CLI next to Claude Code and other agents on Linux and macOS. Sessions sit in Git worktrees, flag when they need approval, and keep running after you close the window.",
         og_desc="A free, open-source desktop app for Codex CLI and other coding agents. Sessions in Git worktrees, approval and finished flags, and sessions that keep running after you close the window."),
    dict(path="gemini-cli/", title="Run Gemini CLI and Antigravity CLI side by side | Skiff",
         og_title="Run Gemini CLI and Antigravity CLI side by side",
         desc="Skiff is a free, open-source desktop app that runs Google's Antigravity CLI or Gemini CLI next to Claude Code, Codex and other agents on Linux and macOS. Sessions sit in Git worktrees, flag when they need approval, and keep running after you close the window.",
         og_desc="A free, open-source desktop app for Google's Antigravity CLI, Gemini CLI and other coding agents. Sessions in Git worktrees, approval and finished flags, and sessions that keep running after you close the window."),
    dict(path="grok-cli/", title="Run Grok Build CLI sessions side by side on Linux and macOS | Skiff",
         og_title="Run Grok Build CLI sessions side by side on Linux and macOS",
         desc="Skiff is a free, open-source desktop app that runs xAI's Grok Build CLI next to Claude Code, Codex and other agents on Linux and macOS. Sessions sit in Git worktrees, ring a bell when they need approval, and keep running after you close the window.",
         og_desc="A free, open-source desktop app for Grok Build and other coding agents. Sessions in Git worktrees, approval flags, and sessions that keep running after you close the window."),
    dict(path="opencode/", title="Run OpenCode sessions side by side on Linux and macOS | Skiff",
         og_title="Run OpenCode sessions side by side on Linux and macOS",
         desc="Skiff is a free, open-source desktop app that runs OpenCode next to Claude Code, Codex and other agents on Linux and macOS. Sessions sit in Git worktrees, flag when they need approval, and keep running after you close the window.",
         og_desc="A free, open-source desktop app for OpenCode and other coding agents. Sessions in Git worktrees, approval and finished flags, and sessions that keep running after you close the window."),
    dict(path="guides/", title="Skiff guides: running coding agents",
         desc="The Skiff user guide, and guides to running Claude Code, Codex and other coding agents: Git worktrees, parallel sessions and sessions that keep running.",
         ld={"@context": "https://schema.org", "@type": "CollectionPage", "name": "Skiff guides", "url": SITE + "guides/",
             "publisher": PUBLISHER, "mainEntity": {"@type": "ItemList", "itemListElement": [
                 {"@type": "ListItem", "position": i + 1, "url": SITE + "guides/" + slug + "/"} for i, slug in enumerate(
                     ["skiff-user-guide", "run-coding-agents-in-parallel", "keep-agent-sessions-running", "git-worktrees-for-coding-agents"])]}}),
    dict(path="guides/skiff-user-guide/", title="Skiff user guide | Skiff", og_title="Skiff user guide", css="guides/skiff-user-guide/guide.css",
         desc="How to set up Skiff and run coding agents in it: Admiral and the Skippers, projects and fleets, sessions and groups, diffs and files, images, the Ledger, workspaces and Settings. Every step is a click or a key.",
         ld={"@context": "https://schema.org", "@type": "CollectionPage", "name": "Skiff user guide", "url": SITE + "guides/skiff-user-guide/",
             "publisher": PUBLISHER, "mainEntity": {"@type": "ItemList", "itemListElement": [
                 {"@type": "ListItem", "position": i + 1, "url": SITE + "guides/skiff-user-guide/" + slug + "/"} for i, slug in enumerate(
                     ["set-up-admiral", "projects-and-fleets", "sessions-and-groups", "side-panel-diffs-and-files", "focus-mode-and-mission-control", "drop-images", "ledger", "workspaces", "settings"])]}}),
    dict(path="guides/skiff-user-guide/set-up-admiral/", type="article", css="guides/skiff-user-guide/guide.css",
         title="Set up Admiral, Skippers and task types | Skiff user guide", og_title="Set up Admiral, Skippers and task types",
         desc="How to name the Skiff agent, pick its agent and model, set the project and fleet Skippers, and tell Admiral which agent runs each kind of task.",
         ld=article("guides/skiff-user-guide/set-up-admiral/", "Set up Admiral, Skippers and task types", "How to name the Skiff agent, pick its agent and model, set the project and fleet Skippers, and tell Admiral which agent runs each kind of task.", "2026-10-29")),
    dict(path="guides/skiff-user-guide/projects-and-fleets/", type="article", css="guides/skiff-user-guide/guide.css",
         title="Projects, fleets and the first start | Skiff user guide", og_title="Projects, fleets and the first start",
         desc="How to add projects to Skiff, make worktrees, put projects in fleets, and start Admiral, project Skippers and fleet Skippers.",
         ld=article("guides/skiff-user-guide/projects-and-fleets/", "Projects, fleets and the first start", "How to add projects to Skiff, make worktrees, put projects in fleets, and start Admiral, project Skippers and fleet Skippers.", "2026-10-29")),
    dict(path="guides/skiff-user-guide/sessions-and-groups/", type="article", css="guides/skiff-user-guide/guide.css",
         title="Sessions, groups, tiles and themes | Skiff user guide", og_title="Sessions, groups, tiles and themes",
         desc="How to start agent sessions in Skiff, put them side by side in groups, lay out the panes, and give projects and sessions their own theme.",
         ld=article("guides/skiff-user-guide/sessions-and-groups/", "Sessions, groups, tiles and themes", "How to start agent sessions in Skiff, put them side by side in groups, lay out the panes, and give projects and sessions their own theme.", "2026-10-29")),
    dict(path="guides/skiff-user-guide/side-panel-diffs-and-files/", type="article", css="guides/skiff-user-guide/guide.css",
         title="Side panel, diffs and files | Skiff user guide", og_title="Side panel, diffs and files",
         desc="How to read the Skiff side panel, review a change in the peek, and browse and open the files of a worktree.",
         ld=article("guides/skiff-user-guide/side-panel-diffs-and-files/", "Side panel, diffs and files", "How to read the Skiff side panel, review a change in the peek, and browse and open the files of a worktree.", "2026-10-29")),
    dict(path="guides/skiff-user-guide/focus-mode-and-mission-control/", type="article", css="guides/skiff-user-guide/guide.css",
         title="Focus mode, maximize and Mission control | Skiff user guide", og_title="Focus mode, maximize and Mission control",
         desc="How to hide the chrome with focus mode, fill the window with one pane, and see the whole agent hierarchy as a graph in Mission control.",
         ld=article("guides/skiff-user-guide/focus-mode-and-mission-control/", "Focus mode, maximize and Mission control", "How to hide the chrome with focus mode, fill the window with one pane, and see every session's screen in Mission control.", "2026-10-29")),
    dict(path="guides/skiff-user-guide/drop-images/", type="article", css="guides/skiff-user-guide/guide.css",
         title="Drop images | Skiff user guide", og_title="Drop images",
         desc="How to give an agent an image in Skiff: drop or paste it on a pane, and find it again in the images library.",
         ld=article("guides/skiff-user-guide/drop-images/", "Drop images", "How to give an agent an image in Skiff: drop or paste it on a pane, and find it again in the images library.", "2026-10-29")),
    dict(path="guides/skiff-user-guide/ledger/", type="article", css="guides/skiff-user-guide/guide.css",
         title="The Ledger and result files | Skiff user guide", og_title="The Ledger and result files",
         desc="How to follow the tasks Admiral and the Skippers run in the Ledger panel, and open the result files they write.",
         ld=article("guides/skiff-user-guide/ledger/", "The Ledger and result files", "How to follow the tasks Admiral and the Skippers run in the Ledger panel, and open the result files they write.", "2026-10-29")),
    dict(path="guides/skiff-user-guide/workspaces/", type="article", css="guides/skiff-user-guide/guide.css",
         title="Workspaces | Skiff user guide", og_title="Workspaces",
         desc="How to show only some projects and fleets in Skiff with a workspace: new, edit, save, save as, open and close.",
         ld=article("guides/skiff-user-guide/workspaces/", "Workspaces", "How to show only some projects and fleets in Skiff with a workspace: new, edit, save, save as, open and close.", "2026-10-29")),
    dict(path="guides/skiff-user-guide/settings/", type="article", css="guides/skiff-user-guide/guide.css",
         title="Settings | Skiff user guide", og_title="Settings",
         desc="The Skiff Settings pages: Agents, Open with, themes and how to manage them, skiffd activity, disk use and the image gallery.",
         ld=article("guides/skiff-user-guide/settings/", "Settings", "The Skiff Settings pages: Agents, Open with, themes and how to manage them, skiffd activity, disk use and the image gallery.", "2026-10-29")),
    dict(path="guides/git-worktrees-for-coding-agents/", type="article",
         title="Git worktrees for coding agents: a practical guide | Skiff",
         og_title="Git worktrees for coding agents: a practical guide",
         desc="How to use git worktrees to run Claude Code, Codex and other coding agents in parallel without edits colliding: the commands, the pitfalls, and how to clean up.",
         ld=article("guides/git-worktrees-for-coding-agents/", "Git worktrees for coding agents: a practical guide",
                    "How to use git worktrees to run Claude Code, Codex and other coding agents in parallel without edits colliding: the commands, the pitfalls, and how to clean up.",
                    "2026-10-05", "2026-10-26")),
    dict(path="guides/run-coding-agents-in-parallel/", type="article",
         title="Run coding agents in parallel: a practical guide | Skiff",
         og_title="Run coding agents in parallel: a practical guide",
         desc="How to run Claude Code, Codex and other coding agents in parallel: pick tasks that don't overlap, give each agent a worktree, know which one needs you, and merge the results.",
         ld=article("guides/run-coding-agents-in-parallel/", "Run coding agents in parallel: a practical guide", "How to run Claude Code, Codex and other coding agents in parallel: pick tasks that don't overlap, give each agent a worktree, know which one needs you, and merge the results.", "2026-10-06", "2026-10-26")),
    dict(path="guides/keep-agent-sessions-running/", type="article",
         title="Keep coding agent sessions running after you close the terminal | Skiff",
         og_title="Keep coding agent sessions running after you close the terminal",
         desc="How to keep Claude Code, Codex and other agents running when the terminal closes: tmux, non-interactive modes, what a reboot ends, and how to resume.",
         ld=article("guides/keep-agent-sessions-running/", "Keep coding agent sessions running after you close the terminal", "How to keep Claude Code, Codex and other agents running when the terminal closes: tmux, non-interactive modes, what a reboot ends, and how to resume.", "2026-10-06", "2026-10-26")),
]

def a(s):
    return html.escape(s, quote=False).replace('"', "&quot;")

def filehash(rel):
    return hashlib.sha1(open(os.path.join(ROOT, rel), "rb").read()).hexdigest()[:8]

def head(p, up, css):
    og_title = p.get("og_title", p["title"])
    og_desc = p.get("og_desc", p["desc"])
    url = SITE + p["path"]
    extra = ""
    if p.get("css"):
        extra = f'<link rel="stylesheet" href="{up}{p["css"]}?v={filehash(p["css"])}">\n'
    ld = ""
    if p.get("ld"):
        ld = '<script type="application/ld+json">\n' + json.dumps(p["ld"], separators=(",", ":"), ensure_ascii=False) + "\n</script>\n"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(p["title"], quote=False)}</title>
<meta name="description" content="{a(p["desc"])}">
<meta property="og:title" content="{a(og_title)}">
<meta property="og:description" content="{a(og_desc)}">
<meta property="og:type" content="{p.get("type", "website")}">
<meta property="og:site_name" content="Skiff">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}social-preview.png?v=3">
<meta property="og:image:width" content="1280">
<meta property="og:image:height" content="640">
<meta property="og:image:alt" content="Skiff: a minimalist desktop workspace for coding agents">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{url}">
<link rel="icon" href="{up}favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&family=Lilita+One&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}site.css?v={css}">
{extra}<script src="https://analytics.ahrefs.com/analytics.js" data-key="{ANALYTICS}" async></script>
{ld}</head>
"""

def bar(up):
    links = f"""<a href="{up}download/">Download</a>
      <a href="{up}guides/">Guides</a>
      <a href="https://github.com/solutionscay/skiff/wiki">Wiki</a>
      <a href="https://github.com/solutionscay/skiff">GitHub</a>
      <a href="{up}support/">Support</a>
      <a href="https://buy.stripe.com/6oU4gz5Ejb4hgsm9mRcZa04">Tip</a>"""
    return f"""<header class="bar">
  <div class="wrap">
    <a class="mark" href="{up or './'}"><img src="{up}skiff.png" alt="">Skiff</a>
    <nav aria-label="Main">
      {links}
    </nav>
    <details class="menu">
      <summary>Menu</summary>
      <nav aria-label="Main">
        {links.replace(chr(10), chr(10) + "  ")}
      </nav>
    </details>
  </div>
</header>"""

def footer(up):
    return f"""<footer>
  <div class="wrap">
    <span>Skiff · MIT license · © 2026 Solutions Cay LLC</span>
    <a href="https://github.com/solutionscay/skiff">GitHub</a>
    <a href="https://github.com/solutionscay/skiff/wiki">Wiki</a>
    <a href="https://www.youtube.com/playlist?list=PLFZ-W0mLJPqY">YouTube</a>
    <a href="https://github.com/solutionscay/skiff/issues">Issues</a>
    <a href="{up}support/">Support</a>
    <a href="https://buy.stripe.com/6oU4gz5Ejb4hgsm9mRcZa04">Tip</a>
  </div>
</footer>"""

def render(p, old, css):
    up = "../" * p["path"].count("/")
    if "<body>" not in old:
        old = f"<body>\n\n{bar(up)}\n\n{old.strip()}\n\n{footer(up)}\n</body>\n</html>\n"
    body = old[old.index("<body>"):]
    body = re.sub(r'<header class="bar">.*?</header>', lambda m: bar(up), body, count=1, flags=re.S)
    body = re.sub(r"<footer>.*?</footer>", lambda m: footer(up), body, count=1, flags=re.S)
    return head(p, up, css) + body

def lastmod(rel, changed):
    if changed:
        return datetime.date.today().isoformat()
    out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return out or datetime.date.today().isoformat()

def dirty(rel):
    return subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=ROOT).returncode != 0

def main():
    check = "--check" in sys.argv
    css = hashlib.sha1(open(os.path.join(ROOT, "site.css"), "rb").read()).hexdigest()[:8]
    stale, urls = [], []
    for p in PAGES:
        rel = p["path"] + "index.html"
        f = os.path.join(ROOT, rel)
        old = open(f, encoding="utf-8").read()
        new = render(p, old, css)
        if new != old:
            stale.append(rel)
            if not check:
                open(f, "w", encoding="utf-8").write(new)
        urls.append((SITE + p["path"], lastmod(rel, new != old or dirty(rel))))
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += "".join(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls)
    sm += "</urlset>\n"
    smf = os.path.join(ROOT, "sitemap.xml")
    if open(smf, encoding="utf-8").read() != sm:
        stale.append("sitemap.xml")
        if not check:
            open(smf, "w", encoding="utf-8").write(sm)
    for s in stale:
        print(("stale: " if check else "wrote: ") + s)
    sys.exit(1 if check and stale else 0)

if __name__ == "__main__":
    main()
