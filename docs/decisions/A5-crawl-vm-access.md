### A5-crawl-vm-access · Give the lead SSH access to the extra crawl-subnet VMs (D20 A)
- [ ] Tell the lead how many VMs, their hostnames, and confirm `ssh <host>` works from the crawl VM without a password prompt; each VM needs its own public IP, Python 3.10+, about 30 GB free.
Unblocks: moving E16 batch ranges off this VM (run.sh FIRST LAST), the Strato gold captures from another IP (E17), the depth-3 expansion.
Answer (2026-10-26): lead moved to lorbeer; ssh works to akazie, aralie, abelie, apfel, aspe. Checked: each has its own public IP (193.175.2.84/.85/.86/.89/.90, one /24), Python 3.10/3.12; apfel has no ensurepip (venv via get-pip.py). Disk/RAM limits -> D23, A6. Closed.
