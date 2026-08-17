#!/usr/bin/env python3
"""Package the extension as a .vsix, with no toolchain.

    python3 editors/vscode/pack.py            # writes bmx-<version>.vsix here
    code --install-extension editors/vscode/bmx-0.1.0.vsix

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
    out = HERE / f"{pkg['name']}-{pkg['version']}.vsix"

    # `reference/bmx.js` lives at the repository root, not here. Staged rather than symlinked,
    # because a .vsix is a zip and a symlink in one is a file nobody can read.
    staged = HERE / "reference"
    staged.mkdir(exist_ok=True)
    (staged / "bmx.mjs").write_text((HERE.parent.parent / "reference" / "bmx.js").read_text())

    missing = [f for f in FILES if not (HERE / f).exists()]
    if missing:
        raise SystemExit(f"cannot package, these are missing: {missing}")

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("extension.vsixmanifest", manifest(pkg))
        for name in FILES:
            z.write(HERE / name, f"extension/{name}")

    print(f"wrote {out.relative_to(HERE.parent.parent)} ({out.stat().st_size} bytes)")
    print("install with:  code --install-extension", out)


if __name__ == "__main__":
    main()
