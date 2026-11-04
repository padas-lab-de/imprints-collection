# A12-e30-lorbeer-driver-restart

Issued 2026-11-04 ~00:00 UTC by the data-collection lead.

E30 runs batches 0-54 on lorbeer (driver PID 2400802, at batch 1). Since 2026-11-03 23:56 UTC aspe runs batches 28-54 of the same list. Without a change, lorbeer would crawl 28-54 again later (double requests to the same hosts).

Action: approve that the lead stops the lorbeer E30 driver bash (PID 2400802) after its current batch ends, and restarts it for the open batches up to 27 (run.sh resumes a batch safely). Only the lead's own E30 process is touched. Not urgent: lorbeer reaches batch 28 only after many batches.

## Answer
User 2026-11-04 ~10:00 UTC: "A12 yes."

Done 10:02 UTC: driver bash 2400802 stopped with SIGTERM while batch 8 ran; batch-8 fetch 408845 kept running. Waiter 541785 (results/E30/logs/wait_9-27.sh) starts run.sh for batches 9-27 (same ROOT, PY, STEP=1, Shopify skip) when 408845 exits; log results/E30/logs/driver_9-27.log. Batches 28-54 stay on aspe.
