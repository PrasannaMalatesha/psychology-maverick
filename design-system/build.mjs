#!/usr/bin/env node
/* Inline the shared design-system assets into each prototype page so every file
   opens standalone (file://, any browser, no server, no symlink).
   design-system/ stays the single editable source; run this to re-propagate:
       node design-system/build.mjs
   Idempotent: first run replaces the <link>/<script src> tags with marked inline
   blocks; later runs refresh the content inside those marks. */
import { readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const DS = dirname(fileURLToPath(import.meta.url));
const PROTO = join(DS, '..', 'design', 'prototype');
const read = (n) => readFileSync(join(DS, n), 'utf8');

const ASSETS = {
  'tokens.css': { tag: 'style', css: read('tokens.css') },
  'app.css':    { tag: 'style', css: read('app.css') },
  'icons.js':   { tag: 'script', js: read('icons.js') },
  'store.js':   { tag: 'script', js: read('store.js') },
  'shell.js':   { tag: 'script', js: read('shell.js') },
};

function inlineOne(html, name, a) {
  const open = `<${a.tag} data-ds="${name}">`;
  const close = `</${a.tag}>`;
  // Escape any literal </script> or </style> in the payload (e.g. inside a
  // comment's usage example) so the inlined block isn't closed prematurely by
  // the HTML parser. A backslash before the slash is inert in JS/CSS but breaks
  // the parser's exact "</tag" match.
  const raw = a.tag === 'style' ? a.css : a.js;
  const payload = raw.replace(/<\/(script|style)/gi, '<\\/$1');
  const block = `${open}\n${payload}\n${close}`;

  // re-run: refresh content between existing marks. Anchor the close on a
  // leading newline so a stray </tag> inside the payload (e.g. in a comment)
  // can't end the match early.
  const marked = new RegExp(`<${a.tag} data-ds="${name.replace('.', '\\.')}">[\\s\\S]*?\\n</${a.tag}>`);
  if (marked.test(html)) return html.replace(marked, block);

  // first run: swap the external reference for the inline block
  if (a.tag === 'style') {
    const link = new RegExp(`<link[^>]*href="[^"]*design-system/${name.replace('.', '\\.')}"[^>]*>`);
    if (link.test(html)) return html.replace(link, block);
  } else {
    const script = new RegExp(`<script[^>]*src="[^"]*design-system/${name.replace('.', '\\.')}"[^>]*></script>`);
    if (script.test(html)) return html.replace(script, block);
  }
  return html; // asset not used on this page
}

let touched = 0;
for (const file of readdirSync(PROTO).filter((f) => f.endsWith('.html'))) {
  const path = join(PROTO, file);
  let html = readFileSync(path, 'utf8');
  const before = html;
  for (const [name, a] of Object.entries(ASSETS)) html = inlineOne(html, name, a);
  if (html !== before) { writeFileSync(path, html); touched++; console.log('inlined →', file); }
}
console.log(`\nDone. ${touched} page(s) updated. Every page is now self-contained.`);
