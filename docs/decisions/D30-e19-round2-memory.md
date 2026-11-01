# D30-e19-round2-memory · How to handle the OOM kills in E19 round 2b?

Issued 2026-11-01 16:35 UTC by the data-collection lead. Blocks: E19 round 2b on akazie and mispel.

## Context
- akazie round2b is DEAD: `recovery exit 137 (try 5)` at 11:58 UTC, all RESTARTS=5 used. 6,730 of 48,555 hosts done (1,780 imprint_found), ~41.8k left. akazie has 4 GB free (user dang 9.2 GB).
- mispel round2b was killed by OOM twice (12:50, 13:21 UTC). The current fetch (pid 1867002) has RSS 25.6 GB after 3 h 13 min, with 2 GB free, so another kill is likely. 13,249 of 40,630 done (3,733 found), ~27.4k left.
- The fetches on aralie, aspe and lorbeer stay at 1.1-1.2 GB RSS after 9.5 h. So a few hosts in these shards make the fetch grow. It is not a general leak.
- Likely cause: `requests_get_with_timeout` (src/ic/cli/fetch.py) reads the body into memory with no size cap. Only the total timeout stops it, so a fast server that sends a large or endless body can put GBs into memory per request, times 16 workers. This is a hypothesis; it is not measured yet.
- abelie and apfel are idle with 23-27 GB free. apfel is the E16 origin VM for batches 157-213, so those hosts go to abelie.

## Options
**Recommend A:** it removes the probable cause before more work is lost, and the idle VMs have the memory.
- **A** Stop the mispel fetch now (fetch resume keeps all finished hosts). Add a body-size cap to fetch.py (MAX_BODY_BYTES, e.g. 10 MB: stop reading, treat the response as too large), with a test, on a branch, and log the size of each capped body. Reshard the akazie and mispel remainders (~69k hosts) over abelie and apfel with the cap, keeping the E16-origin rule. aralie, aspe and lorbeer continue with the old code.
- **B** Leave mispel running (it restarts itself up to 3 more times). Move only the akazie remainder to abelie and apfel, with the current code. No code change.
- **C** As A, but first find the hosts that make the fetch grow (sample the RSS per host on a copy of mispel's shard) before the cap goes in.

## Answer
(open)
