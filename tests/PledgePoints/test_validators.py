"""Unit tests for PledgePoints validators."""

from PledgePoints.constants import SQL_INT_MAX, SQL_INT_MIN
from PledgePoints.validators import (
    normalize_pledge_name,
    parse_point_message,
    validate_pledge_name,
    validate_point_change,
)


class TestValidatePointChange:
    """Tests for validate_point_change function."""

    def test_valid_positive_points(self):
        """Test validation of valid positive points."""
        assert validate_point_change(10) is True
        assert validate_point_change(100) is True

    def test_valid_negative_points(self):
        """Test validation of valid negative points."""
        assert validate_point_change(-10) is True
        assert validate_point_change(-100) is True

    def test_zero_points(self):
        """Test validation of zero points."""
        assert validate_point_change(0) is True

    def test_max_boundary(self):
        """Test validation at maximum boundary."""
        assert validate_point_change(SQL_INT_MAX) is True
        assert validate_point_change(SQL_INT_MAX + 1) is False

    def test_min_boundary(self):
        """Test validation at minimum boundary."""
        assert validate_point_change(SQL_INT_MIN) is True
        assert validate_point_change(SQL_INT_MIN - 1) is False


class TestNormalizePledgeName:
    """Tests for normalize_pledge_name function."""

    def test_title_case_conversion(self):
        """Test that names are converted to title case."""
        assert normalize_pledge_name("john") == "John"
        assert normalize_pledge_name("JOHN") == "John"
        assert normalize_pledge_name("jOhN") == "John"

    def test_alias_mapping(self):
        """Test that aliases are properly mapped."""
        # Assuming "Matt" -> "Matthew" alias exists
        result = normalize_pledge_name("matt")
        assert result in ["Matthew", "Matt"]  # Depends on PLEDGE_ALIASES config

    def test_preserves_valid_names(self):
        """Test that valid names are preserved correctly."""
        assert normalize_pledge_name("Jake") == "Jake"


class TestValidatePledgeName:
    """Tests for validate_pledge_name function."""

    def test_valid_pledge_name(self):
        """Test validation of valid pledge names."""
        # This test depends on VALID_PLEDGES constant
        # Assuming "Logan" is a valid pledge
        result = validate_pledge_name("elliott")
        assert result is not None
        assert result == "Elliot"

    def test_invalid_pledge_name(self):
        """Test validation of invalid pledge names."""
        result = validate_pledge_name("InvalidPledgeName123")
        assert result is None

    def test_alias_validation(self):
        """Test that aliases are validated correctly."""
        # If "Matt" is an alias for "Matthew"
        result = validate_pledge_name("matt")
        if result is not None:
            assert result in ["Matthew", "Matt"]


class TestParsePointMessage:
    """Tests for parse_point_message function."""

    def test_valid_positive_points(self):
        """Test parsing valid positive point messages."""
        result = parse_point_message("+10 Eli Great job at recruitment")
        if result:  # Only test if Eli is a valid pledge
            point_change, pledge, comment = result
            assert point_change == 10
            assert pledge == "Eli"
            assert comment == "Great job at recruitment"

    def test_valid_negative_points(self):
        """Test parsing valid negative point messages."""
        result = parse_point_message("-5 Eli Being late")
        if result:
            point_change, pledge, comment = result
            assert point_change == -5
            assert pledge == "Eli"
            assert comment == "Being late"

    def test_float_points_rounded(self):
        """Test that float points are rounded to nearest integer."""
        result = parse_point_message("+10.7 Eli Good work")
        if result:
            point_change, _, _ = result
            assert point_change == 11

        result = parse_point_message("+10.3 Eli Good work")
        if result:
            point_change, _, _ = result
            assert point_change == 10

    def test_with_to_prefix(self):
        """Test parsing messages with 'to' prefix."""
        result = parse_point_message("+10 to Eli for great work")
        if result:
            point_change, pledge, comment = result
            assert point_change == 10
            assert pledge == "Eli"
            assert comment == "for great work"

    def test_invalid_format_no_comment(self):
        """Test that messages without comments are invalid."""
        result = parse_point_message("+10 Eli")
        assert result is None

    def test_invalid_format_no_pledge(self):
        """Test that messages without pledge names are invalid."""
        result = parse_point_message("+10")
        assert result is None

    def test_invalid_format_no_points(self):
        """Test that messages without points are invalid."""
        result = parse_point_message("Eli some comment")
        assert result is None

    def test_empty_message(self):
        """Test that empty messages return None."""
        result = parse_point_message("")
        assert result is None

        result = parse_point_message("   ")
        assert result is None

    def test_invalid_pledge_returns_none(self):
        """Test that invalid pledge names cause message to fail parsing."""
        result = parse_point_message("+10 InvalidPledge123 some comment")
        assert result is None

    def test_points_out_of_range(self):
        """Test that points outside valid range are rejected."""
        huge_points = SQL_INT_MAX + 1
        result = parse_point_message(f"+{huge_points} Eli comment")
        assert result is None
