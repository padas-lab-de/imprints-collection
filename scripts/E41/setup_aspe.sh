set -e
D=${D:-$HOME/GitHub/imprints-collection-e41}
cd $D
rm -rf .venv
/usr/bin/python3 -m venv --without-pip .venv
SP=$(.venv/bin/python -c "import sysconfig;print(sysconfig.get_paths()['purelib'])")
OLDSP=${OLDSP:-$HOME/GitHub/imprints-collection/.claude/worktrees/agent-a9795ebab2b1874a2/.venv/lib/python3.12/site-packages}
printf '%s\n%s\n' "$D/src" "$OLDSP" > $SP/e41.pth
.venv/bin/python -c "import ic.cli.fetch as f; print(f.__file__); print('UA:', f.HEADERS['User-Agent']); print('NUM_WORKERS', f.NUM_WORKERS)"
.venv/bin/python -c "import pytest" 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -4
mkdir -p $D/datasets/E41 $D/results/E41/logs
rm -f $HOME/e41_tree.tgz
echo SETUP_DONE
