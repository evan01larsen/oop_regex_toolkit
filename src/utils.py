from typing import List, Dict, Optional, Union, Tuple
import re
from functools import lru_cache
from dataclasses import dataclass
import string
import unicodedata

@dataclass
class RegexSyntaxTransformation:
    """Represents a transformation of regex syntax from one format to another"""
    original: str
    transformed: str
    description: str

class RegexUtils:
    """Utility functions for regex pattern manipulation and data cleaning"""
    
    # Common regex pattern components
    COMMON_PATTERNS = {
        'username': r'^[a-zA-Z0-9_-]{3,16}$',
        'password': r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$',
        'hex_color': r'^#?([a-fA-F0-9]{6}|[a-fA-F0-9]{3})$',
        'ipv4': r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
        'time_24h': r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
    }
    
    # Syntax transformations for different regex flavors
    SYNTAX_TRANSFORMS = {
        'python_to_js': [
            RegexSyntaxTransformation(r'(?P<name>...)', r'(?<name>...)', 'Named capture group'),
            RegexSyntaxTransformation(r'\A', r'^', 'Start of string'),
            RegexSyntaxTransformation(r'\Z', r'$', 'End of string')
        ],
        'js_to_python': [
            RegexSyntaxTransformation(r'(?<name>...)', r'(?P<name>...)', 'Named capture group'),
            RegexSyntaxTransformation(r'^', r'\A', 'Start of string'),
            RegexSyntaxTransformation(r'$', r'\Z', 'End of string')
        ]
    }

    @staticmethod
    def clean_input(text: str, preserve_case: bool = False) -> str:
        """
        Clean input text by removing unwanted characters and normalizing whitespace
        
        Args:
            text: Input text to clean
            preserve_case: Whether to preserve original case
            
        Returns:
            Cleaned text string
        """
        # Normalize unicode characters
        text = unicodedata.normalize('NFKD', text)
        
        # Remove non-printable characters
        text = ''.join(char for char in text if char in string.printable)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        if not preserve_case:
            text = text.lower()
            
        return text

    @staticmethod
    @lru_cache(maxsize=128)
    def escape_special_chars(pattern: str) -> str:
        """
        Escape special regex characters in a pattern
        
        Args:
            pattern: Pattern string to escape
            
        Returns:
            Escaped pattern string
        """
        special_chars = '.^$*+?{}[]\\|()'
        return ''.join('\\' + char if char in special_chars else char for char in pattern)

    @staticmethod
    def transform_syntax(pattern: str, from_flavor: str, to_flavor: str) -> str:
        """
        Transform regex syntax between different regex flavors
        
        Args:
            pattern: Original pattern string
            from_flavor: Source regex flavor ('python' or 'js')
            to_flavor: Target regex flavor ('python' or 'js')
            
        Returns:
            Transformed pattern string
        """
        transform_key = f'{from_flavor}_to_{to_flavor}'
        if transform_key in RegexUtils.SYNTAX_TRANSFORMS:
            result = pattern
            for transform in RegexUtils.SYNTAX_TRANSFORMS[transform_key]:
                result = result.replace(transform.original, transform.transformed)
            return result
        return pattern

    @staticmethod
    def extract_pattern_components(pattern: str) -> List[Tuple[str, str]]:
        """
        Extract and categorize components of a regex pattern
        
        Args:
            pattern: Regex pattern to analyze
            
        Returns:
            List of tuples containing (component, category)
        """
        components = []
        current = ''
        category = ''
        
        i = 0
        while i < len(pattern):
            if pattern[i] == '\\':
                if i + 1 < len(pattern):
                    current = pattern[i:i+2]
                    category = 'escape_sequence'
                    i += 2
            elif pattern[i] in '[]':
                j = i + 1
                while j < len(pattern) and pattern[j] != ']':
                    j += 1
                current = pattern[i:j+1]
                category = 'character_class'
                i = j + 1
            elif pattern[i] in '()':
                j = i + 1
                depth = 1
                while j < len(pattern) and depth > 0:
                    if pattern[j] == '(':
                        depth += 1
                    elif pattern[j] == ')':
                        depth -= 1
                    j += 1
                current = pattern[i:j]
                category = 'group'
                i = j
            else:
                current = pattern[i]
                category = 'literal' if pattern[i] not in '.^$*+?{}|' else 'metacharacter'
                i += 1
            
            if current:
                components.append((current, category))
                current = ''
                
        return components

    @staticmethod
    def simplify_pattern(pattern: str) -> str:
        """
        Simplify a regex pattern by removing unnecessary components
        
        Args:
            pattern: Pattern to simplify
            
        Returns:
            Simplified pattern string
        """
        # Remove unnecessary non-capturing groups
        pattern = re.sub(r'\(\?:[^()]+\)', lambda m: m.group()[3:-1], pattern)
        
        # Remove redundant character classes
        pattern = re.sub(r'\[([a-zA-Z0-9])\]', r'\1', pattern)
        
        # Simplify multiple consecutive wildcards
        pattern = re.sub(r'\*+', '*', pattern)
        pattern = re.sub(r'\++', '+', pattern)
        pattern = re.sub(r'\?+', '?', pattern)
        
        return pattern

    @staticmethod
    def is_valid_pattern(pattern: str) -> bool:
        """
        Check if a pattern is valid regex syntax
        
        Args:
            pattern: Pattern to validate
            
        Returns:
            True if pattern is valid, False otherwise
        """
        try:
            re.compile(pattern)
            return True
        except re.error:
            return False

    @staticmethod
    def get_common_pattern(pattern_name: str) -> Optional[str]:
        """
        Get a common regex pattern by name
        
        Args:
            pattern_name: Name of the common pattern
            
        Returns:
            Pattern string if found, None otherwise
        """
        return RegexUtils.COMMON_PATTERNS.get(pattern_name)

    @staticmethod
    def merge_patterns(patterns: List[str], join_type: str = 'AND') -> str:
        """
        Merge multiple patterns into a single pattern
        
        Args:
            patterns: List of patterns to merge
            join_type: Type of join ('AND' or 'OR')
            
        Returns:
            Merged pattern string
        """
        if not patterns:
            return ''
            
        if join_type == 'OR':
            return '|'.join(f'({p})' for p in patterns)
        else:  # AND
            return ''.join(f'(?={p})' for p in patterns)