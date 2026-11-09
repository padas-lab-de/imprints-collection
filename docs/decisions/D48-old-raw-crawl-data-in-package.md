# D48-old-raw-crawl-data-in-package

Issued 2026-11-09 (lead). Blocks: the completeness of the S3 package innkube datasets/imprints/20261109/ (not the count).

**Context:** The D47 inventory (tmp/wrapup/inventory.md) shows that the raw crawl output (page text `imprints_*.jsonl.gz` and `fetch_status_*.tsv`) of the old sources E16, E19, E22, E25-E29, E34 and E36 is only on the VMs (apfel, aspe, abelie, mispel, lorbeer), and for parts of E19 round 2 and E22 only on akazie and aralie. Size: roughly 40 GB or more (E16 alone about 31 GB). The count does not need it: the per-host tables of every crawl dir are in counts/r4/E31_in (929 MB) and go into the package. The page text is needed only to re-extract addresses or topics from the old sources without a re-crawl. The package now gets everything on lorbeer and in the lead tmp (about 20 GB, page text included).

**Recommend A:** the page text is the expensive part to recreate (a re-crawl gives different pages), and the VMs will be released at some point.
- **A** Copy the old raw dirs from all VMs (incl. read-only access to akazie and aralie) to lorbeer, gzip-check them, and upload them to crawls/<source>/ in the package. Cost: about 40+ GB on lorbeer (203 GB free) and S3; read-only copy traffic from the VMs.
- **B** Tables only for the old sources: the package documents that their page text stays on the VMs. Cost: none now; the page text is lost when a VM is wiped.

**Outcome:** A (user, 2026-11-09: "D48 A."). Agent copies the old raw dirs read-only from the VMs (rsync with bandwidth limit, E48 still runs) to lorbeer, gzip-checks, adds them to crawls/<source>/ and uploads.
