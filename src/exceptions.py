import re
from typing import Pattern, Optional, Union
from dataclasses import dataclass

@dataclass
class RegexContext:
    """Context information for regex-related exceptions."""
    pattern: str
    input_string: Optional[str] = None
    position: Optional[int] = None
    message: Optional[str] = None

class RegexBaseError(Exception):
    """Base exception class for all regex-related errors."""
    def __init__(self, context: RegexContext):
        self.context = context
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Format the error message using context information."""
        msg = f"Error with pattern '{self.context.pattern}'"
        if self.context.message:
            msg += f": {self.context.message}"
        if self.context.input_string is not None:
            msg += f"\nInput string: '{self.context.input_string}'"
        if self.context.position is not None:
            msg += f"\nPosition: {self.context.position}"
        return msg

class InvalidRegexError(RegexBaseError):
    """Raised when a regex pattern is invalid."""
    pass

class PatternNotFoundError(RegexBaseError):
    """Raised when a pattern is not found in the input string."""
    pass

class EmptyPatternError(RegexBaseError):
    """Raised when an empty pattern is provided."""
    pass

def validate_regex(pattern: str) -> Union[Pattern, None]:
    """
    Validate a regex pattern and return the compiled pattern if valid.
    
    Args:
        pattern: The regex pattern to validate.
        
    Returns:
        Compiled regex pattern if valid.
        
    Raises:
        EmptyPatternError: If pattern is empty.
        InvalidRegexError: If pattern is invalid.
    """
    if not pattern:
        raise EmptyPatternError(RegexContext(pattern=pattern, message="Empty pattern provided"))
    
    try:
        return re.compile(pattern)
    except re.error as e:
        raise InvalidRegexError(RegexContext(
            pattern=pattern,
            message=str(e)
        ))

def find_pattern(pattern: str, text: str, raise_if_not_found: bool = True) -> Optional[str]:
    """
    Find a pattern in text and return the first match.
    
    Args:
        pattern: The regex pattern to search for.
        text: The text to search in.
        raise_if_not_found: Whether to raise an exception if pattern isn't found.
        
    Returns:
        The first match if found, None otherwise (if raise_if_not_found is False).
        
    Raises:
        PatternNotFoundError: If pattern isn't found and raise_if_not_found is True.
    """
    compiled_pattern = validate_regex(pattern)
    match = compiled_pattern.search(text)
    
    if match is None and raise_if_not_found:
        raise PatternNotFoundError(RegexContext(
            pattern=pattern,
            input_string=text,
            position=0,
            message="Pattern not found in input string"
        ))
    
    return match.group() if match else None

# Example usage:
if __name__ == "__main__":
    try:
        # Invalid regex pattern
        validate_regex("(unclosed parenthesis")
    except InvalidRegexError as e:
        print(f"Invalid regex error: {e}")
    
    try:
        # Pattern not found
        find_pattern(r"\d+", "no numbers here")
    except PatternNotFoundError as e:
        print(f"Pattern not found error: {e}")
    
    try:
        # Empty pattern
        validate_regex("")
    except EmptyPatternError as e:
        print(f"Empty pattern error: {e}")
    
    # Successful pattern matching
    result = find_pattern(r"\w+", "Hello, World!")
    print(f"Found pattern: {result}")  # Outputs: Found pattern: Hello