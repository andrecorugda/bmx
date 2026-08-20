#!/usr/bin/env python3
# not-burxt: standalone — CI's Node-only job; in Burxt, BMX's own suite would need BMX's first host installed
"""Package the extension as a .vsix, with no toolchain.

    python3 editors/vscode/pack.py            # writes bmx.vsix here
    code --install-extension editors/vscode/bmx.vsix

Adapted from Burxt's packer, which is the same three-part archive and the same
promise: this directory needs no toolchain to use. Two differences, both real:
BMX ships no `extension.js` because it has no language server (see README.md for
why the diagnostics are library functions instead), and it declares itself
runnable on the UI side because a grammar has nothing to spawn.

A .vsix is a ZIP with three things in it: an OPC content-types map, a VSIX
manifest, and the extension under `extension/`. `vsce` does more than this —
linting, dependency bundling, marketplace checks — but all of that is for
publishing, and none of it is needed to install locally. Since the extension has
no npm dependencies, a packer in the standard library is the whole job, and it
keeps the promise that this directory needs no toolchain to use.

Why package at all rather than symlinking the folder into the extensions
directory: an installed extension is registered, versioned, upgradable and
uninstallable through the normal UI, and it is the same shape everyone else's
extensions have. A symlink works, until something scans the registry and does not
find you.
"""

import json
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Everything that belongs in the package. Listed rather than globbed, so a stray
# file in the directory never ships by accident.
FILES = [
    "package.json",
    "extension.js",
    # **The reference implementation ships INSIDE the extension**, so the preview renders with no
    # toolchain installed. Copied by `pack.py` from the repository root rather than duplicated in
    # this directory, because two copies of a parser is how they drift.
    "reference/bmx.mjs",
    "language-configuration.json",
    "syntaxes/bmx.tmLanguage.json",
    "icon.png",
    "file-icon.png",
    "README.md",
]

CONTENT_TYPES = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension=".json" ContentType="application/json"/>
  <Default Extension=".js" ContentType="application/javascript"/>
  <Default Extension=".png" ContentType="image/png"/>
  <Default Extension=".svg" ContentType="image/svg+xml"/>
  <Default Extension=".md" ContentType="text/markdown"/>
  <Default Extension=".xml" ContentType="text/xml"/>
  <Default Extension=".vsixmanifest" ContentType="text/xml"/>
</Types>
"""


def escape(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def manifest(pkg):
    tags = ",".join(pkg.get("keywords", []))
    categories = ",".join(pkg.get("contributes", {}) and pkg.get("categories", []))
    # A grammar spawns nothing, so unlike Burxt's this works on either side of a
    # remote — and saying so is what makes highlighting work in vscode.dev and in
    # a container without the extension being installed twice.
    kind = ",".join(pkg.get("extensionKind", ["ui", "workspace"]))
    return f"""<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">
  <Metadata>
    <Identity Language="en-US" Id="{escape(pkg['name'])}" Version="{escape(pkg['version'])}" Publisher="{escape(pkg['publisher'])}"/>
    <DisplayName>{escape(pkg.get('displayName', pkg['name']))}</DisplayName>
    <Description xml:space="preserve">{escape(pkg.get('description', ''))}</Description>
    <Tags>{escape(tags)}</Tags>
    <Categories>{escape(categories)}</Categories>
    <GalleryFlags>Public</GalleryFlags>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="{escape(pkg['engines']['vscode'])}"/>
      <Property Id="Microsoft.VisualStudio.Code.ExtensionDependencies" Value=""/>
      <Property Id="Microsoft.VisualStudio.Code.ExtensionPack" Value=""/>
      <Property Id="Microsoft.VisualStudio.Code.ExtensionKind" Value="{escape(kind)}"/>
      <Property Id="Microsoft.VisualStudio.Services.Links.Source" Value="{escape(pkg.get('repository', {}).get('url', ''))}"/>
    </Properties>
    <Icon>extension/icon.png</Icon>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code"/>
  </Installation>
  <Dependencies/>
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/>
    <Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/README.md" Addressable="true"/>
    <Asset Type="Microsoft.VisualStudio.Services.Icons.Default" Path="extension/icon.png" Addressable="true"/>
  </Assets>
</PackageManifest>
"""


def main():
    pkg = json.loads((HERE / "package.json").read_text())

    # **The filename carries no version, and that is a fix rather than laziness.** It used to be
    # `bmx-<version>.vsix`, which put the version in seven places — two READMEs, three doc pages, this
    # docstring, CI — so bumping it broke every install command in the repository. The result was
    # predictable and measured: **thirty commits changed the package and the version never moved off
    # 0.1.0.** VS Code decides whether to offer an update by comparing versions, so anyone who installed
    # the first 0.1.0 has a grammar that knows only the 0.6 fence and will never be told otherwise.
    #
    # A version belongs where a tool reads it — `package.json`, and the manifest built from it. A stable
    # filename means the install command in the docs is correct forever, and bumping the version costs
    # one edit in one file. `tests/extension.py` fails if that edit is not made.
    out = HERE / f"{pkg['name']}.vsix"

    # `reference/bmx.js` lives at the repository root, not here. Staged rather than symlinked,
    # because a .vsix is a zip and a symlink in one is a file nobody can read.
    staged = HERE / "reference"
    staged.mkdir(exist_ok=True)
    (staged / "bmx.mjs").write_text((HERE.parent.parent / "reference" / "bmx.js").read_text())

    missing = [f for f in FILES if not (HERE / f).exists()]
    if missing:
        raise SystemExit(f"cannot package, these are missing: {missing}")

    # **Every entry gets the same fixed timestamp, so packing twice gives identical bytes.** Without
    # this, three entries moved on every run — the two written from strings take the current time, and
    # `reference/bmx.mjs` is written by this script a moment earlier, so it carries a fresh mtime. The
    # consequence is not cosmetic: **a committed artefact that cannot be reproduced cannot be checked
    # against its source**, so a stale `.vsix` is undetectable and CI's repack-then-inspect step
    # overwrites the evidence before looking at it.
    #
    # The trap this fell into is worth naming, because the check I wrote first had it: two packs run
    # back-to-back land in the same two-second bucket, which is the granularity a zip stores, so a
    # reproducibility test that packs twice in a row **passes on a non-reproducible packer**. It took a
    # three-second sleep to see it. `tests/extension.py` asserts the fixed stamp itself rather than
    # comparing two runs, because that cannot pass by accident.
    EPOCH = (1980, 1, 1, 0, 0, 0)   # the earliest a zip can represent

    def entry(name, external=0o644 << 16):
        info = zipfile.ZipInfo(name, date_time=EPOCH)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = external
        return info

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(entry("[Content_Types].xml"), CONTENT_TYPES)
        z.writestr(entry("extension.vsixmanifest"), manifest(pkg))
        for name in FILES:
            z.writestr(entry(f"extension/{name}"), (HERE / name).read_bytes())

    print(f"wrote {out.relative_to(HERE.parent.parent)} "
          f"({out.stat().st_size} bytes, version {pkg['version']})")
    print("install with:  code --install-extension", out)


if __name__ == "__main__":
    main()
