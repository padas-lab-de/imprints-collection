# D23-shared-vm-crawl (issued 2026-10-26)

### D23-shared-vm-crawl · Which of the three VMs that another user's jobs share (akazie, aralie, abelie) run E16? — before re-splitting ranges · blocks a 3rd/4th/5th E16 driver
Checked 2026-10-26 10:00 UTC (public IPs: akazie .84, aralie .85, abelie .86, apfel .89, aspe .90, all 193.175.2.0/24):
- aspe, apfel: Owler service only; apfel 139 GB disk, 24 GB RAM available. Both run E16 now (52-156, 157-262).
- abelie: 29 GB RAM available, idle CPU, but 5.4 GB free on /; /tank has 3 TB but needs a sudo-created dir (A6).
- akazie: another user's python jobs hold ~26 GB of 32 GB RAM, 4.7 GB available, 2.4 GB swap in use, load 7.5; 18 GB free on /.
- aralie: same user, 6.4 GB RAM available, swap in use, load 8.6; 3.2 GB free on / (needs A6 too).
- One E16 process reaches ~4.3 GB RSS within its first hour (aspe, range 49-51); per 42 batches ~5 GB of output.
**Recommend A:** abelie has the headroom; on akazie/aralie our ~4 GB process would push the other user's jobs into swap or the OOM killer.
- **A** Add abelie only (after A6); akazie and aralie stay out. E16 on 3 VMs.
- **B** All five, with a guard that waits before each range while MemAvailable < 6 GB. More parallelism, risk to the other user's jobs on akazie/aralie.
- **C** Ask the other user first; decide akazie/aralie on their answer.
Answer: (pending)
