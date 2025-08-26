"""
Fix the AccountHolderAddress issue by creating a corrected version of the problematic function
"""

def create_fixed_account_extraction():
    # Read the current file
    with open('function_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the problematic section and replace it
    old_section = '''                if "account" in field_name.lower():
                    if content and len(content) > 4:
                        # Clean but preserve asterisks for validation
                        clean_content = content.replace("-", "").replace(" ", "")
                        print_and_log(f"� Account field '{field_name}': '{clean_content}'")
                        
                        # Prioritize TRUE masked accounts (with * or X)
                        if any(char in clean_content for char in ['*', 'X']) and len(clean_content) >= 4:
                            print_and_log(f"✅ Found TRUE MASKED account in field '{field_name}': {clean_content}")
                            return clean_content
                        elif is_valid_account_number(clean_content) and clean_content.isdigit() and len(clean_content) >= 6:
                            print_and_log(f"✅ Found numeric account in field '{field_name}': {clean_content}")
                            return clean_content'''
    
    new_section = '''                # Only check fields that are specifically account number fields, not address/name fields
                if field_name.lower() in ['accounts', 'account', 'accountnumber', 'account_number']:
                    if content and len(content) > 4:
                        # Clean but preserve asterisks for validation
                        clean_content = content.replace("-", "").replace(" ", "")
                        print_and_log(f"🔍 Account field '{field_name}': '{clean_content}'")
                        
                        # Prioritize TRUE masked accounts (with * or X)
                        if any(char in clean_content for char in ['*', 'X']) and len(clean_content) >= 4:
                            print_and_log(f"✅ Found TRUE MASKED account in field '{field_name}': {clean_content}")
                            return clean_content
                        elif is_valid_account_number(clean_content) and clean_content.isdigit() and len(clean_content) >= 4:
                            print_and_log(f"✅ Found numeric account in field '{field_name}': {clean_content}")
                            return clean_content
                else:
                    # For non-account fields, log them but don't treat as accounts
                    if "account" in field_name.lower():
                        print_and_log(f"📋 Skipping non-account field '{field_name}': '{content[:50] if len(content) > 50 else content}' (not an account number field)")'''
    
    if old_section.replace('�', '').replace('\r', '') in content.replace('�', '').replace('\r', ''):
        print("Found the problematic section - creating fixed version")
        
        # Replace the section, handling the special character
        import re
        # Use a more flexible pattern to match the section
        pattern = r'if "account" in field_name\.lower\(\):\s+if content and len\(content\) > 4:.*?return clean_content'
        
        fixed_content = re.sub(pattern, new_section, content, flags=re.DOTALL)
        
        # Write the fixed content
        with open('function_app_fixed.py', 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print("Created function_app_fixed.py with the corrected logic")
        return True
    else:
        print("Could not find the exact section to replace")
        print("Looking for sections containing 'Account field'...")
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'Account field' in line:
                print(f"Line {i+1}: {line}")
        return False

if __name__ == "__main__":
    create_fixed_account_extraction()
