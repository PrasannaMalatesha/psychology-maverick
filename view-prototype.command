#!/bin/bash
# Double-click this file in Finder to open the Psychology Maverick prototype.
# It serves the pages locally (so every screen renders fully) and opens the hub.
set -e
DIR="$(cd "$(dirname "$0")/design/prototype" && pwd)"
PORT=8777
URL="http://localhost:$PORT/index.html"

# Start a local server only if one isn't already running on this port.
if ! curl -s -o /dev/null "http://localhost:$PORT/index.html" 2>/dev/null; then
  cd "$DIR"
  nohup python3 -m http.server "$PORT" >/dev/null 2>&1 &
  sleep 1
fi

echo "Psychology Maverick prototype → $URL"
open "$URL"
