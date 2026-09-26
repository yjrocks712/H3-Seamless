# Reproducing H3 Seamless on the MiniMax H3 / Wan2GP pipeline

## What this release enables

This release specifies the algorithm and the integration contracts, includes the actual baseline and final output videos, and supplies a [media-build utility](../tools/build_demo.py) for reproducing the labelled comparisons. It is intended to help others inspect, implement, and test the approach. It does **not** include a complete executable renderer, model downloads, deployment scripts, the original private input image/audio, or a verified one-command model installation.

To rebuild the presentation from the included videos, follow the [media instructions](MEDIA.md#integrity-and-reproducible-presentation). To reproduce the model inference, use the integration and evaluation requirements below; rebuilding a GIF does not reproduce an H3 generation run.

The pseudocode must not be described as the exact source used to make the historical output. Exact source recovery, dependency pinning, licensing review, and an independently reproducible example are separate work before claiming a complete code release.

## Minimum integration contract

Start from a working native H3 supplied-audio PDD8 pipeline. Before modifying it, record its commit, all local patches, checkpoint hashes, runtime versions, attention backend, dtypes, precision settings, prompt, reference image, waveform, and random-generator behaviour.

Provide the following interfaces:

1. **Window planner:** produce legal native latent lengths and absolute origins. Reject a final window with no new latents.
2. **Native predictor:** accept the active video state, supplied-audio features, step-specific video/audio sigmas, original conditioning, and correct absolute positions. It must not mutate the supplied state unexpectedly.
3. **Native step controller:** update PDD output plans and native step-dependent state before each call.
4. **Replay store:** nine matching-schedule overlap states, copied into owned storage rather than views retaining an entire previous window.
5. **Bounded audio reader/encoder:** preserve source timing and native causal context, with full-versus-bounded same-backend numerical tests.
6. **Streaming decoder/output writer:** accept each new latent exactly once and preserve native temporal context through end of stream.

Keep model weights unchanged when testing the continuation intervention. Use the same corrected audio precision in comparison arms; otherwise an apparent continuation improvement may be an audio-conditioning change.

## Tests that should pass before a learned-video run

- Planner coverage has no missing or duplicated committed latent indices.
- Every active span respects its cap; overlap traces match the next window's absolute origin, dtype, shape, and device.
- Predictor inputs contain the exact saved prefix at every step; post-update prefixes match the next saved point.
- Changing the new suffix does not silently mutate the stored trace.
- A failed or cancelled window cannot publish partial carry state.
- Attention weights cover every video query and sum to one; nonvideo outputs are not accumulated twice.
- Native Q/K normalization, position encoding, and output projection still execute in the expected order.
- Native attention's storage recycling does not corrupt shared inputs.
- Audio slices use absolute positions and preserve causal masking across key tiles.
- Corrected bounded and native audio encoders pass the same numerical tolerances on the same device/backend.
- Precision settings and patched methods are restored after both success and exceptions.
- Streaming/native learned decoding agrees for a short sequence crossing a decode boundary, including the final tail.
- Final RGB frame count, FPS, timestamps, audio duration, and original/master PCM equality are checked separately.
- Allocation counters remain capped as the **synthetic** timeline grows. Label this a structural test, not a long-video visual result.

The historical suite reported 35 passing tests, but those original tests are not shipped here. Passing newly written synthetic tests does not reproduce the historical GPU evidence.

## Controlled experiment plan

Use one rights-cleared reference image, a fixed prompt, and the same continuous supplied audio. Start with the shortest clip containing a meaningful handoff. Record the exact sampler and audio policies for every arm.

Useful comparisons are:

| Comparison | Question |
| --- | --- |
| Native attention vs local/shared-context attention on the same window | Does the attention change alter detail, motion, or consistency? |
| Native H3 continuation vs replay, with other choices documented | Does the complete handoff change help this test case? |
| Finished-overlap re-noising vs the saved sampled trajectory | Does preserving actual intermediate states matter? |
| Replay off vs on under the same bounded-window attention setup | What changes when the trajectory constraint is removed? |
| Hard replay vs a precisely specified fusion rule | Does allowing overlap adaptation help or hurt? |

Not every pair is automatically bit-matched: the methods may consume random numbers or construct conditions differently. Publish those differences instead of calling a comparison controlled solely because both arms use the same numeric seed.

Evaluate multiple seeds and references, quiet/breathing intervals, speech onsets, head turns, visible hands, lighting variation, and camera movement. Include failures. Inspect full-speed audio/video and dense frame sequences around every handoff, not only attractive endpoints.

Only then extend selected cases to several minutes. Track identity/detail drift, cumulative timing error, pause behaviour, total runtime, and per-window allocation. The audio encoder's repeated access to past keys is an explicit scaling concern.

## A useful public evidence bundle

A future runnable release should include:

- Clean source and tests, exact dependency/checkpoint manifests, upstream patches, and applicable licenses.
- Rights-cleared reference image, exact prompt, and a redistributable audio sample.
- Baseline and candidate outputs covering identical times, with unedited source audio available for comparison.
- Raw numerical measurements, resource counters, checksums, and an explicit failed-test log.
- Clear distinctions between direct measurements, sampled subjective observations, and hypotheses.

Do not include credentials, signed download links, private account or worker identifiers, personal filesystem paths, unrelated project files, or private media in a public bundle.

## Suggested claim after reproducing only the existing short test

> We implemented and tested a bounded-window H3 continuation pipeline with step-matched overlap-trajectory replay. A short example showed promising continuity. Multi-minute stability, natural pause behaviour, and the contribution of each component still require controlled evaluation.

Adjust this statement only when additional evidence supports doing so.
