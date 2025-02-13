from tests.test_file_upload import create_test_excel
from utils.xls_analyzer import XLSAnalyzer

def test_xls_analyzer_dash_to_null_conversion(tmp_path):
    """Test that dash values are converted to null values during Excel parsing"""
    data = {
        'Week Number': [0],
        'Month': [''],
        'Category': ['Development'],
        'Subcategory': [''],
        'Customer': ['-'],
        'Project': ['-'],
        'Task Description': [''],
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
        assert records[0]['Category'] == 'Development'
        assert records[0]['Hours'] == 8.0
        assert records[0]['Date'] == '2024-10-07'

def test_xls_analyzer_handles_missing_columns(tmp_path):
    """Test that the analyzer properly handles missing columns"""
    data = {
        'Category': ['Development'],
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
        assert records[0]['Week Number'] == 0
        assert records[0]['Month'] == ''

def test_xls_analyzer_validates_data_types(tmp_path):
    """Test that the analyzer properly validates and converts data types"""
    data = {
        'Week Number': ['invalid'],
        'Month': ['October'],
        'Category': ['Development'],
        'Subcategory': ['Backend'],
        'Customer': ['Test Customer'],
        'Project': ['Test Project'],
        'Task Description': ['Test task'],
        'Hours': ['invalid'],
        'Date': ['2024-10-07']
    }
    excel_file = create_test_excel(tmp_path, data)

    with open(excel_file, "rb") as f:
        contents = f.read()
        analyzer = XLSAnalyzer()
        records = analyzer.read_excel(contents)

        assert len(records) == 1
        assert isinstance(records[0]['Week Number'], int)
        assert isinstance(records[0]['Hours'], float)
        assert records[0]['Week Number'] == 0
        assert records[0]['Hours'] == 0.0
        assert records[0]['Customer'] == 'Test Customer'
        assert records[0]['Project'] == 'Test Project'