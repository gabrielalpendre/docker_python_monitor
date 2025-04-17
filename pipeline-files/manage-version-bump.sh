#!/bin/bash
set -e

REPO=$1
EXTRAHEADER=$2

echo "## Configurando git..."
git config --global user.email "azuredevops@microsoft.com"
git config --global user.name "Azure DevOps"
git config "http.${REPO}.extraHeader" "${EXTRAHEADER}"

BRANCH="$BUILD_SOURCEBRANCHNAME"
echo "## Branch atual: $BRANCH"

if [[ "$BRANCH" != "master" ]]; then
  echo "❌ Branch não é 'master' — sem tagging no TBD."
  exit 0
fi

# Obtém a mensagem do commit que disparou o build
MERGE_MESSAGE=$(git log -1 --pretty=%B)
echo "## Commit de merge: $MERGE_MESSAGE"

# Extrai a origem do merge, ex: feature/abc, release/1.2, bugfix/xyz
MERGE_SOURCE=$(echo "$MERGE_MESSAGE" | grep -oE 'from (feature|release|bugfix|hotfix)/[^ ]+' | cut -d' ' -f2)

echo "## Branch de origem detectada: $MERGE_SOURCE"

# Define tipo de bump com base no prefixo da branch
if [[ "$MERGE_SOURCE" == release/* ]]; then
  BUMP_TYPE="major"
elif [[ "$MERGE_SOURCE" == feature/* ]]; then
  BUMP_TYPE="minor"
elif [[ "$MERGE_SOURCE" == bugfix/* || "$MERGE_SOURCE" == hotfix/* ]]; then
  BUMP_TYPE="patch"
else
  BUMP_TYPE="patch"
fi

echo "## Tipo de bump detectado: $BUMP_TYPE"

echo "## Buscando tags..."
git fetch --tags

get_latest_version() {
  git tag | grep -E "^v[0-9]+\.[0-9]+\.[0-9]+$" | sort -V | tail -n1
}

increment_version() {
  local version=$1
  local part=$2
  IFS='.' read -r major minor patch <<< "${version#v}"
  case "$part" in
    major) ((major++)); minor=0; patch=0 ;;
    minor) ((minor++)); patch=0 ;;
    patch|*) ((patch++)) ;;
  esac
  echo "v$major.$minor.$patch"
}

BASE_TAG=$(get_latest_version)
[ -z "$BASE_TAG" ] && BASE_TAG="v1.0.0"
echo "Última tag base: $BASE_TAG"

echo "Incrementando versão ($BUMP_TYPE)..."
NEW_TAG=$(increment_version "$BASE_TAG" "$BUMP_TYPE")

echo "## Criando nova tag: $NEW_TAG"
git tag "$NEW_TAG"
git push origin "$NEW_TAG"

if [ $? -ne 0 ]; then
  echo "❌ Falha ao criar a tag $NEW_TAG"
  exit 1
else
  echo "##vso[task.setvariable variable=VERSAO;isOutput=true]$NEW_TAG"
  echo "✅ Tag criada com sucesso: $NEW_TAG"
  exit 0
fi