import re
import dns.resolver
import os
import time

# Cache to avoid repeated DNS lookups
dns_cache = {}
validation_cache = {}

def validate_email(email):
    """
    Validate an email address by:
    1. Checking syntax
    2. Verifying domain has MX records
    3. (Optional) Additional verification if API key is available
    """
    if email in validation_cache:
        return validation_cache[email]
    
    # 1. Basic syntax check
    if not is_valid_email_syntax(email):
        validation_cache[email] = 'Invalid'
        return 'Invalid'
    
    # Extract domain for further checks
    domain = email.split('@')[-1]
    
    # 2. Check if domain has valid MX records
    has_mx = verify_domain_mx(domain)
    
    if not has_mx:
        validation_cache[email] = 'Uncertain'
        return 'Uncertain'
    
    # 3. Check for disposable email domains
    if is_disposable_domain(domain):
        validation_cache[email] = 'Invalid'
        return 'Invalid'
    
    # 4. If API key is available, use additional verification
    abstract_api_key = os.getenv("ABSTRACT_API_KEY")
    
    if abstract_api_key:
        try:
            import requests
            
            url = f"https://emailvalidation.abstractapi.com/v1/?api_key={abstract_api_key}&email={email}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check deliverability
                if "deliverability" in data:
                    deliverability = data["deliverability"]
                    
                    if deliverability == "DELIVERABLE":
                        validation_cache[email] = 'Valid'
                        return 'Valid'
                    elif deliverability == "UNDELIVERABLE":
                        validation_cache[email] = 'Invalid'
                        return 'Invalid'
            
            # If API call fails or results are unclear, fall back to MX check
            validation_cache[email] = 'Uncertain'
            return 'Uncertain'
            
        except Exception as e:
            print(f"Error using email validation API: {str(e)}")
            # Fallback to basic validation
            validation_cache[email] = 'Uncertain'
            return 'Uncertain'
    
    # If no API available, basic validation is our best guess
    validation_cache[email] = 'Valid'
    return 'Valid'

def is_valid_email_syntax(email):
    """Check if email has valid syntax"""
    if not email or not isinstance(email, str):
        return False
    
    # Basic pattern for email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    return bool(re.match(pattern, email))

def verify_domain_mx(domain):
    """Check if domain has MX records (indicating it can receive email)"""
    # Check cache first
    if domain in dns_cache:
        return dns_cache[domain]
    
    try:
        # Look up MX records for domain
        dns.resolver.resolve(domain, 'MX')
        dns_cache[domain] = True
        return True
    except Exception:
        try:
            # If no MX records, try A records
            dns.resolver.resolve(domain, 'A')
            dns_cache[domain] = True
            return True
        except Exception:
            dns_cache[domain] = False
            return False

def is_disposable_domain(domain):
    """Check if domain is a known disposable email provider"""
    disposable_domains = {
        'temp-mail.org', 'tempmail.com', 'throwawaymail.com', 'mailinator.com',
        'yopmail.com', 'guerrillamail.com', 'sharklasers.com', '10minutemail.com',
        'trashmail.com', 'mailnesia.com', 'maildrop.cc', 'getairmail.com',
        'getnada.com', 'emailondeck.com', 'spamgourmet.com', 'fakeinbox.com',
        'tempinbox.com', 'temp-mail.ru', 'dispostable.com'
    }
    
    return domain.lower() in disposable_domains
