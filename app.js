/* SPDX-License-Identifier: MIT-0 */
"use strict";
const byId = (id) => document.getElementById(id);
const node = (tag, value, className) => {
  const result = document.createElement(tag);
  if (value !== undefined) result.textContent = String(value);
  if (className) result.className = className;
  return result;
};
function safeUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === "https:" && !url.username && !url.password ? url.href : null;
  } catch { return null; }
}
function compareVersion(a, b) {
  const parse = (v) => {
    const [core, pre] = v.split("+")[0].split(/-(.*)/s);
    return {core: core.split(".").map(BigInt), pre: pre?.split(".")};
  };
  const left = parse(a), right = parse(b);
  for (let i = 0; i < 3; i++) {
    if (left.core[i] !== right.core[i]) return left.core[i] > right.core[i] ? 1 : -1;
  }
  if (!left.pre || !right.pre) return left.pre ? -1 : right.pre ? 1 : 0;
  for (let i = 0; i < Math.max(left.pre.length, right.pre.length); i++) {
    const x = left.pre[i], y = right.pre[i];
    if (x === y) continue;
    if (x === undefined || y === undefined) return x === undefined ? -1 : 1;
    const nx = /^\d+$/.test(x), ny = /^\d+$/.test(y);
    if (nx !== ny) return nx ? -1 : 1;
    return nx ? (BigInt(x) > BigInt(y) ? 1 : -1) : (x > y ? 1 : -1);
  }
  return 0;
}
function link(label, value) {
  const url = safeUrl(value);
  if (!url) return null;
  const result = node("a", label);
  result.href = url;
  result.target = "_blank";
  result.rel = "noopener noreferrer";
  return result;
}
function packageCard(id, record) {
  const versions = Object.keys(record.versions).sort((a, b) => compareVersion(b, a));
  if (!versions.length) return null;
  const stable = versions.find(v => !v.split("+")[0].includes("-"));
  const latest = record.versions[stable || versions[0]];
  const card = node("article", undefined, "package");
  card.append(node("h3", latest.displayName || id), node("p", id, "id"),
    node("p", latest.description || "説明はありません。", "description"));
  const tags = node("div", undefined, "tags");
  for (const value of [latest.version, latest.license, latest.unity ? `Unity ${latest.unity}+` : null]) {
    if (value) tags.append(node("span", value, "tag"));
  }
  card.append(tags);
  const nav = node("nav");
  for (const [label, value] of [["ドキュメント", latest.documentationUrl], ["変更履歴", latest.changelogUrl], ["ZIP", latest.url]]) {
    const item = link(label, value);
    if (item) nav.append(item);
  }
  card.append(nav);
  const details = node("details"), list = node("ul");
  details.append(node("summary", `すべてのバージョン (${versions.length})`));
  for (const v of versions) {
    const item = node("li"), download = link(v, record.versions[v].url);
    item.append(download || node("span", v));
    list.append(item);
  }
  details.append(list);
  card.append(details);
  card.dataset.search = `${id} ${latest.displayName || ""} ${latest.description || ""}`.toLocaleLowerCase();
  return card;
}
async function start() {
  try {
    const responses = await Promise.all([fetch("./index.json", {cache: "no-store"}), fetch("./site.json", {cache: "no-store"})]);
    if (responses.some(r => !r.ok)) throw new Error("listing fetch failed");
    const [repo, site] = await Promise.all(responses.map(r => r.json()));
    const url = safeUrl(repo.url);
    if (!url || typeof repo.name !== "string" || !repo.packages || typeof repo.packages !== "object") throw new Error("invalid listing");
    document.title = repo.name;
    byId("repo-name").textContent = repo.name;
    byId("description").textContent = site.description || "VCC / ALCOM 用パッケージを配信しています。";
    byId("author").textContent = repo.author;
    byId("repo-url").value = url;
    byId("add-repo").href = `vcc://vpm/addRepo?url=${encodeURIComponent(url)}`;
    byId("add-repo").hidden = false;
    byId("copy").disabled = false;
    byId("copy").addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(url);
        byId("status").textContent = "URL をコピーしました。";
      } catch {
        byId("repo-url").focus(); byId("repo-url").select();
        byId("status").textContent = "URL を選択しました。Ctrl+C / Command+C でコピーしてください。";
      }
    });
    const cards = Object.entries(repo.packages).sort(([a], [b]) => a.localeCompare(b))
      .map(([id, record]) => packageCard(id, record)).filter(Boolean);
    byId("package-list").replaceChildren(...cards);
    byId("count").textContent = cards.length;
    byId("empty").hidden = cards.length > 0;
    byId("search").disabled = false;
    byId("search").addEventListener("input", (event) => {
      const query = event.target.value.toLocaleLowerCase().trim();
      for (const card of cards) card.hidden = !card.dataset.search.includes(query);
      const count = cards.filter(card => !card.hidden).length;
      byId("count").textContent = count;
      byId("empty").hidden = count > 0;
      byId("empty").textContent = cards.length ? "一致するパッケージがありません。" : "公開されているパッケージはまだありません。";
    });
  } catch {
    byId("description").textContent = "リポジトリ情報を読み込めませんでした。";
    byId("status").textContent = "ページを再読み込みするか、JSON リンクからリポジトリ URL を取得してください。";
  }
}
start();
