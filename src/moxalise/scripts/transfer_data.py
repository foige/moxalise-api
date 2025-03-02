#!/usr/bin/env python3
"""
Script to transfer data from "დაზარალებულთა შევსებული ინფორმაცია" to "დაზარალებულთა სია"
in the same Google Spreadsheet.

This script is designed to run as a Google Cloud Run job every 5 minutes.
It can be run directly or via the job_runner.py script.
"""
import hashlib
import logging
import signal
import sys
import time
from typing import Dict, List, Any, Optional, Callable

import click
from google.auth.exceptions import GoogleAuthError

from moxalise.services.google_sheets import GoogleSheetsService
from moxalise.models.spreadsheet import SheetRange, SheetUpdateRequest, SheetAppendRequest

# Global variables for time tracking and graceful shutdown
MAX_EXECUTION_TIME = 240  # 4 minutes in seconds (to allow graceful shutdown before the 5min timeout)
start_time = None
should_exit = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Constants
SOURCE_SHEET = "დაზარალებულთა შევსებული ინფორმაცია"
TARGET_SHEET = "დაზარალებულთა სია"

# Column headers (names) to look for
SOURCE_COLUMN_NAMES = {
    "timestamp": "Column 1",  # First column is often labeled as "Column 1" or might be unnamed
    "name": "სახელი, გვარი",
    "district": "რაიონი",
    "village": "სოფელი",
    "exact_location": "ზუსტი ადგილმდებარეობა",
    "phone": "ტელეფონის ნომერი",
    "needs": "რა სჭირდება?",
    "detailed_info": "დეტალური ინფორმაცია",
    "last_contact": "ბოლო კავშირი",
    "id": "id",  # ID column in source sheet
    "added": "added"  # Process status flag
}

TARGET_COLUMN_NAMES = {
    "name": "სახელი",
    "district": "რაიონი",
    "village": "სოფელი",
    "lat": "lat",
    "lon": "lon",
    "exact_location": "ზუსტი ადგილმდებარეობა",
    "phone": "ტელეფონი",
    "needs": "საჭიროება",
    "detailed_info": "დეტალური ინფორმაცია",
    "priority": "პრიორიტეტი",
    "added_date": "დამატების თარიღი",
    "status": "სტატუსი",
    "updates": "განახლებები",
    "id": "id"
}

def create_short_hash(data: str) -> str:
    """
    Create a short hash from the given data, similar to GitHub's short hashes.
    
    Args:
        data: The data to hash.
        
    Returns:
        A short hash string (8 characters).
    """
    # Create SHA-1 hash (GitHub uses this for their commit hashes)
    hash_object = hashlib.sha1(data.encode('utf-8'))
    # Get first 8 characters of the hex digest
    return hash_object.hexdigest()[:8]

def strip_parentheses(text: str) -> str:
    """
    Remove text in parentheses and trim the result.
    For example, "Name (First Name)" becomes "Name".
    Also handles multi-line text and nested parentheses.
    
    Args:
        text: The text to process.
        
    Returns:
        The cleaned text with parenthetical content removed.
    """
    import re
    # Replace text in parentheses with empty string, handling multi-line text
    cleaned = re.sub(r'\([^)]*\)', '', text, flags=re.DOTALL)
    # Remove newlines and extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

def map_columns(headers: List[str], column_names: Dict[str, str]) -> Dict[str, int]:
    """
    Map column logical names to their positions in the headers.
    
    Args:
        headers: The header row with column names.
        column_names: Dictionary mapping logical names to actual header names.
        
    Returns:
        Dictionary mapping logical names to column indices.
    """
    
    column_map = {}
    
    # Try matches with parentheses removed
    for logical_name, header_name in column_names.items():
        clean_expected = strip_parentheses(header_name.strip())
        
        for i, header in enumerate(headers):
            # Try exact match first
            if header.strip() == header_name.strip():
                column_map[logical_name] = i
                break
                
            # Then try with parentheses removed
            clean_actual = strip_parentheses(header.strip())
            if clean_actual == clean_expected:
                column_map[logical_name] = i
                logger.info(f"Matched column '{logical_name}' by removing parentheses: '{header}' -> '{clean_actual}'")
                break
    
    # Handle special cases
    if "timestamp" not in column_map and len(headers) > 0:
        # Assume first column is timestamp if not found by name
        column_map["timestamp"] = 0
    
    # Log unmapped columns
    for logical_name in column_names:
        if logical_name not in column_map:
            logger.warning(f"Could not map column '{logical_name}' ({column_names[logical_name]})")
            
    return column_map

