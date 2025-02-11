
def test_xls_analyzer_dash_to_none_conversion(tmp_path):
    """Test that dash values are converted to None during Excel parsing"""
    data = {
        'Category': ['Development'],
        'Customer': ['-'],
        'Project': ['-'],
        'Hours': [8.0],
        'Date': ['2024-10-07']
    }
    excel_file = create_test_excel(tmp_path, data)

    with open(excel_file, "rb") as f:
        contents = f.read()
        analyzer = XLSAnalyzer()
        records = analyzer.read_excel(contents)

        assert len(records) == 1
        assert records[0]['Customer'] is None
        assert records[0]['Project'] is None
