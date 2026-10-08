import * as T from 'three';

// An explanatory skin laid on the visible tube surface, never physical hardware.
// +s follows the real route from its first connection to its last connection.
const colors = {steam: '#fff8da', exhaust: '#eef0f3', water: '#9ef4e4', fuel: '#ffe184', flue: '#ebc7a2'};
const segments = 18;

export function visiblePipeRadius(route, insulation, jacket) {
  // A jacket stays at its manufactured radius when the insulation is hidden.
  return route.od / 2 + ((insulation || (jacket && route.jacket_mm > 0)) ? route.insulation_mm : 0)
    + (jacket ? route.jacket_mm : 0);
}
function ribbon(color, order) {
  const geometry = new T.BufferGeometry();
  geometry.setAttribute('position', new T.BufferAttribute(new Float32Array((segments + 1) * 2 * 3), 3));
  const indices = [];
  for (let i = 0; i < segments; i++) {
    const a = 2 * i;
    indices.push(a, a + 1, a + 2, a + 1, a + 3, a + 2);
  }
  geometry.setIndex(indices);
  const material = new T.MeshBasicMaterial({color, side: T.DoubleSide,
    transparent: true, opacity: 1, depthTest: false, depthWrite: false});
  const mesh = new T.Mesh(geometry, material);
  mesh.renderOrder = order;
  // Vertices move along bends each frame; stale bounds must not cull markers.
  mesh.frustumCulled = false;
  return mesh;
}

export function pipeArrows(curve, route) {
  const group = new T.Group();
  group.name = 'Surface direction arrows · ' + route.id;
  group.userData.viewOnly = true;
  group.userData.routeId = route.id;
  const length = curve.getLength();
  const count = Math.max(1, Math.ceil(length / 280));
  const markers = Array.from({length: count}, (_, i) => {
    const border = ribbon('#08151f', 904), fill = ribbon(colors[route.fluid] || colors.water, 905);
    const marker = new T.Group();
    marker.name = route.id + ' → ' + (i + 1);
    marker.add(border, fill);group.add(marker);
    return {marker, border, fill};
  });
  const point = new T.Vector3(), tangent = new T.Vector3(), normal = new T.Vector3(), side = new T.Vector3();
  const fallback = new T.Vector3(), skin = new T.Vector3();
  const inverse = new T.Matrix4(), cameraLocal = new T.Vector3();

  function draw(mesh, distance, radius, arrowLength, width, border, radiusAt) {
    const position = mesh.geometry.attributes.position;
    for (let i = 0; i <= segments; i++) {
      const u = i / segments;
      const along=distance + (u - .5) * arrowLength;
      const s = along / length;
      const surfaceRadius = radiusAt ? radiusAt(along)+(border ? .7 : 1.1) : radius;
      point.copy(curve.getPointAt(T.MathUtils.clamp(s, 0, 1)));
      tangent.copy(curve.getTangentAt(T.MathUtils.clamp(s, 0, 1))).normalize();
      normal.subVectors(cameraLocal, point).addScaledVector(tangent, -normal.dot(tangent));
      if (normal.lengthSq() < 1e-8) {
        fallback.set(Math.abs(tangent.z) < .9 ? 0 : 1, 0, Math.abs(tangent.z) < .9 ? 1 : 0);
        normal.copy(fallback).addScaledVector(tangent, -fallback.dot(tangent));
      }
      normal.normalize();side.crossVectors(tangent, normal).normalize();
      // Stem, then a broad arrowhead tapering to the downstream tip.
      let half = u < .61 ? .23 : .5 * (1 - u) / .39;
      if (border) half += .07;
      const angle = Math.min(1.35, half * width / radius);
      for (let j = 0; j < 2; j++) {
        const signed = j ? angle : -angle;
        skin.copy(point).addScaledVector(normal, Math.cos(signed) * surfaceRadius)
          .addScaledVector(side, Math.sin(signed) * surfaceRadius);
        position.setXYZ(2 * i + j, skin.x, skin.y, skin.z);
      }
    }
    position.needsUpdate = true;
  }

  return {group, markers, update({camera, radius, phase = 0, visible, clippingPlanes, radiusAt}) {
    group.visible = visible;
    if (!visible) return;
    group.updateWorldMatrix(true, false);
    inverse.copy(group.matrixWorld).invert();
    cameraLocal.copy(camera.getWorldPosition(new T.Vector3())).applyMatrix4(inverse);
    const arrowLength = Math.min(length * .65, Math.max(50, Math.min(95, radius * 1.5)));
    const width = Math.min(75, radius * 1.15);
    // Keep each whole glyph inside the route, including the end connections.
    const margin = arrowLength * .55;
    const span = Math.max(0, length - 2 * margin);
    markers.forEach(({marker, border, fill}, i) => {
      const t = ((i + .5) / count + phase) % 1;
      const distance = margin + t * span;
      marker.userData.routeFraction = distance / length;
      marker.userData.surfaceRadius_mm = radiusAt ? radiusAt(distance) : radius;
      marker.userData.direction = 'source-to-destination';
      for (const mesh of [border, fill]) mesh.material.clippingPlanes = clippingPlanes;
      draw(border, distance, radius + .7, arrowLength * 1.07, width, true, radiusAt);
      draw(fill, distance, radius + 1.1, arrowLength, width, false, radiusAt);
    });
  }};
}
