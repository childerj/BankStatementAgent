# -*- coding: utf-8 -*-
"""
Throttling Configuration for Bank Statement Processing

Adjust these settings based on your OpenAI plan and processing requirements:

OpenAI API Rate Limits by Plan:
- Free Tier: 3 RPM (requests per minute)
- Pay-as-you-go: 3,500 RPM
- Tier 1 ($5+ spent): 3,500 RPM  
- Tier 2 ($50+ spent): 5,000 RPM
- Tier 3 ($100+ spent): 5,000 RPM
- Tier 4 ($1,000+ spent): 10,000 RPM
- Tier 5 ($5,000+ spent): 10,000 RPM

Azure OpenAI typically has more generous limits but varies by deployment.
"""

# === THROTTLING CONFIGURATION ===
class ThrottlingConfig:
    """Centralized throttling configuration"""
    
    # OpenAI API rate limiting (adjust based on your plan)
    CALLS_PER_MINUTE = 50          # Conservative default - adjust based on your tier
    MIN_DELAY_BETWEEN_CALLS = 2    # Minimum seconds between OpenAI calls
    
    # Retry configuration for failed calls
    RETRY_DELAYS = [2, 5, 10, 20]  # Exponential backoff delays in seconds
    MAX_RETRIES = len(RETRY_DELAYS)
    
    # Processing queue settings
    INITIAL_PROCESSING_DELAY_MIN = 1   # Minimum random delay before processing (seconds)
    INITIAL_PROCESSING_DELAY_MAX = 5   # Maximum random delay before processing (seconds)
    
    # Timeout settings
    DOCUMENT_INTELLIGENCE_TIMEOUT = 480  # 8 minutes for Document Intelligence operations
    FUNCTION_TIMEOUT_MINUTES = 10        # Total function timeout (set in host.json)
    
    # Error handling
    RETRYABLE_ERROR_KEYWORDS = [
        'rate limit', 'quota', 'too many requests', '429',  # Rate limiting
        'timeout', 'connection', 'network', 'socket'        # Network issues
    ]
    
    @classmethod
    def get_summary(cls):
        """Get a human-readable summary of current throttling settings"""
        return f"""
Throttling Configuration Summary:
- OpenAI Rate Limit: {cls.CALLS_PER_MINUTE} calls/minute
- Min Delay Between Calls: {cls.MIN_DELAY_BETWEEN_CALLS}s
- Max Retries: {cls.MAX_RETRIES} attempts with backoff: {cls.RETRY_DELAYS}
- Processing Delay: {cls.INITIAL_PROCESSING_DELAY_MIN}-{cls.INITIAL_PROCESSING_DELAY_MAX}s random
- Doc Intelligence Timeout: {cls.DOCUMENT_INTELLIGENCE_TIMEOUT}s
- Function Timeout: {cls.FUNCTION_TIMEOUT_MINUTES} minutes
        """.strip()
    
    @classmethod
    def adjust_for_plan(cls, plan_type: str):
        """Adjust settings for specific OpenAI plans"""
        plan_configs = {
            'free': {'calls_per_minute': 3, 'min_delay': 20},
            'tier1': {'calls_per_minute': 30, 'min_delay': 2},
            'tier2': {'calls_per_minute': 50, 'min_delay': 1.5},
            'tier3': {'calls_per_minute': 50, 'min_delay': 1.5},
            'tier4': {'calls_per_minute': 100, 'min_delay': 1},
            'tier5': {'calls_per_minute': 100, 'min_delay': 1},
            'azure': {'calls_per_minute': 60, 'min_delay': 1}  # Azure OpenAI is typically more generous
        }
        
        if plan_type.lower() in plan_configs:
            config = plan_configs[plan_type.lower()]
            cls.CALLS_PER_MINUTE = config['calls_per_minute']
            cls.MIN_DELAY_BETWEEN_CALLS = config['min_delay']
            print(f"✅ Throttling adjusted for {plan_type.upper()} plan")
            print(cls.get_summary())
        else:
            print(f"⚠️ Unknown plan type '{plan_type}', using default settings")

# === USAGE EXAMPLES ===
if __name__ == "__main__":
    # Show current configuration
    print("Current Throttling Configuration:")
    print(ThrottlingConfig.get_summary())
    
    # Example: Adjust for different plans
    print("\n" + "="*50)
    print("Adjusting for Azure OpenAI plan:")
    ThrottlingConfig.adjust_for_plan('azure')
