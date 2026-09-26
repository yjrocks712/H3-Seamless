# H3 Seamless: results, evidence, and limitations

## Evidence status

The experiment occurred on 9 September 2026. The figures below are transcribed from contemporaneous source/report records inspected during preparation of this publication on 27 September. They are **historical measurements**, not measurements from a new run performed for this release.

The archived output videos were recovered through their existing workspace links for this release. We freshly checked stream metadata, source checksums, and selected comparison frames, then packaged stream-preserving viewing copies and labelled comparison assets. The final V14 source checksum matches the contemporaneous record. See [the media evidence](MEDIA.md) to watch the actual result and inspect the before/after.

The GPU measurements, regression counts, original/master PCM equality, and dense transition review below remain historical evidence; they were not rerun for publication. The original input image/audio, complete renderer bundle, and raw logs are not included. The videos let readers inspect the output, but this package alone does not reproduce model inference or independently verify every reported numerical measurement.

## See the difference

The native control abruptly reframes between frames 31 and 32, at about 1.33 seconds. Both the earlier shared-attention V7 output and final V14 output retain the shot through those frames. The [before/after presentation](../assets/before-after.mp4) places native and V14 footage side by side over the same opening 20 seconds; [adjacent-frame evidence](../assets/boundary-proof.png) makes the change easy to inspect.

The native/V7 pair was a matched attention study. Native/V14 is a whole-pipeline comparison, not an isolated replay ablation: replay first takes effect at the later window handoff. The [handoff excerpts](../assets/handoffs.mp4) show the two actual V14 transitions. These are separate pieces of evidence, not interchangeable claims.

## The final short run

| Check | Recorded result |
| --- | --- |
| Video | 957 frames, 39.875 seconds, 1024 × 576, 24 FPS |
| Generation | Three windows; two handoffs |
| Sampler evaluations | 24: eight per window |
| Native attention-layer traversals | 1,200 |
| Dense attention calls | 5,200 |
| Original image encodes | One |
| Decoded video reused as generation input | None |
| Generated latent history reused | Yes, the overlap trajectory |
| Local regression suite | 35 tests passed |
| Bounded audio versus corrected native CUDA | Worst absolute error 0.00000309944; `atol=rtol=0.0002` |
| Learned streaming decoder versus native | 124 frames; measured difference zero |
| Master audio | Original decoded PCM preserved exactly |
| Maximum active video window | 142 temporal latents |
| Maximum two-trace overlap allocation | 140.4844 MiB |
| Maximum streaming-decoder input buffer | Ten temporal latents |
| Resident model tensors | 115.8338 GiB |
| Peak PyTorch allocation / reservation | 126.1947 / 127.0371 GiB |
| Inference model evictions | Zero |
| Recorded render-worker elapsed time | 283.7945 seconds |

The elapsed time is the historical worker measurement, not total cold-start deployment time or a repeatable performance benchmark. PyTorch counters are not a measurement of every byte of device memory used by all processes. CPU source-PCM reading, initial noise construction, loading, and output delivery existed; “no offloading” here refers to model/activation offloading during inference.

## What the visual review actually established

The recorded review inspected approximately 4-FPS overview samples, full-resolution endpoints and face crops, and all 25 frames in each of two transition neighborhoods (469–493 and 826–850). It reported no obvious identity jump, scene cut, camera reset, clothing change, or gross anatomical discontinuity in those inspected samples.

Endpoint review found recognizable facial structure and preserved overall detail, with minor local texture/expression differences. This was not pixel-identical facial preservation. Fast hand details were sometimes motion-blurred.

These are qualitative, sampled observations. They are not a blinded perceptual study, a complete frame-by-frame defect audit, or a full-speed audiovisual acceptance score.

## The important unresolved issue: mouth behaviour around pauses

Subsequent review raised concerns around approximately 9, 19–22, and 27–30 seconds. Frame sequences showed an open-mouth hold in one region and transitions from rest into speech-like mouth movement in others. The precise renderer-level cause was not isolated.

The follow-up file-level audio audit found:

- Source and lossless master had identical decoded PCM and sample counts.
- Source and delivered MP4 transcriptions each contained the same 89 recognized words; ASR agreement alone is not ground truth.
- No new internal audio dropout was detected by the reported signal test.
- The model-conditioning waveform matched the expected resample.

This supports **audio integrity**, not correct mouth motion. Nonzero audio energy is not proof that someone is speaking, and a good whole-clip timing offset does not validate natural pauses or phoneme-level lip shapes. No validated pause-behaviour fix is claimed here.

The coarse generation handoffs were at about 20.0417 and 34.9167 seconds. The 9- and 27-second concerns were not those coarse joins. Their timing alone does not establish whether attention, audio conditioning, or base-model behaviour caused them.

## What failed before the successful render

An early worker had insufficient available GPU memory and failed during loading, before the continuation method ran. A later attempt loaded the stack but failed the audio parity gate before video generation. These are failures, not successful visual experiments.

The audio diagnostic reproduced a maximum absolute discrepancy of 0.0023185 with 992 values outside the original tolerance in the first window. Disabling TF32 for the relevant audio convolution path resolved the same-backend comparison. The reference and bounded encoder were both evaluated under the corrected policy.

An additional corrected CPU-versus-CUDA comparison still had five values outside tolerance among 102,080. That diagnostic was not exact cross-device equivalence; the required gate was bounded versus native encoding on the same CUDA backend. We do not hide that distinction by reporting only the successful comparison.

## What this experiment does not establish

- Reliable five-, ten-, or twenty-minute learned-video generation. Longer synthetic planner tests are not rendered videos.
- A causal quality advantage attributable solely to trajectory replay, solely to attention, or solely to the audio fix.
- Superiority to every Wan2GP continuation mode or later implementation.
- Guaranteed lip synchronization, expressive performance, correct hands, or drift-free output.
- Constant-time generation, low-memory deployment of the complete model, or consumer-GPU viability.
- A new research algorithm absent from prior literature.

There was no matched full-39.875-second V7 control. The earlier V7 clip covered roughly 20 seconds, so it cannot answer what would have happened at later timestamps. The audio correction also changes conditioning relative to the older TF32 policy, complicating attribution.

## The defensible finding

We completed the implementation, fixed the audio-encoding numerical blocker, and successfully generated the short real-model test using bounded active video state and latent-state handoffs. The inspected handoffs had no obvious identity jump or scene reset. These are concrete engineering results, not only a proposed design.

Natural pause behaviour and long-duration robustness remained unresolved. The result establishes that this H3 integration worked in the documented test; it does not establish universal continuity, a world-first algorithm, or which component individually caused the observed visual improvement.
