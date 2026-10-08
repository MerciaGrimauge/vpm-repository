#!/usr/bin/env python3
# SPDX-License-Identifier: MIT-0
"""Collect registered public GitHub Releases into a VPM index, without fetching ZIPs."""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_JSON = 1024 * 1024


NAME = re.compile(r"[a-z0-9][a-z0-9_-]*(?:\.[a-z0-9][a-z0-9_-]*)+\Z")


SEMVER = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?\Z"
)


SHA256 = re.compile(r"[0-9a-fA-F]{64}\Z")


REPO = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+\Z")


class Invalid(ValueError):
    """Invalid input, reported without a traceback by the CLI."""


def require(condition, message):
    if not condition:
        raise Invalid(message)


def text(value, label):
    require(
        isinstance(value, str) and bool(value.strip()),
        f"{label}: nonempty string required",
    )
    return value


def object_value(value, label):
    require(isinstance(value, dict), f"{label}: object required")
    return value


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def finite_float(value):
    result = float(value)
    require(math.isfinite(result), "nonfinite JSON number")
    return result


def decode_json(data, label):
    require(len(data) <= MAX_JSON, f"{label}: JSON exceeds 1 MiB")
    try:
        return json.loads(
            data.decode("utf-8-sig"),
            object_pairs_hook=unique_object,
            parse_float=finite_float,
            parse_constant=lambda _: (_ for _ in ()).throw(
                Invalid("nonfinite JSON number")
            ),
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise Invalid(f"{label}: invalid UTF-8 JSON") from error


def read_json(file):
    with Path(file).open("rb") as stream:
        return decode_json(stream.read(MAX_JSON + 1), str(file))


def write_json(file, value):
    file = Path(file)
    file.parent.mkdir(parents=True, exist_ok=True)
    temporary = file.with_name(file.name + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(file)


def https_url(value, label, *, zip_file=False):
    text(value, label)
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise Invalid(f"{label}: invalid URL") from error
    require(
        parsed.scheme == "https"
        and parsed.hostname
        and not parsed.username
        and not parsed.password
        and not parsed.fragment
        and port in (None, 443)
        and not any(c.isspace() or ord(c) < 32 for c in value),
        f"{label}: public HTTPS URL required",
    )
    if zip_file:
        require(
            parsed.path.lower().endswith(".zip"), f"{label}: URL path must end in .zip"
        )
    return parsed


def version(value):
    text(value, "version")
    match = SEMVER.fullmatch(value)
    require(match is not None, f"invalid SemVer: {value}")
    prerelease = match[4]
    if prerelease:
        for part in prerelease.split("."):
            require(
                not (part.isdigit() and len(part) > 1 and part[0] == "0"),
                f"numeric prerelease identifier has leading zero: {value}",
            )
    return match


def manifest(value):
    result = copy.deepcopy(object_value(value, "manifest"))
    require(
        isinstance(result.get("name"), str) and NAME.fullmatch(result["name"]),
        "invalid package name",
    )
    version(result.get("version"))
    text(result.get("displayName"), "displayName")
    author = object_value(result.get("author"), "author")
    text(author.get("name"), "author.name")
    email = text(author.get("email"), "author.email")
    require(
        "@" in email and not any(c.isspace() for c in email), "invalid author.email"
    )
    text(
        result.get("license"),
        "license (explicit license declaration required)",
    )
    https_url(result.get("url"), "package.url", zip_file=True)
    if "zipSHA256" in result:
        require(
            isinstance(result["zipSHA256"], str)
            and SHA256.fullmatch(result["zipSHA256"]),
            "invalid zipSHA256",
        )
        result["zipSHA256"] = result["zipSHA256"].lower()
    if "vpmDependencies" in result:
        for name, constraint in object_value(
            result["vpmDependencies"], "vpmDependencies"
        ).items():
            require(NAME.fullmatch(name), f"invalid dependency name: {name}")
            text(constraint, f"dependency {name}")
    for field in ("documentationUrl", "changelogUrl"):
        if field in result:
            https_url(result[field], field)
    return result


def merge(packages, item):
    item = manifest(item)
    versions = packages.setdefault(item["name"], {"versions": {}})["versions"]
    old = versions.get(item["version"])
    require(
        old is None or old == item,
        f"published version changed: {item['name']}@{item['version']} (publish a new version)",
    )
    versions[item["version"]] = item


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class GitHub:
    """Fetch only GitHub API JSON and JSON manifest assets. Never fetch ZIPs."""

    ASSET_HOSTS = {
        "github.com",
        "release-assets.githubusercontent.com",
        "objects.githubusercontent.com",
    }

    def __init__(self, token=None):
        self.token = token
        self.opener = build_opener(NoRedirect())

    def json(self, url, *, asset=False):
        for _ in range(6):
            parsed = https_url(url, "GitHub request")
            require(
                parsed.hostname in (self.ASSET_HOSTS if asset else {"api.github.com"}),
                "unexpected GitHub request host",
            )
            headers = {
                "User-Agent": "vpm-public-release-collector",
                "Accept": "application/vnd.github+json",
            }
            if parsed.hostname == "api.github.com":
                headers["X-GitHub-Api-Version"] = "2022-11-28"
                if self.token:
                    headers["Authorization"] = f"Bearer {self.token}"
            try:
                with self.opener.open(
                    Request(url, headers=headers), timeout=30
                ) as response:
                    return decode_json(response.read(MAX_JSON + 1), "GitHub JSON")
            except HTTPError as error:
                if asset and error.code in (301, 302, 303, 307, 308):
                    url = error.headers.get("Location", "")
                    continue
                raise Invalid(
                    f"GitHub HTTP {error.code}; check public repository access / API rate limit"
                ) from error
            except (URLError, TimeoutError) as error:
                raise Invalid("GitHub request failed or timed out") from error
        raise Invalid("too many GitHub redirects")

    def pages(self, endpoint):
        for page in range(1, 101):
            data = self.json(
                f"https://api.github.com/{endpoint}?per_page=100&page={page}"
            )
            require(isinstance(data, list), "GitHub API list response required")
            yield from data
            if len(data) < 100:
                return
        raise Invalid(
            "GitHub pagination limit reached; use explicit release records for larger histories"
        )


def github_sources(config, packages, client):
    for source in config["githubRepos"]:
        repo = source["repo"]
        for release in client.pages(f"repos/{repo}/releases"):
            object_value(release, "GitHub release")
            if release.get("draft") or (
                release.get("prerelease") and not source.get("includePrerelease", False)
            ):
                continue
            release_id = release.get("id")
            require(
                isinstance(release_id, int) and release_id > 0,
                "invalid GitHub release id",
            )
            assets = list(client.pages(f"repos/{repo}/releases/{release_id}/assets"))
            manifests = [
                a
                for a in assets
                if a.get("name") == source.get("manifestAsset", "package.json")
            ]
            if not manifests:
                continue
            require(len(manifests) == 1, f"{repo}: ambiguous manifest asset")
            asset = manifests[0]
            require(
                isinstance(asset.get("size"), int) and 0 < asset["size"] <= MAX_JSON,
                "manifest asset exceeds limit",
            )
            item = object_value(
                client.json(asset.get("browser_download_url"), asset=True),
                "GitHub package manifest",
            )
            version(item.get("version"))
            require(
                isinstance(item.get("name"), str) and NAME.fullmatch(item["name"]),
                "invalid GitHub package name",
            )
            if source.get("packageName") and item["name"] != source["packageName"]:
                continue
            if version(item["version"])[4] and not source.get(
                "includePrerelease", False
            ):
                continue
            filename = source.get("zipAsset", "{name}-{version}.zip").format(
                name=item["name"], version=item["version"]
            )
            zips = [a for a in assets if a.get("name") == filename]
            require(len(zips) == 1, f"{repo}: expected one release asset {filename}")
            item["url"] = zips[0].get("browser_download_url")
            digest = zips[0].get("digest")
            if digest is not None:
                require(
                    isinstance(digest, str)
                    and digest.startswith("sha256:")
                    and SHA256.fullmatch(digest[7:]),
                    "invalid GitHub ZIP digest",
                )
                if "zipSHA256" in item:
                    require(
                        isinstance(item["zipSHA256"], str)
                        and SHA256.fullmatch(item["zipSHA256"])
                        and item["zipSHA256"].lower() == digest[7:].lower(),
                        "manifest/GitHub ZIP digest mismatch",
                    )
                item["zipSHA256"] = digest[7:]
            merge(packages, item)


OWNER = "MerciaGrimauge"
ROOT = Path(__file__).resolve().parents[1]
FIELDS = frozenset(
    {
        "name",
        "version",
        "displayName",
        "description",
        "unity",
        "unityRelease",
        "author",
        "license",
        "licensesUrl",
        "documentationUrl",
        "changelogUrl",
        "url",
        "zipSHA256",
        "vpmDependencies",
        "dependencies",
        "legacyFolders",
        "legacyFiles",
        "legacyPackages",
        "keywords",
        "samples",
        "type",
        "hideInEditor",
    }
)
SENSITIVE = re.compile(
    r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|"
    r"AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY|"
    r"\b(?:sk|xox[baprs])-[A-Za-z0-9_-]{20,}|"
    r"(?<![A-Za-z0-9+.-])[A-Za-z]:[\\/]|/[U]sers/|/[h]ome/|"
    r"Co-authored-by:|<INSTRUCTIONS>|会話ログ|作業指示|監査結果|開発記録",
    re.IGNORECASE,
)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SECRET_QUERY = re.compile(r"(?:token|secret|password|signature|api[_-]?key)=", re.I)


def check_public_text(value, email):
    if isinstance(value, dict):
        for key, child in value.items():
            check_public_text(key, email)
            check_public_text(child, email)
    elif isinstance(value, list):
        for child in value:
            check_public_text(child, email)
    elif isinstance(value, str):
        require(not SENSITIVE.search(value), "unexpected sensitive text")
        require(
            all(found == email for found in EMAIL.findall(value)), "unexpected email"
        )
        require(not SECRET_QUERY.search(value), "credential-bearing text")


def validate_sources(value):
    require(isinstance(value, list), "sources must be an array")
    seen = set()
    for source in value:
        require(isinstance(source, dict), "source must be an object")
        require(
            set(source)
            == {"repo", "packageName", "manifestAsset", "includePrerelease"},
            "unexpected source fields",
        )
        require(
            isinstance(source["repo"], str) and REPO.fullmatch(source["repo"]),
            "invalid repository",
        )
        require(
            source["repo"].split("/")[0] == OWNER
            and source["repo"].split("/")[1] not in (".", ".."),
            "unexpected repository owner",
        )
        require(
            isinstance(source["packageName"], str)
            and NAME.fullmatch(source["packageName"]),
            "invalid package name",
        )
        asset = source["manifestAsset"]
        require(
            isinstance(asset, str) and re.fullmatch(r"[A-Za-z0-9_.-]+\.json", asset),
            "invalid manifest asset name",
        )
        require(type(source["includePrerelease"]) is bool, "invalid prerelease flag")
        require(source["packageName"] not in seen, "duplicate package registration")
        seen.add(source["packageName"])
    return value


def validate_index(value):
    require(
        isinstance(value, dict)
        and set(value) == {"name", "id", "url", "author", "packages"},
        "unexpected listing fields",
    )
    require(value["name"] == "MerciaGrimauge VPM Repository", "unexpected listing name")
    require(value["id"] == "io.github.merciagrimauge.vpm", "unexpected listing ID")
    require(
        value["url"] == "https://merciagrimauge.github.io/vpm-repository/index.json",
        "unexpected listing URL",
    )
    require(isinstance(value["packages"], dict), "invalid package table")
    for name, record in value["packages"].items():
        require(
            isinstance(record, dict) and set(record) == {"versions"},
            "invalid package record",
        )
        require(isinstance(record["versions"], dict), "invalid version table")
        for number, item in record["versions"].items():
            require(
                isinstance(item, dict)
                and item.get("name") == name
                and item.get("version") == number,
                "package keys do not match manifest",
            )
            manifest(item)
    return value


def synchronize(root, client=None):
    # Anonymous requests make inaccessible repositories fail before any collection.
    client = client or GitHub()
    previous = validate_index(read_json(root / "index.json"))
    sources = validate_sources(read_json(root / "sources.json"))
    profile = client.json(f"https://api.github.com/users/{OWNER}")
    require(
        profile.get("login") == OWNER and type(profile.get("id")) is int,
        "invalid public owner",
    )
    require(
        previous["author"]
        in {OWNER, profile.get("name"), f"{profile.get('name')} ({OWNER})"},
        "unexpected listing author",
    )
    email = f"{profile['id']}+{OWNER}@users.noreply.github.com"
    for repository in {source["repo"] for source in sources}:
        metadata = client.json(f"https://api.github.com/repos/{repository}")
        require(
            metadata.get("private") is False
            and metadata.get("full_name") == repository,
            "only registered public repositories are supported",
        )
    packages = copy.deepcopy(previous["packages"])
    github_sources({"githubRepos": sources}, packages, client)
    repositories = {source["packageName"]: source["repo"] for source in sources}
    require(
        set(packages) <= set(previous["packages"]) | set(repositories),
        "unregistered package",
    )
    added = 0
    for name, record in packages.items():
        for number, item in record["versions"].items():
            if number in previous["packages"].get(name, {}).get("versions", {}):
                require(
                    item == previous["packages"][name]["versions"][number],
                    "published version changed",
                )
                continue
            require(set(item) <= FIELDS, "unexpected manifest fields")
            require(
                set(item["author"]) <= {"name", "email", "url"},
                "unexpected author fields",
            )
            require(
                item["author"]["name"]
                in {OWNER, profile.get("name"), f"{profile.get('name')} ({OWNER})"},
                "unexpected package author",
            )
            require(item["author"]["email"] == email, "unexpected author email")
            parsed = https_url(item["url"], "package URL", zip_file=True)
            require(
                parsed.hostname == "github.com"
                and parsed.path.startswith(f"/{repositories[name]}/releases/download/")
                and not parsed.query,
                "unexpected package URL",
            )
            require(SHA256.fullmatch(item.get("zipSHA256", "")), "ZIP digest required")
            for field in ("documentationUrl", "changelogUrl", "licensesUrl"):
                if field in item:
                    require(
                        not https_url(item[field], field).query, "unexpected URL query"
                    )
            if "url" in item["author"]:
                require(
                    item["author"]["url"] == f"https://github.com/{OWNER}",
                    "unexpected author URL",
                )
            added += 1
    result = previous | {"packages": packages}
    check_public_text(result, email)
    if result != previous:
        write_json(root / "index.json", result)
    return added


def main():
    try:
        added = synchronize(ROOT)
        print(f"Collected {added} new package versions")
        return 0
    except (Invalid, OSError, KeyError, TypeError, ValueError):
        print(
            "Collection failed; verify public Release assets and source configuration",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
