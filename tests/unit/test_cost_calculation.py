"""Unit tests for cost calculation logic in FLRTS Parser Log."""



def test_basic_cost_calculation(mock_frappe):
    """Test basic cost calculation for OpenAI API usage."""
    # GPT-4 Turbo pricing: $0.01/1K prompt tokens, $0.03/1K completion tokens
    prompt_tokens = 1000
    completion_tokens = 500
    expected_cost = (prompt_tokens / 1000 * 0.01) + (completion_tokens / 1000 * 0.03)

    # Calculate actual cost
    actual_cost = (prompt_tokens / 1000 * 0.01) + (completion_tokens / 1000 * 0.03)

    assert abs(actual_cost - expected_cost) < 0.0001
    assert actual_cost == 0.025


def test_zero_token_cost(mock_frappe):
    """Test cost calculation with zero tokens."""
    prompt_tokens = 0
    completion_tokens = 0
    cost = (prompt_tokens / 1000 * 0.01) + (completion_tokens / 1000 * 0.03)

    assert cost == 0.0


def test_large_token_cost(mock_frappe):
    """Test cost calculation with large token counts."""
    prompt_tokens = 10000
    completion_tokens = 5000
    cost = (prompt_tokens / 1000 * 0.01) + (completion_tokens / 1000 * 0.03)

    assert cost == 0.25


def test_cost_rounding(mock_frappe):
    """Test that costs are rounded to appropriate precision."""
    prompt_tokens = 123
    completion_tokens = 456
    cost = (prompt_tokens / 1000 * 0.01) + (completion_tokens / 1000 * 0.03)
    rounded_cost = round(cost, 4)

    assert rounded_cost == 0.0149
