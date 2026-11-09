#!/bin/bash
# E41: deploy the D39 B tree (git archive of 3a23d5d = T/E34/round3/e34r3_tree.tgz) to ~/GitHub/imprints-collection-e41 on a VM
# Usage (on the VM): bash setup_e41.sh   (expects ~/e41_tree.tgz). Like T/E34/round3/setup_r3.sh.
set -e
D=${D:-$HOME/GitHub/imprints-collection-e41}
mkdir -p $D
cd $D
test -f pyproject.toml || tar xzf $HOME/e41_tree.tgz -C $D
rm -rf .venv
OLD=${OLD:-$HOME/GitHub/imprints-collection/.venv}
$OLD/bin/python --version
$OLD/bin/python -m pip --version
$OLD/bin/python -m venv --without-pip .venv
$OLD/bin/python -m pip --python $D/.venv/bin/python install -q -e . pytest 2>&1 | tail -8
.venv/bin/python -c "import ic, sys; print(ic.__file__, sys.executable)"
.venv/bin/python -c "import ic.cli.fetch as f; print('UA:', f.HEADERS['User-Agent']); print('NUM_WORKERS', f.NUM_WORKERS)"
.venv/bin/python -m pytest -q 2>&1 | tail -4
mkdir -p $D/datasets/E41 $D/results/E41/logs
rm -f $HOME/e41_tree.tgz
echo SETUP_DONE
