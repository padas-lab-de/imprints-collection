# A7-ssh-dir-owner-lorbeer (issued 2026-10-26)
- [ ] A7-ssh-dir-owner-lorbeer: on the lead VM lorbeer, `sudo chown dinzinger: ~/.ssh` (it is owned by root, so ssh cannot save host keys: GitHub ssh fails "Host key verification failed").
Workaround in use: crawl-VM host keys in ~/.config/ic-ssh/known_hosts, `ssh -o UserKnownHostsFile=~/.config/ic-ssh/known_hosts <vm>`.
Unblocks: git fetch/push to origin from the lead VM without the workaround.
Answer (2026-10-26): user ran `sudo chown dinzinger: ~/.ssh` on lorbeer. Host keys of the 5 VMs and github.com (SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU) added to ~/.ssh/known_hosts; plain `ssh <vm>` and git push work.
