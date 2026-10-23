# D12-town-granularity-metric (2026-10-23) — open
Context: 31/47 Qwen address errors are town granularity (gold "Grimma /OT Kaditzsch" vs pred "Grimma"); draft guideline v0.1 says drop district suffixes, old gold keeps them.
Recommend A. A: primary address metric = location match via geocoding (both gold and prediction geocoded with Photon; match if same postcode+street or within 100 m), keep field-level exact/normalized as secondary; guideline: copy town as written (matches old gold). B: strip district suffixes in gold and predictions during normalization. C: leave as is.
