import frappe


def execute(doc, method):
    """Calculate OpenAI API cost based on token usage and model pricing."""

    # Normalize missing token counts to zero
    prompt_tokens = int(doc.prompt_tokens or 0)
    completion_tokens = int(doc.completion_tokens or 0)

    # Skip only if both are zero
    if prompt_tokens == 0 and completion_tokens == 0:
        return

    # Define pricing per model (per 1M tokens, updated rates)
    pricing = {
        "gpt-4o-2024-08-06": {"input": 0.00000375, "output": 0.000015},
        "gpt-4o-mini": {"input": 0.0000006, "output": 0.0000024},
        "gpt-4o": {"input": 0.00000375, "output": 0.000015},  # Fallback for generic name
    }

    # Normalize model name for lookup (strip whitespace, lowercase)
    model_key = doc.model_name.strip().lower() if doc.model_name else ""

    # Get pricing for model with fallback warning
    if model_key in pricing:
        model_pricing = pricing[model_key]
    else:
        model_pricing = pricing["gpt-4o"]
        frappe.logger().warning(
            f"Unknown model '{doc.model_name}' in cost calculation for {doc.name}, "
            f"falling back to gpt-4o pricing"
        )

    # Calculate cost
    input_cost = prompt_tokens * model_pricing["input"]
    output_cost = completion_tokens * model_pricing["output"]
    total_cost = input_cost + output_cost

    # Set field (rounded to 6 decimal places)
    doc.estimated_cost_usd = round(total_cost, 6)

    # Log calculation for debugging
    frappe.logger().debug(
        f"Calculated cost for {doc.name}: "
        f"{prompt_tokens} input + {completion_tokens} output = ${total_cost:.6f}"
    )
