const fs = require('fs');
const path = require('path');

// Paths
const inputPath = '/Users/yum.ishii/SaraokuDB/static-frontend/public/data/horses.json';
const outputPath = '/Users/yum.ishii/SaraokuDB/static-frontend/public/data/horses_fixed.json';

console.log('Reading file...');
const content = fs.readFileSync(inputPath, 'utf8');

console.log('Fixing JSON...');
// Remove newlines within strings
let fixedContent = '';
let inString = false;
let escapeNext = false;

for (let i = 0; i < content.length; i++) {
  const char = content[i];
  
  if (escapeNext) {
    fixedContent += char;
    escapeNext = false;
    continue;
  }
  
  if (char === '\\') {
    escapeNext = true;
    fixedContent += char;
    continue;
  }
  
  if (char === '"') {
    inString = !inString;
  }
  
  if (char === '\n' && inString) {
    // Skip newlines within strings
    continue;
  }
  
  fixedContent += char;
}

// Parse the fixed JSON to validate it
try {
  const json = JSON.parse(fixedContent);
  console.log('JSON is valid!');
  
  // Save the fixed content
  fs.writeFileSync(outputPath, JSON.stringify(json, null, 2));
  console.log(`Fixed JSON saved to: ${outputPath}`);
  
  // Create a minified version as well
  fs.writeFileSync(inputPath, JSON.stringify(json));
  console.log(`Minified JSON saved to: ${inputPath}`);
  
  console.log('Done!');
} catch (error) {
  console.error('Error parsing fixed JSON:', error);
  // Save the fixed content anyway for debugging
  fs.writeFileSync(outputPath, fixedContent);
  console.log(`Partially fixed content saved to: ${outputPath}`);
}
