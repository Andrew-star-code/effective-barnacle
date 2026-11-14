#!/usr/bin/env bash
# Сборка образов WeKnora из подмодуля weknora/ (ветка corp/v<версия> форка с патчами).
# Контекст сборки — `git archive` закоммиченного HEAD подмодуля, а не рабочая копия: образ
# соответствует коммиту, даже если на Windows файлы вычеканы с CRLF; незакоммиченное в образ не попадает.
# Образы: ${PREFIX}/weknora-{app,docreader,ui}:<тег>, тег — `git describe` подмодуля
# (v0.9.0 без патчей, v0.9.0-N-g<коммит> с патчами). Dev-стек берёт их через
# WEKNORA_IMAGE_PREFIX и WEKNORA_VERSION (deploy/compose/README.md).
#
# Переменные: WEKNORA_IMAGE_PREFIX (по умолчанию corp), WEKNORA_IMAGES (какие образы,
# по умолчанию "app docreader ui"), GOPROXY, NPM_REGISTRY, APT_MIRROR — зеркала для
# сборки без интернета (этап 10).
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
src="$root/weknora"
prefix="${WEKNORA_IMAGE_PREFIX:-corp}"
images="${WEKNORA_IMAGES:-app docreader ui}"

if [ ! -f "$src/docker/Dockerfile.app" ]; then
  echo "weknora-build: подмодуль weknora/ пуст — git submodule update --init" >&2
  exit 1
fi

tag="$(git -C "$src" describe --tags --always)"
commit="$(git -C "$src" rev-parse --short=9 HEAD)"
version="${tag#v}"
build_time="$(date -u '+%Y-%m-%d %H:%M:%S UTC')"

echo "weknora-build: $(git -C "$src" rev-parse --abbrev-ref HEAD) @ $commit → $prefix/weknora-*:$tag"

for image in $images; do
  case "$image" in
    app)
      docker build \
        --build-arg GOPROXY_ARG="${GOPROXY:-}" \
        --build-arg VERSION_ARG="$version" \
        --build-arg COMMIT_ID_ARG="$commit" \
        --build-arg BUILD_TIME_ARG="$build_time" \
        --build-arg GO_VERSION_ARG=docker \
        -f docker/Dockerfile.app -t "$prefix/weknora-app:$tag" - < <(git -C "$src" archive HEAD)
      ;;
    docreader)
      docker build \
        --build-arg APT_MIRROR="${APT_MIRROR:-}" \
        -f docker/Dockerfile.docreader -t "$prefix/weknora-docreader:$tag" - < <(git -C "$src" archive HEAD)
      ;;
    ui)
      docker build \
        --build-arg VITE_FRONTEND_COMMIT="$commit" \
        ${NPM_REGISTRY:+--build-arg NPM_REGISTRY="$NPM_REGISTRY"} \
        -f Dockerfile -t "$prefix/weknora-ui:$tag" - < <(git -C "$src" archive HEAD:frontend)
      ;;
    *)
      echo "weknora-build: неизвестный образ '$image' (app, docreader, ui)" >&2
      exit 1
      ;;
  esac
done

echo "weknora-build: готово. Запуск: WEKNORA_IMAGE_PREFIX=$prefix WEKNORA_VERSION=$tag make dev-up"
