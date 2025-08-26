import io, json, requests, pandas as pd

DOWNLOAD_URL = "https://worldacceptance-my.sharepoint.com/:x:/p/jeff_childers/EU4h9XwapzZJi-e4dyYJb0YBws-K7GlI7mq2gpGnGvRk2Q?download=1"

print("🚀 Direct SharePoint Download")
print("="*50)
print(f"🔗 URL: {DOWNLOAD_URL}")
print()

try:
    print("🔄 Downloading file...")
    r = requests.get(DOWNLOAD_URL, timeout=60)
    r.raise_for_status()  # will error if the link isn't public/accessible
    
    print(f"✅ Download successful!")
    print(f"   Status: {r.status_code}")
    print(f"   Content-Type: {r.headers.get('content-type', 'unknown')}")
    print(f"   Size: {len(r.content):,} bytes")
    print()
    
    print("📊 Reading Excel file...")
    # Read first sheet (or pass sheet_name="YourSheet")
    df = pd.read_excel(io.BytesIO(r.content))
    
    print(f"✅ Excel file processed!")
    print(f"   Rows: {df.shape[0]:,}")
    print(f"   Columns: {df.shape[1]:,}")
    print(f"   Column names: {list(df.columns)}")
    print()
    
    # Convert to JSON
    print("🔄 Converting to JSON...")
    records_json = df.to_json(orient="records")
    data = json.loads(records_json)  # list of dicts
    
    print(f"✅ JSON conversion complete!")
    print(len(data), "rows")
    print()
    
    # Save the data
    print("💾 Saving files...")
    
    # Save Excel file
    with open("US_Bank_List_Real.xlsx", "wb") as f:
        f.write(r.content)
    
    # Save JSON file
    with open("US_Bank_List_Real.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    # Save CSV file
    df.to_csv("US_Bank_List_Real.csv", index=False)
    
    print("   📄 US_Bank_List_Real.xlsx")
    print("   📄 US_Bank_List_Real.json")
    print("   📄 US_Bank_List_Real.csv")
    print()
    
    print("📋 DATA PREVIEW:")
    print("-" * 80)
    print(df.head(10).to_string())
    print("-" * 80)
    
    if len(data) > 10:
        print(f"... and {len(data) - 10} more rows")
    
    print()
    print("🎯 SUCCESS! All files saved and data converted to JSON")
    
except requests.exceptions.RequestException as e:
    print(f"❌ Download error: {e}")
    print("💡 The URL might require authentication or the file might not be publicly accessible")
    
except Exception as e:
    print(f"❌ Processing error: {e}")
    print("💡 The downloaded content might not be a valid Excel file")

print("\n✅ Process completed!")
