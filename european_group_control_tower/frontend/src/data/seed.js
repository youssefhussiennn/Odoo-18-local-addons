import seed from './seed.json';
import { autoMap, acidMap, buildDataset } from '../lib/importer.js';

// Builds the initial dataset from the two Excel files that were converted to seed.json.
export function seedData() {
  const headers = Object.keys(seed.shipments[0] || {});
  const mapping = autoMap(headers);
  const acidMapping = autoMap(Object.keys(seed.acid[0] || {}));
  return buildDataset(seed.shipments, mapping, acidMap(seed.acid, acidMapping), 'Initial load from european-group-shipments.xlsx + acid.xlsx');
}
