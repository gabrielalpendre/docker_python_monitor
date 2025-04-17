#!/bin/bash
set -e

REPO=$1
EXTRAHEADER=$2

echo "## Configurando git..."
git config --global user.email "azuredevops@microsoft.com"
git config --global user.name "Azure DevOps"
git config "http.${REPO}.extraHeader" "${EXTRAHEADER}"

echo "## Buscando tags da master..."
git fetch origin master --tags

get_latest_version() {
  git tag --merged origin/master | grep -E "^v[0-9]+\.[0-9]+\.[0-9]+$" | sort -V | tail -n1
}

increment_version() {
  local version=$1
  IFS='.' read -r major minor patch <<< "${version#v}"
  ((patch++))
  echo "v$major.$minor.$patch-beta"
}

BASE_TAG=$(get_latest_version)
[ -z "$BASE_TAG" ] && BASE_TAG="v1.0.0"
echo "Última tag na master: $BASE_TAG"

BETA_VERSION=$(increment_version "$BASE_TAG")
echo "🔧 Versão beta gerada: $BETA_VERSION"
echo "##vso[task.setvariable variable=VERSAO;isOutput=true]$BETA_VERSION"