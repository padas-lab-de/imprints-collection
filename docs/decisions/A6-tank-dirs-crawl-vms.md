# A6-tank-dirs-crawl-vms (issued 2026-10-26)
- [ ] A6-tank-dirs-crawl-vms: on abelie (and akazie/aralie if D23 B/C): `ssh -t abelie 'sudo mkdir -p /tank/dinzinger && sudo chown dinzinger: /tank/dinzinger'` (sudo needs your password). Root disks are 95-97% full; /tank (ZFS) has ~3 TB free.
Unblocks: E16 driver on abelie (D23 A).
Answer (2026-10-26): user ran `sudo mkdir -p /tank/docker/dinzinger && sudo chown dinzinger: /tank/docker/dinzinger` (exists on abelie; not on akazie/aralie). Lead cloned lead-record to /tank/docker/dinzinger/imprints-collection on abelie, symlinked ~/GitHub/imprints-collection, .venv via get-pip, 186 tests pass. No E16 there (D23).
