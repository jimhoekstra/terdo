from terdo.utils.io import add_markdown_extension


def test_add_markdown_extension():
    """Test adding the markdown extension to a given file name."""
    before = "Test file name"
    expected = "Test file name.md"

    result = add_markdown_extension(before)
    assert result == expected
