cd $HOME/GitHub/imprints-collection-e34r3
.venv/bin/python -c "import ic.cli.fetch as f; print(f.__file__); print(f.HEADERS['User-Agent']); print(f.NUM_WORKERS)" 2>&1 | tail -3
grep -rn '"User-Agent"\|User-Agent' src | head
.venv/bin/python -m pytest -q tests/test_fetch_user_agent.py tests/test_fetch_skip_provider.py 2>&1 | tail -3
ps -eo pid,user,etime,args | grep -E "ic.ic|fetch" | grep -v grep | cut -c1-200
echo "other users procs:"; ps -eo user,pcpu,args --sort=-pcpu | head -6 | cut -c1-150
