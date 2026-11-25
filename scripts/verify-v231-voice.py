#!/usr/bin/env python3
"""Porte de livraison v2.3.1 : aucun ancien MP3 accepté comme nouveau pack."""
import hashlib, importlib.util, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(b):return hashlib.sha256(b).hexdigest()
def verify():
    spec=importlib.util.spec_from_file_location('voice_generator',ROOT/'scripts/generate-voice-pack.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    data=ROOT/'static/data'
    expected={k:(t,kind) for k,t,kind in mod.clips(*(load(data/f) for f in ('meditations.json','yoga.json','pose-guidance.json','salutations.json')))}
    folder=ROOT/'static/voice/vivienne-fr-v3'
    m=load(folder/'manifest.json')
    assert m['packId']=='vivienne-fr-v3' and m['voiceId']==mod.VOICE and m['locale']=='fr-FR'
    assert m['rateYoga']==mod.RATE_YOGA and m['rateMeditation']==mod.RATE_MEDITATION
    assert len(expected)==183 and set(expected)==set(m['files'])
    for key,(text,kind) in expected.items():
        item=m['files'][key]
        assert item['src']==key+'.mp3' and item['kind']==kind and item['textSha256']==sha(text.encode()),key
        b=(folder/item['src']).read_bytes()
        assert len(b)>=2000 and sha(b)==item['sha256'] and item['bytes']==len(b),key
        assert b.startswith((b'ID3',b'\xff')),key
    print('VOICE_V3_OK 183 clips, identité, textes et empreintes')
if __name__=='__main__':verify()
