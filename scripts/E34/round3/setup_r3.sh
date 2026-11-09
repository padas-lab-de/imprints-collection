set -e
D=$HOME/GitHub/imprints-collection-e34r3
mkdir -p $D
cd $D
test -f pyproject.toml || tar xzf $HOME/e34r3_tree.tgz -C $D
rm -rf .venv
OLD=$HOME/GitHub/imprints-collection/.venv
$OLD/bin/python --version
$OLD/bin/python -m pip --version
$OLD/bin/python -m venv --without-pip .venv
$OLD/bin/python -m pip --python $D/.venv/bin/python install -q -e . pytest 2>&1 | tail -8
.venv/bin/python -c "import ic, sys; print(ic.__file__, sys.executable)"
grep -n "ImprintsCollectionBot" src/ic/cli/fetch.py
.venv/bin/python -m pytest -q 2>&1 | tail -15
