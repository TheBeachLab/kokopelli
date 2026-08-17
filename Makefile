.PHONY: all app app-check app-notarize app-signed build install sync check test clean

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
	@test -n "$(NOTARY_PROFILE)" || (echo "Set NOTARY_PROFILE to a notarytool Keychain profile" >&2; exit 2)
	uv run python util/app/notarize_app.py dist/Kokopelli.app --profile "$(NOTARY_PROFILE)" --output "$(RELEASE_ZIP)" --force

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
