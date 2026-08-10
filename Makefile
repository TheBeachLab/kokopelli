.PHONY: all build install sync check test clean

all: build

build:
	cmake -S libfab -B build
	cmake --build build --parallel
	cmake --install build

install: sync build

sync:
	uv sync --dev

check: build
	uv run python kokopelli --check

test: build
	uv run pytest

clean:
	cmake -E remove_directory build
	cmake -E rm -f libfab/libfab.dylib libfab/libfab.so
