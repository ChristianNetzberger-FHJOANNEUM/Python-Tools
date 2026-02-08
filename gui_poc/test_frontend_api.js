// Test in Browser Console:
fetch('/api/projects/pasang-wedding-slideshow/media?limit=3&type=all')
  .then(r => r.json())
  .then(data => {
    console.log('API Response Structure:');
    console.log('Keys:', Object.keys(data));
    if (data.media && data.media.length > 0) {
      console.log('\nFirst item keys:', Object.keys(data.media[0]));
      console.log('\nFirst item:', data.media[0]);
      
      // Check colored item
      const colored = data.media.find(m => m.color);
      if (colored) {
        console.log('\nColored item:', colored.name, colored);
      }
    }
  });
