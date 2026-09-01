#!/bin/sh
# Watchdog for cups-test: the Canon G2030 (USB) sometimes leaves CUPS's
# backend stuck reporting "Waiting for printer to become available" even
# after the printer is powered back on and /dev/usb/lp0 is available again.
# A plain `docker restart cups-test` reliably clears this (confirmed live,
# 2026-09-01) — this script automates that instead of requiring someone to
# notice and SSH in manually every time.
#
# Install (run once on the STB, as root):
#   chmod +x /opt/cups-print-manager/scripts/cups-watchdog.sh
#   cp /opt/cups-print-manager/scripts/cups-watchdog.cron /etc/cron.d/cups-watchdog
#
# Logs to /var/log/cups-watchdog.log (created by the cron redirect, not by
# this script) — check it if you want to see what the watchdog has done.

set -eu

CONTAINER="cups-test"
PRINTER="Canon-G2030"
USB_DEVICE="/dev/usb/lp0"
STATE_FILE="/tmp/cups-watchdog.state"
LAST_RESTART_FILE="/tmp/cups-watchdog.last-restart"
COOLDOWN_SECONDS=600 # don't restart more than once per 10 minutes

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') $*"
}

# Nothing to do if the container isn't even running — that needs a human,
# not a restart (restarting a container that isn't running is a no-op here
# but the real problem, if any, is elsewhere). Exact-match via `grep -x`
# rather than `docker ps --filter name=`, whose substring-vs-regex matching
# behavior isn't worth relying on for a one-line check.
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  log "WARN: ${CONTAINER} is not running, skipping (needs manual attention)"
  exit 0
fi

STATUS_OUTPUT=$(docker exec "$CONTAINER" lpstat -p "$PRINTER" 2>/dev/null || true)

if ! echo "$STATUS_OUTPUT" | grep -q "Waiting for printer to become available"; then
  # Healthy — clear any stuck-streak we were tracking.
  rm -f "$STATE_FILE"
  exit 0
fi

# Stuck message present. Only act if the USB device is actually there — if
# the printer is genuinely off, restarting cups-test will just fail again
# (its device mapping can't be satisfied), so leave it alone for a human.
if ! docker exec "$CONTAINER" test -e "$USB_DEVICE" 2>/dev/null; then
  log "INFO: printer reports waiting, but ${USB_DEVICE} is absent — printer is genuinely off, not restarting"
  rm -f "$STATE_FILE"
  exit 0
fi

NOW=$(date +%s)

if [ ! -f "$STATE_FILE" ]; then
  # First time seeing it stuck — record and wait for the next run to
  # confirm this isn't just a few-second blip before doing anything
  # disruptive.
  echo "$NOW" >"$STATE_FILE"
  log "INFO: printer stuck detected, will confirm on next check before restarting"
  exit 0
fi

if [ -f "$LAST_RESTART_FILE" ]; then
  LAST_RESTART=$(cat "$LAST_RESTART_FILE")
  ELAPSED=$((NOW - LAST_RESTART))
  if [ "$ELAPSED" -lt "$COOLDOWN_SECONDS" ]; then
    log "INFO: printer still stuck but restarted ${ELAPSED}s ago (cooldown ${COOLDOWN_SECONDS}s) — waiting"
    exit 0
  fi
fi

log "ACTION: printer stuck across two checks and USB device present — restarting ${CONTAINER}"
docker restart "$CONTAINER" >/dev/null
echo "$NOW" >"$LAST_RESTART_FILE"
rm -f "$STATE_FILE"
