from ._pricing_information import model_pricing


def calculate_cost(
    model_name: str,
    input_token: int | None = None,
    output_token: int | None = None,
    formatted: bool = False,
    is_batch: bool = False,
) -> tuple[float | str, float | str, float | str]:
    model_name = model_name.strip().lower()

    pricing_info = model_pricing[model_name]
    if pricing_info is None:
        raise ValueError(f"Model {model_name} does not have a pricing information.")

    in_key = (
        "batch_input_price"
        if is_batch and pricing_info["batch_input_price"]
        else "input_price"
    )
    out_key = (
        "batch_output_price"
        if is_batch and pricing_info["batch_output_price"]
        else "output_price"
    )

    input_cost = (pricing_info[in_key] * input_token if input_token else 0) / 1000000
    output_cost = (
        pricing_info[out_key] * output_token if output_token else 0
    ) / 1000000
    total_cost = input_cost + output_cost

    if formatted:
        input_cost = f"{input_cost:.10f}".rstrip("0").rstrip(".")
        output_cost = f"{output_cost:.10f}".rstrip("0").rstrip(".")
        total_cost = f"{total_cost:.10f}".rstrip("0").rstrip(".")

    return input_cost, output_cost, total_cost


def get_pricing_info(model_name: str) -> tuple[str, str]:
    pricing_info = model_pricing[model_name]
    if pricing_info is None:
        raise ValueError(
            f"Pricing information for the given model {model_name} is not available"
        )
    output_price = pricing_info["output_price"]
    input_price = pricing_info["input_price"]
    return output_price, input_price
