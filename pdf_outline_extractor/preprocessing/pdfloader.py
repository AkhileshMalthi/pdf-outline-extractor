"""
Preprocessing (PDF Loader)
Load pages with PyMuPDF.

For each page:
Extract text blocks, font size, font name, position (x, y).
"""

import pymupdf

class PDFLoader:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = pymupdf.open(pdf_path)

    def load_pages(self):
        pages = []
        for page_num, page in enumerate(self.doc, start=1):
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if block["type"] == 0:  # type 0 = text
                    for line in block["lines"]:
                        line_text = ""
                        font_sizes = []
                        fonts = []
                        for span in line["spans"]:
                            line_text += span["text"].strip() + " "
                            font_sizes.append(span["size"])
                            fonts.append(span["font"])
                        line_text = line_text.strip()
                        if line_text:
                            pages.append({
                                "text": line_text,
                                "page": page_num,
                                "font_size": max(font_sizes),
                                "font_name": fonts[0],  # take first font in line
                                "bbox": block["bbox"]
                            })
        return pages

if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) != 2:
        print("Usage: python pdfloader.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    loader = PDFLoader(pdf_path)
    blocks = loader.load_pages()
    print(json.dumps(blocks, indent=2))