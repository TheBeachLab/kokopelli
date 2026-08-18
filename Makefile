.PHONY: all app app-check app-notarize app-signed build dmg dmg-notarize install sync check test clean

RELEASE_DMG ?= dist/Kokopelli-0.3.0-macOS-arm64.dmg
RELEASE_ZIP ?= dist/Kokopelli-0.3.0-macOS-arm64.zip

all: build

build:
	cmake -S libfab -B build
	cmake --build build --parallel
	cmake --install build

install: sync build

app: sync build
	uv run python util/app/make_app.py

app-check:
	uv run python util/app/check_app.py dist/Kokopelli.app

app-signed: sync build
	@test -n "$(DEVELOPER_IDENTITY)" || (echo "Set DEVELOPER_IDENTITY to a Developer ID Application certificate" >&2; exit 2)
	MACOS_CODESIGN_IDENTITY="$(DEVELOPER_IDENTITY)" uv run python util/app/make_app.py

app-notarize: app-signed
	@test -n "$(NOTARY_PROFILE)" || { test -n "$(NOTARY_API_KEY)" && test -n "$(NOTARY_API_KEY_ID)" && test -n "$(NOTARY_API_ISSUER)"; } || (echo "Set NOTARY_PROFILE, or NOTARY_API_KEY + NOTARY_API_KEY_ID + NOTARY_API_ISSUER" >&2; exit 2)
	NOTARY_PROFILE="$(NOTARY_PROFILE)" NOTARY_API_KEY="$(NOTARY_API_KEY)" NOTARY_API_KEY_ID="$(NOTARY_API_KEY_ID)" NOTARY_API_ISSUER="$(NOTARY_API_ISSUER)" uv run python util/app/notarize_app.py dist/Kokopelli.app --output "$(RELEASE_ZIP)" --force

dmg: app
	uv run python util/app/make_dmg.py dist/Kokopelli.app --output "$(RELEASE_DMG)" --volume-name "Kokopelli 0.3.0" --force

dmg-notarize: app-signed
	@test -n "$(NOTARY_PROFILE)" || { test -n "$(NOTARY_API_KEY)" && test -n "$(NOTARY_API_KEY_ID)" && test -n "$(NOTARY_API_ISSUER)"; } || (echo "Set NOTARY_PROFILE, or NOTARY_API_KEY + NOTARY_API_KEY_ID + NOTARY_API_ISSUER" >&2; exit 2)
	NOTARY_PROFILE="$(NOTARY_PROFILE)" NOTARY_API_KEY="$(NOTARY_API_KEY)" NOTARY_API_KEY_ID="$(NOTARY_API_KEY_ID)" NOTARY_API_ISSUER="$(NOTARY_API_ISSUER)" uv run python util/app/make_dmg.py dist/Kokopelli.app --output "$(RELEASE_DMG)" --volume-name "Kokopelli 0.3.0" --identity "$(DEVELOPER_IDENTITY)" --force

sync:
	uv sync --dev

check: build
	uv run python kokopelli --check

test: build
	uv run pytest

clean:
	cmake -E remove_directory build
	cmake -E remove_directory dist
	cmake -E rm -f libfab/libfab.dylib libfab/libfab.so
