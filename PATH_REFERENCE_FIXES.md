# API Key Setup Path Reference Fixes

## Date: 2026-01-28

## Issue
Error messages in `pdf_generator/ai_service.py` and `pdf_generator/test_api_key.py` were referencing `docs/API_KEY_SETUP.md`, which would be resolved as `/home/lnz/DEV/clima-scope/docs/API_KEY_SETUP.md` - a location where the file doesn't exist.

The actual file location is: `pdf_generator/docs/API_KEY_SETUP.md`

## Fixes Applied

### 1. pdf_generator/ai_service.py

Updated two error messages in the `_get_api_key()` method:

**Line 58 (OPENAI_API_KEY error):**
- Before: `"See docs/API_KEY_SETUP.md for instructions."`
- After: `"See pdf_generator/docs/API_KEY_SETUP.md for instructions."`

**Line 67 (ANTHROPIC_API_KEY error):**
- Before: `"See docs/API_KEY_SETUP.md for instructions."`
- After: `"See pdf_generator/docs/API_KEY_SETUP.md for instructions."`

### 2. pdf_generator/test_api_key.py

Updated help text in the API key not found error message:

**Line 46:**
- Before: `print("See docs/API_KEY_SETUP.md for detailed instructions.")`
- After: `print("See pdf_generator/docs/API_KEY_SETUP.md for detailed instructions.")`

## Verification

✅ Confirmed file exists at: `/home/lnz/DEV/clima-scope/pdf_generator/docs/API_KEY_SETUP.md`
✅ All 3 references updated to use correct path: `pdf_generator/docs/API_KEY_SETUP.md`
✅ Grepped codebase to verify all instances updated

## Impact

Users encountering API key configuration errors will now be directed to the correct documentation location, regardless of which directory they're running the scripts from.

## Files Modified

1. `pdf_generator/ai_service.py` - Lines 58, 67
2. `pdf_generator/test_api_key.py` - Line 46

No other files reference these error messages.
