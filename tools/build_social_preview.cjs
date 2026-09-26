#!/usr/bin/env node
/* Build the GitHub share card from an actual comparison frame.
 * Requires Node.js, FFmpeg, and Sharp (`npm install --no-save sharp`).
 * Run from anywhere: node tools/build_social_preview.cjs [--replace]
 * This does not generate or retouch video. It scales frame 32 of the
 * published comparison and adds project branding outside the footage.
 */
const fs = require('node:fs');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const sharp = require('sharp');

async function main() {
  const args = process.argv.slice(2);
  if (args.some(arg => arg !== '--replace')) throw new Error('Usage: build_social_preview.cjs [--replace]');
  const assets = path.resolve(__dirname, '../assets');
  const output = path.join(assets, 'social-preview.png');
  if (fs.existsSync(output) && !args.includes('--replace')) {
    throw new Error('social-preview.png exists; pass --replace to rebuild it.');
  }
  const result = spawnSync('ffmpeg', ['-v', 'error', '-i', path.join(assets, 'before-after.mp4'),
    '-vf', 'select=eq(n\\,32)', '-frames:v', '1', '-f', 'image2pipe', '-c:v', 'png', '-'],
    {maxBuffer: 16 * 1024 * 1024});
  if (result.error) throw result.error;
  if (result.status !== 0) throw new Error(result.stderr.toString());
  const frame = await sharp(result.stdout).resize(1184, 392).png().toBuffer();
  const typography = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="640">
    <rect width="1280" height="640" fill="#101820"/>
    <rect x="48" y="32" width="7" height="19" rx="2" fill="#b6f36b"/>
    <g font-family="Arial,Helvetica,sans-serif">
      <text x="68" y="48" font-size="19" letter-spacing="1.5" fill="#b6f36b">MINIMAX H3 / WAN2GP</text>
      <text x="1232" y="48" text-anchor="end" font-size="18" fill="#aabbb1">yjrocks712 / H3-Seamless</text>
      <text x="45" y="118" font-size="68" font-weight="700" fill="#f4f5eb">H3 Seamless</text>
      <text x="48" y="163" font-size="29" fill="#f4f5eb">Keep the scene going.</text>
      <text x="1232" y="161" text-anchor="end" font-size="21" fill="#b6f36b">40-second demo · 3 windows · 2 handoffs</text>
      <text x="48" y="620" font-size="21" fill="#f4f5eb">Video continuation. Real before / after. Full method.</text>
      <text x="1232" y="620" text-anchor="end" font-size="16" fill="#aabbb1">Methodology + footage release</text>
    </g>
  </svg>`);
  const card = await sharp(typography).composite([{input: frame, left: 48, top: 192}])
    .png({compressionLevel: 9}).toBuffer();
  if (card.length >= 1_000_000) throw new Error('Card exceeds the GitHub preview size target.');
  fs.writeFileSync(output, card, {flag: args.includes('--replace') ? 'w' : 'wx'});
  console.log(`Built 1280x640 social-preview.png (${card.length} bytes) from comparison frame 32.`);
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
