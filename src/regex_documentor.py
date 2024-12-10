import re
from typing import List, Tuple, Dict
from dataclasses import dataclass
import sre_parse
import sre_constants

@dataclass
class RegexComponent:
    """Represents a component of a regex pattern with its explanation"""
    pattern: str
    explanation: str
    start_pos: int
    end_pos: int

class RegexDocumenter:
    """Documents regex patterns by breaking them down into plain English explanations"""
    
    SPECIAL_CHARS = {
        '^': 'start of string',
        '$': 'end of string',
        '.': 'any character except newline',
        '*': 'zero or more times',
        '+': 'one or more times',
        '?': 'zero or one time',
        '\\d': 'digit',
        '\\D': 'non-digit',
        '\\w': 'word character',
        '\\W': 'non-word character',
        '\\s': 'whitespace',
        '\\S': 'non-whitespace',
        '\\b': 'word boundary',
        '\\B': 'non-word boundary'
    }

    QUANTIFIER_DESC = {
        '*': 'zero or more times',
        '+': 'one or more times',
        '?': 'optionally',
        '{m,n}': 'between {m} and {n} times',
        '{m}': 'exactly {m} times',
        '{m,}': 'at least {m} times'
    }

    def __init__(self):
        self.components: List[RegexComponent] = []

    def document_pattern(self, pattern: str) -> str:
        """
        Breaks down a regex pattern into plain English explanation
        
        Args:
            pattern: The regex pattern to document
            
        Returns:
            A detailed explanation of the pattern in plain English
        """
        try:
            # Parse the pattern
            parsed = sre_parse.parse(pattern)
            self.components = []
            self._process_parsed_pattern(parsed, 0)
            
            # Generate the complete documentation
            full_doc = f"Pattern: {pattern}\n\nBreakdown:\n"
            
            # Add component-wise explanation
            for i, comp in enumerate(sorted(self.components, key=lambda x: x.start_pos), 1):
                full_doc += f"\n{i}. {comp.explanation}"
                if i < len(self.components):
                    full_doc += "\n"
            
            return full_doc
            
        except (re.error, sre_constants.error) as e:
            return f"Error: Invalid regex pattern - {str(e)}"

    def _process_parsed_pattern(self, parsed, start_pos: int = 0) -> int:
        """
        Recursively processes the parsed regex pattern
        
        Args:
            parsed: The parsed regex pattern
            start_pos: Current position in the pattern
            
        Returns:
            The ending position after processing
        """
        current_pos = start_pos
        
        for op, args in parsed:
            if op == sre_constants.LITERAL:
                char = chr(args)
                self.components.append(RegexComponent(
                    char,
                    f"Match the literal character '{char}'",
                    current_pos,
                    current_pos + 1
                ))
                current_pos += 1
                
            elif op == sre_constants.ANY:
                self.components.append(RegexComponent(
                    '.',
                    "Match any character except newline",
                    current_pos,
                    current_pos + 1
                ))
                current_pos += 1
                
            elif op == sre_constants.IN:
                charset, length = self._process_charset(args)
                self.components.append(RegexComponent(
                    charset,
                    f"Match {self._describe_charset(args)}",
                    current_pos,
                    current_pos + length
                ))
                current_pos += length
                
            elif op == sre_constants.MAX_REPEAT or op == sre_constants.MIN_REPEAT:
                min_count, max_count, item = args
                quantifier = self._get_quantifier_str(min_count, max_count)
                sub_pattern, length = self._get_subpattern(item)
                
                self.components.append(RegexComponent(
                    f"{sub_pattern}{quantifier}",
                    f"Match {self._describe_subpattern(item)} {self._describe_quantifier(min_count, max_count)}",
                    current_pos,
                    current_pos + length + len(quantifier)
                ))
                current_pos += length + len(quantifier)
                
            elif op == sre_constants.AT:
                anchor = self._describe_anchor(args)
                self.components.append(RegexComponent(
                    anchor['symbol'],
                    anchor['description'],
                    current_pos,
                    current_pos + len(anchor['symbol'])
                ))
                current_pos += len(anchor['symbol'])

        return current_pos

    def _process_charset(self, charset) -> Tuple[str, int]:
        """Process a character set and return its string representation and length"""
        result = []
        length = 0
        
        for item in charset:
            if isinstance(item, tuple):
                op, args = item
                if op == sre_constants.LITERAL:
                    result.append(chr(args))
                    length += 1
                elif op == sre_constants.RANGE:
                    start, end = args
                    result.append(f"{chr(start)}-{chr(end)}")
                    length += 3
            else:
                result.append(str(item))
                length += len(str(item))
                
        return f"[{''.join(result)}]", length + 2

    def _describe_charset(self, charset) -> str:
        """Generate a description for a character set"""
        parts = []
        
        for item in charset:
            if isinstance(item, tuple):
                op, args = item
                if op == sre_constants.LITERAL:
                    parts.append(f"'{chr(args)}'")
                elif op == sre_constants.RANGE:
                    start, end = args
                    parts.append(f"any character from '{chr(start)}' to '{chr(end)}'")
            else:
                parts.append(str(item))
                
        return f"any of: {', '.join(parts)}"

    def _get_quantifier_str(self, min_count: int, max_count: int) -> str:
        """Convert min and max counts to quantifier string"""
        if min_count == 0 and max_count == sre_constants.MAXREPEAT:
            return '*'
        elif min_count == 1 and max_count == sre_constants.MAXREPEAT:
            return '+'
        elif min_count == 0 and max_count == 1:
            return '?'
        elif min_count == max_count:
            return f"{{{min_count}}}"
        elif max_count == sre_constants.MAXREPEAT:
            return f"{{{min_count},}}"
        else:
            return f"{{{min_count},{max_count}}}"

    def _describe_quantifier(self, min_count: int, max_count: int) -> str:
        """Generate a description for a quantifier"""
        quantifier = self._get_quantifier_str(min_count, max_count)
        desc = self.QUANTIFIER_DESC.get(quantifier, '')
        
        if not desc:
            if '{' in quantifier:
                nums = quantifier[1:-1].split(',')
                if len(nums) == 1:
                    desc = f"exactly {nums[0]} times"
                elif nums[1] == '':
                    desc = f"at least {nums[0]} times"
                else:
                    desc = f"between {nums[0]} and {nums[1]} times"
                    
        return desc

    def _get_subpattern(self, item) -> Tuple[str, int]:
        """Process a subpattern and return its string representation and length"""
        if isinstance(item, tuple):
            op, args = item
            if isinstance(args, tuple):
                return str(args[0]), len(str(args[0]))
        return str(item), len(str(item))

    def _describe_subpattern(self, item) -> str:
        """Generate a description for a subpattern"""
        if isinstance(item, tuple):
            op, args = item
            if isinstance(args, tuple):
                return f"the pattern '{args[0]}'"
        return f"the pattern '{item}'"

    def _describe_anchor(self, anchor) -> Dict[str, str]:
        """Generate a description for an anchor"""
        anchors = {
            sre_constants.AT_BEGINNING: {'symbol': '^', 'description': 'Match at the start of the string'},
            sre_constants.AT_END: {'symbol': '$', 'description': 'Match at the end of the string'},
            sre_constants.AT_BOUNDARY: {'symbol': '\\b', 'description': 'Match at a word boundary'},
            sre_constants.AT_NON_BOUNDARY: {'symbol': '\\B', 'description': 'Match at a non-word boundary'}
        }
        return anchors.get(anchor, {'symbol': '', 'description': 'Unknown anchor'})

def main():
    # Example usage
    documenter = RegexDocumenter()
    
    test_patterns = [
        r'^\d{3}-\d{2}-\d{4}$',
        r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',
        r'(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?'
    ]
    
    for pattern in test_patterns:
        print(documenter.document_pattern(pattern))
        print("\n" + "="*50 + "\n")

if __name__ == '__main__':
    main()