"""
Test suite for MessageWindow and MessageCapture functionality in pyptv_gui.py

This module tests the message logging system that captures print statements
and displays them in the GUI with timestamp functionality and save capabilities.
"""

import pytest
import sys
import io
import os
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the classes to test
from pyptv.pyptv_gui import MessageWindow, MessageCapture


class TestMessageWindow:
    """Test cases for MessageWindow class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.message_window = MessageWindow()
    
    def test_message_window_initialization(self):
        """Test that MessageWindow initializes with correct default values"""
        assert self.message_window.messages == ""
        assert self.message_window.max_lines == 1000
        assert self.message_window.auto_scroll is True
        # Check that button methods exist (they're created as trait methods)
        assert hasattr(self.message_window, '_clear_button_fired')
        assert hasattr(self.message_window, '_save_button_fired')
    
    def test_add_message_single(self):
        """Test adding a single message"""
        test_message = "Test message 1"
        self.message_window.add_message(test_message)
        
        # Check that message was added with timestamp
        assert test_message in self.message_window.messages
        assert "[" in self.message_window.messages  # Timestamp format
        assert "]" in self.message_window.messages
    
    def test_add_message_multiple(self):
        """Test adding multiple messages"""
        messages = ["Message 1", "Message 2", "Message 3"]
        
        for msg in messages:
            self.message_window.add_message(msg)
        
        # Check all messages are present
        for msg in messages:
            assert msg in self.message_window.messages
        
        # Check that messages are separated by newlines
        lines = self.message_window.messages.split('\n')
        assert len(lines) == 3
    
    def test_add_empty_message(self):
        """Test that empty messages are not added"""
        self.message_window.add_message("")
        self.message_window.add_message("   ")  # Whitespace only
        
        assert self.message_window.messages == ""
    
    def test_message_line_limit(self):
        """Test that message line limit is enforced"""
        # Set a small max_lines for testing
        self.message_window.max_lines = 3
        
        # Add more messages than the limit
        for i in range(5):
            self.message_window.add_message(f"Message {i+1}")
        
        lines = self.message_window.messages.split('\n')
        assert len(lines) == 3
        
        # Check that only the last 3 messages remain
        assert "Message 3" in self.message_window.messages
        assert "Message 4" in self.message_window.messages
        assert "Message 5" in self.message_window.messages
        assert "Message 1" not in self.message_window.messages
        assert "Message 2" not in self.message_window.messages
    
    def test_clear_messages(self):
        """Test clearing all messages"""
        # Add some messages first
        self.message_window.add_message("Message 1")
        self.message_window.add_message("Message 2")
        assert self.message_window.messages != ""
        
        # Clear messages
        self.message_window.clear_messages()
        assert self.message_window.messages == ""
    
    def test_clear_button_fired(self):
        """Test the clear button callback"""
        # Add some messages
        self.message_window.add_message("Test message")
        assert self.message_window.messages != ""
        
        # Trigger clear button
        self.message_window._clear_button_fired()
        assert self.message_window.messages == ""
    
    def test_save_log_no_messages(self):
        """Test saving log when there are no messages"""
        with patch('builtins.print') as mock_print:
            self.message_window.save_log()
            mock_print.assert_called_with("No messages to save")
    
    def test_save_log_with_messages(self):
        """Test saving log with messages to file"""
        # Add test messages
        test_messages = ["Test message 1", "Test message 2"]
        for msg in test_messages:
            self.message_window.add_message(msg)
        
        # Use temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                with patch('builtins.print') as mock_print:
                    self.message_window.save_log()
                
                # Check that print was called with success message
                mock_print.assert_called()
                call_args = str(mock_print.call_args)
                assert "Log saved to:" in call_args
                assert "pyptv_session_log_" in call_args
                
                # Check that file was created
                log_files = list(Path(temp_dir).glob("pyptv_session_log_*.txt"))
                assert len(log_files) == 1
                
                # Check file contents
                with open(log_files[0], 'r') as f:
                    content = f.read()
                    assert "PyPTV Session Log" in content
                    assert "Test message 1" in content
                    assert "Test message 2" in content
                    assert "=" * 60 in content
            finally:
                os.chdir(original_cwd)
    
    def test_save_button_fired(self):
        """Test the save button callback"""
        # Add a test message
        self.message_window.add_message("Test message for save")
        
        # Mock the save_log method
        with patch.object(self.message_window, 'save_log') as mock_save:
            self.message_window._save_button_fired()
            mock_save.assert_called_once()
    
    def test_timestamp_format(self):
        """Test that timestamps are in correct format"""
        test_message = "Timestamp test message"
        self.message_window.add_message(test_message)
        
        lines = self.message_window.messages.split('\n')
        assert len(lines) == 1
        
        # Check timestamp format [HH:MM:SS]
        line = lines[0]
        assert line.startswith('[')
        timestamp_end = line.find(']')
        assert timestamp_end > 0
        
        timestamp_str = line[1:timestamp_end]
        # Verify timestamp format (HH:MM:SS)
        try:
            datetime.strptime(timestamp_str, "%H:%M:%S")
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {timestamp_str}")


class TestMessageCapture:
    """Test cases for MessageCapture class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.message_window = MessageWindow()
        self.message_capture = MessageCapture(self.message_window)
        self.original_stdout = sys.stdout
    
    def teardown_method(self):
        """Clean up after each test"""
        # Restore original stdout
        sys.stdout = self.original_stdout
    
    def test_message_capture_initialization(self):
        """Test MessageCapture initialization"""
        assert self.message_capture.message_window is self.message_window
        assert self.message_capture.original_stdout is sys.stdout
        assert self.message_capture.original_stderr is sys.stderr
        assert hasattr(self.message_capture, 'buffer')
    
    def test_write_to_capture(self):
        """Test writing text to message capture"""
        test_text = "Test output message"
        
        # Capture both stdout and message window
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.message_capture.original_stdout = mock_stdout
            self.message_capture.write(test_text)
            
            # Check that text was written to stdout
            assert test_text in mock_stdout.getvalue()
        
        # Check that message was added to message window
        assert test_text in self.message_window.messages
    
    def test_write_empty_text(self):
        """Test writing empty text"""
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.message_capture.original_stdout = mock_stdout
            self.message_capture.write("")
            
            # Empty text should still be written to stdout
            assert mock_stdout.getvalue() == ""
        
        # But should not add empty message to window
        assert self.message_window.messages == ""
    
    def test_flush_method(self):
        """Test the flush method"""
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            mock_stdout.flush = MagicMock()
            self.message_capture.original_stdout = mock_stdout
            
            self.message_capture.flush()
            mock_stdout.flush.assert_called_once()
    
    def test_stdout_redirection(self):
        """Test that stdout redirection works properly"""
        # Replace stdout with message capture
        sys.stdout = self.message_capture
        
        try:
            # Test printing
            print("Test stdout redirection")
            
            # Check that message was captured
            assert "Test stdout redirection" in self.message_window.messages
            
        finally:
            # Restore stdout
            sys.stdout = self.original_stdout


