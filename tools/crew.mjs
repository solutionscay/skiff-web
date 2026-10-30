#!/usr/bin/env node
// The crew row: Admiral (the mascot head) and five Skippers, each in a theme's main color
// (crates/skiff-core/themes in the skiff repo). Writes the faces between the
// <!-- crew --> markers in index.html and tools/social-preview.html. With a
// path, it also writes the README banner there (docs/crew.svg in skiff):
//
//     node tools/crew.mjs [../skiff/docs/crew.svg]
//
// The faces come from skipper-avatar.mjs, a copy of the app's generator.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { skipperAvatar, admiralAvatar } from "./skipper-avatar.mjs";

// rhythm() reads the page clock; at 0 the phases stay the same on every run.
performance.now = () => 0;

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));

const CREW = [
  ["Admiral", "#8eb4ff"], // Blue Note, as the mascot's cap band
  ["atlas", "#4fd4ff"],   // Adriatic
  ["harbor", "#34d07c"],  // Emerald
  ["devbox", "#ffcf3f"],  // Macaw
  ["skiff", "#ff7f2a"],   // Afterburner
  ["tide", "#ff52b0"],    // Flamingo
];
const face = (name) => (name === "Admiral" ? admiralAvatar() : skipperAvatar(name));

// The blink and the head turn from apps/desktop/src/styles/skippers.css.
const BLINK = `.skipper-face .sk-eyes { transform-box: fill-box; transform-origin: center; animation: var(--blink-anim, sk-blink) var(--blink, 5s) var(--blink-delay, 0s) infinite steps(1, end); }
.skipper-face :is(.sk-turn, .sk-cap, .sk-front) { animation-duration: var(--face-turn, 42s); animation-delay: var(--face-turn-delay, 0s); animation-iteration-count: infinite; animation-timing-function: ease-in-out; }
.skipper-face .sk-turn { transform-origin: 16px 16px; animation-name: sk-lean; }
.skipper-face .sk-cap { transform-box: fill-box; transform-origin: center; animation-name: sk-capslide; }
.skipper-face .sk-front { transform-box: fill-box; transform-origin: center; animation-name: sk-slide; }
@keyframes sk-blink { 0% { transform: scaleY(1); } 97.4% { transform: scaleY(0.1); } 100% { transform: scaleY(1); } }
@keyframes sk-blink2 { 0% { transform: scaleY(1); } 93.6% { transform: scaleY(0.1); } 95.4% { transform: scaleY(1); } 97.4% { transform: scaleY(0.1); } 100% { transform: scaleY(1); } }
/* the three turns, at 30 %, 63 % and 96 % of the cycle: 0.6 % in, 2.9 % held, 0.6 % back */
@keyframes sk-lean {
  0%, 30%, 34.1%, 63%, 67.1%, 100% { transform: translate(0, 0) scaleX(1); }
  30.6%, 33.5% { transform: translate(calc(var(--dir, 1) * 0.45px), 0) scaleX(0.97); }
  63.6%, 66.5% { transform: translate(calc(var(--dir, 1) * -0.45px), 0) scaleX(0.97); }
}
@keyframes sk-capslide {
  0%, 30%, 34.1%, 63%, 67.1%, 95%, 99.1%, 100% { transform: translate(0, 0) scaleX(1); }
  30.6%, 33.5% { transform: translate(calc(var(--dir, 1) * 0.5px), 0) scaleX(0.97); }
  63.6%, 66.5% { transform: translate(calc(var(--dir, 1) * -0.5px), 0) scaleX(0.97); }
  95.6%, 98.5% { transform: translate(0, -0.5px) scaleX(1); }
}
@keyframes sk-slide {
  0%, 30%, 34.1%, 63%, 67.1%, 95%, 99.1%, 100% { transform: translate(0, 0) scaleX(1); }
  30.6%, 33.5% { transform: translate(calc(var(--dir, 1) * 1.5px), 0) scaleX(0.92); }
  63.6%, 66.5% { transform: translate(calc(var(--dir, 1) * -1.5px), 0) scaleX(0.92); }
  95.6%, 98.5% { transform: translate(0, -1px) scaleX(1); }
}
@media (prefers-reduced-motion: reduce) { .skipper-face :is(.sk-eyes, .sk-look, .sk-front, .sk-cap, .sk-turn) { animation: none; } }`;

const LABEL = "The Skiff crew: Admiral and five Skippers";
const row = (indent) =>
  `<div class="crew" role="img" aria-label="${LABEL}">\n`
  + CREW.map(([n, c]) => `${indent}  <span class="skipper-face" style="--pc:${c}">${face(n)}</span>\n`).join("")
  + `${indent}</div>`;

function splice(rel, indent) {
  const f = path.join(ROOT, rel);
  const old = fs.readFileSync(f, "utf8");
  const re = /<!-- crew -->[\s\S]*?<!-- \/crew -->/;
  if (!re.test(old)) throw new Error(`no <!-- crew --> markers in ${rel}`);
  const out = old.replace(re, `<!-- crew -->\n${indent}${row(indent)}\n${indent}<!-- /crew -->`);
  if (out !== old) { fs.writeFileSync(f, out); console.log(`wrote: ${rel}`); }
}

// The README banner: the wordmark (Lilita One as outlines, so it needs no
// font) and the six faces, 64 px each, on the site's dark panel.
function banner(file) {
  const W = 880, H = 176, S = 64, GAP = 16;
  const x0 = W - 48 - CREW.length * S - (CREW.length - 1) * GAP;
  const mark = fs.readFileSync(path.join(ROOT, "tools", "skiff-wordmark.path"), "utf8").trim();
  const faces = CREW.map(([n, c], i) =>
    `<g class="skipper-face" style="--pc:${c}" transform="translate(${x0 + i * (S + GAP)} ${(H - S) / 2}) scale(${S / 32})">${face(n).replace("<svg ", '<svg width="32" height="32" ')}</g>`).join("\n");
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="Skiff, with ${LABEL.slice(10)}">
<title>Skiff</title>
<style>
${BLINK}
</style>
<rect x="0.5" y="0.5" width="${W - 1}" height="${H - 1}" rx="12" fill="#0f1216" stroke="#232a33"/>
<path transform="translate(48 ${H / 2 + 35})" fill="#e6e8eb" d="${mark}"/>
${faces}
</svg>
`;
  fs.writeFileSync(file, svg);
  console.log(`wrote: ${file}`);
}

splice("index.html", "      ");
splice("tools/social-preview.html", "    ");
if (process.argv[2]) banner(path.resolve(process.argv[2]));
