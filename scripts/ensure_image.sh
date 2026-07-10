ensure_image() {
  local tag="$1" context="$2"
  if docker image inspect "$tag" >/dev/null 2>&1; then
    echo "image $tag already exists"
    return 0
  fi
  echo "building $tag from $context"
  docker build -t "$tag" "$context"
}