class TestMessageWindowIntegration:
    """Integration tests for MessageWindow and MessageCapture working together"""
    
    def setup_method(self):
        """Set up integration test fixtures"""
        self.message_window = MessageWindow()
        self.message_capture = MessageCapture(self.message_window)
        self.original_stdout = sys.stdout
    
    def teardown_method(self):
        """Clean up after integration tests"""
        sys.stdout = self.original_stdout
    
    def test_full_integration(self):
        """Test full integration of message capture and display"""
        # Set up stdout redirection
        sys.stdout = self.message_capture
        
        try:
            # Test various print statements
            print("Starting PyPTV session")
            print("Loading parameters...")
            print("Processing images")
            print("Detection finished")
            
            # Check that all messages were captured
            messages = self.message_window.messages
            assert "Starting PyPTV session" in messages
            assert "Loading parameters..." in messages
            assert "Processing images" in messages
            assert "Detection finished" in messages
            
            # Check that messages have timestamps
            lines = messages.split('\n')
            assert len(lines) == 4
            for line in lines:
                assert line.startswith('[')
                assert ']' in line
            
        finally:
            sys.stdout = self.original_stdout
    
    def test_save_captured_log(self):
        """Test saving a log with captured messages"""
        # Set up stdout redirection
        sys.stdout = self.message_capture
        
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                # Generate some log messages
                print("Test message 1")
                print("Test message 2")
                print("Test message 3")
                
                # Save the log
                with patch('builtins.print') as mock_print:
                    self.message_window.save_log()
                
                # Verify file was created and contains messages
                log_files = list(Path(temp_dir).glob("pyptv_session_log_*.txt"))
                assert len(log_files) == 1
                
                with open(log_files[0], 'r') as f:
                    content = f.read()
                    assert "Test message 1" in content
                    assert "Test message 2" in content
                    assert "Test message 3" in content
                    assert "PyPTV Session Log" in content
                
            finally:
                os.chdir(original_cwd)
                sys.stdout = self.original_stdout


