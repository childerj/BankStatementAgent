"""
BAI2 Bank Information Integration
Demonstrates how to integrate the bank information loader with BAI2 processing
"""

import os
import sys
import json
import logging
from bank_info_loader import BankMatcher

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BAI2Processor:
    """
    BAI2 processor with integrated bank information lookup
    """
    
    def __init__(self):
        self.bank_matcher = BankMatcher()
        logger.info("🏦 BAI2 Processor initialized with bank matching")
    
    def process_bank_statement(self, bank_name, statement_data=None):
        """
        Process a bank statement with bank information lookup
        
        Args:
            bank_name (str): Name of the bank from the statement
            statement_data (dict, optional): Additional statement data
            
        Returns:
            dict: Processing result with bank info and account details
        """
        logger.info(f"📋 Processing statement for bank: {bank_name}")
        
        # Get bank information using fuzzy matching
        bank_info = self.bank_matcher.get_bank_info(bank_name)
        
        # Prepare result
        result = {
            "bank_name": bank_name,
            "processing_timestamp": self.bank_matcher._get_timestamp(),
            "bank_info_found": False,
            "account_number": None,
            "routing_number": None,
            "processing_method": "fallback"
        }
        
        if bank_info and bank_info.get("account_number") and bank_info.get("routing_number"):
            # Found matching bank information
            result.update({
                "bank_info_found": True,
                "matched_bank_name": bank_info["bank_name"],
                "account_number": bank_info["account_number"],
                "routing_number": bank_info["routing_number"],
                "address": bank_info.get("address", ""),
                "match_confidence": bank_info.get("match_confidence", 0),
                "processing_method": "wac_bank_info"
            })
            
            logger.info(f"✅ Using WAC bank info - Account: {bank_info['account_number']}, Routing: {bank_info['routing_number']}")
            
        else:
            # No match found, use fallback method
            logger.info("⚠️ No bank match found, using fallback processing method")
            result.update({
                "processing_method": "fallback",
                "fallback_reason": "No matching bank found above 80% threshold"
            })
        
        # Add statement data if provided
        if statement_data:
            result["statement_data"] = statement_data
            
        return result
    
    def process_bai2_file(self, file_path, bank_name=None):
        """
        Process a BAI2 file with bank information lookup
        
        Args:
            file_path (str): Path to the BAI2 file
            bank_name (str, optional): Bank name (if not provided, will try to extract from file)
            
        Returns:
            dict: Processing result
        """
        logger.info(f"📄 Processing BAI2 file: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"❌ File not found: {file_path}")
            return {"error": f"File not found: {file_path}"}
        
        # If bank name not provided, try to extract from filename or content
        if not bank_name:
            bank_name = self._extract_bank_name_from_file(file_path)
        
        if not bank_name:
            logger.warning("⚠️ No bank name found, using generic processing")
            bank_name = "Unknown Bank"
        
        # Read file content (simplified for demo)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
                
            statement_data = {
                "file_path": file_path,
                "file_size": len(file_content),
                "content_preview": file_content[:200] + "..." if len(file_content) > 200 else file_content
            }
            
            return self.process_bank_statement(bank_name, statement_data)
            
        except Exception as e:
            logger.error(f"❌ Error reading file: {e}")
            return {"error": f"Error reading file: {e}"}
    
    def _extract_bank_name_from_file(self, file_path):
        """
        Extract bank name from file path or content
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            str: Extracted bank name or None
        """
        # Try to extract from filename
        filename = os.path.basename(file_path).lower()
        
        # Common bank name patterns in filenames
        bank_patterns = {
            "stockyard": "Stock Yards Bank",
            "vera": "VeraBank",
            "community": "Community Bank",
            "citizens": "Citizens Bank of Kentucky",
            "prosperity": "Prosperity Bank"
        }
        
        for pattern, bank_name in bank_patterns.items():
            if pattern in filename:
                logger.info(f"🔍 Extracted bank name from filename: {bank_name}")
                return bank_name
        
        # Could also try to extract from file content here
        # For now, return None
        return None
    
    def get_yaml_bank_info(self):
        """
        Get all bank information in YAML format
        
        Returns:
            str: YAML formatted bank information
        """
        return self.bank_matcher.get_yaml_bank_info()

def demo_integration():
    """
    Demonstrate the BAI2 integration with bank matching
    """
    print("🧪 BAI2 Bank Integration Demo")
    print("=" * 60)
    
    processor = BAI2Processor()
    
    # Test cases
    test_banks = [
        "Stock Yards Bank",
        "VeraBank", 
        "Community Bank",
        "Wells Fargo",  # This should fall back
        "Chase"         # This should fall back
    ]
    
    for bank_name in test_banks:
        print(f"\n📋 Testing: '{bank_name}'")
        print("-" * 40)
        
        result = processor.process_bank_statement(bank_name)
        
        print(f"✅ Bank: {result['bank_name']}")
        print(f"✅ Method: {result['processing_method']}")
        
        if result['bank_info_found']:
            print(f"✅ Account: {result['account_number']}")
            print(f"✅ Routing: {result['routing_number']}")
            print(f"✅ Confidence: {result.get('match_confidence', 0):.1f}%")
        else:
            print(f"⚠️ Reason: {result.get('fallback_reason', 'No match found')}")
    
    # Show YAML output
    print(f"\n📄 Complete Bank Information (YAML):")
    print("=" * 60)
    yaml_info = processor.get_yaml_bank_info()
    print(yaml_info[:500] + "..." if len(yaml_info) > 500 else yaml_info)

if __name__ == "__main__":
    demo_integration()
