"""Native relational test of the cosmic web.

The web is treated as a graph of *relationships* (exact ratios between connected
nodes), never as points at absolute coordinates. Connectivity is taken from the
observed catalog (Tempel fil_id + spine ordering), never computed from Euclidean
proximity. All quantities flow through aramis.geometry.native (composition, mediant,
continued-fraction tension, phi-coherence) — no Euclidean distance, no projection,
no means/KDE/z-scores.
"""
