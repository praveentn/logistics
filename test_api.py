#!/usr/bin/env python3
"""Quick API test script."""

import requests
import json

# Test creating a warehouse
print("Creating warehouse...")
warehouse_data = {
    "warehouse_code": "WH-001",
    "name": "Main Warehouse",
    "location": "New York, NY",
    "capacity": 10000
}

response = requests.post(
    "http://localhost:8003/api/v1/warehouses",
    json=warehouse_data
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Test creating inventory items
print("\nCreating inventory items...")
inventory_items = [
    {
        "warehouse_id": response.json()["id"],
        "sku": "LAPTOP-001",
        "item_name": "Dell Laptop",
        "quantity": 100,
        "reorder_level": 10
    },
    {
        "warehouse_id": response.json()["id"],
        "sku": "MOUSE-001",
        "item_name": "Wireless Mouse",
        "quantity": 200,
        "reorder_level": 20
    }
]

for item in inventory_items:
    response = requests.post(
        "http://localhost:8003/api/v1/inventory",
        json=item
    )
    print(f"Created: {item['sku']} - Status: {response.status_code}")

# Test creating an order
print("\nCreating order via API Gateway...")
order_data = {
    "customer_name": "John Doe",
    "customer_email": "john.doe@example.com",
    "origin_address": "123 Main St, New York, NY 10001",
    "destination_address": "456 Oak Ave, Los Angeles, CA 90001",
    "package_weight": 5.5,
    "package_dimensions": "30x20x15",
    "items": [
        {
            "item_name": "Dell Laptop",
            "quantity": 1,
            "sku": "LAPTOP-001"
        },
        {
            "item_name": "Wireless Mouse",
            "quantity": 2,
            "sku": "MOUSE-001"
        }
    ]
}

response = requests.post(
    "http://localhost:8000/api/v1/orders",
    json=order_data
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 201:
    order_number = response.json()["order_number"]
    print(f"\n✅ Order created successfully: {order_number}")

    # Wait a moment for event processing
    import time
    time.sleep(3)

    # Check if shipment was created
    print(f"\nChecking shipment for order {order_number}...")
    response = requests.get(f"http://localhost:8000/api/v1/shipments/order/{order_number}")
    if response.status_code == 200:
        print(f"✅ Shipment created: {response.json()['tracking_number']}")
    else:
        print(f"❌ No shipment found (status: {response.status_code})")

    # Check notifications
    print("\nChecking notifications...")
    response = requests.get("http://localhost:8000/api/v1/notifications?page=1&page_size=10")
    if response.status_code == 200:
        notifications = response.json()
        print(f"✅ {len(notifications)} notifications sent")
    else:
        print(f"❌ Could not fetch notifications (status: {response.status_code})")

print("\n=== Test Complete ===")
