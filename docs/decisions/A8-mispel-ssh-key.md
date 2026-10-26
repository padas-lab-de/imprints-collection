# A8-mispel-ssh-key (issued 2026-10-26, data-collection lead)

**Action:** add lorbeer's public key to `~/.ssh/authorized_keys` on mispel (mispel.dimis.fim.uni-passau.de), so the lead can set up E16 there.

Context: the user cleared lorbeer and mispel for E16 under D23 on 2026-10-26. `ssh mispel` from lorbeer: host key now in known_hosts; login fails with `Permission denied (publickey)` (id_ed25519 is offered and rejected).

Key to add (lorbeer ~/.ssh/id_ed25519.pub):
`ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAID7KIAd4AcugoSVUXBdyaYJqAYb9PDbltNC1SeiNFVlT michael.dinzinger@uni-passau.de`

Unblocks: mispel takes E16 batches 214-262 from apfel's range (then needs the apfel driver lowered to 213, like A9).

**Answer:** open.
