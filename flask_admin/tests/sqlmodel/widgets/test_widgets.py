"""
Tests for SQLModel widgets module.
"""

from markupsafe import Markup

from flask_admin.contrib.sqlmodel.widgets import CheckboxListInput


class MockField:
    """Mock field for testing widgets."""

    def __init__(self, name, choices):
        self.name = name
        self._choices = choices

    def iter_choices(self):
        """Mock iter_choices method."""
        return self._choices


class TestCheckboxListInput:
    """Test the CheckboxListInput widget."""

    def test_widget_call_wtforms_legacy(self):
        """Test widget with WTForms legacy format (3 elements)."""
        widget = CheckboxListInput()

        # Mock field with legacy choice format (value, label, selected)
        choices = [
            ("1", "Option 1", True),
            ("2", "Option 2", False),
            ("3", "Option <script>", False),  # Test HTML escaping
        ]
        field = MockField("test_field", choices)

        result = widget(field)

        assert isinstance(result, Markup)
        result_str = str(result)

        # Check that all options are present
        assert 'value="1"' in result_str
        assert 'value="2"' in result_str
        assert 'value="3"' in result_str

        # Check labels
        assert "Option 1" in result_str
        assert "Option 2" in result_str
        assert "Option &lt;script&gt;" in result_str  # Should be escaped

        # Check selected state
        assert " checked" in result_str  # First option should be checked
        assert result_str.count(" checked") == 1  # Only one should be checked

        # Check structure
        assert 'class="checkbox"' in result_str
        assert 'type="checkbox"' in result_str
        assert f'name="{field.name}"' in result_str

    def test_widget_call_wtforms_new(self):
        """Test widget with WTForms new format (4 elements)."""
        widget = CheckboxListInput()

        # Mock field with new choice format (value, label, selected, render_kw)
        choices = [
            ("1", "Option 1", False, {}),
            ("2", "Option 2", True, {}),
        ]
        field = MockField("multi_field", choices)

        result = widget(field)

        assert isinstance(result, Markup)
        result_str = str(result)

        # Check that options are present
        assert 'value="1"' in result_str
        assert 'value="2"' in result_str

        # Check selected state (second option selected)
        assert result_str.count(" checked") == 1
        # Find the position of the checked option
        checked_pos = result_str.find(" checked")
        option2_pos = result_str.find('value="2"')
        assert checked_pos > option2_pos  # checked should come after value="2"

    def test_widget_call_empty_choices(self):
        """Test widget with no choices."""
        widget = CheckboxListInput()
        field = MockField("empty_field", [])

        result = widget(field)

        assert isinstance(result, Markup)
        assert str(result) == ""

    def test_widget_call_special_characters(self):
        """Test widget with special characters in labels."""
        widget = CheckboxListInput()

        choices = [
            ("special", 'Label with "quotes" & <tags>', False),
            ("unicode", "Label with ñ and é", True),
        ]
        field = MockField("special_field", choices)

        result = widget(field)
        result_str = str(result)

        # Check HTML escaping
        assert "&#34;quotes&#34;" in result_str or "&quot;quotes&quot;" in result_str
        assert "&lt;tags&gt;" in result_str
        assert "&amp;" in result_str

        # Unicode should be preserved
        assert "ñ and é" in result_str

    def test_widget_template_structure(self):
        """Test the template structure is correctly formatted."""
        widget = CheckboxListInput()

        # Verify template exists and has expected structure
        assert hasattr(widget, "template")
        template = widget.template

        # Check template contains required placeholders
        assert "%(id)s" in template
        assert "%(name)s" in template
        assert "%(label)s" in template
        assert "%(selected)s" in template

        # Check HTML structure
        assert 'class="checkbox"' in template
        assert 'type="checkbox"' in template
        assert "<label>" in template
        assert "</label>" in template

    def test_widget_multiple_selected(self):
        """Test widget with multiple selected options."""
        widget = CheckboxListInput()

        choices = [
            ("1", "First", True),
            ("2", "Second", True),
            ("3", "Third", False),
        ]
        field = MockField("multi_select", choices)

        result = widget(field)
        result_str = str(result)

        # Should have two checked items
        assert result_str.count(" checked") == 2

        # All options should be present
        assert 'value="1"' in result_str
        assert 'value="2"' in result_str
        assert 'value="3"' in result_str

    def test_widget_id_and_name_handling(self):
        """Test that widget correctly handles id and name attributes."""
        widget = CheckboxListInput()

        choices = [("test_id", "Test Label", False)]
        field = MockField("test_name", choices)

        result = widget(field)
        result_str = str(result)

        # Check that both id and name use the choice value
        assert 'id="test_id"' in result_str
        assert 'name="test_name"' in result_str  # name comes from field
        assert 'value="test_id"' in result_str
