# Testing Best Practices 🧪

## What Tests Should Be

Tests are **examples of how your code should behave**. Nothing more, nothing less.

### Core Principles
1. **Simple** - Easy to read and understand
2. **Fast** - Run in milliseconds 
3. **Focused** - Test one behavior at a time
4. **Clear** - Obvious what passed/failed
5. **Maintainable** - Less test code than actual code

## Test Structure

### AAA Pattern (Arrange-Act-Assert)
```python
def test_valid_registration_number():
    # Arrange
    regno = "AB1234567890123"
    
    # Act
    result = validate_regno(regno)
    
    # Assert
    assert result is None
```

### Test Naming Convention
- `test_[what_you're_testing]_[expected_behavior]`
- Examples:
  - `test_valid_regno_returns_none`
  - `test_empty_regno_returns_error`
  - `test_wrong_length_rejected`

## What Makes a Good Test

### ✅ DO
- **One assertion per test** (usually)
- **Descriptive test names** that explain the behavior
- **Simple error messages** with actual vs expected
- **Test edge cases** (empty, null, boundary values)
- **Use meaningful test data**

### ❌ DON'T
- **Long error messages** with code samples
- **Teaching in tests** - documentation belongs elsewhere
- **Complex setup** - keep it simple
- **Testing implementation** - test behavior instead
- **Massive test classes** - break them down

## Example: Good vs Bad Tests

### ❌ BAD (Overkill)
```python
def test_valid_regno_passes(self):
    """Long docstring explaining everything..."""
    print("🧪 TESTING: Valid registration number formats")
    
    if error is not None:
        pytest.fail(f"""
🔴 VALID REGNO REJECTED - Here's how to fix it:
[20 lines of code templates and explanations]
        """)
```

### ✅ GOOD (Simple)
```python
def test_valid_regno_accepted():
    """Valid registration numbers should be accepted"""
    assert validate_regno("AB1234567890123") is None
    assert validate_regno("XY9876543210987") is None

def test_empty_regno_rejected():
    """Empty registration number should be rejected"""
    error = validate_regno("")
    assert error is not None
    assert "required" in error.lower()
```

## Test Organization

### File Structure
```
tests/
├── unit/                    # Fast, isolated tests
│   ├── test_validation.py   # Input validation
│   ├── test_auth.py         # Authentication logic
│   └── test_models.py       # Data models
├── integration/             # Multi-component tests
│   └── test_api.py          # API endpoint tests
└── conftest.py              # Shared test setup
```

### Test Classes (Optional)
Group related tests, but keep them small:
```python
class TestRegnoValidation:
    def test_valid_format_accepted(self):
        assert validate_regno("AB1234567890123") is None
    
    def test_wrong_length_rejected(self):
        assert validate_regno("AB123") is not None
```

## Test Data Strategy

### Use Meaningful Examples
```python
# Good - real-world examples
valid_regnos = ["AB1234567890123", "XY9876543210987"]

# Bad - meaningless data  
valid_regnos = ["XX0000000000000", "AA1111111111111"]
```

### Edge Cases to Test
- **Empty/null inputs**
- **Boundary values** (min/max lengths)
- **Invalid formats**
- **Special characters**
- **Unicode/encoding issues**

## Error Messages in Tests

### ✅ Good Error Messages
```python
assert result is None, f"Valid regno '{regno}' was rejected: {result}"
assert error is not None, f"Invalid regno '{regno}' was accepted"
assert "uppercase" in error, f"Error message unclear: {error}"
```

### ❌ Bad Error Messages
```python
pytest.fail("""
🔴 MASSIVE ERROR MESSAGE WITH:
- Code templates
- Step-by-step instructions
- Multiple implementation options
- Documentation that belongs elsewhere
""")
```

## When Tests Fail

### What You Should See
```
FAILED test_validation.py::test_empty_regno_rejected
assert None is not None
AssertionError: Invalid regno '' was accepted
```

### What You Should Do
1. **Read the test name** - tells you what should happen
2. **Look at the test code** - shows you the expected behavior
3. **Fix your implementation** - make the test pass
4. **Re-run the test** - verify it works

## Test Coverage Goals

### Focus Areas
- **Happy path** - normal, valid inputs
- **Error cases** - invalid inputs and edge cases
- **Business rules** - critical logic and constraints
- **Security** - authentication, authorization, validation

### Don't Test
- **Third-party libraries** - assume they work
- **Framework code** - focus on your business logic
- **Trivial getters/setters** - unless they have logic
- **Private implementation details** - test public behavior

## Integration with Development

### TDD Workflow
1. **Write a failing test** for new functionality
2. **Write minimal code** to make it pass
3. **Refactor** while keeping tests green
4. **Repeat** for next requirement

### Running Tests
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_validation.py

# Run with verbose output
uv run pytest -v

# Run specific test
uv run pytest tests/unit/test_validation.py::test_valid_regno_accepted
```

## Summary

**Tests should be boring.** If your tests are more interesting than your actual code, you're doing it wrong.

Keep them simple, focused, and maintainable. Let the tests guide your implementation, but don't let them become more complex than the code they're testing.
