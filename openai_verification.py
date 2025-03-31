import os
import json
import time
from openai import OpenAI

# Cache for OpenAI responses to avoid repeated calls
ai_cache = {}

# Flag to track if OpenAI quota is exceeded
ai_quota_exceeded = False

# Error message to display in the UI
ai_error_message = ""

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
openai = OpenAI(api_key=OPENAI_API_KEY)

def check_api_status():
    """
    Check the OpenAI API status
    
    Returns:
    - True if API is working, False otherwise
    """
    global ai_quota_exceeded, ai_error_message
    
    # If no API key, set error and return False
    if not OPENAI_API_KEY:
        ai_error_message = "No OpenAI API key found. Advanced verification is disabled."
        return False
    
    # If quota already exceeded, return False
    if ai_quota_exceeded:
        return False
    
    # Try a simple API call to check if the API is working
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Return the word 'working' if you can read this."}
            ],
            max_tokens=5
        )
        return True
    except Exception as e:
        error_msg = str(e)
        print(f"API check failed: {error_msg}")
        
        if "quota" in error_msg.lower() or "insufficient" in error_msg.lower():
            ai_quota_exceeded = True
            ai_error_message = "OpenAI API quota exceeded. Advanced verification has been disabled."
        elif "api key" in error_msg.lower() or "apikey" in error_msg.lower():
            ai_quota_exceeded = True
            ai_error_message = "Invalid OpenAI API key. Advanced verification has been disabled."
        else:
            ai_error_message = f"OpenAI API error: {error_msg}. Some verification features may be limited."
        
        return False

def verify_contact_with_ai(field_name, field_value, row_data, use_deep_search=False):
    """
    Use OpenAI to verify a specific field in the contact data
    
    Parameters:
    - field_name: The name of the field being verified
    - field_value: The value of the field
    - row_data: Dictionary containing all data for this row
    - use_deep_search: Whether to use the more powerful model with more context for thorough verification
    
    Returns:
    - Status string: 'Valid', 'Uncertain', or 'Invalid'
    """
    global ai_quota_exceeded
    
    # If no API key or quota exceeded, return uncertain
    if not OPENAI_API_KEY or ai_quota_exceeded:
        if ai_quota_exceeded:
            print(f"OpenAI quota exceeded. Skipping AI verification for {field_name}.")
        return 'Uncertain'
    
    # Create a cache key that includes the deep_search flag
    cache_key = f"{field_name}:{field_value}:{hash(json.dumps(row_data, default=str))}:{use_deep_search}"
    
    # Check cache
    if cache_key in ai_cache:
        return ai_cache[cache_key]
    
    try:
        # Select model and settings based on deep search flag
        if use_deep_search:
            model = "gpt-4"  # More powerful model for deep search
            max_tokens = 400
            print(f"Using DeepSearch mode for {field_name}: {field_value}")
        else:
            model = "gpt-3.5-turbo"  # Standard model for regular verification
            max_tokens = 150
        
        # Prepare prompt for OpenAI - enhanced for deep search if needed
        prompt = create_verification_prompt(field_name, field_value, row_data, use_deep_search)
        
        # Set up system message based on verification needs
        system_message = "You are a data verification expert specializing in contact and company information."
        
        if use_deep_search and field_name == "Contact Job Title":
            system_message += " You must verify job titles by considering company size, industry trends, and typical organizational structures."
        elif use_deep_search and "LinkedIn" in field_name:
            system_message += " You must verify LinkedIn profiles by examining URL patterns and consistency with other contact information."
        
        system_message += " Your task is to verify if the given information appears to be accurate based on your knowledge and the context provided. Respond with a JSON object containing a 'status' field with one of these values: 'Valid', 'Uncertain', or 'Invalid', and a 'reason' field explaining your decision."
        
        # Call OpenAI with selected model
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=max_tokens
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        status = result.get('status', 'Uncertain')
        reason = result.get('reason', 'No reason provided')
        
        print(f"AI verification for {field_name}: {status} - {reason}")
        
        # Cache the result
        ai_cache[cache_key] = status
        
        return status
    
    except Exception as e:
        global ai_error_message
        error_msg = str(e)
        print(f"Error using OpenAI for verification: {error_msg}")
        
        # Check if this is a quota-related error
        if "quota" in error_msg.lower() or "insufficient" in error_msg.lower():
            print("API quota exceeded. Disabling AI verification for future requests.")
            ai_quota_exceeded = True
            ai_error_message = "OpenAI API quota exceeded. Advanced verification has been disabled."
        elif "api key" in error_msg.lower() or "apikey" in error_msg.lower():
            print("Invalid API key. Disabling AI verification for future requests.")
            ai_quota_exceeded = True
            ai_error_message = "Invalid OpenAI API key. Advanced verification has been disabled."
        else:
            ai_error_message = f"OpenAI API error: {error_msg}. Some verification features may be limited."
            
        return 'Uncertain'

def create_verification_prompt(field_name, field_value, row_data, use_deep_search=False):
    """
    Create an appropriate prompt for the verification task
    
    Parameters:
    - field_name: The name of the field being verified
    - field_value: The value of the field
    - row_data: Dictionary containing all data for this row
    - use_deep_search: Whether to use enhanced prompts for deeper verification
    
    Returns:
    - A prompt string for the verification task
    """
    prompt = f"""I need to verify if this information is correct:
Field: {field_name}
Value: {field_value}

Here's the context (other information about this contact):
"""
    
    # Add context from other fields
    for k, v in row_data.items():
        if k != field_name and not k.endswith('_status'):
            prompt += f"{k}: {v}\n"
    
    # Standard verification instructions
    prompt += "\nBased on this information and your knowledge, analyze if the value for the field appears to be valid, uncertain, or invalid."
    
    # Enhanced verification instructions for deep search
    if use_deep_search:
        if field_name == "Contact Job Title":
            prompt += """
            
For this job title verification:
1. Check if the job title is typical for the company's industry
2. Consider the company size and whether such a position would exist there
3. Verify if the job title aligns with the person's LinkedIn profile
4. Look for any inconsistencies between the job title and other contact information
5. Consider if the job title has appropriate seniority for the contact's other attributes
"""
        elif "LinkedIn" in field_name:
            prompt += """
            
For this LinkedIn profile verification:
1. Check if the URL format matches LinkedIn's standard format
2. Verify if the profile name matches the contact's name
3. Consider if the profile seems to belong to someone at the specified company
4. Look for any inconsistencies with other contact information
"""
        elif field_name in ["Company Name", "Company Domain"]:
            prompt += """
            
For this company verification:
1. Check if the company name and domain align with each other
2. Verify if the company appears to be legitimate based on industry and other details
3. Consider if the company location matches the provided address information
4. Look for any inconsistencies that might suggest the company is not valid
"""
        else:
            prompt += """
            
For this detailed verification:
1. Check if the information is internally consistent with other contact details
2. Verify if the information follows expected patterns and formats
3. Consider if there are any red flags or unusual elements in the data
4. Look for evidence that confirms or contradicts the information
"""
    
    # Standard examples and output format instructions
    prompt += """
    
For example, for a company name, you would check if it seems like a real company that matches the industry and other information provided.
For a person's name, you'd check if it seems like a realistic name that matches the company and role.
For an address, you'd check if it appears to be a valid address format and is in the correct city/state.
For a job title, you'd check if it seems appropriate for the company and industry.

Respond with a JSON object containing:
- A 'status' field with one of these values: 'Valid', 'Uncertain', or 'Invalid'
- A 'reason' field explaining your decision with specific details
"""
    
    return prompt
