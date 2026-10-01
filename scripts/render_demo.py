#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Crop the HDR recording and render an annotated GIF and SDR social video.

Usage: python3 scripts/render_demo.py /path/to/original.mp4
The default crop is the Blender window in the supplied 1906x1306 recording.
The source uses Blender's 400-nit HDR view transform. The MP4 stays in HDR;
the GIF and social MP4 are tone mapped and include an animated mouse indicator.
"""
import argparse
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from demo_mouse import render_sequence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--crop', type=int, nargs=4, metavar=('X', 'Y', 'WIDTH', 'HEIGHT'),
                        default=(46, 38, 1814, 1214))
    parser.add_argument('--peak-nits', type=float, default=400)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    root = Path(__file__).resolve().parents[1]
    destination = root / 'docs' / 'media'
    destination.mkdir(parents=True, exist_ok=True)

    probe = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_streams',
        '-of', 'json', str(source)], text=True))['streams'][0]
    if (probe.get('color_transfer'), probe.get('color_primaries')) != ('smpte2084', 'bt2020'):
        parser.error('This conversion expects the original PQ/BT.2020 HDR recording')
    x, y, width, height = args.crop
    if (min(x, y) < 0 or min(width, height) <= 0
            or x + width > probe['width'] or y + height > probe['height']
            or any(v % 2 for v in args.crop) or args.peak_nits <= 100):
        parser.error('Use an in-bounds, even crop and an HDR peak above 100 nits')
    crop = f'crop={width}:{height}:{x}:{y}'

    with TemporaryDirectory(prefix='demo-', dir=destination) as temporary:
        temporary = Path(temporary)
        video = temporary / 'orbit-wheel-zoom.mp4'
        gif = temporary / 'orbit-wheel-zoom.gif'
        social = temporary / 'orbit-wheel-zoom-social.mp4'
        annotated = temporary / 'annotated.mkv'
        duration = float(probe['duration'])
        indicators = temporary / 'mouse'
        render_sequence(indicators, duration)
        base = ['ffmpeg', '-hide_banner', '-loglevel', 'warning', '-i', str(source)]
        subprocess.run(base + [
            '-map', '0:v:0', '-vf', crop, '-an', '-c:v', 'libsvtav1',
            '-preset', '8', '-crf', '18', '-svtav1-params', 'lp=4',
            '-pix_fmt', 'yuv420p10le', '-color_range', 'tv',
            '-color_primaries', 'bt2020', '-color_trc', 'smpte2084',
            '-colorspace', 'bt2020nc', '-movflags', '+faststart', '-y', str(video)
        ], check=True)
        filters = (
            f'[0:v]{crop},fps=30,'
            'zscale=transfer=linear:npl=100,format=gbrpf32le,'
            'zscale=primaries=bt709,'
            f'tonemap=mobius:param=0.3:desat=0:peak={args.peak_nits / 100},'
            'zscale=transfer=iec61966-2-1:matrix=gbr:range=full,format=gbrp,'
            'scale=1280:-2:flags=lanczos[scene];'
            '[1:v]scale=392:120:flags=lanczos[mouse];'
            '[scene][mouse]overlay=x=27:y=H-h-96:format=rgb:shortest=1,format=bgr0[out]'
        )
        subprocess.run(base + [
            '-thread_queue_size', '64', '-framerate', '30', '-i', str(indicators / '%04d.png'),
            '-filter_complex', filters, '-map', '[out]', '-an',
            '-c:v', 'ffv1', '-level', '3', '-pix_fmt', 'bgr0',
            '-color_primaries', 'bt709', '-color_trc', 'iec61966-2-1',
            '-colorspace', 'rgb', '-color_range', 'pc', '-y', str(annotated)
        ], check=True)
        sdr_base = ['ffmpeg', '-hide_banner', '-loglevel', 'warning', '-i', str(annotated)]
        gif_filters = (
            'fps=12,scale=960:-2:flags=lanczos,split[a][b];'
            '[a]palettegen=max_colors=192:stats_mode=diff[p];'
            '[b][p]paletteuse=dither=none:diff_mode=rectangle'
        )
        subprocess.run(sdr_base + ['-filter_complex', gif_filters, '-loop', '0', '-y', str(gif)],
                       check=True)
        subprocess.run(sdr_base + [
            '-vf', 'format=gbrp,zscale=primariesin=bt709:transferin=iec61966-2-1:matrixin=gbr:'
                   'rangein=full:transfer=bt709:matrix=bt709:range=limited,format=yuv420p',
            '-an', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
            '-color_primaries', 'bt709', '-color_trc', 'bt709',
            '-colorspace', 'bt709', '-color_range', 'tv',
            '-movflags', '+faststart', '-y', str(social)
        ], check=True)
        for artifact in (video, gif, social):
            output = destination / artifact.name
            artifact.replace(output)
            print(f'{output}: {output.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