def setup_signal_handlers():
    """
    Setup signal handlers for graceful shutdown.
    """
    def signal_handler(sig, frame):
        global should_exit
        logger.info(f"Received signal {sig}, will exit after completing current row")
        should_exit = True
        
    # Register handlers for common termination signals
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    signal.signal(signal.SIGINT, signal_handler)   # Interrupt from keyboard (Ctrl+C)

def check_time_limit():
    """
    Check if we're approaching the time limit.
    
    Returns:
        bool: True if we should exit, False otherwise.
    """
    global start_time, should_exit
    
    if should_exit:
        return True
        
    if start_time is None:
        return False
        
    elapsed = time.time() - start_time
    if elapsed >= MAX_EXECUTION_TIME:
        logger.warning(f"Approaching time limit ({elapsed:.1f}s/{MAX_EXECUTION_TIME}s), will exit after current row")
        should_exit = True
        return True
        
    return False

def verify_headers_unchanged(
    service: GoogleSheetsService,
    sheet_name: str,
    original_headers: List[Any]
) -> bool:
    """
    Verify that sheet headers haven't changed since we started processing.
    
    Args:
        service: The Google Sheets service to use.
        sheet_name: The name of the sheet to check.
        original_headers: The original headers we expect to still be present.
        
    Returns:
        bool: True if headers are unchanged, False if they have changed.
    """
    try:
        # Get just the header row
        header_range = SheetRange(sheet_name=sheet_name, start_cell="A1", end_cell=f"Z1")
        header_data = service.get_sheet_data(header_range)
        
        if not header_data.values:
            logger.warning(f"Could not retrieve current headers from {sheet_name}")
            return False
            
        current_headers = header_data.values[0]
        
        # Check if the headers match
        if len(current_headers) != len(original_headers):
            logger.warning(f"Header count changed in {sheet_name}: {len(original_headers)} -> {len(current_headers)}")
            return False
            
        for i, (orig, curr) in enumerate(zip(original_headers, current_headers)):
            if orig != curr:
                logger.warning(f"Header changed at position {i} in {sheet_name}: '{orig}' -> '{curr}'")
                return False
                
        return True
    except Exception as e:
        logger.error(f"Error verifying headers in {sheet_name}: {str(e)}")
        return False

def generate_row_id(
    row: List[Any],
    source_indices: Dict[str, int]
) -> str:
    """
    Generate a unique ID for a row based on its content.
    
    Args:
        row: The row data.
        source_indices: Mapping of column names to indices.
        
    Returns:
        str: The generated ID.
    """
    # Check if row already has an ID
    existing_id = ""
    if "id" in source_indices and len(row) > source_indices["id"]:
        existing_id = row[source_indices["id"]]
    
    if existing_id:
        return existing_id
    
    # Get all relevant data
    name = row[source_indices.get("name", 1)] if len(row) > source_indices.get("name", 1) else ""
    district = row[source_indices.get("district", 2)] if len(row) > source_indices.get("district", 2) else ""
    village = row[source_indices.get("village", 3)] if len(row) > source_indices.get("village", 3) else ""
    phone = row[source_indices.get("phone", 0)] if "phone" in source_indices and len(row) > source_indices["phone"] else ""
    exact_location = row[source_indices.get("exact_location", 0)] if "exact_location" in source_indices and len(row) > source_indices["exact_location"] else ""
    timestamp = row[source_indices.get("timestamp", 0)] if len(row) > source_indices.get("timestamp", 0) else ""
    
    # Create hash data: include phone and exact_location if they exist, only include timestamp if neither exist
    hash_components = []
    
    # Always include these basic identifiers
    hash_components.append(name)
    hash_components.append(district)
    hash_components.append(village)
    
    # Include phone and/or exact_location if they exist
    if phone:
        hash_components.append(phone)
    if exact_location:
        hash_components.append(exact_location)
    
    # Only include timestamp if neither phone nor exact_location exist
    if not phone and not exact_location and timestamp:
        hash_components.append(timestamp)
    
    # Create hash from combined data
    hash_data = "|".join(hash_components)
    return create_short_hash(hash_data)

