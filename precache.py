#!/usr/bin/env python3
"""Precache the Minecraft files ForgeGradle 1.2 can no longer download.

ForgeGradle 1.2 fetches the version json, the asset index and the client and server
jars from Mojang's retired S3 bucket, and the asset objects over plain http, which
Mojang's servers now refuse. This script downloads the same files from Mojang's
current (piston) servers, checks each against Mojang's SHA-1, and puts them where
ForgeGradle looks for them. build.gradle disables ForgeGradle's own download tasks
for the S3 files, so run this before the first gradlew setupDecompWorkspace.

Uses GRADLE_USER_HOME when set, like gradlew; otherwise ~/.gradle.
"""
import hashlib, json, os, re, urllib.request
from concurrent.futures import ThreadPoolExecutor

MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
ASSET_URL = "https://resources.download.minecraft.net/%s/%s"

def fetch(url, sha1):
    for attempt in range(3):
        try:
            data = urllib.request.urlopen(url, timeout=60).read()
        except OSError:
            if attempt == 2:
                raise
            continue
        if hashlib.sha1(data).hexdigest() == sha1:
            return data
    raise SystemExit("%s: does not match its SHA-1 %s" % (url, sha1))

def cached(path, sha1):
    if not os.path.isfile(path):
        return False
    with open(path, "rb") as fh:
        return hashlib.sha1(fh.read()).hexdigest() == sha1

def precache(url, sha1, path):
    if not cached(path, sha1):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path + ".part", "wb") as fh:
            fh.write(fetch(url, sha1))
        os.replace(path + ".part", path)

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "build.gradle")) as fh:
        mc = re.search(r'version\s*=\s*"(\d[\d.]*)-', fh.read()).group(1)
    home = os.environ.get("GRADLE_USER_HOME") or os.path.join(os.path.expanduser("~"), ".gradle")
    cache = os.path.join(home, "caches", "minecraft")
    print("Precaching Minecraft %s for ForgeGradle in %s" % (mc, cache))

    with urllib.request.urlopen(MANIFEST, timeout=60) as fh:
        entry = next(v for v in json.load(fh)["versions"] if v["id"] == mc)
    version_json = os.path.join(cache, "versionJsons", mc + ".json")
    precache(entry["url"], entry["sha1"], version_json)
    with open(version_json, "rb") as fh:
        version = json.load(fh)

    index = version["assetIndex"]
    index_json = os.path.join(cache, "assets", "indexes", version["assets"] + ".json")
    precache(index["url"], index["sha1"], index_json)
    for side, path in (("client", "minecraft/%s/minecraft-%s.jar"), ("server", "minecraft_server/%s/minecraft_server-%s.jar")):
        download = version["downloads"][side]
        precache(download["url"], download["sha1"], os.path.join(cache, "net", "minecraft", *(path % (mc, mc)).split("/")))

    with open(index_json, "rb") as fh:
        hashes = sorted(set(o["hash"] for o in json.load(fh)["objects"].values()))
    with ThreadPoolExecutor(16) as pool:
        list(pool.map(lambda h: precache(ASSET_URL % (h[:2], h), h, os.path.join(cache, "assets", "objects", h[:2], h)), hashes))
    print("Done: version json, asset index, client and server jars, %d asset objects" % len(hashes))

if __name__ == "__main__":
    main()
