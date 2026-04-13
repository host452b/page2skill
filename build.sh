#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

usage() {
    cat <<EOF
bookmark2skill build helper

Usage: ./build.sh <command>

Commands:
  install     Install in production mode (pip install .)
  develop     Install in editable/dev mode with test dependencies
  test        Run full test suite
  dist        Build sdist + wheel to dist/
  clean       Remove build artifacts, caches, dist/
  check       Compile check all modules + run tests
  help        Show this message

Examples:
  ./build.sh develop    # first time setup
  ./build.sh test       # run tests
  ./build.sh dist       # build package for distribution
EOF
}

cmd_install() {
    echo "==> Installing bookmark2skill..."
    pip install .
    echo "==> Done. Run: b2k --version"
}

cmd_develop() {
    echo "==> Installing in editable mode with dev dependencies..."
    pip install -e ".[dev]"
    echo "==> Done. Run: b2k --version"
}

cmd_test() {
    echo "==> Running tests..."
    pytest tests/ -v
}

cmd_dist() {
    echo "==> Building distribution..."
    pip install build 2>/dev/null || true
    python -m build
    echo "==> Artifacts in dist/"
    ls -lh dist/
}

cmd_clean() {
    echo "==> Cleaning build artifacts..."
    rm -rf dist/ build/ *.egg-info src/*.egg-info
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
    echo "==> Clean."
}

cmd_check() {
    echo "==> Compile check..."
    find src -name "*.py" -exec python -m py_compile {} +
    echo "==> All modules compile OK"
    echo "==> Running tests..."
    pytest tests/ -v
}

case "${1:-help}" in
    install) cmd_install ;;
    develop) cmd_develop ;;
    test)    cmd_test ;;
    dist)    cmd_dist ;;
    clean)   cmd_clean ;;
    check)   cmd_check ;;
    help|*)  usage ;;
esac
