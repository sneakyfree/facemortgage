#!/usr/bin/env node
/**
 * PWA Icon Generator
 *
 * Generates PWA icons from the improved favicon.svg.
 * Uses sharp for SVG-to-PNG conversion at all required sizes.
 *
 * Usage: node scripts/generate-icons.js
 *
 * Dependencies: sharp (npm install sharp --save-dev)
 */

const fs = require('fs');
const path = require('path');

// Check if sharp is available
let sharp;
try {
  sharp = require('sharp');
} catch (e) {
  console.log('Sharp not installed. Install with: npm install sharp --save-dev');
  process.exit(1);
}

const iconsDir = path.join(__dirname, '../public/icons');
const publicDir = path.join(__dirname, '../public');
const sizes = [72, 96, 128, 144, 152, 192, 384, 512];

// Read the main favicon SVG
const svgPath = path.join(iconsDir, 'favicon.svg');

async function main() {
  // Ensure icons directory exists
  if (!fs.existsSync(iconsDir)) {
    fs.mkdirSync(iconsDir, { recursive: true });
  }

  // Check if SVG exists
  if (!fs.existsSync(svgPath)) {
    console.error('Error: favicon.svg not found in public/icons/');
    process.exit(1);
  }

  console.log('🎨 Generating PWA icons from favicon.svg...\n');

  const svgBuffer = fs.readFileSync(svgPath);

  // Generate PWA icons at all sizes
  for (const size of sizes) {
    const filename = `icon-${size}x${size}.png`;
    const outputPath = path.join(iconsDir, filename);

    try {
      await sharp(svgBuffer)
        .resize(size, size)
        .png()
        .toFile(outputPath);
      console.log(`  ✅ Generated ${filename}`);
    } catch (err) {
      console.error(`  ❌ Error creating ${filename}:`, err.message);
    }
  }

  // Create apple-touch-icon (180x180)
  try {
    const appleIconPath = path.join(iconsDir, 'apple-touch-icon.png');
    await sharp(svgBuffer)
      .resize(180, 180)
      .png()
      .toFile(appleIconPath);
    console.log('  ✅ Generated apple-touch-icon.png (180x180)');

    // Copy to public root for iOS compatibility
    fs.copyFileSync(appleIconPath, path.join(publicDir, 'apple-touch-icon.png'));
    console.log('  ✅ Copied apple-touch-icon.png to public/');
  } catch (err) {
    console.error('  ❌ Error creating apple-touch-icon:', err.message);
  }

  // Generate favicon PNGs
  try {
    await sharp(svgBuffer)
      .resize(32, 32)
      .png()
      .toFile(path.join(publicDir, 'favicon-32x32.png'));
    console.log('  ✅ Generated favicon-32x32.png');

    await sharp(svgBuffer)
      .resize(16, 16)
      .png()
      .toFile(path.join(publicDir, 'favicon-16x16.png'));
    console.log('  ✅ Generated favicon-16x16.png');
  } catch (err) {
    console.error('  ❌ Error creating favicon PNGs:', err.message);
  }

  console.log('\n🎉 Done! Icons generated successfully.');
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
