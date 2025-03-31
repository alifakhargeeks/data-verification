import pandas as pd
import time
from web_utils import get_company_info_from_web
from email_validator import validate_email
from openai_verification import verify_contact_with_ai

def verify_data(row_data, columns_to_verify, use_ai=True, use_deep_search=False):
    """
    Verify data for a single row and return the row with verification status
    
    Parameters:
    - row_data: DataFrame row to verify
    - columns_to_verify: List of column names to verify
    - use_ai: Whether to use AI for verification
    - use_deep_search: Whether to use more thorough verification with advanced AI models
    
    Returns:
    - DataFrame row with verification status columns added
    """
    # Create a deep copy to avoid modifying the original
    verified_row = row_data.copy(deep=True)
    
    # For each row, we'll verify each specified column
    for col in columns_to_verify:
        # Create a new column for verification status
        status_col = f"{col}_status"
        verified_row[status_col] = 'Uncertain'  # Default to uncertain
        
        # If value is empty, mark as uncertain and continue
        if pd.isna(row_data.iloc[0][col]) or row_data.iloc[0][col] == '':
            verified_row[status_col] = 'Uncertain'
            continue
        
        # Specific verification logic based on column type
        try:
            if col == "Email":
                # Verify email
                email_status = validate_email(row_data.iloc[0][col])
                verified_row[status_col] = email_status
                
            elif col in ["First Name", "Last Name"]:
                # Verify name by checking against company info
                company = None
                for company_col in ["Company", "Company Name"]:
                    if company_col in row_data.columns and not pd.isna(row_data.iloc[0][company_col]):
                        company = row_data.iloc[0][company_col]
                        break
                
                company_domain = row_data.iloc[0]["Company Domain"] if "Company Domain" in row_data.columns else None
                
                if company:
                    name_status = verify_name_against_company(
                        row_data.iloc[0]["First Name"], 
                        row_data.iloc[0]["Last Name"], 
                        company,
                        company_domain
                    )
                    verified_row[status_col] = name_status
                else:
                    verified_row[status_col] = 'Uncertain'
                    
            elif col in ["Company", "Company Name"]:
                # Verify company existence
                company = row_data.iloc[0][col]
                company_domain = row_data.iloc[0]["Company Domain"] if "Company Domain" in row_data.columns else None
                
                company_status = verify_company_exists(company, company_domain)
                verified_row[status_col] = company_status
                
            elif col == "Company Domain":
                # Verify company domain
                domain = row_data.iloc[0][col]
                
                # Get company name from appropriate column
                company = None
                for company_col in ["Company", "Company Name"]:
                    if company_col in row_data.columns and not pd.isna(row_data.iloc[0][company_col]):
                        company = row_data.iloc[0][company_col]
                        break
                
                domain_status = verify_company_domain(domain, company)
                verified_row[status_col] = domain_status
                
            elif col in ["Company Address", "Company City", "Company State", "Company Country", "Company Postal Code"]:
                # Verify address components
                # Get company name from appropriate column
                company = None
                for company_col in ["Company", "Company Name"]:
                    if company_col in row_data.columns and not pd.isna(row_data.iloc[0][company_col]):
                        company = row_data.iloc[0][company_col]
                        break
                
                address_component = row_data.iloc[0][col]
                
                address_status = verify_address_component(
                    col, address_component, company, row_data, use_ai, use_deep_search
                )
                verified_row[status_col] = address_status
                
            elif col in ["BYD_Industries", "Company Industry"]:
                # Verify industry
                industry = row_data.iloc[0][col]
                
                # Get company name from appropriate column
                company = None
                for company_col in ["Company", "Company Name"]:
                    if company_col in row_data.columns and not pd.isna(row_data.iloc[0][company_col]):
                        company = row_data.iloc[0][company_col]
                        break
                
                industry_status = verify_industry(industry, company, use_ai, use_deep_search)
                verified_row[status_col] = industry_status
            
            else:
                # For any other columns, use AI verification if enabled
                value = row_data.iloc[0][col]
                row_dict = row_data.iloc[0].to_dict()
                
                if use_ai:
                    # Use OpenAI to verify this field, with deep search if enabled
                    ai_status = verify_contact_with_ai(col, value, row_dict, use_deep_search)
                    verified_row[status_col] = ai_status
                else:
                    # Skip AI verification if disabled
                    verified_row[status_col] = 'Uncertain'
        
        except Exception as e:
            # If verification fails, mark as uncertain
            verified_row[status_col] = 'Uncertain'
            print(f"Error verifying {col}: {str(e)}")
    
    # Add a small delay to avoid rate limiting in API calls
    time.sleep(0.2)
    
    return verified_row

