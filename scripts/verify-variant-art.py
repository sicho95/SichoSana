#!/usr/bin/env python3
"""Verify exact generated variant images; extract only known files from the optional upload."""
import hashlib,json,zipfile,struct,zlib,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'static/data/variant-art.json').read_text())
guidance=json.loads((root/'static/data/pose-guidance.json').read_text())
assert set(manifest['easy'])==set(guidance['poses'])
files=manifest['files']; assert len(files)==14
assert set(manifest['easy'].values())|{v['image'] for items in manifest['alternatives'].values() for v in items}==set(files)
folder=root/'static/media/variants'
archive=root/'SichoSana_variantes_v1.zip'
if '--extract' in sys.argv and archive.is_file():
    with zipfile.ZipFile(archive) as z:
        expected={'static/media/variants/'+k+'.png' for k in files}
        assert len(z.namelist())==14 and set(z.namelist())==expected
        folder.mkdir(parents=True,exist_ok=True)
        for k,sha in files.items():
            name='static/media/variants/'+k+'.png'
            assert z.getinfo(name).file_size<4_000_000
            data=z.read(name)
            assert hashlib.sha256(data).hexdigest()==sha,k
            (folder/(k+'.png')).write_bytes(data)
for k,sha in files.items():
    data=(folder/(k+'.png')).read_bytes()
    assert hashlib.sha256(data).hexdigest()==sha,k
    assert data[:8]==b'\x89PNG\r\n\x1a\n'
    assert struct.unpack('>II',data[16:24])==(1200,900),k
    pos=8
    while pos<len(data):
        n=struct.unpack('>I',data[pos:pos+4])[0]
        part=data[pos+4:pos+8+n]
        assert len(part)==n+4 and zlib.crc32(part)==struct.unpack('>I',data[pos+8+n:pos+12+n])[0],k
        pos+=12+n
        if part[:4]==b'IEND':break
    assert pos==len(data) and part[:4]==b'IEND',k
print('VARIANT_ART_OK 14 PNG, 13 variantes guidées et 1 alternative')
