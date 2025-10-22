import frappe


def execute(doc, method):
    """Calculate OpenAI API cost based on token usage and model pricing."""

    # Skip if tokens not set
    if not doc.prompt_tokens or not doc.completion_tokens:
        return

    # Define pricing per model (per token)
    pricing = {
        "gpt-4o-2024-08-06": {"input": 0.0000025, "output": 0.000010},
        "gpt-4o-mini": {"input": 0.00000015, "output": 0.0000006},
        "gpt-4o": {"input": 0.0000025, "output": 0.000010},  # Fallback for generic name
    }

    # Get pricing for model (default to gpt-4o if unknown)
    model_pricing = pricing.get(doc.model_name, pricing["gpt-4o"])

    # Calculate cost
    input_cost = doc.prompt_tokens * model_pricing["input"]
    output_cost = doc.completion_tokens * model_pricing["output"]
    total_cost = input_cost + output_cost

    # Set field (rounded to 6 decimal places)
    doc.estimated_cost_usd = round(total_cost, 6)

    # Log calculation for debugging
    frappe.logger().debug(
        f"Calculated cost for {doc.name}: "
        f"{doc.prompt_tokens} input + {doc.completion_tokens} output = ${total_cost:.6f}"
    )
