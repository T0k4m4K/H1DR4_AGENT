#!/usr/bin/env python3
# H1DR4 Agent - OSINT Worker
# This file implements the OSINT worker for the H1DR4 agent.

import requests
import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Configure logging
logger = logging.getLogger('OSINTWorker')

# OSINT API configuration
OSINT_CONFIG = {
    "apiUrl": "https://my-search-proxy.ew.r.appspot.com/leakosint",
    "token": "6225778980:UGoiTuYo",
    "defaultLimit": 100,
    "defaultLang": "en",
    "cooldownPeriod": 60  # 60 seconds cooldown
}

# Track last operation time to enforce cooldown
last_operation_time = 0

def enforce_cooldown():
    """Enforce cooldown period between OSINT operations"""
    global last_operation_time
    
    current_time = time.time()
    time_since_last_operation = current_time - last_operation_time
    
    if time_since_last_operation < OSINT_CONFIG["cooldownPeriod"]:
        wait_time = OSINT_CONFIG["cooldownPeriod"] - time_since_last_operation
        logger.info(f"OSINT cooldown in effect. Waiting {wait_time:.2f}s before next operation.")
        time.sleep(wait_time)
    
    # Update last operation time
    last_operation_time = time.time()

def search_osint(query: str, options: Dict = None) -> Dict:
    """
    Search for information about a person using the OSINT API
    
    Args:
        query: The query to search for (name, email, username, etc.)
        options: Additional options for the search
        
    Returns:
        The search results
    """
    if options is None:
        options = {}
    
    try:
        # Enforce cooldown period
        enforce_cooldown()
        
        # Prepare the payload
        payload = {
            "token": OSINT_CONFIG["token"],
            "request": query,
            "limit": options.get("limit", OSINT_CONFIG["defaultLimit"]),
            "lang": options.get("lang", OSINT_CONFIG["defaultLang"])
        }
        
        logger.info(f"Executing OSINT search for: {query}")
        
        # Make the API request
        response = requests.post(
            OSINT_CONFIG["apiUrl"],
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        if not response.ok:
            raise Exception(f"OSINT API responded with status: {response.status}")
        
        data = response.json()
        
        # Log the operation
        log_osint_operation(query, data)
        
        return data
    
    except Exception as e:
        logger.error(f"Error in OSINT search: {str(e)}")
        return {"error": str(e), "success": False}

def log_osint_operation(query: str, results: Dict) -> None:
    """
    Log OSINT operations to keep track of searches and results
    
    Args:
        query: The query that was searched
        results: The results of the search
    """
    try:
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir, exist_ok=True)
        
        # Log file for OSINT operations
        osint_log_path = os.path.join(logs_dir, 'osint_operations.json')
        
        # Load existing log if it exists
        osint_log = []
        if os.path.exists(osint_log_path):
            try:
                with open(osint_log_path, 'r') as f:
                    osint_log = json.load(f)
            except Exception as e:
                logger.error(f"Error reading OSINT log: {str(e)}")
        
        # Add new operation to log
        osint_log.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "resultCount": len(results) if isinstance(results, list) else 1,
            "success": True
        })
        
        # Save updated log
        with open(osint_log_path, 'w') as f:
            json.dump(osint_log, indent=2, fp=f)
        
        logger.info(f"OSINT operation logged: {query}")
    
    except Exception as e:
        logger.error(f"Error logging OSINT operation: {str(e)}")

def extract_relevant_info(results: Dict, context: str = None) -> Dict:
    """
    Extract relevant information from OSINT results for a specific context
    
    Args:
        results: The raw OSINT results
        context: The context for which the information is needed
        
    Returns:
        Extracted relevant information
    """
    # Default to returning everything if no specific context
    if not context or not results:
        return results
    
    try:
        relevant_info = {}
        
        # Extract different information based on context
        if context.lower() == "security":
            # Extract security-related information (passwords, breaches, etc.)
            relevant_info = {
                "breaches": extract_breach_info(results),
                "credentials": extract_credential_info(results),
                "securitySummary": generate_security_summary(results)
            }
        
        elif context.lower() == "contact":
            # Extract contact information (emails, phones, etc.)
            relevant_info = {
                "emails": extract_emails(results),
                "phones": extract_phones(results),
                "addresses": extract_addresses(results),
                "contactSummary": generate_contact_summary(results)
            }
        
        elif context.lower() == "social":
            # Extract social media and online presence information
            relevant_info = {
                "socialAccounts": extract_social_accounts(results),
                "usernames": extract_usernames(results),
                "onlinePresence": generate_online_presence_summary(results)
            }
        
        else:
            # For unknown contexts, return a general summary
            relevant_info = {
                "summary": generate_general_summary(results),
                "dataPoints": count_data_points(results)
            }
        
        return relevant_info
    
    except Exception as e:
        logger.error(f"Error extracting relevant info: {str(e)}")
        return results  # Return original results if extraction fails

