from collections.abc import Mapping

from workflow_app.models import ProductRow


class ProductRowValidationError(ValueError):
    def __init__(self, errors: dict[str, str]) -> None:
        self.errors = errors
        super().__init__("Invalid product row")


def validate_product_row(row: Mapping[str, str]) -> ProductRow:
    from decimal import Decimal

    sku = row["sku"].strip().upper()
    name = row["name"].strip()
    price = Decimal(row["price"].strip())
    quantity = int(row["quantity"].strip())
    errors: dict[str, str] = {}

    if not sku:
        errors["sku"] = "is required"
    if not name:
        errors["name"] = "is required"
    if price < 0:
        errors["price"] = "must be zero or greater"
    if quantity < 0:
        errors["quantity"] = "must be zero or greater"
    if errors:
        raise ProductRowValidationError(errors)

    return ProductRow(
        sku=sku,
        name=name,
        price=price,
        quantity=quantity,
    )
