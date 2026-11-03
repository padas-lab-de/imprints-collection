# A12-e30-lorbeer-driver-restart

Issued 2026-11-04 ~00:00 UTC by the data-collection lead.

E30 runs batches 0-54 on lorbeer (driver PID 2400802, at batch 1). Since 2026-11-03 23:56 UTC aspe runs batches 28-54 of the same list. Without a change, lorbeer would crawl 28-54 again later (double requests to the same hosts).

Action: approve that the lead stops the lorbeer E30 driver bash (PID 2400802) after its current batch ends, and restarts it for the open batches up to 27 (run.sh resumes a batch safely). Only the lead's own E30 process is touched. Not urgent: lorbeer reaches batch 28 only after many batches.

## Answer
(open)
