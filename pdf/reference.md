_Due to length constraints, this reference file contains a summary. For the complete advanced reference with all examples, see the Anthropic skills repository._

# PDF Processing Advanced Reference

## pypdfium2 Library (Apache/BSD License)

Fast PDF rendering and image generation using Chromium's PDF library.

```python
import pypdfium2 as pdfium
from PIL import Image

# Render PDF to images
pdf = pdfium.PdfDocument("document.pdf")
page = pdf[0]
bitmap = page.render(scale=2.0)
img = bitmap.to_pil()
img.save("page_1.png")
```

## JavaScript Libraries

### pdf-lib (MIT License)

Create and manipulate PDFs in JavaScript/Node.js.

```javascript
import { PDFDocument } from 'pdf-lib';
import fs from 'fs';

// Load and modify PDF
const pdfBytes = fs.readFileSync('input.pdf');
const pdfDoc = await PDFDocument.load(pdfBytes);
const page = pdfDoc.addPage();
page.drawText('Hello World', { x: 100, y: 500 });
fs.writeFileSync('output.pdf', await pdfDoc.save());
```

### pdfjs-dist (Apache License)

Mozilla's PDF renderer for browsers.

```javascript
import * as pdfjsLib from 'pdfjs-dist';

const pdf = await pdfjsLib.getDocument('file.pdf').promise;
const page = await pdf.getPage(1);
const textContent = await page.getTextContent();
```

## Advanced Command-Line Tools

### poppler-utils

```bash
# Extract with coordinates
pdftotext -bbox-layout document.pdf output.xml

# High-res images
pdftoppm -png -r 300 document.pdf output

# Extract embedded images
pdfimages -j document.pdf images/img
```

### qpdf Advanced

```bash
# Split pages
qpdf --split-pages=3 input.pdf group_%02d.pdf

# Optimize
qpdf --linearize input.pdf web-optimized.pdf

# Repair
qpdf --check input.pdf
```

## Advanced Python Techniques

### pdfplumber Advanced

```python
import pdfplumber

with pdfplumber.open("doc.pdf") as pdf:
    page = pdf.pages[0]
    
    # Extract with coordinates
    chars = page.chars
    
    # Custom table settings
    tables = page.extract_tables({
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines"
    })
```

### reportlab Advanced

```python
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

data = [['Product', 'Q1', 'Q2'], ['Widgets', '120', '135']]
table = Table(data)
table.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.grey),
    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
    ('GRID', (0,0), (-1,-1), 1, colors.black)
]))
```

## Performance Tips

- Use `pdftotext` for fast plain text extraction
- Use `pdfimages` instead of rendering for image extraction
- Process large PDFs in chunks to manage memory
- Use qpdf for splitting before processing

## Troubleshooting

### Encrypted PDFs
```python
from pypdf import PdfReader

reader = PdfReader("encrypted.pdf")
if reader.is_encrypted:
    reader.decrypt("password")
```

### Corrupted PDFs
```bash
qpdf --check corrupted.pdf
qpdf --replace-input corrupted.pdf
```

### OCR for Scanned PDFs
```python
import pytesseract
from pdf2image import convert_from_path

images = convert_from_path('scanned.pdf')
text = pytesseract.image_to_string(images[0])
```

## License Information

- pypdf: BSD License
- pdfplumber: MIT License
- pypdfium2: Apache/BSD License
- reportlab: BSD License
- poppler-utils: GPL-2 License
- qpdf: Apache License
- pdf-lib: MIT License
- pdfjs-dist: Apache License
