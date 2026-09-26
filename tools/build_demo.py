#!/usr/bin/env python3
"""Build honest, time-aligned presentation media from existing H3 outputs.

Requires FFmpeg/FFprobe and ImageMagick for vector label rendering. Does not render AI video, retouch frames, enhance faces,
interpolate motion, alter speed, or train anything. Inputs remain untouched.
"""
import argparse
import hashlib
from html import escape
import json
from pathlib import Path
import subprocess
import tempfile


def run(*args, **kwargs):
    subprocess.run(args, check=True, **kwargs)


def probe(path):
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries',
        'stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,duration:format=duration',
        '-of', 'json', str(path)], text=True))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--attention', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parents[1] / 'assets')
    parser.add_argument('--font', type=Path)
    parser.add_argument('--replace', action='store_true', help='Replace this tool\'s generated media in --out.')
    args = parser.parse_args()
    out = args.out
    media_names = ('native-control.mp4', 'attention-v7.mp4', 'h3-seamless-v14.mp4',
                   'before-after.mp4', 'before-after.gif', 'handoffs.mp4',
                   'handoffs.gif', 'boundary-proof.png')
    sources = {'native-control': args.before, 'attention-v7': args.attention,
               'h3-seamless-v14': args.after}
    targets = [out / name for name in (*media_names, 'media-manifest.json')]
    source_paths = {path.resolve() for path in sources.values()}
    for target in targets:
        if target.resolve() in source_paths:
            raise SystemExit('Output would replace an input. Choose a different --out directory.')
        if target.exists() and not args.replace:
            raise SystemExit(f'Output already exists: {target}. Choose a new --out or pass --replace.')
    candidates = [args.font, Path('/System/Library/Fonts/Supplemental/Arial.ttf'),
                  Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
    font = next((p for p in candidates if p and p.is_file()), None)
    if font is None:
        raise SystemExit('Pass --font with an installed TrueType font.')
    scratch = tempfile.TemporaryDirectory(prefix='h3-seamless-labels-')
    ffmpeg = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y' if args.replace else '-n']
    manifest = {'purpose': 'Presentation media derived from existing outputs; no new AI render.',
                'source_files': {}, 'generated_files': {}}
    for name, source in sources.items():
        info = probe(source)
        video = next(s for s in info['streams'] if s['codec_type'] == 'video')
        expected = 957 if name == 'h3-seamless-v14' else 481
        actual = (video['width'], video['height'], video['r_frame_rate'], int(video['nb_frames']))
        if actual != (1024, 576, '24/1', expected):
            raise SystemExit(f'{name}: expected 1024x576, 24 FPS, {expected} frames; got {actual}.')
        manifest['source_files'][name] = {'sha256': sha(source), 'media': info}
    out.mkdir(parents=True, exist_ok=True)
    for name, source in sources.items():
        # Container-only rewrite: preserve audio/video packets; strip metadata.
        run(*ffmpeg, '-i', str(source), '-map', '0:v:0', '-map', '0:a:0',
            '-c', 'copy', '-map_metadata', '-1', '-map_chapters', '-1',
            '-movflags', '+faststart', str(out / (name + '.mp4')))

    def label_card(name, left, right):
        parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="424">',
                 '<rect width="1280" height="46" fill="#111820"/>',
                 '<rect y="406" width="1280" height="18" fill="#111820"/>']
        for x, (heading, footer, colour) in zip((18, 658), (left, right)):
            parts.append(f'<text x="{x}" y="30" font-family="Arial" font-size="21" fill="{colour}">{escape(heading)}</text>')
            parts.append(f'<text x="{x}" y="419" font-family="Arial" font-size="11" fill="#b2bdc7">{escape(footer)}</text>')
        parts.append('</svg>')
        path = Path(scratch.name) / (name + '.png')
        run('magick', '-background', 'none', '-font', str(font), 'svg:-', str(path), input=''.join(parts).encode())
        return path

    def panel(index, start, duration):
        return (f'[{index}:v]trim=start={start}:duration={duration},setpts=PTS-STARTPTS,'
                f'scale=640:360:flags=lanczos,pad=640:424:0:46:color=0x111820[p{index}]')

    duration = 481 / 24
    labels = label_card('comparison',
        ('BEFORE  /  Native H3 control', 'Same 1024 x 576 output size | Opening 20.04 seconds', '#ffbf93'),
        ('AFTER  /  H3 Seamless - V14', 'Same narration interval | Pipeline comparison, not an isolated ablation', '#b6f36b'))
    graph = ';'.join([
        panel(0, 0, duration), panel(1, 0, duration),
        '[p0][p1]hstack=inputs=2[pair];[pair][2:v]overlay=shortest=1[v]'])
    run(*ffmpeg, '-i', str(args.before), '-i', str(args.after), '-loop', '1', '-i', str(labels), '-filter_complex', graph,
        '-map', '[v]', '-map', '1:a:0', '-t', str(duration), '-c:v', 'libx264',
        '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-c:a', 'aac',
        '-b:a', '192k', '-map_metadata', '-1', '-movflags', '+faststart',
        str(out / 'before-after.mp4'))

    def gif(source, target, seconds):
        filt = (f'trim=duration={seconds},fps=12,scale=960:-1:flags=lanczos,split[a][b];'
                '[a]palettegen=max_colors=192:stats_mode=diff[p];'
                '[b][p]paletteuse=dither=sierra2_4a')
        run(*ffmpeg, '-i', str(source), '-filter_complex', filt, '-an', '-loop', '0', str(target))

    gif(out / 'before-after.mp4', out / 'before-after.gif', 4)
    labels = label_card('handoffs',
        ('HANDOFF 01  /  20.04 seconds', 'Final V14 footage | 18.00-22.00 s | Normal speed', '#b6f36b'),
        ('HANDOFF 02  /  34.92 seconds', 'Final V14 footage | 33.00-37.00 s | Normal speed', '#b6f36b'))
    graph = ';'.join([
        panel(0, 18, 4), panel(1, 33, 4),
        '[p0][p1]hstack=inputs=2[pair];[pair][2:v]overlay=shortest=1[v]'])
    run(*ffmpeg, '-i', str(args.after), '-i', str(args.after), '-loop', '1', '-i', str(labels), '-filter_complex', graph,
        '-map', '[v]', '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '19',
        '-pix_fmt', 'yuv420p', '-map_metadata', '-1', '-movflags', '+faststart', str(out / 'handoffs.mp4'))
    gif(out / 'handoffs.mp4', out / 'handoffs.gif', 4)

    # Two adjacent frames, not a best-looking-frame substitution.
    graph = "select='eq(n,31)+eq(n,32)',tile=1x2"
    run(*ffmpeg, '-i', str(out / 'before-after.mp4'), '-vf', graph,
        '-frames:v', '1', str(out / 'boundary-proof.png'))

    manifest['comparisons'] = {
        'before-after': {'left': 'native-control', 'right': 'h3-seamless-v14',
                         'source_interval_seconds': [0, duration], 'gif_interval_seconds': [0, 4],
                         'type': 'complete-pipeline comparison; replay does not begin until after the opening window'},
        'matched-attention-study': {'before': 'native-control', 'after': 'attention-v7',
                                   'type': 'historically verified matching initial state and prompt/image encoding'},
        'handoffs': {'left_interval_seconds': [18, 22], 'right_interval_seconds': [33, 37],
                     'source': 'h3-seamless-v14', 'speed': '1x'},
        'boundary-proof': {'source_video_frame_indices': [31, 32], 'source_fps': 24}}
    for name in sorted(media_names):
        file = out / name
        manifest['generated_files'][name] = {'sha256': sha(file), 'bytes': file.stat().st_size,
                                            'media': probe(file)}
    (out / 'media-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    scratch.cleanup()
    print('Built and documented', len(manifest['generated_files']), 'media assets.')


if __name__ == '__main__':
    main()
