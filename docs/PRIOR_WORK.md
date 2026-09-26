# Prior work and attribution

## What we are taking credit for

**We built H3 Seamless and got it running successfully in the documented short test.** The project contribution is the H3-specific implementation and integration: local video attention with shared context, direct step-matched overlap-trajectory replay, absolute timing, bounded audio processing, native streaming decoding, and the tested audio precision correction.

The project owner set the requirements and evaluated results. Codex proposed, wrote, and integrated the experimental code during the task. Related prior research and substantial implementation work can both deserve credit. This implementation is ours; not every underlying idea originated here.

The relevant question is whether **everything we implemented was already described in FreeLOC**. The answer is **no**: trajectory replay was an additional mechanism. That does not make it unprecedented in the broader literature.

## Upstream foundation

- **MiniMax H3:** the pretrained model and its learned generation ability. We did not train a replacement model.
- **[Wan2GP](https://github.com/deepbeepmeep/Wan2GP):** the H3 runtime/integration, native PDD sampling path, packing, encoders, and decoders used as the starting point. We do not take credit for these components.

For the native-continuation comparison, the [versioned H3 pipeline](https://github.com/deepbeepmeep/Wan2GP/blob/7e6242e4b6e3e60eaf4a888115141979f3e5c471/models/minimax_h3/pipeline.py#L692) shows encoded history frames plus a final-frame condition. The comparison is to that inspected path, not a blanket description of all Wan2GP architectures or current features.

The complete patched deployment environment is not included in this release. The linked upstream commit identifies the comparison source; it is not, by itself, a complete reproducibility manifest for V14.

## Direct research inspiration: FreeLOC

**Paper:** [Free-Lunch Long Video Generation via Layer-Adaptive O.O.D Correction](https://arxiv.org/html/2603.25209v1), Jiahao Tian and colleagues, 2026. **Code:** [Westlake-AGI-Lab/FreeLOC](https://github.com/Westlake-AGI-Lab/FreeLOC).

FreeLOC directly informed our attention design: emphasize local detail while retaining a persistent consistency reference. Its published method includes relative-position remapping, tiered sparse attention, and layer-adaptive probing. We did not reproduce those three components as a complete package. Our H3 adaptation uses native positions and its own overlapping video/audio attention policy.

FreeLOC's described method is not the source of the separate saved-trajectory handoff. Calling this project a complete FreeLOC port would therefore be inaccurate.

## Related prior work: FrameCache

**Paper:** [Screen, Cache, and Match: A Training-Free Causality-Consistent Reference Frame Framework for Human Animation](https://arxiv.org/html/2601.22160v2), Jianan Wang and colleagues. The relevant version is dated 10 April 2026.

Its **TAAG** component saves overlap latent states throughout denoising and uses corresponding states when processing adjacent chunks. This is the closest methodological match identified in our comparison. The paper explicitly discusses hard overwriting, then proposes frequency-separated fusion to retain flexibility; V14 hard-copies the saved states. V14 does not implement FrameCache's dynamic reference selection or proposed frequency fusion.

The relevant explanation is [Section 3.3, equations 9–15](https://arxiv.org/html/2601.22160v2#S3.SS3). That is evidence of related published methodology, not evidence that their full system and ours are identical. We have not verified an official public code repository; the inspected paper says code will be released.

## Related prior work: VidRD / Reuse and Diffuse

**Paper:** [Reuse and Diffuse: Iterative Denoising for Text-to-Video Generation](https://arxiv.org/html/2309.03549v1), Jiaxi Gu and colleagues, 2023. **Code:** [anonymous0x233/ReuseAndDiffuse](https://github.com/anonymous0x233/ReuseAndDiffuse).

VidRD is an older example of extending video through reuse of noise and intermediate denoising states. Its frame-order reversal and staged guidance differ from V14's chronological, all-step overlap replay. See [Section 4.3](https://arxiv.org/html/2309.03549v1#S4.SS3).

## Other background references

FIFO-Diffusion, VideoMerge, and Diff-VF appeared in the broader project research. Their mention is not a claim that V14 implemented their algorithms. They should not be presented as three imported software components merely because they were discussed during exploration.

## Development chronology

The inspected development records distinguish the proposal, implementation, and later identification of related work. Times below are UTC.

| Recorded event | Time |
| --- | --- |
| Codex explicitly proposed retaining the overlap's original eight-step latent trajectory without decoding/re-encoding | 9 September 2026, 00:06:58 |
| A broader search for latent-trajectory/overlap continuation began | 9 September 2026, 00:07:30 |
| A raw search capture contained a FrameCache mention; that section was absent from the truncated excerpt delivered to the model | 9 September 2026, 00:08:00 |
| The first overlap-trajectory implementation patch was recorded | 9 September 2026, 00:11:12 |
| A named VidRD search appeared during the later prior-art investigation | 22 September 2026, 20:35:30 |

The chronology supports crediting Codex with proposing and implementing the H3 mechanism during the task. It does not support saying FrameCache never appeared anywhere in the search history. No direct consultation of the FrameCache paper before the first implementation was found in the audit. The substantive comparison identifying FrameCache and VidRD as related prior work occurred later.

Accordingly, **FreeLOC is credited as an explicit design inspiration; FrameCache and VidRD are credited as related prior work, not asserted sources of the original proposal.** We do not claim that no other researcher implemented the idea, or that our integration was the first on H3.

## Public attribution wording

> Prior work was present in FrameCache, which is a research framework described in a paper, and VidRD, which is a research framework with both a paper and a public code repository.

FreeLOC was a documented attention-design inspiration. FrameCache and VidRD are identified here as related prior work, not as established sources of the original implementation proposal or as repositories copied into this release. Similarity alone does not establish the historical source of an idea.

We make no claim about the presence or absence of particular papers in an AI model's training data. Failed recall cannot establish that provenance. Nor does independently writing an implementation establish that its underlying method is new to the field.

Model weights, upstream code, and papers retain their respective authorship and licensing. This documentation does not relicense or redistribute those assets.
