#!/usr/bin/env bash
# =============================================================================
#  IM-Benchmark-Lab — Google Colab Setup Script
# -----------------------------------------------------------------------------
#  Dùng:
#    !bash /content/colab_setup.sh
#
#  Tùy chọn:
#    RUN_TESTS=0      bỏ qua pytest
#    RUN_SAMPLE=0     bỏ qua thí nghiệm mẫu
#    WARMUP_DATA=1    tải trước 5 bộ dữ liệu
#    RUN_GUI_SMOKE=1  thử GUI bằng Xvfb
#    BRANCH=main      nhánh Git
#    REPO_URL=...     repo/fork khác
#    PROJECT_DIR=...  thư mục source
#    VENV_DIR=...     thư mục venv
#    UPDATE_SOURCE=1  git pull source hiện có
# =============================================================================

set -Eeuo pipefail

REPO_URL="${REPO_URL:-https://github.com/SLMR05-05/influence-maximization-benchmark.git}"
BRANCH="${BRANCH:-main}"
WORKDIR="${WORKDIR:-/content}"
VENV_DIR="${VENV_DIR:-$WORKDIR/im_env}"

RUN_TESTS="${RUN_TESTS:-1}"
RUN_SAMPLE="${RUN_SAMPLE:-1}"
WARMUP_DATA="${WARMUP_DATA:-0}"
RUN_GUI_SMOKE="${RUN_GUI_SMOKE:-0}"
UPDATE_SOURCE="${UPDATE_SOURCE:-0}"

log()  { printf '\n\033[1;34m[%s]\033[0m %s\n' "$1" "$2"; }
ok()   { printf '\033[1;32m  ✓\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m  ! %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m[ERROR]\033[0m %s\n' "$*" >&2; exit 1; }

run_root() {
    if [ "$(id -u)" -eq 0 ]; then "$@"; else sudo "$@"; fi
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || pwd)"
if [ -z "${PROJECT_DIR:-}" ]; then
    if [ -f "$SCRIPT_DIR/pyproject.toml" ] && [ -d "$SCRIPT_DIR/src/im_research" ]; then
        PROJECT_DIR="$SCRIPT_DIR"
    else
        PROJECT_DIR="$WORKDIR/influence-maximization-benchmark"
    fi
fi

printf '\n\033[1;36m============================================================\n'
printf '  IM-Benchmark-Lab — Google Colab Setup\n'
printf '============================================================\033[0m\n'
printf '  Repo   : %s\n  Branch : %s\n  Source : %s\n  Venv   : %s\n' \
    "$REPO_URL" "$BRANCH" "$PROJECT_DIR" "$VENV_DIR"

# ── 1. System dependencies ───────────────────────────────────────────────────
log "1/8" "Cài system dependencies..."
export DEBIAN_FRONTEND=noninteractive
run_root apt-get update -qq
run_root apt-get install -y -qq \
    git cmake build-essential g++ python3-dev python3-venv python3-tk libgomp1

ok "System dependencies OK"
printf '  cmake : %s\n  g++   : %s\n  python: %s\n' \
    "$(cmake --version | head -n 1)" \
    "$(g++ --version | head -n 1)" \
    "$(python3 --version 2>&1)"

# ── 2. Source code ───────────────────────────────────────────────────────────
log "2/8" "Lấy source code..."
if [ -f "$PROJECT_DIR/pyproject.toml" ] && [ -d "$PROJECT_DIR/src/im_research" ]; then
    ok "Đã có source: $PROJECT_DIR"
else
    if [ -d "$PROJECT_DIR" ] && [ -n "$(ls -A "$PROJECT_DIR" 2>/dev/null)" ]; then
        die "Thư mục '$PROJECT_DIR' không phải repo IM-Benchmark-Lab. Hãy xóa hoặc đặt PROJECT_DIR khác."
    fi
    run_root mkdir -p "$(dirname "$PROJECT_DIR")"
    git clone --branch "$BRANCH" "$REPO_URL" "$PROJECT_DIR"
    ok "Đã clone source."
fi

if [ -d "$PROJECT_DIR/.git" ]; then
    git config --global --add safe.directory "$PROJECT_DIR" 2>/dev/null || true
    if [ "$UPDATE_SOURCE" = "1" ]; then
        log "2b/8" "Cập nhật source (UPDATE_SOURCE=1)..."
        git -C "$PROJECT_DIR" fetch origin "$BRANCH"
        git -C "$PROJECT_DIR" checkout "$BRANCH"
        git -C "$PROJECT_DIR" pull --ff-only origin "$BRANCH" \
            || warn "Không pull được (thay đổi cục bộ). Dùng code hiện tại."
    fi
    printf '  Commit: %s\n' "$(git -C "$PROJECT_DIR" rev-parse --short HEAD 2>/dev/null || echo 'n/a')"
fi

cd "$PROJECT_DIR"
mkdir -p data/raw data/processed runs

# ── 3. Venv ──────────────────────────────────────────────────────────────────
log "3/8" "Tạo môi trường ảo..."
if [ ! -x "$VENV_DIR/bin/python" ]; then
    python3 -m venv "$VENV_DIR"
    ok "Đã tạo venv: $VENV_DIR"
else
    ok "Dùng lại venv: $VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel
