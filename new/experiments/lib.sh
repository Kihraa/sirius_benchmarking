timeout_for_sf() {
  local sf="$1"
  case "$sf" in
    300) echo "${TIMEOUT_SF300:-${TIMEOUT:-120}}" ;;
    1000) echo "${TIMEOUT_SF1000:-${TIMEOUT:-120}}" ;;
    *) echo "${TIMEOUT:-120}" ;;
  esac
}
