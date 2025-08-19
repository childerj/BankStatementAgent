#!/usr/bin/env python3
"""
Simple lookup for known routing numbers to verify Prosperity Bank
"""

def check_prosperity_routing():
    """Check known routing numbers for Prosperity Bank"""
    print("🏦 Checking known routing numbers for Prosperity Bank...")
    
    # Known routing numbers for major banks (for reference)
    known_routing_numbers = {
        "PROSPERITY BANK": [
            "113122655",  # Prosperity Bank - Texas
            "113024915",  # Prosperity Bank - Alternative
            "113024465"   # Prosperity Bank - Another location
        ],
        "WELLS FARGO": ["121000248", "111900659"],
        "CHASE": ["021000021", "322271627"],
        "BANK OF AMERICA": ["026009593", "111000025"]
    }
    
    bank_name = "PROSPERITY BANK"
    if bank_name in known_routing_numbers:
        routing_numbers = known_routing_numbers[bank_name]
        print(f"✅ Found {len(routing_numbers)} routing number(s) for {bank_name}:")
        for i, routing in enumerate(routing_numbers, 1):
            print(f"   {i}. {routing}")
        
        primary_routing = routing_numbers[0]
        print(f"\n🎯 Primary routing number: {primary_routing}")
        return primary_routing
    else:
        print(f"❌ No known routing numbers for {bank_name}")
        return None

def compare_with_bai2_result():
    """Compare with what we got in the BAI2 file"""
    print("\n" + "="*60)
    print("📊 Comparing with BAI2 file result...")
    
    correct_routing = check_prosperity_routing()
    bai2_routing = "1515"
    
    print(f"\n🔍 Analysis:")
    print(f"   Expected (Prosperity Bank): {correct_routing}")
    print(f"   Found in BAI2:             {bai2_routing}")
    print(f"   Match:                     {'✅ Yes' if correct_routing == bai2_routing else '❌ No'}")
    
    if correct_routing and bai2_routing != correct_routing:
        print(f"\n💡 Issue identified:")
        print(f"   - The routing number {bai2_routing} is incorrect")
        print(f"   - Should be {correct_routing}")
        print(f"   - This suggests OpenAI lookup failed or returned wrong value")
        
        # Check if 1515 is a substring or related
        if bai2_routing in correct_routing:
            print(f"   - {bai2_routing} appears to be a substring of {correct_routing}")
        else:
            print(f"   - {bai2_routing} is completely unrelated to correct routing number")

if __name__ == "__main__":
    compare_with_bai2_result()