def process_spreadsheet_data():
    """
    Process data from the source sheet and transfer it to the target sheet.
    With graceful shutdown support when approaching time limits.
    Uses batch operations to reduce API calls.
    """
    global start_time
    
    # Initialize timer
    start_time = time.time()
    
    try:
        service = GoogleSheetsService()
        logger.info(f"Connected to Google Sheets service")
        
        # Get all data from source sheet
        source_range = SheetRange(sheet_name=SOURCE_SHEET, start_cell="A1", end_cell="Z100000")
        source_data = service.get_sheet_data(source_range)
        
        if not source_data.values:
            logger.warning(f"No data found in source sheet: {SOURCE_SHEET}")
            return
            
        # Extract headers
        source_headers = source_data.values[0]
        source_indices = map_columns(source_headers, SOURCE_COLUMN_NAMES)
        
        # Store original source headers for consistency checks
        original_source_headers = source_headers.copy()
        
        # Get all data from target sheet
        target_range = SheetRange(sheet_name=TARGET_SHEET, start_cell="A1", end_cell="Z100000")
        target_data = service.get_sheet_data(target_range)
        
        if not target_data.values:
            logger.warning(f"No data found in target sheet: {TARGET_SHEET}")
            return
            
        target_headers = target_data.values[0]
        target_indices = map_columns(target_headers, TARGET_COLUMN_NAMES)
        
        # Store original target headers for consistency checks
        original_target_headers = target_headers.copy()
        
        # Prepare for batch operations
        rows_to_append = []  # Rows to append to target sheet
        rows_to_mark = {}    # Rows to mark as added in source sheet {A1_notation: value}
        ids_to_add = {}      # IDs to add to source sheet {A1_notation: value}
        
        # Maximum batch size
        MAX_BATCH_SIZE = 100
        
        # Process each row in source data (skip header)
        rows_processed = 0
        rows_collected = 0
        rows_transferred = 0
        
        # Define a function to execute the batched operations
        def execute_batch_operations():
            nonlocal rows_transferred
            
            # Handle batch append
            if rows_to_append:
                # Get the next row after the last data row (length of values = number of rows including header)
                next_row = len(target_data.values) + 1
                
                logger.info(f"Appending at row {next_row}")
                
                append_request = SheetAppendRequest(
                    range=SheetRange(sheet_name=TARGET_SHEET, start_cell=f"A{next_row}"),
                    values=rows_to_append,
                    value_input_option="USER_ENTERED"
                )
                append_result = service.append_sheet_data(append_request)
                logger.info(f"Batch appended {len(rows_to_append)} rows to target sheet: {append_result.appended_range}")
                rows_transferred += len(rows_to_append)
                rows_to_append.clear()
            
            # Handle batch updates (IDs and marking as added)
            batch_updates = {**ids_to_add, **rows_to_mark}
            if batch_updates:
                update_result = service.batch_update_sheet_data(batch_updates)
                logger.info(f"Batch updated {len(batch_updates)} cells in source sheet")
                ids_to_add.clear()
                rows_to_mark.clear()
        
        # Process rows
        for i, row in enumerate(source_data.values[1:], start=1):
            # Check if we should exit before starting a new row
            if check_time_limit() and rows_processed > 0:
                logger.info(f"Exiting due to time limit after processing {rows_processed} rows")
                execute_batch_operations()  # Make sure to process any pending operations
                break
                
            rows_processed += 1
            
            # Check if row is already added
            if "added" in source_indices and len(row) > source_indices["added"]:
                added_value = row[source_indices["added"]]
                if added_value and str(added_value).upper() == "TRUE":
                    continue
            
            # Before processing this row, verify headers haven't changed
            # This helps prevent race conditions if someone is editing the sheet structure
            if rows_processed % 10 == 0:  # Reduced frequency to every 10 rows instead of 5
                source_headers_ok = verify_headers_unchanged(service, SOURCE_SHEET, original_source_headers)
                target_headers_ok = verify_headers_unchanged(service, TARGET_SHEET, original_target_headers)
                
                if not source_headers_ok or not target_headers_ok:
                    logger.error("Headers changed during processing. Aborting to prevent data corruption.")
                    execute_batch_operations()  # Make sure to process any pending operations
                    break
            
            # Check if the row already has an ID
            had_existing_id = False
            if "id" in source_indices and len(row) > source_indices["id"]:
                had_existing_id = bool(row[source_indices["id"]])
            
            # Get or generate a unique ID for the row (using the updated generate_row_id function)
            unique_id = generate_row_id(row, source_indices)
            
            # If the row didn't have an ID before, add the new one to the batch update
            if "id" in source_indices and not had_existing_id:
                    id_col_letter = chr(65 + source_indices["id"])  # Convert index to column letter (A, B, C, etc.)
                    id_cell = f"'{SOURCE_SHEET}'!{id_col_letter}{i+1}"
                    ids_to_add[id_cell] = [[unique_id]]
                    
                    # Update the row data with the new ID
                    if len(row) <= source_indices["id"]:
                        # Extend the row if needed
                        while len(row) <= source_indices["id"]:
                            row.append("")
                    row[source_indices["id"]] = unique_id
            
            # Prepare row for target sheet with empty values
            max_target_index = max(target_indices.values()) if target_indices else 13
            target_row = [""] * (max_target_index + 1)
            
            # Map data from source to target
            field_mapping = {
                "name": "name",
                "district": "district",
                "village": "village",
                "exact_location": "exact_location",
                "phone": "phone",
                "needs": "needs",
                "detailed_info": "detailed_info"
            }
            
            for target_field, source_field in field_mapping.items():
                if (source_field in source_indices and
                    target_field in target_indices and
                    len(row) > source_indices[source_field]):
                    target_row[target_indices[target_field]] = row[source_indices[source_field]]
            
            # Add additional fields
            if "added_date" in target_indices:
                target_row[target_indices["added_date"]] = time.strftime("%m/%d/%Y %H:%M:%S")
                
            if "status" in target_indices:
                target_row[target_indices["status"]] = "მომლოდინე"
                
            if "id" in target_indices:
                target_row[target_indices["id"]] = unique_id
            
            # Add row to batch append
            rows_to_append.append(target_row)
            rows_collected += 1
            
            # Add to batch update for marking as added
            if "added" in source_indices:
                added_col_letter = chr(65 + source_indices["added"])  # Convert index to column letter (A, B, C, etc.)
                added_cell = f"'{SOURCE_SHEET}'!{added_col_letter}{i+1}"
                rows_to_mark[added_cell] = [["TRUE"]]
            
            # Execute batch operations when we hit the batch size
            if rows_collected >= MAX_BATCH_SIZE:
                execute_batch_operations()
                rows_collected = 0
        
        # Execute any remaining batch operations
        if rows_collected > 0:
            execute_batch_operations()
        
        logger.info(f"Processed {rows_processed} rows, transferred {rows_transferred} rows")
        
    except GoogleAuthError as e:
        logger.error(f"Authentication error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing spreadsheet data: {str(e)}")

@click.command()
@click.option(
    '--max-time',
    default=240,
    help='Maximum execution time in seconds before graceful shutdown (default: 240)'
)
def main(max_time):
    """
    Run the data transfer process with time limit handling.
    """
    global MAX_EXECUTION_TIME
    
    # Update max execution time if specified
    if max_time and max_time > 0:
        MAX_EXECUTION_TIME = max_time
        
    logger.info(f"Starting data transfer process (max execution time: {MAX_EXECUTION_TIME}s)")
    
    # Setup signal handlers for graceful shutdown
    setup_signal_handlers()
    
    # Run the process
    process_spreadsheet_data()
    
    # Report how much time we used
    elapsed = time.time() - start_time if start_time is not None else 0
    logger.info(f"Data transfer process completed in {elapsed:.1f}s")

if __name__ == "__main__":
    main()