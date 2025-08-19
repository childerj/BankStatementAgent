#!/usr/bin/env python3
"""
Quick test to determine if PDFs are digital (text-based) or scanned (image-based)
"""

import pdfplumber
import os

def test_pdf_type(pdf_path):
    """Test if a PDF is digital or scanned by checking extractable text"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_text = ""
            total_chars = 0
            
            print(f"\n📄 Testing: {os.path.basename(pdf_path)}")
            print(f"   Pages: {len(pdf.pages)}")
            
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text() or ""
                page_chars = len(page_text.strip())
                total_chars += page_chars
                
                print(f"   Page {page_num}: {page_chars:,} characters")
                
                if page_text.strip():
                    total_text += page_text + "\n"
            
            print(f"   📊 Total extractable text: {total_chars:,} characters")
            
            # Determine if PDF is digital or scanned
            if total_chars > 100:  # Reasonable threshold
                print("   ✅ DIGITAL PDF - PDFPlumber will work well!")
                print("   🚀 Expected: Fast, accurate extraction")
            elif total_chars > 20:
                print("   ⚠️  LIMITED TEXT - Might be partially scanned")  
                print("   🤖 Expected: Will likely fallback to Document Intelligence")
            else:
                print("   🚫 SCANNED PDF - Little to no extractable text")
                print("   🤖 Expected: Will use Document Intelligence (OCR)")
            
            # Show a sample of extracted text if available
            if total_text.strip():
                sample = total_text.strip()[:200].replace('\n', ' ')
                print(f"   📝 Text sample: \"{sample}...\"")
            
            return total_chars > 100
            
    except Exception as e:
        print(f"   ❌ Error testing {pdf_path}: {str(e)}")
        return False

def main():
    """Test all PDFs in the Test Docs folder"""
    test_folder = "Test Docs"
    
    print("🔍 PDF TYPE ANALYSIS")
    print("=" * 50)
    print("Testing PDFs to determine if they're digital or scanned...")
    
    if not os.path.exists(test_folder):
        print(f"❌ Test folder '{test_folder}' not found")
        return
    
    pdf_files = [f for f in os.listdir(test_folder) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"❌ No PDF files found in '{test_folder}'")
        return
    
    print(f"📁 Found {len(pdf_files)} PDF file(s)")
    
    digital_pdfs = []
    scanned_pdfs = []
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(test_folder, pdf_file)
        is_digital = test_pdf_type(pdf_path)
        
        if is_digital:
            digital_pdfs.append(pdf_file)
        else:
            scanned_pdfs.append(pdf_file)
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    print(f"✅ Digital PDFs (PDFPlumber optimal): {len(digital_pdfs)}")
    for pdf in digital_pdfs:
        print(f"   • {pdf}")
    
    print(f"🤖 Scanned PDFs (Document Intelligence needed): {len(scanned_pdfs)}")
    for pdf in scanned_pdfs:
        print(f"   • {pdf}")
    
    print("\n💡 RECOMMENDATION:")
    if digital_pdfs:
        print("   • Digital PDFs will be processed quickly with PDFPlumber")
    if scanned_pdfs:
        print("   • Scanned PDFs will use AI Document Intelligence (slower but more capable)")
    
    print("\n🎯 Your Azure Function handles both types automatically!")

if __name__ == "__main__":
    main()
