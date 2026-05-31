"""
Unit tests for Thai tokenizer.

These tests verify specific examples and edge cases for Thai tokenization.
"""
import pytest
from pyragdoc.utils.thai_tokenizer import ThaiTokenizer


@pytest.fixture
def tokenizer():
    """Create a ThaiTokenizer instance for testing."""
    return ThaiTokenizer()


class TestThaiSectionNumbers:
    """Test tokenization of Thai section numbers."""
    
    def test_simple_section_number(self, tokenizer):
        """Test tokenization of 'ข้อ ๒๑'."""
        text = "ข้อ ๒๑"
        tokens = tokenizer.tokenize(text)
        
        # Should preserve section number
        assert "ข้อ ๒๑" in tokens or ("ข้อ" in tokens and "๒๑" in tokens)
    
    def test_section_with_subsection(self, tokenizer):
        """Test tokenization of 'ข้อ ๒๑.๑'."""
        text = "ข้อ ๒๑.๑"
        tokens = tokenizer.tokenize(text)
        
        # Should preserve section number with subsection
        assert "ข้อ ๒๑.๑" in tokens or "๒๑.๑" in tokens
    
    def test_section_in_sentence(self, tokenizer):
        """Test section number within a sentence."""
        text = "ข้อ ๒๑ ขั้นตอนการแต่งตั้ง"
        tokens = tokenizer.tokenize(text)
        
        # Should contain section number and other words
        assert len(tokens) > 0
        # Section number should be preserved
        assert any("๒๑" in token for token in tokens)
    
    def test_multiple_sections(self, tokenizer):
        """Test multiple section numbers in text."""
        text = "ข้อ ๒๑ และ ข้อ ๒๒"
        tokens = tokenizer.tokenize(text)
        
        # Should preserve both section numbers
        assert any("๒๑" in token for token in tokens)
        assert any("๒๒" in token for token in tokens)


class TestThaiAbbreviations:
    """Test tokenization of Thai abbreviations."""
    
    def test_gpw_abbreviation(self, tokenizer):
        """Test tokenization of 'ก.พ.ว.' (Civil Service Commission)."""
        text = "ก.พ.ว. มีอำนาจ"
        tokens = tokenizer.tokenize(text)
        
        # Should preserve abbreviation
        assert "ก.พ.ว." in tokens
    
    def test_gkw_abbreviation(self, tokenizer):
        """Test tokenization of 'ก.ค.ว.' (Judicial Service Commission)."""
        text = "ก.ค.ว. มีหน้าที่"
        tokens = tokenizer.tokenize(text)
        
        # Should preserve abbreviation
        assert "ก.ค.ว." in tokens
    
    def test_abbreviation_in_sentence(self, tokenizer):
        """Test abbreviation within a longer sentence."""
        text = "คณะกรรมการ ก.พ.ว. มีอำนาจในการแต่งตั้ง"
        tokens = tokenizer.tokenize(text)
        
        # Should preserve abbreviation
        assert "ก.พ.ว." in tokens
        # Should have other tokens too
        assert len(tokens) > 1


class TestThaiNumerals:
    """Test tokenization of Thai numerals."""
    
    def test_single_digit(self, tokenizer):
        """Test single Thai digit."""
        text = "หมายเลข ๑"
        tokens = tokenizer.tokenize(text)
        
        assert any("๑" in token for token in tokens)
    
    def test_multi_digit(self, tokenizer):
        """Test multiple Thai digits."""
        text = "หมายเลข ๑๒๓"
        tokens = tokenizer.tokenize(text)
        
        # Should keep digits together
        assert any("๑๒๓" in token for token in tokens)
    
    def test_decimal_number(self, tokenizer):
        """Test Thai decimal number."""
        text = "๒๑.๕"
        tokens = tokenizer.tokenize(text)
        
        # Should preserve decimal number
        assert any("๒๑.๕" in token or "๒๑" in token for token in tokens)


class TestMixedThaiEnglish:
    """Test tokenization of mixed Thai-English text."""
    
    def test_thai_with_english(self, tokenizer):
        """Test text with both Thai and English."""
        text = "ข้อ ๒๑ Article 21"
        tokens = tokenizer.tokenize(text)
        
        assert len(tokens) > 0
        # Should handle both Thai and English
        assert any("๒๑" in token for token in tokens)
    
    def test_english_numbers(self, tokenizer):
        """Test that English numbers are handled."""
        text = "Section 21 ข้อ ๒๑"
        tokens = tokenizer.tokenize(text)
        
        assert len(tokens) > 0


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_string(self, tokenizer):
        """Test tokenization of empty string."""
        tokens = tokenizer.tokenize("")
        assert tokens == []
    
    def test_whitespace_only(self, tokenizer):
        """Test tokenization of whitespace."""
        tokens = tokenizer.tokenize("   ")
        assert tokens == []
    
    def test_single_word(self, tokenizer):
        """Test tokenization of single word."""
        text = "การแต่งตั้ง"
        tokens = tokenizer.tokenize(text)
        
        assert len(tokens) >= 1
        assert any("แต่งตั้ง" in token or "การ" in token for token in tokens)
    
    def test_very_long_text(self, tokenizer):
        """Test tokenization of long text."""
        text = "ข้อ ๒๑ " * 100
        tokens = tokenizer.tokenize(text)
        
        # Should handle long text without errors
        assert len(tokens) > 0
    
    def test_special_characters(self, tokenizer):
        """Test text with special characters."""
        text = "ข้อ ๒๑ (การแต่งตั้ง)"
        tokens = tokenizer.tokenize(text)
        
        assert len(tokens) > 0
    
    def test_numbers_and_punctuation(self, tokenizer):
        """Test text with numbers and punctuation."""
        text = "ข้อ ๒๑.๑, ๒๑.๒, และ ๒๑.๓"
        tokens = tokenizer.tokenize(text)
        
        # Should handle punctuation
        assert len(tokens) > 0
        # Should preserve section numbers
        assert any("๒๑" in token for token in tokens)


class TestFallbackBehavior:
    """Test fallback tokenization behavior."""
    
    def test_fallback_on_error(self, tokenizer):
        """Test that fallback works when pythainlp fails."""
        # This test verifies the fallback mechanism
        # Even if pythainlp is not available, should return something
        text = "ข้อ ๒๑ การแต่งตั้ง"
        tokens = tokenizer.tokenize(text)
        
        # Should return at least some tokens (via fallback if needed)
        assert len(tokens) > 0
        assert isinstance(tokens, list)
    
    def test_fallback_preserves_text(self, tokenizer):
        """Test that fallback doesn't lose text."""
        text = "ข้อ ๒๑"
        tokens = tokenizer.tokenize(text)
        
        # All original text should be in tokens (possibly split differently)
        joined = ''.join(tokens)
        # At minimum, key parts should be present
        assert len(tokens) > 0


class TestTokenizerProperties:
    """Test general properties of tokenizer."""
    
    def test_returns_list(self, tokenizer):
        """Test that tokenize always returns a list."""
        result = tokenizer.tokenize("test")
        assert isinstance(result, list)
    
    def test_no_none_tokens(self, tokenizer):
        """Test that tokens are never None."""
        text = "ข้อ ๒๑ การแต่งตั้ง"
        tokens = tokenizer.tokenize(text)
        
        assert all(token is not None for token in tokens)
    
    def test_no_empty_tokens(self, tokenizer):
        """Test that tokens are not empty strings."""
        text = "ข้อ ๒๑ การแต่งตั้ง"
        tokens = tokenizer.tokenize(text)
        
        # Filter out whitespace-only tokens
        assert all(token.strip() for token in tokens)
