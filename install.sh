#!/usr/bin/env bash
set -e

# Synco installer (Linux)
# - Creates a Python venv in ./venv
# - Marks main.py executable
# - Creates start.sh and stop.sh wrappers

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[synco] Project directory: $PROJECT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[synco] python3 not found. Install Python 3 first."
  exit 1
fi

echo "[synco] Creating virtual environment..."
python3 -m venv "$PROJECT_DIR/venv"

echo "[synco] Upgrading pip inside venv..."
"$PROJECT_DIR/venv/bin/python" -m pip install --upgrade pip >/dev/null

echo "[synco] Making main.py executable..."
chmod +x "$PROJECT_DIR/main.py"

echo "[synco] Creating start.sh..."
cat > "$PROJECT_DIR/start.sh" <<'SH'
#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
./venv/bin/python main.py &
echo "[synco] Started in background. Check synco.pid and logs above."
SH
chmod +x "$PROJECT_DIR/start.sh"

echo "[synco] Creating stop.sh..."
cat > "$PROJECT_DIR/stop.sh" <<'SH'
#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
./venv/bin/python main.py --stop
SH
chmod +x "$PROJECT_DIR/stop.sh"

echo
echo "[synco] Install complete."
echo "Next steps:"
echo "  1. Install rclone and configure a remote (see README)."
echo "  2. Create and edit synco.json in this folder."
echo "  3. Run ./start.sh to start syncing."
echo "  4. Run ./stop.sh to stop."
