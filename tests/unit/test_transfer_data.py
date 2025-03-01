"""
Test module for transfer_data script.

This module contains unit tests for the transfer_data script, ensuring it
correctly transfers data from the source sheet to the target sheet.
"""
import unittest
from unittest.mock import MagicMock, patch

from moxalise.models.spreadsheet import SheetData, SheetRange
from moxalise.scripts.transfer_data import (
    create_short_hash,
    map_columns,
    process_spreadsheet_data,
    generate_row_id,
    SOURCE_COLUMN_NAMES,
    TARGET_COLUMN_NAMES,
)


class TestTransferData(unittest.TestCase):
    """Test case for transfer_data script."""
    
    def test_generate_row_id(self):
        """Test the generate_row_id function."""
        # Given
        row = ["2025-02-25 20:15:27", "მანანა როყვა", "ოზურგეთი", "ანასეული", "სახლი 5"]
        source_indices = {
            "timestamp": 0,
            "name": 1,
            "district": 2,
            "village": 3
        }
        
        # When - using a patch to return a predictable hash
        with patch("moxalise.scripts.transfer_data.create_short_hash", return_value="abc12345"):
            result = generate_row_id(row, source_indices)
        
        # Then
        self.assertEqual(result, "abc12345")
        
        # Test with existing ID
        row_with_id = row + ["", "", "", "", "existing_id"]
        source_indices_with_id = source_indices.copy()
        source_indices_with_id["id"] = 9
        
        result_with_id = generate_row_id(row_with_id, source_indices_with_id)
        self.assertEqual(result_with_id, "existing_id")  # Should return existing ID
    
    def test_strip_parentheses(self):
        """Test the strip_parentheses function."""
        # Import the function directly now that it's standalone
        from moxalise.scripts.transfer_data import strip_parentheses
        
        # Test cases
        test_cases = [
            # Simple case
            ("Name (Extra Info)", "Name"),
            # Multi-line text
            ("Status\n(Pending/Complete)", "Status"),
            # Complex case with multiple parentheses
            ("Needs(Multiple)\n(Food, Medicine, Evacuation)", "Needs"),
            # No parentheses
            ("Plain Text", "Plain Text"),
            # Just whitespace cleanup
            ("Text  with    spaces", "Text with spaces"),
        ]
        
        for input_text, expected_output in test_cases:
            self.assertEqual(strip_parentheses(input_text), expected_output)

    def test_create_short_hash(self):
        """Test the create_short_hash function."""
        # Given
        data = "2025-02-25 20:15:27|მანანა, როყვა, მარინა ზედგინიძე|ოზურგეთი|ანასეული"
        
        # When
        result = create_short_hash(data)
        
        # Then
        self.assertEqual(len(result), 8)  # Hash should be 8 chars long
        self.assertTrue(all(c in "0123456789abcdef" for c in result))  # Valid hex chars

    def test_map_columns(self):
        """Test the map_columns function."""
        # Given
        headers = [
            "Column 1",
            "სახელი, გვარი",
            "რაიონი (Region)",
            "სოფელი (Village)",
            "ზუსტი ადგილმდებარეობა",
            "unknown"
        ]
        
        # When
        result = map_columns(headers, SOURCE_COLUMN_NAMES)
        
        # Then
        self.assertEqual(result["timestamp"], 0)
        self.assertEqual(result["name"], 1)
        self.assertEqual(result["district"], 2)  # Should match even with "(Region)" in the header
        self.assertEqual(result["village"], 3)   # Should match even with "(Village)" in the header
        self.assertEqual(result["exact_location"], 4)
        self.assertNotIn("unknown", result)

    @patch("moxalise.scripts.transfer_data.GoogleSheetsService")
    @patch("moxalise.scripts.transfer_data.time.time")
    @patch("moxalise.scripts.transfer_data.create_short_hash")
    def test_process_spreadsheet_data(self, mock_hash, mock_time, mock_service_class):
        """Test the process_spreadsheet_data function with mock data."""
        # Setup mock service and time
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # Mock time.time() to return fixed values
        # Need many values for multiple calls to time.time() from various places:
        # - Initial start_time
        # - When checking time limit
        # - For logging calls that use time.time()
        # - For final elapsed time reporting
        mock_time.side_effect = [100] + [150] * 20  # Provide plenty of values to avoid StopIteration
        
        # Mock hash function to return a predictable ID
        mock_hash.return_value = "abc12345"
        
        # Mock source sheet data
        source_data = SheetData(
            range="'დაზარალებულთა შევსებული ინფორმაცია'!A1:J3",
            values=[
                ["Column 1", "სახელი, გვარი", "რაიონი", "სოფელი", "ზუსტი ადგილმდებარეობა", 
                 "ტელეფონის ნომერი", "რა სჭირდება?", "დეტალური ინფორმაცია", "ბოლო კავშირი", "added"],
                ["2/25/2025 20:15:27", "გიორგი გიორგაძე", "ოზურგეთი", "ანასეული", 
                 "სახლი 5", "555000000", "მოხუცები არიან", "", "", ""],
                ["2/26/2025 10:30:15", "მარინა გიორგაძე", "ლანჩხუთი", "ნიგოითი", 
                 "სახლი 10", "555111111", "საკვები", "ოჯახი 3 წევრი", "", "TRUE"]
            ]
        )
        
        # Mock target sheet data
        target_data = SheetData(
            range="'დაზარალებულთა სია'!A1:N2",
            values=[
                ["სახელი", "რაიონი", "სოფელი", "lat", "lon", "ზუსტი ადგილმდებარეობა", 
                 "ტელეფონი", "საჭიროება(ები)", "დეტალური ინფორმაცია", "პრიორიტეტი", 
                 "დამატების თარიღი", "სტატუსი", "განახლებები", "id"],
                ["დავით გიორგაძე", "ლანჩხუთი", "ბარლეფში კიროვი", "", "", "", 
                 "555222222", "არასრულწლოვანი სიცხიანი ბავშვები", "", "", 
                 "2/26/2025 4:00:00", "მომლოდინე", "", "ac321d8a"]
            ]
        )
        
        # Configure mocks for service
        mock_service.get_sheet_data.side_effect = [source_data, target_data]
        # Mock the append_sheet_data method for batch operations
        mock_append_response = MagicMock()
        mock_append_response.appended_range = "მომლოდინე!A2:N2"
        mock_service.append_sheet_data.return_value = mock_append_response
        
        # Mock the batch_update_sheet_data method for batch operations
        mock_batch_update_result = {
            "'დაზარალებულთა შევსებული ინფორმაცია'!J2": 1,  # 1 cell updated for marking as added
        }
        mock_service.batch_update_sheet_data.return_value = mock_batch_update_result
        
        # Mock verify_headers_unchanged and check_time_limit to avoid early exits
        with patch("moxalise.scripts.transfer_data.verify_headers_unchanged", return_value=True), \
             patch("moxalise.scripts.transfer_data.check_time_limit", return_value=False):
            # Run function
            process_spreadsheet_data()
        
        # Verify
        # Check that we read both sheets
        self.assertEqual(mock_service.get_sheet_data.call_count, 2)
        
        # Verify we attempted to batch append rows
        self.assertEqual(mock_service.append_sheet_data.call_count, 1)
        
        # Verify we attempted to batch update the source sheet
        self.assertEqual(mock_service.batch_update_sheet_data.call_count, 1)
        
        # Verify the batch data contains the expected operations
        batch_data = mock_service.batch_update_sheet_data.call_args[0][0]
        self.assertIsInstance(batch_data, dict)
        # At least one entry should be present (marking a row as added)
        self.assertGreater(len(batch_data), 0)
        
        # Check that at least one entry contains the TRUE value (for marking as added)
        found_true = False
        for key, values in batch_data.items():
            if values == [["TRUE"]]:
                found_true = True
                break
        self.assertTrue(found_true, "Should have at least one entry marking a row as added with TRUE")
        
    def test_verify_headers_unchanged(self):
        """Test the verify_headers_unchanged function."""
        # Import the function directly
        from moxalise.scripts.transfer_data import verify_headers_unchanged
        
        # Create mock service
        mock_service = MagicMock()
        
        # Case 1: Headers match (success)
        original_headers = ["Header1", "Header2", "Header3"]
        
        # Mock response for success case
        success_response = SheetData(
            range="'Sheet1'!A1:Z1",
            values=[["Header1", "Header2", "Header3"]]
        )
        
        # Case 2: Header count mismatch
        count_mismatch_response = SheetData(
            range="'Sheet1'!A1:Z1",
            values=[["Header1", "Header2"]]  # Missing a header
        )
        
        # Case 3: Header text mismatch
        text_mismatch_response = SheetData(
            range="'Sheet1'!A1:Z1",
            values=[["Header1", "Changed!", "Header3"]]  # Second header changed
        )
        
        # Case 4: No data returned
        empty_response = SheetData(
            range="'Sheet1'!A1:Z1",
            values=[]
        )
        
        # Test success case
        mock_service.get_sheet_data.return_value = success_response
        self.assertTrue(verify_headers_unchanged(mock_service, "Sheet1", original_headers))
        
        # Test header count mismatch
        mock_service.get_sheet_data.return_value = count_mismatch_response
        self.assertFalse(verify_headers_unchanged(mock_service, "Sheet1", original_headers))
        
        # Test header text mismatch
        mock_service.get_sheet_data.return_value = text_mismatch_response
        self.assertFalse(verify_headers_unchanged(mock_service, "Sheet1", original_headers))
        
        # Test empty response
        mock_service.get_sheet_data.return_value = empty_response
        self.assertFalse(verify_headers_unchanged(mock_service, "Sheet1", original_headers))
        
        # Test exception case
        mock_service.get_sheet_data.side_effect = Exception("API error")
        self.assertFalse(verify_headers_unchanged(mock_service, "Sheet1", original_headers))


