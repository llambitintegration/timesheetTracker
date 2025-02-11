from tests.test_file_upload import create_test_excel
from utils.xls_analyzer import XLSAnalyzer
from utils.validators import DEFAULT_CUSTOMER, DEFAULT_PROJECT

def test_xls_analyzer_dash_to_default_conversion(tmp_path):
    """Test that dash values are converted to default values during Excel parsing"""
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
        assert records[0]['Customer'] == DEFAULT_CUSTOMER
        assert records[0]['Project'] == DEFAULT_PROJECT
        assert records[0]['Category'] == 'Development'
        assert records[0]['Hours'] == 8.0
        assert records[0]['Date'] == '2024-10-07'