import re
from dataclasses import dataclass
from typing import List, Optional, Union
from enum import Enum

class CharacterClass(Enum):
    DIGIT = r'\d'
    WORD = r'\w'
    WHITESPACE = r'\s'
    ANY = r'.'
    
class Quantifier(Enum):
    ZERO_OR_MORE = '*'
    ONE_OR_MORE = '+'
    ZERO_OR_ONE = '?'

@dataclass
class PatternComponent:
    value: str
    quantifier: Optional[Quantifier] = None
    
    def __str__(self) -> str:
        if self.quantifier:
            return f'{self.value}{self.quantifier.value}'
        return self.value

class PatternBuilder:
    def __init__(self):
        self.components: List[PatternComponent] = []
        
    def add(self, component: Union[str, PatternComponent]) -> 'PatternBuilder':
        if isinstance(component, str):
            component = PatternComponent(re.escape(component))
        self.components.append(component)
        return self
    
    def digit(self, quantifier: Optional[Quantifier] = None) -> 'PatternBuilder':
        self.components.append(PatternComponent(CharacterClass.DIGIT.value, quantifier))
        return self
    
    def word(self, quantifier: Optional[Quantifier] = None) -> 'PatternBuilder':
        self.components.append(PatternComponent(CharacterClass.WORD.value, quantifier))
        return self
    
    def whitespace(self, quantifier: Optional[Quantifier] = None) -> 'PatternBuilder':
        self.components.append(PatternComponent(CharacterClass.WHITESPACE.value, quantifier))
        return self
    
    def any(self, quantifier: Optional[Quantifier] = None) -> 'PatternBuilder':
        self.components.append(PatternComponent(CharacterClass.ANY.value, quantifier))
        return self
    
    def group(self, *components: Union[str, PatternComponent]) -> 'PatternBuilder':
        group_builder = PatternBuilder()
        for component in components:
            group_builder.add(component)
        group_pattern = f'({str(group_builder)})'
        self.components.append(PatternComponent(group_pattern))
        return self
    
    def or_(self, *patterns: Union[str, 'PatternBuilder']) -> 'PatternBuilder':
        pattern_strings = []
        for pattern in patterns:
            if isinstance(pattern, str):
                pattern_strings.append(re.escape(pattern))
            else:
                pattern_strings.append(str(pattern))
        or_pattern = f'({"|".join(pattern_strings)})'
        self.components.append(PatternComponent(or_pattern))
        return self
    
    def repeat(self, min_times: int = 0, max_times: Optional[int] = None) -> 'PatternBuilder':
        if not self.components:
            raise ValueError("Cannot add repetition to empty pattern")
        last_component = self.components[-1]
        if max_times is None:
            self.components[-1] = PatternComponent(f'({last_component.value}){{{min_times},}}')
        else:
            self.components[-1] = PatternComponent(f'({last_component.value}){{{min_times},{max_times}}}')
        return self
    
    def compile(self) -> re.Pattern:
        return re.compile(str(self))
    
    def __str__(self) -> str:
        return ''.join(str(component) for component in self.components)

class PatternGenerator:
    @staticmethod
    def phone_number(country: str = 'US') -> re.Pattern:
        builder = PatternBuilder()
        if country == 'US':
            return (builder
                .add('(')
                .digit().repeat(3)
                .add(')')
                .whitespace()
                .digit().repeat(3)
                .add('-')
                .digit().repeat(4)
                .compile())
        raise ValueError(f"Pattern for country {country} not implemented")
    
    @staticmethod
    def email() -> re.Pattern:
        local_part = (PatternBuilder()
            .word()
            .or_('.', '-', '_')
            .word(Quantifier.ZERO_OR_MORE))
        
        domain = (PatternBuilder()
            .word()
            .add('.')
            .word().repeat(2, 63))
        
        return (PatternBuilder()
            .add(str(local_part))
            .add('@')
            .add(str(domain))
            .compile())
    
    @staticmethod
    def url() -> re.Pattern:
        protocol = (PatternBuilder()
            .or_('http://', 'https://', 'ftp://')
            .word(Quantifier.ZERO_OR_MORE))
        
        domain = (PatternBuilder()
            .word()
            .add('.')
            .word().repeat(2, 63))
        
        path = (PatternBuilder()
            .add('/')
            .word()
            .or_('/', '-', '_', '.')
            .word(Quantifier.ZERO_OR_MORE))
        
        return (PatternBuilder()
            .add(str(protocol))
            .add(str(domain))
            .add(str(path))
            .compile())

# Example usage
if __name__ == '__main__':
    # Create pattern for US phone numbers
    phone_pattern = PatternGenerator.phone_number()
    assert phone_pattern.match('(123) 456-7890')
    
    # Create pattern for email addresses
    email_pattern = PatternGenerator.email()
    assert email_pattern.match('user.name-123@example.com')
    
    # Create pattern for URLs
    url_pattern = PatternGenerator.url()
    assert url_pattern.match('https://www.example.com/path/to/resource')
    
    # Create custom pattern using builder
    custom_pattern = (PatternBuilder()
        .digit().repeat(3)
        .add('-')
        .word().repeat(2, 5)
        .compile())
    assert custom_pattern.match('123-ab')
    assert custom_pattern.match('456-abcde')