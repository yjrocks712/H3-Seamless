# MiniMax H3 video continuation: the H3 Seamless method

This document describes the historical V14 implementation that produced the reported short test. Code blocks are explanatory pseudocode, not a runnable substitute for the native H3 pipeline.

## 1. Keep two different kinds of window separate

There are **generation windows** and smaller **attention windows inside them**.

A generation window owns the current noisy video state and undergoes eight native PDD evaluations. Attention windows restrict which video/audio tokens a video query can use inside each model evaluation. Changing attention does not itself move generation forward to the next chunk; trajectory replay performs that handoff.

V14 carries only the overlap trajectory between generation windows. It does not retain transformer hidden states or an ever-growing video KV cache. It is not mathematically equivalent to denoising the complete video jointly.

## 2. Tested configuration and geometry

The tested path was `minimax_h3_fl2va_pdd`, supplied audio, native eight-step sampling, dense SDPA, and the original 50-layer BF16 transformer. It used no newly trained weights or added application LoRAs. Native PDD step-dependent output plans were retained.

| Parameter | Value |
| --- | --- |
| Output | 957 RGB frames; 39.875 seconds; 24 FPS |
| Resolution | 1024 × 576 |
| Video latent spatial grid | 36 × 64 |
| Video latent channels | 24 |
| Working video dtype | FP32 |
| Native predicted video output dtype | BF16 |
| Maximum active temporal latents | 142 |
| Replayed overlap temporal latents | 37 |
| Window stride | 105 temporal latents |
| Saved states per overlap | 9: initial state plus 8 updates |
| Opening seed | 8055 |
| Later-window seed rule | `8055 + window_index * 1_000_003` |

For this native temporal packing:

```text
RGB frames F = 17*k + 5
temporal latents L = 5*k + 2

F(L) = 5 + 17*((L - 2)/5), for valid L
```

Thus 142 latents correspond to 481 frames, or 20.0417 seconds. An overlap of 37 latents corresponds to 124 frames, or 5.1667 seconds. The 105-latent stride advances 357 RGB-frame positions, or 14.875 seconds.

For the 282-latent test timeline, the half-open spans were:

| Window | Active latent indices | Incoming overlap | Newly committed indices |
| --- | --- | --- | --- |
| 0 | `[0, 142)` | None | `[0, 142)` |
| 1 | `[105, 247)` | `[105, 142)` | `[142, 247)` |
| 2 | `[210, 282)` | `[210, 247)` | `[247, 282)` |

Latents are committed only once. The decoder's temporal context/blend means latent boundaries cannot simply be treated as independently decoded RGB clip boundaries. In the recorded output, the first fully new frames at the two handoffs were 481 and 838, with short decoder blends preceding them.

## 3. Local video attention with shared context

The original V7 attention intervention was carried into each V14 active window. It operates after native Q/K normalization and positional encoding, before the native attention output projection.

For each video query, the allowed keys are:

- Video tokens in its local temporal attention window.
- The aligned supplied-audio tokens for that local interval.
- The existing original-image and prompt/context tokens.

Prompt, original-image, and audio queries are evaluated globally **within the active generation window**, allowing their updated representations to share information at subsequent layers. This does not give V14 access to every past video frame.

For a full 142-latent active window, the local spans are `[0,37)`, `[30,72)`, `[65,107)`, and `[100,142)`. Short final windows use clipped spans. Native attention is evaluated on each local slice, and overlapping video-query outputs are accumulated with normalized weights.

The raw weighting rule uses a five-point cosine ramp `0.5*(1-cos(linspace(0,pi,5)))`. For noninitial slices, the first two latent weights are zero and the next five ramp upward. Nonfinal slices taper their last five weights downward. Normalize by total coverage so every video query's weights sum to one. Nonvideo queries are evaluated once, without duplicate accumulation.

The callback may recycle its query storage, so independent Q/K/V slices are necessary; otherwise one local evaluation can corrupt another. Accumulation is FP32 and returned in the native query dtype.

This is our H3 attention adaptation. Its conceptual relationship to FreeLOC, and the components not reproduced from that work, are documented in [Prior work](PRIOR_WORK.md).

## 4. Save and replay the entire overlap trajectory

Let `z[k,i]` be generation window `k` at schedule point `i`. Let `P` select its overlapping prefix and `S` select the previous window's matching suffix. The replay invariant is:

```text
P(z[k,i]) = S(z[k-1,i])
```

It holds at each corresponding schedule point. Frame order is chronological. We copy the previous sampled states themselves; we do not synthesize approximate noisy states by adding fresh noise to the final clean overlap.

The trace has shape `[9, batch, channels, overlap_time, height, width]`. For this experiment, that is `[9, 1, 24, 37, 36, 64]` in FP32.

```python
# Pseudocode: native_step and predict are H3-specific integration points.
carry = None
for window in chronological_windows:
    z = make_fresh_noise(window)
    audio = encode_supplied_audio_at_absolute_positions(window)
    outgoing = allocate_nine_suffix_states() if not window.final else None

    for i in range(8):
        if carry is not None:
            z.prefix.copy_(carry[i])

        if outgoing is not None:
            outgoing[i].copy_(z.suffix)

        configure_native_pdd_and_lora_step(i)
        prediction = predict(z, audio, video_sigma[i], audio_sigma[i],
                             original_reference, original_prompt,
                             absolute_positions(window))
        z = native_step(z, prediction, video_sigma[i], video_sigma[i + 1])

        if carry is not None:
            z.prefix.copy_(carry[i + 1])

    if outgoing is not None:
        outgoing[8].copy_(z.suffix)

    decoder.consume_new_latents_only(z, skip=window.incoming_overlap)
    carry = outgoing
    release_completed_window_tensors()

decoder.finish_with_native_end_context()
```

