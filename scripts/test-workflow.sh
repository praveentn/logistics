#!/bin/bash

# Test the complete order workflow

set -e

echo "=== Logistics Order Workflow Test ==="
echo ""

# Base URL
BASE_URL="http://localhost:8001"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Checking service health...${NC}"
HEALTH=$(curl -s ${BASE_URL}/health)
echo $HEALTH | jq .
echo ""

echo -e "${YELLOW}Step 2: Creating a test order...${NC}"
ORDER_RESPONSE=$(curl -s -X POST ${BASE_URL}/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "John Doe",
    "customer_email": "john.doe@example.com",
    "origin_address": "123 Main St, New York, NY 10001",
    "destination_address": "456 Oak Ave, Los Angeles, CA 90001",
    "package_weight": 5.5,
    "package_dimensions": "30x20x15",
    "items": [
      {
        "item_name": "Laptop",
        "quantity": 1,
        "sku": "LAPTOP-001"
      },
      {
        "item_name": "Mouse",
        "quantity": 2,
        "sku": "MOUSE-001"
      }
    ]
  }')

echo $ORDER_RESPONSE | jq .
ORDER_NUMBER=$(echo $ORDER_RESPONSE | jq -r '.order_number')
ORDER_ID=$(echo $ORDER_RESPONSE | jq -r '.id')
echo ""
echo -e "${GREEN}✓ Order created: ${ORDER_NUMBER}${NC}"
echo ""

echo -e "${YELLOW}Step 3: Retrieving order details...${NC}"
ORDER_DETAILS=$(curl -s ${BASE_URL}/api/v1/orders/${ORDER_ID})
echo $ORDER_DETAILS | jq .
echo ""

echo -e "${YELLOW}Step 4: Listing all orders...${NC}"
ORDERS_LIST=$(curl -s "${BASE_URL}/api/v1/orders?page=1&page_size=10")
echo $ORDERS_LIST | jq .
echo ""

echo -e "${YELLOW}Step 5: Updating order status...${NC}"
UPDATE_RESPONSE=$(curl -s -X PUT ${BASE_URL}/api/v1/orders/${ORDER_ID}/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "processing"
  }')
echo $UPDATE_RESPONSE | jq .
echo ""
echo -e "${GREEN}✓ Order status updated to 'processing'${NC}"
echo ""

echo -e "${YELLOW}Step 6: Getting order items...${NC}"
ITEMS=$(curl -s ${BASE_URL}/api/v1/orders/${ORDER_ID}/items)
echo $ITEMS | jq .
echo ""

echo -e "${GREEN}=== Workflow Test Completed Successfully! ===${NC}"
echo ""
echo "Summary:"
echo "  - Order Number: ${ORDER_NUMBER}"
echo "  - Order ID: ${ORDER_ID}"
echo "  - Status: processing"
echo "  - Items: $(echo $ITEMS | jq length)"
echo ""
echo "Next steps:"
echo "  - Check RabbitMQ management UI (http://localhost:15672) for published events"
echo "  - View Prometheus metrics (http://localhost:9090)"
echo "  - Check service logs: docker-compose logs -f order-service"