@pytest.mark.parametrize("max_lines,num_messages,expected_lines", [
    (5, 3, 3),     # Less messages than limit
    (5, 5, 5),     # Equal to limit
    (5, 8, 5),     # More messages than limit
    (1, 3, 1),     # Very small limit
])
def test_message_line_limits(max_lines, num_messages, expected_lines):
    """Parametrized test for message line limits"""
    window = MessageWindow()
    window.max_lines = max_lines
    
    for i in range(num_messages):
        window.add_message(f"Message {i+1}")
    
    actual_lines = len(window.messages.split('\n')) if window.messages else 0
    assert actual_lines == expected_lines


def test_message_window_usage_example():
    """
    Example test demonstrating typical usage of MessageWindow system
    This shows how the message capture system would be used in PyPTV
    """
    # Set up the message system like in the actual GUI
    message_window = MessageWindow()
    message_capture = MessageCapture(message_window)
    
    # Store original stdout
    original_stdout = sys.stdout
    
    try:
        # Redirect stdout to capture messages (like in MainGUI.__init__)
        sys.stdout = message_capture
        
        # Simulate typical PyPTV operations that print status messages
        print("PyPTV session started")
        print("Loading experiment parameters...")
        print("Initializing cameras...")
        print("Reading calibration files...")
        print("Detection processing started")
        print("Found 150 particles in frame 1")
        print("Found 142 particles in frame 2") 
        print("Correspondence analysis completed")
        print("3D reconstruction finished")
        print("Tracking completed successfully")
        
        # Verify all messages were captured with timestamps
        messages = message_window.messages
        expected_phrases = [
            "PyPTV session started",
            "Loading experiment parameters",
            "Initializing cameras",
            "Reading calibration files", 
            "Detection processing started",
            "Found 150 particles",
            "Found 142 particles",
            "Correspondence analysis completed",
            "3D reconstruction finished",
            "Tracking completed successfully"
        ]
        
        for phrase in expected_phrases:
            assert phrase in messages, f"Expected phrase '{phrase}' not found in messages"
        
        # Verify timestamp format in each line
        lines = messages.split('\n')
        assert len(lines) == 10  # Should have 10 lines for 10 print statements
        
        for line in lines:
            # Each line should start with [HH:MM:SS] timestamp
            assert line.startswith('['), f"Line doesn't start with timestamp: {line}"
            timestamp_end = line.find(']')
            assert timestamp_end > 0, f"No closing bracket found in line: {line}"
            
            # Extract and validate timestamp format
            timestamp_str = line[1:timestamp_end]
            try:
                datetime.strptime(timestamp_str, "%H:%M:%S")
            except ValueError:
                pytest.fail(f"Invalid timestamp format '{timestamp_str}' in line: {line}")
        
        # Test clearing messages
        message_window.clear_messages()
        assert message_window.messages == ""
        
        # Test that new messages can be added after clearing
        print("New message after clear")
        assert "New message after clear" in message_window.messages
        
    finally:
        # Always restore original stdout
        sys.stdout = original_stdout


if __name__ == "__main__":
    pytest.main([__file__])
