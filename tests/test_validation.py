from decimal import Decimal

import pytest

from workflow_app.models import ProductRow
from workflow_app.validation import ProductRowValidationError, validate_product_row


def test_validate_product_row_normalizes_valid_inventory_data() -> None:
    result = validate_product_row(
        {"sku": " sku-001 ", "name": " Blue Widget ", "price": "12.50", "quantity": "3"}
    )

    assert result == ProductRow(
        sku="SKU-001",
        name="Blue Widget",
        price=Decimal("12.50"),
        quantity=3,
    )


def test_validate_product_row_reports_all_invalid_fields() -> None:
    with pytest.raises(ProductRowValidationError) as exc_info:
        validate_product_row({"sku": " ", "name": "", "price": "-1.00", "quantity": "-2"})

    assert exc_info.value.errors == {
        "sku": "is required",
        "name": "is required",
        "price": "must be zero or greater",
        "quantity": "must be zero or greater",
    }