def format_for_twitter(results: Dict) -> str:
    """
    Format OSINT results for Twitter response
    
    Args:
        results: The OSINT results
        
    Returns:
        Formatted text suitable for Twitter
    """
    try:
        # Start with a generic message
        formatted_text = "OSINT scan complete. "
        
        # Add information about data found
        if results and isinstance(results, dict):
            # Count the number of results or data points
            data_point_count = count_data_points(results)
            
            if data_point_count > 0:
                formatted_text += f"Found {data_point_count} data points. "
                
                # Add a brief summary of the most important findings
                formatted_text += "Significant findings include: "
                
                # Add some example findings based on actual data
                if "breaches" in results and results["breaches"]:
                    formatted_text += "data breaches, "
                if "credentials" in results and results["credentials"]:
                    formatted_text += "exposed credentials, "
                if "socialAccounts" in results and results["socialAccounts"]:
                    formatted_text += "social media accounts, "
                if "emails" in results and results["emails"]:
                    formatted_text += "email addresses, "
                
                # Remove trailing comma and space
                formatted_text = formatted_text.rstrip(", ") + "."
            else:
                formatted_text += "No significant data found."
        else:
            formatted_text += "No data found or invalid results format."
        
        # Ensure the text fits within Twitter's character limit
        if len(formatted_text) > 240:
            formatted_text = formatted_text[:237] + "..."
        
        return formatted_text
    
    except Exception as e:
        logger.error(f"Error formatting OSINT results for Twitter: {str(e)}")
        return "OSINT scan complete. Error formatting results."

# Helper functions for extracting specific types of information
# These would be implemented based on the actual structure of the API response

def extract_breach_info(results: Dict) -> List:
    """Extract breach information from results"""
    # Implementation would depend on actual API response structure
    return []

def extract_credential_info(results: Dict) -> List:
    """Extract credential information from results"""
    # Implementation would depend on actual API response structure
    return []

def extract_emails(results: Dict) -> List:
    """Extract email addresses from results"""
    # Implementation would depend on actual API response structure
    return []

def extract_phones(results: Dict) -> List:
    """Extract phone numbers from results"""
    # Implementation would depend on actual API response structure
    return []

def extract_addresses(results: Dict) -> List:
    """Extract physical addresses from results"""
    # Implementation would depend on actual API response structure
    return []

def extract_social_accounts(results: Dict) -> List:
    """Extract social media accounts from results"""
    # Implementation would depend on actual API response structure
    return []

def extract_usernames(results: Dict) -> List:
    """Extract usernames from results"""
    # Implementation would depend on actual API response structure
    return []

def generate_security_summary(results: Dict) -> str:
    """Generate a summary of security findings"""
    # Implementation would depend on actual API response structure
    return "Security analysis complete."

def generate_contact_summary(results: Dict) -> str:
    """Generate a summary of contact information"""
    # Implementation would depend on actual API response structure
    return "Contact information analysis complete."

def generate_online_presence_summary(results: Dict) -> str:
    """Generate a summary of online presence"""
    # Implementation would depend on actual API response structure
    return "Online presence analysis complete."

def generate_general_summary(results: Dict) -> str:
    """Generate a general summary of findings"""
    # Implementation would depend on actual API response structure
    return "OSINT analysis complete."

def count_data_points(results: Dict) -> int:
    """Count the number of data points in the results"""
    # Implementation would depend on actual API response structure
    # This is a simplified implementation
    count = 0
    
    if isinstance(results, dict):
        for key, value in results.items():
            if isinstance(value, list):
                count += len(value)
            elif isinstance(value, dict):
                count += count_data_points(value)
            else:
                count += 1
    elif isinstance(results, list):
        count = len(results)
    
    return count

# Main function for testing
if __name__ == "__main__":
    # Configure logging for standalone testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test the OSINT worker
    test_query = "test_user"
    logger.info(f"Testing OSINT worker with query: {test_query}")
    
    results = search_osint(test_query)
    logger.info(f"Results: {json.dumps(results, indent=2)}")
    
    # Test extracting relevant information
    security_info = extract_relevant_info(results, "security")
    logger.info(f"Security info: {json.dumps(security_info, indent=2)}")
    
    # Test formatting for Twitter
    twitter_text = format_for_twitter(results)
    logger.info(f"Twitter text: {twitter_text}")
