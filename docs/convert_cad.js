// Triangulate the original manufacturer STEP with the pinned OpenCascade importer.
// Run: node convert_cad.js; python3 build_cad_assets.py
const fs = require('fs');
require('./vendor/occt-import-js/dist/occt-import-js.js')().then(occt => {
  const result = occt.ReadStepFile(fs.readFileSync('models/cat-5cp2120w.step'), {
    linearUnit: 'millimeter', linearDeflectionType: 'absolute_value',
    linearDeflection: 0.3, angularDeflection: 0.3
  });
  if (!result.success) throw Error('STEP import failed');
  fs.writeFileSync('models/cat-5cp2120w.mesh.json', JSON.stringify(result));
  console.log('Imported manufacturer STEP: ' + result.meshes.length + ' bodies.');
}).catch(error => { console.error(error.message); process.exitCode = 1; });