ok "Python trong venv: $(python --version 2>&1)"

# ── 4. Python dependencies ───────────────────────────────────────────────────
log "4/8" "Cài thư viện Python..."
python -m pip install --no-cache-dir -r "$PROJECT_DIR/requirements.txt"
python -m pip install --no-cache-dir --no-build-isolation -e "$PROJECT_DIR"
ok "Python dependencies OK"

# ── 5. Build C++ core ────────────────────────────────────────────────────────
log "5/8" "Build C++ core + pybind11..."
cd "$PROJECT_DIR"
rm -rf build
mkdir -p build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release \
         -DCMAKE_CXX_FLAGS="-O3 -march=native -fopenmp"
make -j"$(nproc)"
cd "$PROJECT_DIR"

SO_PATH="$(find "$PROJECT_DIR/src/im_research" -maxdepth 1 -name '_im_core*.so' -print -quit)"
[ -n "$SO_PATH" ] || die "Không tìm thấy _im_core*.so trong src/im_research/"
ok "C++ core: $SO_PATH"

# ── 6. Smoke test ────────────────────────────────────────────────────────────
log "6/8" "Smoke test Python ↔ C++..."
export PYTHONPATH="$PROJECT_DIR/src:${PYTHONPATH:-}"

python - <<'PY'
import im_research
from im_research import _im_core

print(f"  im_research : {im_research.__file__}")
print(f"  C++ core    : {_im_core.__file__}")

g = _im_core.Graph.from_edge_list(3, [(0, 1), (1, 2)], [0.5, 0.5], False)
print(f"  Graph test  : {g.num_nodes()} đỉnh, {g.num_edges()} cạnh")

ev = _im_core.Evaluator(
    g, _im_core.DiffusionModel.IndependentCascade,
    num_mc_simulations=50, seed=42,
)
print(f"  IC spread   : {ev.evaluate([0])}")
PY
ok "Import và C++ evaluator OK"

# ── 7. Tests + warm-up ───────────────────────────────────────────────────────
if [ "$RUN_TESTS" = "1" ]; then
    log "7/8" "Chạy unit tests..."
    python -m pytest "$PROJECT_DIR/tests/unit" -v
    ok "Unit tests OK"
else
    log "7/8" "Bỏ qua unit tests (RUN_TESTS=0)."
fi

if [ "$WARMUP_DATA" = "1" ]; then
    log "7b/8" "Tải trước 5 bộ dữ liệu..."
    python - <<'PY'
from im_research.data.loader import load_networkx_graph

for name in ["Karate Club", "Dolphins", "ego-Facebook", "NetHEPT", "Email-Enron"]:
    try:
        g, _ = load_networkx_graph(name)
        print(f"  {name:15s} {g.number_of_nodes():>6} đỉnh / {g.number_of_edges():>7} cạnh")
    except Exception as exc:
        print(f"  {name:15s} LỖI: {exc}")
PY
    ok "Warm-up dữ liệu OK"
fi

# ── 8. Sample experiment ─────────────────────────────────────────────────────
if [ "$RUN_SAMPLE" = "1" ]; then
    log "8/8" "Chạy thí nghiệm mẫu trên Karate Club..."
    python -m im_research.experiments.runner \
        --dataset "Karate Club" --model IC --p 0.1 \
        --k 10 --mc 200 --mc_val 1000 --runs 1 \
        --algo iga --algo ga --algo celf \
        --algo degree_discount --algo pagerank --algo degree
    ok "Thí nghiệm mẫu OK. Kết quả trong runs/."
else
    log "8/8" "Bỏ qua thí nghiệm mẫu (RUN_SAMPLE=0)."
fi

# ── 9. GUI smoke test ────────────────────────────────────────────────────────
if [ "$RUN_GUI_SMOKE" = "1" ]; then
    log "9/9" "GUI smoke test với Xvfb..."
    run_root apt-get install -y -qq xvfb xauth
    xvfb-run -a -s "-screen 0 1400x900x24" python - <<'PY'
from im_research.gui.app import IMApp

app = IMApp()
app.after(3000, app.destroy)
app.mainloop()
print("  GUI khởi động và đóng thành công.")
PY
    ok "GUI smoke test OK"
fi

# ── Tổng kết ─────────────────────────────────────────────────────────────────
printf '\n\033[1;32m============================================================\n'
printf '  HOÀN TẤT SETUP\n'
printf '============================================================\033[0m\n'
cat <<EOF
  Project : $PROJECT_DIR
  Venv    : $VENV_DIR
  Python  : $(python --version 2>&1)

  Kích hoạt lại:
    source $VENV_DIR/bin/activate
    cd "$PROJECT_DIR"
    export PYTHONPATH="$PROJECT_DIR/src:\$PYTHONPATH"

  Chạy thí nghiệm:
    python -m im_research.experiments.runner \\
      --dataset "Karate Club" --model IC --p 0.1 \\
      --k 10 --mc 200 --mc_val 1000 --runs 1 \\
      --algo iga --algo ga --algo celf \\
      --algo degree_discount --algo pagerank --algo degree

  Unit tests:
    python -m pytest tests/unit -v

  GUI (cần display — không dùng trực tiếp trên Colab):
    python src/im_research/gui/main_app.py
============================================================
EOF
