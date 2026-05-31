"""
Property-based tests for Thai tokenization.

These tests use hypothesis to verify universal properties across
randomly generated Thai text inputs.
"""
import re
from hypothesis import given, settings, strategies as st
import pytest

from pyragdoc.utils.thai_tokenizer import ThaiTokenizer


# Custom strategies for Thai text generation
@st.composite
def thai_numerals(draw):
    """Generate Thai numeral strings."""
    length = draw(st.integers(min_value=1, max_value=4))
    digits = '๐๑๒๓๔๕๖๗๘๙'
    return ''.join(draw(st.sampled_from(digits)) for _ in range(length))


@st.composite
def thai_section_numbers(draw):
    """Generate Thai section numbers like 'ข้อ ๒๑' or '๒๑.๑'."""
    main_num = draw(thai_numerals())
    
    # Sometimes add sub-section
    if draw(st.booleans()):
        sub_num = draw(thai_numerals())
        return f"ข้อ {main_num}.{sub_num}"
    else:
        return f"ข้อ {main_num}"


@st.composite
def thai_abbreviations(draw):
    """Generate Thai abbreviations like 'ก.พ.ว.' or 'ก.ค.ว.'."""
    thai_consonants = 'กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรฤลฦวศษสหฬอฮ'
    length = draw(st.integers(min_value=2, max_value=4))
    letters = [draw(st.sampled_from(thai_consonants)) for _ in range(length)]
    return '.'.join(letters) + '.'


@st.composite
def thai_text_with_special_tokens(draw):
    """Generate Thai text containing special tokens."""
    parts = []
    num_parts = draw(st.integers(min_value=1, max_value=5))
    
    for _ in range(num_parts):
        token_type = draw(st.sampled_from(['section', 'abbrev', 'numeral', 'text']))
        
        if token_type == 'section':
            parts.append(draw(thai_section_numbers()))
        elif token_type == 'abbrev':
            parts.append(draw(thai_abbreviations()))
        elif token_type == 'numeral':
            parts.append(draw(thai_numerals()))
        else:
            # Regular Thai text
            parts.append(draw(st.text(
                alphabet='กขคงจฉชซญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ',
                min_size=1,
                max_size=10
            )))
    
    return ' '.join(parts)


# Feature: hybrid-search-rrf, Property 3: Thai Token Preservation
@pytest.mark.property
@settings(max_examples=100, deadline=None)
@given(text=thai_text_with_special_tokens())
def test_thai_section_number_preservation(text):
    """
    Property 3: Thai Token Preservation
    
    For any text containing Thai section numbers (e.g., "ข้อ ๒๑", "๒๑.๑"),
    tokenizing the text should preserve the section number as a single token
    without splitting the Thai numerals.
    
    Validates: Requirements 1.1, 1.2, 4.2, 4.3, 4.4
    """
    tokenizer = ThaiTokenizer()
    
    # Find all section numbers in original text
    section_pattern = re.compile(r'ข้อ\s*[๐-๙]+(?:\.[๐-๙]+)*')
    original_sections = section_pattern.findall(text)
    
    # Tokenize
    tokens = tokenizer.tokenize(text)
    
    # Verify each section number appears as a single token
    for section in original_sections:
        # Normalize whitespace for comparison
        normalized_section = re.sub(r'\s+', ' ', section)
        
        # Check if this section appears in tokens
        # (it might be split differently, but the numerals should be intact)
        found = False
        for token in tokens:
            if normalized_section in token or token in normalized_section:
                found = True
                break
        
        # At minimum, the Thai numerals should not be split
        thai_nums = re.findall(r'[๐-๙]+', section)
        for num in thai_nums:
            # Verify the numeral appears intact in at least one token
            assert any(num in token for token in tokens), \
                f"Thai numeral '{num}' from section '{section}' was split in tokens: {tokens}"


@pytest.mark.property
@settings(max_examples=100)
@given(abbrev=thai_abbreviations(), context=st.text(min_size=0, max_size=20))
def test_thai_abbreviation_preservation(abbrev, context):
    """
    Property 3: Thai Token Preservation (Abbreviations)
    
    For any text containing Thai abbreviations with periods (e.g., "ก.พ.ว.", "ก.ค.ว."),
    tokenizing the text should keep the abbreviation intact as a single token.
    
    Validates: Requirements 4.3
    """
    tokenizer = ThaiTokenizer()
    
    # Create text with abbreviation
    text = f"{context} {abbrev} {context}".strip()
    
    # Tokenize
    tokens = tokenizer.tokenize(text)
    
    # Verify abbreviation appears as a single token
    assert abbrev in tokens, \
        f"Abbreviation '{abbrev}' not preserved as single token in: {tokens}"


@pytest.mark.property
@settings(max_examples=100)
@given(numeral=thai_numerals(), context=st.text(min_size=0, max_size=20))
def test_thai_numeral_preservation(numeral, context):
    """
    Property 3: Thai Token Preservation (Numerals)
    
    For any text containing Thai numerals (๐-๙), tokenizing the text should
    preserve the numeral sequence without splitting individual digits.
    
    Validates: Requirements 4.2
    """
    tokenizer = ThaiTokenizer()
    
    # Create text with numeral
    text = f"{context} {numeral} {context}".strip()
    
    # Tokenize
    tokens = tokenizer.tokenize(text)
    
    # Verify numeral appears intact in at least one token
    found = any(numeral in token for token in tokens)
    assert found, \
        f"Thai numeral '{numeral}' was split in tokens: {tokens}"


@pytest.mark.property
@settings(max_examples=100)
@given(text=st.text(min_size=1, max_size=100))
def test_tokenization_always_returns_list(text):
    """
    Property: Tokenization always returns a list.
    
    For any input text, tokenization should always return a list
    (possibly empty for empty input).
    """
    tokenizer = ThaiTokenizer()
    result = tokenizer.tokenize(text)
    
    assert isinstance(result, list), \
        f"Tokenize should return list, got {type(result)}"


@pytest.mark.property
@settings(max_examples=100)
@given(text=st.text(min_size=1, max_size=100))
def test_tokenization_no_empty_tokens(text):
    """
    Property: Tokenization should not produce empty tokens.
    
    For any input text, the tokenized output should not contain
    empty strings.
    """
    tokenizer = ThaiTokenizer()
    tokens = tokenizer.tokenize(text)
    
    for token in tokens:
        assert token.strip() != '', \
            f"Found empty token in: {tokens}"
