"""Independent integrity check for files downloaded by Assay; stdlib only."""
from pathlib import Path
import json, struct, sys, zlib
import xml.etree.ElementTree as ET
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
        else:
            scene=json.loads(data)
            assert scene.get('type')=='excalidraw', f'Invalid scene type: {p}'
            elements=[e for e in scene['elements'] if not e.get('isDeleted')]
            assert len(elements)==1 and elements[0]['type']=='rectangle', f'Wrong exported scene: {p}'
            assert elements[0]['width']>100 and elements[0]['height']>100, f'Wrong geometry: {p}'
        print(f'VALID {p.relative_to(root)} ({len(data)} bytes)')
print('All required export formats are present and structurally valid.')
