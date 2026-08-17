.PHONY: all app app-check build install sync check test clean

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
