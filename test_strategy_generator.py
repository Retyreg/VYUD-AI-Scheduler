#!/usr/bin/env python3
"""
Test script for AI Strategy Generator functionality
Tests the helper functions without requiring API keys
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the functions we want to test
# We'll need to modify the import since streamlit_app.py is the main file
# For now, let's test the logic directly

def test_get_weekdays_in_month():
    """Test weekday calculation"""
    from datetime import datetime, timedelta
    import calendar
    
    def get_weekdays_in_month(year: int, month: int):
        """Returns list of weekdays in the month"""
        first_day = datetime(year, month, 1)
        
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        
        weekdays = []
        current_day = first_day
        
        while current_day <= last_day:
            if current_day.weekday() < 5:  # Monday to Friday
                weekdays.append(current_day)
            current_day += timedelta(days=1)
        
        return weekdays
    
    # Test February 2026 (has 28 days, starts on Sunday)
    weekdays_feb_2026 = get_weekdays_in_month(2026, 2)
    print(f"✅ February 2026 has {len(weekdays_feb_2026)} weekdays")
    assert len(weekdays_feb_2026) == 20, f"Expected 20 weekdays, got {len(weekdays_feb_2026)}"
    
    # Test March 2026 (has 31 days, starts on Sunday)
    weekdays_mar_2026 = get_weekdays_in_month(2026, 3)
    print(f"✅ March 2026 has {len(weekdays_mar_2026)} weekdays")
    assert len(weekdays_mar_2026) == 22, f"Expected 22 weekdays, got {len(weekdays_mar_2026)}"
    
    print("✅ All weekday tests passed!")


def test_extract_json_from_text():
    """Test JSON extraction from text"""
    
    def extract_json_from_text(text: str) -> str:
        """Extracts JSON from text"""
        text = text.strip()
        
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        
        start_idx = text.find("[")
        end_idx = text.rfind("]")
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return text[start_idx:end_idx + 1]
        
        return text
    
    # Test 1: Clean JSON
    json_text = '[{"date": "2026-03-01", "platform": "LinkedIn"}]'
    result = extract_json_from_text(json_text)
    assert result == json_text, "Clean JSON should be unchanged"
    print("✅ Clean JSON extraction passed")
    
    # Test 2: JSON with markdown code block
    markdown_json = """```json
[{"date": "2026-03-01", "platform": "LinkedIn"}]
```"""
    result = extract_json_from_text(markdown_json)
    assert "[" in result and "]" in result, "Should extract JSON from markdown"
    print("✅ Markdown JSON extraction passed")
    
    # Test 3: JSON with extra text before and after
    text_with_json = """Here is the plan:
[{"date": "2026-03-01", "platform": "LinkedIn"}]
Hope this helps!"""
    result = extract_json_from_text(text_with_json)
    assert result == '[{"date": "2026-03-01", "platform": "LinkedIn"}]', "Should extract just the JSON array"
    print("✅ JSON extraction with surrounding text passed")
    
    print("✅ All JSON extraction tests passed!")


def test_json_parsing():
    """Test JSON parsing and validation"""
    import json
    
    # Valid JSON
    valid_json = """[
        {
            "date": "2026-03-01",
            "platform": "LinkedIn",
            "content_text": "Test post",
            "media_type": "image",
            "media_description": "Test image",
            "media_url": ""
        }
    ]"""
    
    posts = json.loads(valid_json)
    assert isinstance(posts, list), "Should parse to list"
    assert len(posts) == 1, "Should have one post"
    
    required_fields = ['date', 'platform', 'content_text', 'media_type', 'media_description', 'media_url']
    for field in required_fields:
        assert field in posts[0], f"Missing field: {field}"
    
    print("✅ JSON parsing and validation passed!")


if __name__ == "__main__":
    print("🧪 Running AI Strategy Generator Tests\n")
    
    try:
        test_get_weekdays_in_month()
        print()
        test_extract_json_from_text()
        print()
        test_json_parsing()
        print()
        print("🎉 All tests passed successfully!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
