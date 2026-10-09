/* SPDX-License-Identifier: MIT-0 */
"use strict";

function getElement(id) {
  return document.getElementById(id);
}

function createElement(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = String(text);
  if (className) element.className = className;
  return element;
}

// 表示するリンクは、認証情報を含まないHTTPS URLに限定します。
function safeUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === "https:" && !url.username && !url.password ? url.href : null;
  } catch {
    return null;
  }
}

function createLink(label, value) {
  const url = safeUrl(value);
  if (!url) return null;

  const link = createElement("a", label);
  link.href = url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  return link;
}

// ビルドメタデータを除き、数値部分とプレリリース識別子を別々に比較します。
function parseVersion(version) {
  const [core, prerelease] = version.split("+")[0].split(/-(.*)/s);
  return {
    core: core.split(".").map(BigInt),
    prerelease: prerelease?.split("."),
  };
}

function comparePrereleaseIdentifiers(left, right) {
  if (left === right) return 0;
  if (left === undefined || right === undefined) return left === undefined ? -1 : 1;

  const leftIsNumeric = /^\d+$/.test(left);
  const rightIsNumeric = /^\d+$/.test(right);
  if (leftIsNumeric !== rightIsNumeric) return leftIsNumeric ? -1 : 1;

  if (leftIsNumeric) return BigInt(left) > BigInt(right) ? 1 : -1;
  return left > right ? 1 : -1;
}

function comparePrereleaseVersions(left, right) {
  if (!left || !right) {
    if (left) return -1;
    return right ? 1 : 0;
  }

  const identifierCount = Math.max(left.length, right.length);
  for (let index = 0; index < identifierCount; index++) {
    const comparison = comparePrereleaseIdentifiers(left[index], right[index]);
    if (comparison !== 0) return comparison;
  }
  return 0;
}

function compareVersion(leftVersion, rightVersion) {
  const left = parseVersion(leftVersion);
  const right = parseVersion(rightVersion);

  for (let index = 0; index < 3; index++) {
    if (left.core[index] !== right.core[index]) {
      return left.core[index] > right.core[index] ? 1 : -1;
    }
  }
  return comparePrereleaseVersions(left.prerelease, right.prerelease);
}

function createPackageTags(manifest) {
  const tags = createElement("div", undefined, "tags");
  const values = [
    manifest.version,
    manifest.license,
    manifest.unity ? `Unity ${manifest.unity}+` : null,
  ];
  for (const value of values) {
    if (value) tags.append(createElement("span", value, "tag"));
  }
  return tags;
}

function createPackageLinks(manifest) {
  const navigation = createElement("nav");
  const links = [
    ["ドキュメント", manifest.documentationUrl],
    ["変更履歴", manifest.changelogUrl],
    ["ZIP", manifest.url],
  ];
  for (const [label, url] of links) {
    const link = createLink(label, url);
    if (link) navigation.append(link);
  }
  return navigation;
}

function createVersionHistory(record, sortedVersions) {
  const details = createElement("details");
  const list = createElement("ul");
  details.append(createElement("summary", `すべてのバージョン (${sortedVersions.length})`));

  for (const version of sortedVersions) {
    const item = createElement("li");
    const download = createLink(version, record.versions[version].url);
    item.append(download || createElement("span", version));
    list.append(item);
  }
  details.append(list);
  return details;
}

function packageCard(id, record) {
  const sortedVersions = Object.keys(record.versions).sort((left, right) =>
    compareVersion(right, left),
  );
  if (sortedVersions.length === 0) return null;

  // 安定版があれば優先し、なければ最新のプレリリースを表示します。
  const newestStableVersion = sortedVersions.find(
    (version) => !version.split("+")[0].includes("-"),
  );
  const displayedManifest = record.versions[newestStableVersion || sortedVersions[0]];
  const card = createElement("article", undefined, "package");
  card.append(
    createElement("h3", displayedManifest.displayName || id),
    createElement("p", id, "id"),
    createElement("p", displayedManifest.description || "説明はありません。", "description"),
    createPackageTags(displayedManifest),
    createPackageLinks(displayedManifest),
    createVersionHistory(record, sortedVersions),
  );
  card.dataset.search =
    `${id} ${displayedManifest.displayName || ""} ${displayedManifest.description || ""}`.toLocaleLowerCase();
  return card;
}

async function loadRepositoryData() {
  const responses = await Promise.all([
    fetch("./index.json", { cache: "no-store" }),
    fetch("./site.json", { cache: "no-store" }),
  ]);
  if (responses.some((response) => !response.ok)) throw new Error("listing fetch failed");

  const [repository, site] = await Promise.all(responses.map((response) => response.json()));
  return { repository, site };
}

function validateRepository(repository) {
  const url = safeUrl(repository.url);
  if (
    !url ||
    typeof repository.name !== "string" ||
    !repository.packages ||
    typeof repository.packages !== "object"
  ) {
    throw new Error("invalid listing");
  }
  return url;
}

function renderRepositoryHeader(repository, site, url) {
  document.title = repository.name;
  getElement("repo-name").textContent = repository.name;
  getElement("description").textContent =
    site.description || "ALCOM 向けパッケージを配信しています。";
  getElement("author").textContent = repository.author;
  getElement("repo-url").value = url;
  getElement("add-repo").href = `vcc://vpm/addRepo?url=${encodeURIComponent(url)}`;
  getElement("add-repo").hidden = false;
}

async function copyRepositoryUrl(url) {
  try {
    await navigator.clipboard.writeText(url);
    getElement("status").textContent = "URL をコピーしました。";
  } catch {
    getElement("repo-url").focus();
    getElement("repo-url").select();
    getElement("status").textContent =
      "URL を選択しました。Ctrl+C / Command+C でコピーしてください。";
  }
}

function enableCopyButton(url) {
  getElement("copy").disabled = false;
  getElement("copy").addEventListener("click", () => copyRepositoryUrl(url));
}

function updatePackageCount(count) {
  getElement("count").textContent = count;
  getElement("empty").hidden = count > 0;
}

function renderPackageList(packages) {
  const cards = Object.entries(packages)
    .sort(([leftId], [rightId]) => leftId.localeCompare(rightId))
    .map(([id, record]) => packageCard(id, record))
    .filter(Boolean);
  getElement("package-list").replaceChildren(...cards);
  updatePackageCount(cards.length);
  return cards;
}

function filterPackageCards(cards, query) {
  for (const card of cards) card.hidden = !card.dataset.search.includes(query);
  const visibleCount = cards.filter((card) => !card.hidden).length;
  updatePackageCount(visibleCount);
  getElement("empty").textContent = cards.length
    ? "一致するパッケージがありません。"
    : "公開されているパッケージはまだありません。";
}

function enableSearch(cards) {
  getElement("search").disabled = false;
  getElement("search").addEventListener("input", (event) => {
    const query = event.target.value.toLocaleLowerCase().trim();
    filterPackageCards(cards, query);
  });
}

function showLoadError() {
  getElement("description").textContent = "リポジトリ情報を読み込めませんでした。";
  getElement("status").textContent =
    "ページを再読み込みするか、JSON リンクからリポジトリ URL を取得してください。";
}

async function start() {
  try {
    const { repository, site } = await loadRepositoryData();
    const url = validateRepository(repository);
    renderRepositoryHeader(repository, site, url);
    enableCopyButton(url);
    const cards = renderPackageList(repository.packages);
    enableSearch(cards);
  } catch {
    showLoadError();
  }
}

start();
