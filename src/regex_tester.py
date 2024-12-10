import re
from typing import Optional, List, Dict, Union, Pattern
from dataclasses import dataclass
from enum import Enum, auto

class RegexError(Exception):
    """Custom exception for regex-related errors"""
    pass

class PatternType(Enum):
    """Enum defining common regex pattern types"""
    EMAIL = auto()
    PHONE = auto()
    URL = auto()
    DATE = auto()
    CUSTOM = auto()

@dataclass
class MatchResult:
    """Data class to store regex match results"""
    matched: bool
    value: str
    groups: tuple = ()
    span: tuple = ()
    named_groups: dict = None

class RegexValidator:
    """Class for validating and managing regex patterns"""
    
    _PREDEFINED_PATTERNS = {
        PatternType.EMAIL: r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        PatternType.PHONE: r'^\+?1?\d{9,15}$',
        PatternType.URL: r'^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$',
        PatternType.DATE: r'^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$'
    }

    def __init__(self):
        self.compiled_patterns: Dict[str, Pattern] = {}

    def validate_pattern(self, pattern: str) -> bool:
        """Validate if a regex pattern is syntactically correct"""
        try:
            re.compile(pattern)
            return True
        except re.error:
            return False

    def get_predefined_pattern(self, pattern_type: PatternType) -> str:
        """Get a predefined pattern by type"""
        if pattern_type == PatternType.CUSTOM:
            raise RegexError("Custom pattern type requires a pattern string")
        return self._PREDEFINED_PATTERNS.get(pattern_type)

class RegexCompiler:
    """Class for compiling and caching regex patterns"""
    
    def __init__(self):
        self._cache: Dict[str, Pattern] = {}

    def compile_pattern(self, pattern: str, flags: int = 0) -> Pattern:
        """Compile a pattern and cache it"""
        cache_key = f"{pattern}_{flags}"
        if cache_key not in self._cache:
            try:
                self._cache[cache_key] = re.compile(pattern, flags)
            except re.error as e:
                raise RegexError(f"Invalid regex pattern: {str(e)}")
        return self._cache[cache_key]

    def clear_cache(self):
        """Clear the pattern cache"""
        self._cache.clear()

class RegexMatcher:
    """Class for performing regex matches and extracting information"""
    
    def __init__(self):
        self.compiler = RegexCompiler()

    def match(self, pattern: str, text: str, flags: int = 0) -> MatchResult:
        """Perform a regex match and return structured results"""
        compiled_pattern = self.compiler.compile_pattern(pattern, flags)
        match = compiled_pattern.match(text)
        
        if match:
            return MatchResult(
                matched=True,
                value=match.group(),
                groups=match.groups(),
                span=match.span(),
                named_groups=match.groupdict()
            )
        return MatchResult(matched=False, value="")

    def find_all(self, pattern: str, text: str, flags: int = 0) -> List[MatchResult]:
        """Find all matches in the text"""
        compiled_pattern = self.compiler.compile_pattern(pattern, flags)
        matches = compiled_pattern.finditer(text)
        
        return [
            MatchResult(
                matched=True,
                value=match.group(),
                groups=match.groups(),
                span=match.span(),
                named_groups=match.groupdict()
            )
            for match in matches
        ]

    def replace(self, pattern: str, text: str, replacement: str, flags: int = 0) -> str:
        """Replace matches with the replacement string"""
        compiled_pattern = self.compiler.compile_pattern(pattern, flags)
        return compiled_pattern.sub(replacement, text)

# Example usage
def main():
    # Create instances
    validator = RegexValidator()
    matcher = RegexMatcher()

    # Example pattern and text
    pattern = r"(\w+)@(\w+)\.(\w+)"
    text = "Contact us at: john@example.com and jane@company.org"

    # Validate pattern
    if validator.validate_pattern(pattern):
        # Find all matches
        matches = matcher.find_all(pattern, text)
        
        # Process matches
        for match in matches:
            print(f"Match found: {match.value}")
            print(f"Groups: {match.groups}")
            print(f"Span: {match.span}")
            print("---")

    # Using predefined patterns
    email_pattern = validator.get_predefined_pattern(PatternType.EMAIL)
    email = "test@example.com"
    match_result = matcher.match(email_pattern, email)
    print(f"Valid email: {match_result.matched}")

if __name__ == "__main__":
    main()