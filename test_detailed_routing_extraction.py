#!/usr/bin/env python3

import os
import sys
from pathlib import Path
from io import BytesIO
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
import json

def test_detailed_routing_extraction():
    """Test detailed routing number extraction from Prosperity PDF"""
    
    # Load environment from local settings
    def load_local_settings():
        try:
            with open('local.settings.json', 'r') as f:
                settings = json.load(f)
                for key, value in settings.get('Values', {}).items():
                    os.environ[key] = value
                print(f"[INFO] Loaded {len(settings.get('Values', {}))} environment variables from local.settings.json")
        except Exception as e:
            print(f"[WARNING] Could not load local.settings.json: {e}")
    
    load_local_settings()
    
    # Test Prosperity PDF
    pdf_path = "Test Docs/8-1-25_Prosperity.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found at {pdf_path}")
        return
    
    print(f"Testing routing number extraction from: {pdf_path}")
    
    # Initialize Document Intelligence
    try:
        di_client = DocumentIntelligenceClient(
            endpoint=os.environ["DOCINTELLIGENCE_ENDPOINT"],
            credential=AzureKeyCredential(os.environ["DOCINTELLIGENCE_KEY"])
        )
        print("[INFO] Document Intelligence client initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Document Intelligence: {e}")
        return
    
    # Initialize OpenAI
    try:
        openai_client = AzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_KEY"],
            api_version="2024-02-01"
        )
        print("[INFO] OpenAI client initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize OpenAI: {e}")
        return
    
    # Analyze document with Document Intelligence
    try:
        with open(pdf_path, "rb") as f:
            file_bytes = f.read()
        
        poller = di_client.begin_analyze_document(
            "prebuilt-bankStatement.us",
            BytesIO(file_bytes),
            content_type="application/pdf"
        )
        result = poller.result()
        print("[INFO] Document Intelligence analysis completed")
    except Exception as e:
        print(f"[ERROR] Document Intelligence analysis failed: {e}")
        return
    
    # Extract bank name from Document Intelligence
    bank_name = None
    if result.documents:
        for doc in result.documents:
            if hasattr(doc, 'fields') and doc.fields:
                if 'BankName' in doc.fields:
                    field = doc.fields['BankName']
                    if hasattr(field, 'content'):
                        bank_name = field.content
                    elif hasattr(field, 'value_string'):
                        bank_name = field.value_string
                    elif hasattr(field, 'value'):
                        bank_name = str(field.value)
                    break
    
    if not bank_name and result.tables:
        for table in result.tables:
            for cell in table.cells:
                content = cell.content.strip().lower()
                if any(bank in content for bank in ['prosperity', 'bank']):
                    potential_bank = cell.content.strip()
                    if 'prosperity' in potential_bank.lower():
                        bank_name = potential_bank
                        break
            if bank_name:
                break
    
    print(f"[EXTRACTED] Bank Name from Document Intelligence: '{bank_name}'")
    
    # Look for routing numbers in OCR text with detailed logging
    ocr_routing = None
    all_text = ""
    potential_routing_numbers = []
    
    if result.pages:
        for page_idx, page in enumerate(result.pages):
            print(f"\n[DEBUG] Processing page {page_idx + 1}")
            if hasattr(page, 'lines'):
                for line_idx, line in enumerate(page.lines):
                    all_text += line.content + " "
                    print(f"[DEBUG] Line {line_idx}: {line.content}")
                    
                    # Look for 9-digit numbers
                    words = line.content.split()
                    for word_idx, word in enumerate(words):
                        # Find all digit sequences
                        clean_word = ''.join(c for c in word if c.isdigit())
                        if len(clean_word) >= 9:
                            if len(clean_word) == 9:
                                potential_routing_numbers.append(clean_word)
                                print(f"[FOUND] Potential routing number: {clean_word} from word: {word}")
                                if not ocr_routing:  # Take the first one
                                    ocr_routing = clean_word
                            elif len(clean_word) > 9:
                                print(f"[DEBUG] Long number found: {clean_word} from word: {word}")
    
    print(f"\n[EXTRACTED] All potential routing numbers: {potential_routing_numbers}")
    print(f"[EXTRACTED] Selected OCR Routing Number: {ocr_routing}")
    
    # Test OpenAI lookup if we have a bank name
    openai_routing = None
    if bank_name:
        try:
            prompt = f"""You are a banking expert. Given the bank name "{bank_name}", return the primary routing number for this bank.
            
Return ONLY the 9-digit routing number with no other text. If you cannot determine the routing number, return "UNKNOWN"."""
            
            print(f"[DEBUG] Sending OpenAI prompt for bank: {bank_name}")
            
            response = openai_client.chat.completions.create(
                model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
                messages=[
                    {"role": "system", "content": "You are a helpful banking assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0
            )
            
            openai_routing = response.choices[0].message.content.strip()
            print(f"[EXTRACTED] OpenAI Routing Number: {openai_routing}")
            
        except Exception as e:
            print(f"[ERROR] OpenAI lookup failed: {e}")
    else:
        print("[WARNING] No bank name found - skipping OpenAI lookup")
    
    # Summary
    print("\n" + "="*60)
    print("ROUTING NUMBER EXTRACTION SUMMARY")
    print("="*60)
    print(f"Bank Name (DI):     {bank_name}")
    print(f"OCR Routing:        {ocr_routing}")
    print(f"OpenAI Routing:     {openai_routing}")
    print(f"All OCR candidates: {potential_routing_numbers}")
    
    # Final determination (mimic function logic)
    final_routing = None
    if ocr_routing and len(ocr_routing) == 9:
        final_routing = ocr_routing
        print(f"FINAL CHOICE:       {final_routing} (from OCR)")
    elif openai_routing and openai_routing != "UNKNOWN" and len(openai_routing) == 9:
        final_routing = openai_routing
        print(f"FINAL CHOICE:       {final_routing} (from OpenAI)")
    else:
        print("FINAL CHOICE:       NONE - Would create ERROR BAI2")
    
    print("="*60)

if __name__ == "__main__":
    test_detailed_routing_extraction()