Both copies matter: restore the incoming prefix before prediction and restore its next recorded state after the update. Capture the outgoing suffix at the initial point and after every update, including the final point. Validate shape, dtype, device, absolute starting index, and step count before accepting a trace. On a failed window, discard its incomplete carry state.

The overlap constrains the context seen by newly generated frames. It does not prove that their motion, identity, or expression will be correct, and an error in a saved overlap can propagate forward.

## 5. Preserve native sampling semantics

The schedule has nine FP32 values made on CPU and transferred to the device. With `b_i = 1 - i/8`:

```text
video_sigma_i = 12*b_i / (1 + 11*b_i)
audio_sigma_i =  3*b_i / (1 +  2*b_i)
```

Before each evaluation, refresh the native video/audio PDD plans and the native step index. Do not assume that supplying the correct sigma alone configures all PDD state.

The historical video update preserved the native operation order:

```python
ratio = sigma_next / sigma
denoised = prediction.mul_(sigma).add_(z)
z.mul_(ratio).add_(denoised, alpha=1.0 - ratio)
```

Here the prediction buffer is BF16 and the working video buffer is FP32. Intermediate rounding follows those in-place operations. This is not a generic declaration that every diffusion model uses the same velocity sign or update; an implementation on another model must follow that model's sampler.

The opening noise came from native preparation. Later windows used the recorded seed rule and fresh noise, after which the replay trace overwrote their overlap prefixes. The image was encoded once. These choices do not make the complete output bit-identical to an earlier full-timeline run.

## 6. Keep audio and position clocks absolute

For a window beginning at latent index `s`, the RGB-frame origin is `17*(s//5)`. Audio features occur at 40 positions per second, so the slice starts at:

```text
audio_start = round(rgb_origin * 40 / 24)
audio_end   = round((rgb_origin + F(window_latents)) * 40 / 24)
```

Round absolute endpoints, not a per-window duration accumulated repeatedly. Target audio temporal coordinates shift by `audio_start`; target video coordinates shift by `rgb_origin*(5/3)` in the native packing convention. The original-reference coordinate remains unchanged. This preserves native physical-time positions; it is not FreeLOC-style position remapping.

The delivered narration comes from one continuous source waveform. It is not generated again or assembled from separately edited speech chunks. The output master preserves the original 44.1 kHz stereo PCM; model conditioning uses a 32 kHz resample.

## 7. Bounded audio encoding and the precision fix

Simply cutting the waveform at every video window can alter audio context. The bounded encoder therefore retained global causal audio attention while computing only a bounded query/key workspace:

- Native 800-sample stride at 32 kHz, or 40 audio latent positions per second.
- Query cap 802 positions; key tiles 256 positions.
- A conservative 32-latent convolution halo on each side, clipped at actual endpoints.
- Recompute older key/value feature tiles from the immutable source waveform.
- Apply the causal mask using absolute query/key positions.
- Combine key-tile attention using a running maximum, normalizer, and weighted-value sum, then apply the native projections and normalization.

No growing audio KV cache was retained. This saves workspace at the cost of repeated computation: audio work can grow with the length of the preceding history. Bounded memory is not a claim of constant per-second runtime.

Real-weight testing found that the tested B200's TF32 convolution policy produced shape-dependent differences between full-waveform and tiled audio encoding. The correction scoped IEEE FP32 arithmetic to **both** the bounded audio encoder and the native audio-encoding reference, restoring caller settings after success or failure. Video/text precision and the model weights were unchanged.

The unchanged comparison tolerances were `atol=0.0002` and `rtol=0.0002`. Same-backend CUDA parity passed after the correction. This does not imply exact CPU/CUDA parity or bit identity to the old TF32 conditioning. See [Results](RESULTS.md).

## 8. Stream the native decoder, not separate finished clips

A single streaming decoder receives the first window's complete latent sequence, then only each later window's new suffix. It keeps enough context to reproduce the native temporal decoding/blending rules.

The audited path processes native seven-latent neighborhoods. Each decoded neighborhood yields 28 internal RGB frames; it emits the native 17-frame selection, retains the five-frame blend tail, and advances five latent positions. The final five frames are emitted once at end of stream. Latents are cast to the native decoder dtype before denormalization, matching the native rounding order.

Do not independently decode each generation window and concatenate its apparent finished output. A window's padded end may differ from decoding after subsequent context has become available. The bounded decoder was checked against the real native decoder over 124 frames in the recorded test.

## 9. What is bounded, and what is not

The active video state, overlap traces, local attention workspaces, audio query/key workspace, and decoder input buffer have fixed caps for a chosen resolution and window size. At most two overlap traces coexist during handoff.

```text
two_trace_bytes = 2 * 9 * 1 * 24 * 37 * 36 * 64 * 4
                = 140.484375 MiB
```

The pretrained model weights are additional and large. The recorded run had about 115.83 GiB of resident model tensors and peaked at about 126.19 GiB of PyTorch allocation. This was not a consumer-GPU demonstration.

The source audio and output files still grow with duration. Recomputed historical audio keys increase work. Absolute video positions continue advancing beyond the short range already tested. Error accumulation and positional extrapolation remain research questions even if allocation counters stay bounded.
