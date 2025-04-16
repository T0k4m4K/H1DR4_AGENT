#!/usr/bin/env python3
# Standalone OSINT Test Script
# This script tests the OSINT worker with a real query for Justin Trudeau

import os
import sys
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('OSINTTest')

# Import the OSINT worker module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from osint_worker import search_osint, extract_relevant_info, format_for_twitter
    logger.info("Successfully imported OSINT worker module")
except ImportError as e:
    logger.error(f"Failed to import OSINT worker module: {e}")
    sys.exit(1)

def test_osint_query(query, contexts=None):
    """
    Test the OSINT worker with a specific query
    
    Args:
        query: The query to search for (name, email, username, etc.)
        contexts: List of contexts to extract information for
    """
    if contexts is None:
        contexts = ["security", "social", "contact"]
    
    logger.info(f"Testing OSINT search for: {query}")
    
    try:
        # Perform the OSINT search
        start_time = datetime.now()
        results = search_osint(query)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Check if we got results
        if not results:
            logger.error(f"No results found for query: {query}")
            return False
        
        # Log basic results info
        result_type = type(results).__name__
        result_size = len(json.dumps(results))
        logger.info(f"Received {result_type} results ({result_size} bytes) in {duration:.2f} seconds")
        
        # Save raw results to file
        results_dir = "osint_results"
        os.makedirs(results_dir, exist_ok=True)
        results_file = os.path.join(results_dir, f"{query.replace(' ', '_')}_raw.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Raw results saved to: {results_file}")
        
        # Process results for each context
        for context in contexts:
            logger.info(f"Extracting {context} information...")
            context_info = extract_relevant_info(results, context)
            
            # Save context-specific results
            context_file = os.path.join(results_dir, f"{query.replace(' ', '_')}_{context}.json")
            with open(context_file, 'w') as f:
                json.dump(context_info, f, indent=2)
            logger.info(f"{context.capitalize()} information saved to: {context_file}")
        
        # Format for Twitter
        twitter_text = format_for_twitter(results)
        logger.info(f"Twitter format ({len(twitter_text)} chars): {twitter_text}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing OSINT query: {e}")
        return False

def main():
    """Main entry point for the test script"""
    # Define test queries
    test_queries = [
        "Justin Trudeau",
        "Elon Musk",
        "Mark Zuckerberg"
    ]
    
    # Test each query
    success_count = 0
    for query in test_queries:
        logger.info(f"===== Testing query: {query} =====")
        if test_osint_query(query):
            success_count += 1
        logger.info(f"===== Completed query: {query} =====\n")
    
    # Report results
    logger.info(f"Testing completed: {success_count}/{len(test_queries)} queries successful")
    
    return 0 if success_count == len(test_queries) else 1

if __name__ == "__main__":
    sys.exit(main())
