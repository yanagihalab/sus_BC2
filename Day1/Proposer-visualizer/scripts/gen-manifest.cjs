#!/usr/bin/env node
/* scripts/gen-manifest.cjs
 * public/out または out にある .csv を列挙して index.json を生成
 * - 優先探索: public/out -> out
 * - 書き込み不可なら out/index.json へフォールバック
 */
const fs = require("fs");
const path = require("path");

const cwd = process.cwd();
const candidates = [
  path.resolve(cwd, "public", "out"),
  path.resolve(cwd, "out"),
];

function listCsv(dir) {
  try {
    return fs
      .readdirSync(dir, { withFileTypes: true })
      .filter((ent) => ent.isFile() && /\.csv$/i.test(ent.name))
      .map((ent) => ent.name)
      .sort();
  } catch {
    return [];
  }
}

function ensureDir(dir) {
  try {
    fs.mkdirSync(dir, { recursive: true });
  } catch (_) {}
}

let srcDir = null;
for (const dir of candidates) {
  try {
    const st = fs.statSync(dir);
    if (st.isDirectory()) {
      srcDir = dir;
      break;
    }
  } catch (_) {}
}

if (!srcDir) {
  console.error('[manifest] No "public/out" or "out" directory found.');
  process.exit(1);
}

const files = listCsv(srcDir);
const payload = {
  generatedAt: new Date().toISOString(),
  files, // 例: ["local_proposer_sequence.csv","local_proposer_transitions.csv","local_proposer_nodes.csv"]
};

function writeManifest(dstDir) {
  const dst = path.join(dstDir, "index.json");
  ensureDir(dstDir);
  fs.writeFileSync(dst, JSON.stringify(payload, null, 2));
  console.log(`[manifest] wrote ${dst} (${files.length} csv)`);
  return true;
}

let wrote = false;

// まず srcDir に書き込みを試みる
try {
  wrote = writeManifest(srcDir);
} catch (err) {
  console.warn(`[manifest] cannot write to ${srcDir}: ${err.message}`);
}

// public/out が書き込み不可のケース（ro マウント等）では out/ にフォールバック
if (!wrote && srcDir.endsWith(path.sep + path.join("public", "out"))) {
  const fallback = path.resolve(cwd, "out");
  try {
    wrote = writeManifest(fallback);
  } catch (err) {
    console.error(`[manifest] fallback failed to ${fallback}: ${err.message}`);
    process.exit(2);
  }
}

if (!wrote) {
  // srcDir が out/ なのに書けない場合など
  console.error("[manifest] failed to write index.json.");
  process.exit(3);
}

console.log(`[manifest] ${files.length} csv -> index.json ready`);