def verify_name_against_company(first_name, last_name, company, company_domain=None):
    """Verify if name appears to be associated with the company"""
    try:
        # Get company information from web
        company_info = get_company_info_from_web(company, company_domain)
        
        # Look for name in company information
        full_name = f"{first_name} {last_name}".lower()
        
        # If name is found in company info, mark as valid
        if full_name in company_info.lower():
            return 'Valid'
        
        # If we can't find the name but the search was successful, consider it potentially invalid
        return 'Uncertain'
    
    except Exception as e:
        print(f"Error verifying name against company: {str(e)}")
        return 'Uncertain'

def verify_company_exists(company, company_domain=None):
    """Verify if the company exists based on web information"""
    try:
        # Get company information from web
        company_info = get_company_info_from_web(company, company_domain)
        
        # If we found substantial information, mark as valid
        if len(company_info) > 100:  # Arbitrary threshold for "substantial" info
            return 'Valid'
        elif len(company_info) > 0:
            return 'Uncertain'
        else:
            return 'Invalid'
    
    except Exception as e:
        print(f"Error verifying company existence: {str(e)}")
        return 'Uncertain'

def verify_company_domain(domain, company=None):
    """Verify if the company domain is valid and matches the company"""
    if not domain or pd.isna(domain) or domain == '':
        return 'Uncertain'
    
    try:
        # Basic domain format validation
        if '.' not in domain or ' ' in domain:
            return 'Invalid'
        
        # Check if domain is accessible
        import requests
        url = f"https://{domain}"
        response = requests.head(url, timeout=5)
        
        # If domain responds, mark as valid
        if response.status_code < 400:
            # If company name is provided, check if it's in the domain
            if company and not pd.isna(company) and company != '':
                # Create simplified versions for comparison
                simple_company = ''.join(e.lower() for e in company if e.isalnum())
                simple_domain = ''.join(e.lower() for e in domain if e.isalnum())
                
                # If company name is in domain, very likely valid
                if simple_company in simple_domain:
                    return 'Valid'
                else:
                    # Domain works but doesn't contain company name, uncertain
                    return 'Uncertain'
            else:
                # Domain works but no company to compare with
                return 'Valid'
        else:
            # Domain doesn't respond, but might still be valid
            return 'Uncertain'
    
    except Exception as e:
        print(f"Error verifying company domain: {str(e)}")
        return 'Uncertain'

def verify_address_component(component_type, component_value, company=None, row_data=None, use_ai=True, use_deep_search=False):
    """Verify if an address component matches company information"""
    try:
        if company and not pd.isna(company) and company != '':
            # Get company information from web
            company_info = get_company_info_from_web(company)
            
            # Different verification based on component type
            if component_type == "Company Address":
                # Address verification is more complex as formats vary
                # Look for address components in company info
                address_parts = str(component_value).lower().split()
                matches = sum(1 for part in address_parts if part in company_info.lower())
                
                # If many parts match, likely valid
                if matches > len(address_parts) / 2:
                    return 'Valid'
                elif matches > 0:
                    return 'Uncertain'
                else:
                    return 'Invalid'
                
            elif component_type in ["Company City", "Company State", "Company Country"]:
                # City, state, and country verification are more straightforward
                if str(component_value).lower() in company_info.lower():
                    return 'Valid'
                else:
                    # Use AI verification for more sophisticated checking if enabled
                    if use_ai and row_data is not None:
                        row_dict = row_data.iloc[0].to_dict()
                        # Pass the use_deep_search parameter
                        ai_status = verify_contact_with_ai(component_type, component_value, row_dict, use_deep_search)
                        return ai_status
                    return 'Uncertain'
                
            elif component_type == "Company Postal Code":
                # Postal code verification is harder from web info
                # Often need specialized address verification APIs
                # For now, just check if it appears in company info
                if str(component_value) in company_info:
                    return 'Valid'
                else:
                    return 'Uncertain'
        else:
            # No company to verify against
            return 'Uncertain'
    
    except Exception as e:
        print(f"Error verifying address component: {str(e)}")
        return 'Uncertain'

def verify_industry(industry, company=None, use_ai=True, use_deep_search=False):
    """Verify if the industry matches the company information"""
    try:
        if company and not pd.isna(company) and company != '':
            # Get company information from web
            company_info = get_company_info_from_web(company)
            
            # Check if industry is mentioned in company info
            if str(industry).lower() in company_info.lower():
                return 'Valid'
            else:
                # If AI verification is enabled, use it for more sophisticated checking
                if use_ai:
                    # Create a mock row dictionary with essential information
                    row_dict = {
                        "Company Name": company,
                        "Company Industry": industry
                    }
                    
                    # Use OpenAI to verify the industry
                    ai_status = verify_contact_with_ai("Company Industry", industry, row_dict, use_deep_search)
                    return ai_status
                else:
                    return 'Uncertain'
        else:
            # No company to verify against
            return 'Uncertain'
    
    except Exception as e:
        print(f"Error verifying industry: {str(e)}")
        return 'Uncertain'
