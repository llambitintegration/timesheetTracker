
def test_normalize_customer_name_dash_conversion():
    """Test that dash values are properly normalized to default customer"""
    from utils.validators import normalize_customer_name, DEFAULT_CUSTOMER
    
    # Test various dash/empty scenarios
    assert normalize_customer_name('-') == DEFAULT_CUSTOMER
    assert normalize_customer_name(None) == DEFAULT_CUSTOMER
    assert normalize_customer_name('') == DEFAULT_CUSTOMER
    
    # Test regular customer name remains unchanged
    assert normalize_customer_name('Test Customer') == 'Test Customer'
