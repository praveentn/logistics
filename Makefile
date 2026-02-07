# Makefile for Logistics Microservices

.PHONY: help build-order build-all up down logs clean k8s-deploy k8s-delete k8s-status test

# Default target
help:
	@echo "Logistics Microservices - Available Commands"
	@echo "=============================================="
	@echo ""
	@echo "Local Development (Docker Compose):"
	@echo "  make up              - Start all services with docker-compose"
	@echo "  make down            - Stop all services"
	@echo "  make logs            - View logs from all services"
	@echo "  make logs-order      - View logs from order service"
	@echo "  make build-order     - Build order service image"
	@echo "  make clean           - Remove all containers and volumes"
	@echo ""
	@echo "Kubernetes Deployment:"
	@echo "  make k8s-deploy      - Deploy all services to Kubernetes"
	@echo "  make k8s-delete      - Delete all resources from Kubernetes"
	@echo "  make k8s-status      - Show status of all pods and services"
	@echo "  make k8s-logs-order  - View order service logs in K8s"
	@echo "  make k8s-port-forward - Port forward services for local access"
	@echo ""
	@echo "Testing:"
	@echo "  make test            - Run basic API tests"
	@echo "  make test-workflow   - Test complete order workflow"
	@echo ""
	@echo "Utilities:"
	@echo "  make shell-order     - Open shell in order service container"
	@echo "  make db-shell        - Open PostgreSQL shell"
	@echo "  make rabbitmq-ui     - Open RabbitMQ management UI"
	@echo ""

# Docker Compose targets
up:
	docker-compose up -d
	@echo "Services starting... Check status with 'docker-compose ps'"
	@echo "Access points:"
	@echo "  - Order Service API: http://localhost:8001/docs"
	@echo "  - RabbitMQ Management: http://localhost:15672 (admin/admin_password_123)"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - Grafana: http://localhost:3000 (admin/admin)"

down:
	docker-compose down

logs:
	docker-compose logs -f

logs-order:
	docker-compose logs -f order-service

build-order:
	docker-compose build order-service

build-all:
	docker-compose build

clean:
	docker-compose down -v
	docker system prune -f

# Kubernetes targets
k8s-deploy:
	@echo "Deploying to Kubernetes..."
	kubectl apply -f k8s/base/namespace/
	kubectl apply -f k8s/base/postgresql/
	kubectl apply -f k8s/base/rabbitmq/
	@echo "Waiting for infrastructure to be ready..."
	kubectl wait --for=condition=ready pod -l app=postgresql -n logistics-demo --timeout=120s
	kubectl wait --for=condition=ready pod -l app=rabbitmq -n logistics-demo --timeout=120s
	@echo "Deploying Order Service..."
	kubectl apply -f k8s/base/order-service/
	@echo ""
	@echo "Deployment complete! Check status with: make k8s-status"

k8s-delete:
	kubectl delete namespace logistics-demo

k8s-status:
	@echo "=== Namespace ==="
	kubectl get namespace logistics-demo
	@echo ""
	@echo "=== Pods ==="
	kubectl get pods -n logistics-demo
	@echo ""
	@echo "=== Services ==="
	kubectl get svc -n logistics-demo
	@echo ""
	@echo "=== HPA ==="
	kubectl get hpa -n logistics-demo
	@echo ""
	@echo "=== PVC ==="
	kubectl get pvc -n logistics-demo

k8s-logs-order:
	kubectl logs -f deployment/order-service -n logistics-demo

k8s-port-forward:
	@echo "Port forwarding services..."
	@echo "Order Service will be available at http://localhost:8001"
	kubectl port-forward svc/order-service 8001:8001 -n logistics-demo

# Testing targets
test:
	@echo "Running basic API tests..."
	@curl -s http://localhost:8001/health | jq .
	@echo ""
	@curl -s http://localhost:8001/ | jq .

test-workflow:
	@echo "Testing order creation workflow..."
	@bash scripts/test-workflow.sh

# Utility targets
shell-order:
	docker-compose exec order-service /bin/sh

db-shell:
	docker-compose exec postgres psql -U postgres -d orders_db

rabbitmq-ui:
	@echo "Opening RabbitMQ Management UI..."
	@echo "URL: http://localhost:15672"
	@echo "Username: admin"
	@echo "Password: admin_password_123"
	@xdg-open http://localhost:15672 2>/dev/null || open http://localhost:15672 2>/dev/null || start http://localhost:15672 2>/dev/null || echo "Please open http://localhost:15672 in your browser"
