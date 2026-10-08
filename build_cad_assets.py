"""Pack triangulated manufacturer CAD into glTF; preserve physical dimensions."""
from pathlib import Path
import array
import json
import struct
ROOT = Path(__file__).resolve().parent


def main():
    raw = json.loads((ROOT / 'models/cat-5cp2120w.mesh.json').read_text())
    assert raw['success']
    doc = {'asset': {'version': '2.0', 'generator': 'steam-zaz968m CAD packer'},
           'scene': 0, 'scenes': [{'nodes': []}], 'nodes': [], 'meshes': [],
           'materials': [], 'bufferViews': [], 'accessors': [], 'buffers': []}
    buffer = bytearray()
    all_min = [float('inf')] * 3; all_max = [-float('inf')] * 3
    # Factory STEP is X-width, Y-height, Z-length. Rotate to project X-length/Y-width/Z-height.
    for m in raw['meshes']:
        a = m['attributes']['position']['array']
        for i in range(0, len(a), 3):
            for j, value in enumerate([a[i + 2], a[i], a[i + 1]]):
                all_min[j] = min(all_min[j], value); all_max[j] = max(all_max[j], value)
    def access(values, code, component, kind, target, bounds=False):
        chunk = array.array(code, values).tobytes()
        while len(buffer) % 4: buffer.append(0)
        view = len(doc['bufferViews']); doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(buffer), 'byteLength': len(chunk), 'target': target})
        buffer.extend(chunk)
        item = {'bufferView': view, 'componentType': component, 'count': len(values) // (3 if kind == 'VEC3' else 1), 'type': kind}
        if bounds:
            item['min'] = [min(values[j::3]) for j in range(3)]; item['max'] = [max(values[j::3]) for j in range(3)]
        doc['accessors'].append(item); return len(doc['accessors']) - 1
    for n, m in enumerate(raw['meshes']):
        a = m['attributes']['position']['array']; positions = []
        for i in range(0, len(a), 3): positions.extend((v - all_min[j]) / 1000 for j, v in enumerate([a[i+2], a[i], a[i+1]]))
        attrs = {'POSITION': access(positions, 'f', 5126, 'VEC3', 34962, True)}
        if 'normal' in m['attributes']:
            a = m['attributes']['normal']['array']; normals = []
            for i in range(0, len(a), 3): normals.extend([a[i+2], a[i], a[i+1]])
            attrs['NORMAL'] = access(normals, 'f', 5126, 'VEC3', 34962)
        indices = access(m['index']['array'], 'I', 5125, 'SCALAR', 34963)
        color = m.get('color', [.58, .65, .7])
        doc['materials'].append({'name': 'OEM color', 'pbrMetallicRoughness': {'baseColorFactor': [*color, 1], 'metallicFactor': .45, 'roughnessFactor': .55}})
        doc['meshes'].append({'name': m['name'], 'primitives': [{'attributes': attrs, 'indices': indices, 'material': n}]})
        doc['nodes'].append({'mesh': n, 'name': m['name']}); doc['scenes'][0]['nodes'].append(n)
    doc['buffers'] = [{'byteLength': len(buffer)}]
    doc['extras'] = {'source': 'Cat Pumps 5CP2120W_0.STEP', 'units': 'metres', 'axes': 'X length; Y width; Z height', 'size_mm': [all_max[j] - all_min[j] for j in range(3)], 'note': 'Geometry only; motor, hoses and service clearances are absent.'}
    header = json.dumps(doc, separators=(',', ':'), ensure_ascii=False).encode()
    header += b' ' * ((-len(header)) % 4); buffer.extend(b'\0' * ((-len(buffer)) % 4))
    out = struct.pack('<III', 0x46546C67, 2, 12+8+len(header)+8+len(buffer)) + struct.pack('<II', len(header), 0x4E4F534A) + header + struct.pack('<II', len(buffer), 0x004E4942) + buffer
    (ROOT / 'models/cat-5cp2120w.glb').write_bytes(out)
    print(json.dumps({'size_mm': doc['extras']['size_mm'], 'meshes': len(raw['meshes']), 'glb_bytes': len(out)}))


if __name__ == '__main__': main()
