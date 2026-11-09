A=/home/dinzinger/GitLab/fim/imprints-collection/.claude/worktrees/agent-ac135c557903ea23f/scripts/E40
T=/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E40
R=$HOME/GitHub/imprints-collection-e35/datasets/E40
mkdir -p "$R/scan"
cp -a "$A"/results/. "$R/"
cp -a "$A"/targets_classified.tsv "$T"/targets_raw.tsv "$R/"
cp -a "$T"/scan/. "$R/scan/"
sha256sum "$A/results/flagged_sites.tsv" "$R/flagged_sites.tsv"
ls "$R/scan" | wc -l
du -sh --apparent-size "$R"
