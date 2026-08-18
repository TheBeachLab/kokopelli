# macOS release and notarization

This guide covers public Kokopelli releases outside the Mac App Store. Local
development builds do not require Apple credentials; use `make app` and
`make app-check` for those.

The release tools also work with other correctly structured macOS application
bundles. Keep credentials and private keys outside the repository.

## Prerequisites

- macOS on the architecture being packaged;
- a `Developer ID Application` certificate installed with its private key;
- membership in the corresponding Apple Developer team; and
- either a `notarytool` Keychain profile or an App Store Connect Team API key.

Confirm that the signing identity is available:

```bash
security find-identity -v -p codesigning
```

Use the complete identity shown by that command in the examples below:

```bash
export DEVELOPER_IDENTITY="Developer ID Application: Your Name (TEAM_ID)"
```

## Choose a notarization credential

### Keychain profile

A Keychain profile is convenient for an interactive Mac. Store it once; the
same profile can be reused by multiple application builds for the same account
and team:

```bash
xcrun notarytool store-credentials PROFILE_NAME \
  --apple-id YOUR_APPLE_ID \
  --team-id YOUR_TEAM_ID
```

Set the profile name for the release commands:

```bash
export NOTARY_PROFILE="PROFILE_NAME"
```

### Team API key for unattended builds

For remote or unattended operation, use an App Store Connect **Team API key**.
Apple states that individual API keys cannot authenticate `notarytool`.
Download the `.p8` file once, store it outside the repository, and make it
readable only by its owner:

```bash
chmod 600 /secure/path/AuthKey_KEY_ID.p8

export NOTARY_API_KEY="/secure/path/AuthKey_KEY_ID.p8"
export NOTARY_API_KEY_ID="KEY_ID"
export NOTARY_API_ISSUER="ISSUER_UUID"
```

Do not set `NOTARY_PROFILE` when using API credentials. All three API variables
are required together.

Apple documents [Team API key creation and protection][api-keys] and
[`notarytool` authentication][notarytool].

## Build a signed and notarized app archive

With either credential method configured in the environment, run:

```bash
make app-notarize DEVELOPER_IDENTITY="$DEVELOPER_IDENTITY"
```

The workflow:

1. builds the self-contained `dist/Kokopelli.app` bundle;
2. signs nested code and the application with Hardened Runtime and a secure
   timestamp;
3. verifies the Developer ID signature;
4. submits a ZIP to Apple and waits for the result;
5. staples and validates the ticket on the application;
6. checks Gatekeeper acceptance; and
7. creates `dist/Kokopelli-0.3.0-macOS-arm64.zip`.

## Build a drag-to-Applications DMG

A local unsigned DMG needs no Apple credentials:

```bash
make dmg
```

For public distribution, build, sign, notarize, staple, and validate the DMG:

```bash
make dmg-notarize DEVELOPER_IDENTITY="$DEVELOPER_IDENTITY"
```

The result is `dist/Kokopelli-0.3.0-macOS-arm64.dmg`. Its Finder window places
`Kokopelli.app` beside an `/Applications` link with a drag arrow. The release
workflow submits the outermost DMG to Apple and validates the mounted app after
notarization.

## Reuse the tools with another app

`util/app/notarize_app.py` accepts any correctly signed `.app`, verifies its
distribution signature and Hardened Runtime, submits it to Apple, staples the
ticket, checks Gatekeeper, and creates a distributable ZIP.

`util/app/make_dmg.py` accepts any `.app`, creates the graphical Finder layout,
optionally signs and notarizes the disk image, verifies the image checksum, and
validates the mounted application.

Inspect their complete command-line interfaces with:

```bash
uv run python util/app/notarize_app.py --help
uv run python util/app/make_dmg.py --help
```

Both tools accept either `--profile` or the complete set `--api-key`,
`--api-key-id`, and `--api-issuer`. The equivalent `NOTARY_*` environment
variables are useful for automation.

## Independent validation

Before publishing a DMG, the most important independent checks are:

```bash
codesign --verify --verbose=2 dist/Kokopelli-0.3.0-macOS-arm64.dmg
xcrun stapler validate dist/Kokopelli-0.3.0-macOS-arm64.dmg
spctl --assess --type open --context context:primary-signature --verbose=4 \
  dist/Kokopelli-0.3.0-macOS-arm64.dmg
hdiutil verify dist/Kokopelli-0.3.0-macOS-arm64.dmg
```

Gatekeeper should report `accepted` with `source=Notarized Developer ID`.

[api-keys]: https://developer.apple.com/documentation/appstoreconnectapi/creating-api-keys-for-app-store-connect-api
[notarytool]: https://developer.apple.com/documentation/technotes/tn3147-migrating-to-the-latest-notarization-tool
