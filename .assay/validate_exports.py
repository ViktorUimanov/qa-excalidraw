"""Independent integrity check for files downloaded by Assay; stdlib only."""
from pathlib import Path
import json, struct, sys, zlib
import xml.etree.ElementTree as ET


def assert_visible_png(data, compressed, width, height):
    """Decode our canvas's 8-bit PNG and reject an empty/uniform export."""
    depth, color, compression, filtering, interlace = data[24:29]
    assert depth == 8 and color in (2, 6) and (compression, filtering, interlace) == (0, 0, 0), "Unsupported PNG encoding"
    channels = 4 if color == 6 else 3
    stride = width * channels
    raw = zlib.decompress(compressed)
    assert len(raw) == height * (stride + 1), "Wrong decoded PNG size"
    previous = bytearray(stride)
    pixels = []
    for y in range(height):
        offset = y * (stride + 1)
        kind = raw[offset]
        assert 0 <= kind <= 4, "Invalid PNG row filter"
        row = bytearray(raw[offset + 1:offset + 1 + stride])
        for x in range(stride):
            left = row[x - channels] if x >= channels else 0
            up = previous[x]
            upper_left = previous[x - channels] if x >= channels else 0
            prediction = left + up - upper_left
            distances = [abs(prediction - v) for v in (left, up, upper_left)]
            paeth = (left, up, upper_left)[distances.index(min(distances))]
            row[x] = (row[x] + (0, left, up, (left + up) // 2, paeth)[kind]) & 255
        pixels.extend(tuple(row[x:x + channels]) for x in range(0, stride, channels))
        previous = row
    background = pixels[0]
    ink = sum(max(abs(a - b) for a, b in zip(pixel, background)) > 20 for pixel in pixels)
    assert ink > 50, "Export contains no visible drawing (uniform/blank image)"


root = Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent/'runs'
found = {name:[p for p in root.rglob(name) if p.is_file()] for name in ('export.svg','export.png','scene.excalidraw')}
for name, paths in found.items():
    if not paths: raise SystemExit(f'Missing expected download: {name}')
    for p in paths:
        data=p.read_bytes()
        if name.endswith('.svg'):
            tree=ET.fromstring(data)
            assert tree.tag.endswith('svg'), f'Not SVG: {p}'
            assert any(e.tag.endswith('path') and e.get('d') for e in tree.iter()), f'No drawing paths: {p}'
        elif name.endswith('.png'):
            assert data[:8]==b'\x89PNG\r\n\x1a\n', f'Invalid PNG signature: {p}'
            width,height=struct.unpack('>II',data[16:24]);assert width>20 and height>20, f'Empty PNG: {p}'
            pos=8;compressed=b'';ended=False
            while pos<len(data):
                size=struct.unpack('>I',data[pos:pos+4])[0];kind=data[pos+4:pos+8];chunk=data[pos+8:pos+8+size]
                crc=struct.unpack('>I',data[pos+8+size:pos+12+size])[0]
                assert zlib.crc32(kind+chunk)&0xffffffff==crc, f'Invalid PNG CRC: {p}'
                if kind==b'IDAT':compressed+=chunk
                if kind==b'IEND':ended=True
                pos+=12+size
            assert ended and len(zlib.decompress(compressed))>100, f'Invalid PNG data: {p}'
            assert_visible_png(data, compressed, width, height)
        else:
            scene=json.loads(data)
            assert scene.get('type')=='excalidraw', f'Invalid scene type: {p}'
            elements=[e for e in scene['elements'] if not e.get('isDeleted')]
            assert len(elements)==1 and elements[0]['type']=='rectangle', f'Wrong exported scene: {p}'
            assert elements[0]['width']>100 and elements[0]['height']>100, f'Wrong geometry: {p}'
        print(f'VALID {p.relative_to(root)} ({len(data)} bytes)')
print('All required export formats are present and structurally valid.')
