// Dashboard JavaScript - Vanilla JS implementation

// Configuration
const REFRESH_INTERVAL = 10000; // 10 seconds
let refreshTimer = null;

// Main initialization
document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard initialized');
    fetchDashboardData();
    startAutoRefresh();
});

// Auto-refresh functionality
function startAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }
    refreshTimer = setInterval(() => {
        fetchDashboardData();
    }, REFRESH_INTERVAL);
}

// Fetch all dashboard data
async function fetchDashboardData() {
    try {
        const response = await fetch('/api/stats/overview');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        updateDashboard(data);
        updateLastUpdated();
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
        showError();
    }
}

// Update dashboard with fetched data
function updateDashboard(data) {
    // Update Orders
    if (data.orders) {
        updateElement('total-orders', data.orders.total_orders || 0);
        updateElement('pending-orders', data.orders.pending_orders || 0);
        updateElement('delivered-orders', data.orders.delivered_orders || 0);
        updateStatusBadge('order-status', data.orders.status);
    }

    // Update Shipments
    if (data.shipments) {
        updateElement('total-shipments', data.shipments.total_shipments || 0);
        updateElement('active-shipments', data.shipments.active_shipments || 0);
        updateElement('delivered-shipments', data.shipments.delivered_shipments || 0);
        updateStatusBadge('shipment-status', data.shipments.status);
    }

    // Update Inventory
    if (data.inventory) {
        updateElement('total-inventory', data.inventory.total_items || 0);
        updateElement('low-stock-items', data.inventory.low_stock_items || 0);
        updateStatusBadge('inventory-status', data.inventory.status);
    }

    // Update Notifications
    if (data.notifications) {
        updateElement('notifications-sent', data.notifications.notifications_sent_today || 0);
        updateStatusBadge('notification-status', data.notifications.status);
    }

    // Update Service Health
    if (data.service_health) {
        updateServiceHealth(data.service_health);
    }
}

// Update individual element
function updateElement(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
        // Add a subtle animation on update
        element.classList.add('loading');
        setTimeout(() => {
            element.classList.remove('loading');
        }, 300);
    }
}

// Update status badge
function updateStatusBadge(elementId, status) {
    const element = document.getElementById(elementId);
    if (element) {
        // Remove all status classes
        element.classList.remove('success', 'error', 'warning', 'loading');

        // Add appropriate class based on status
        if (status === 'success') {
            element.classList.add('success');
            element.textContent = 'Connected';
        } else if (status === 'error') {
            element.classList.add('error');
            element.textContent = 'Error';
        } else {
            element.classList.add('warning');
            element.textContent = 'Unknown';
        }
    }
}

// Update service health section
function updateServiceHealth(healthData) {
    const healthGrid = document.getElementById('service-health-grid');
    const overallHealth = document.getElementById('overall-health');

    if (!healthGrid || !healthData.services) return;

    // Clear existing cards
    healthGrid.innerHTML = '';

    // Create service health cards
    healthData.services.forEach(service => {
        const card = createServiceHealthCard(service);
        healthGrid.appendChild(card);
    });

    // Update overall health
    if (overallHealth) {
        overallHealth.classList.remove('success', 'error', 'warning', 'loading');
        if (healthData.all_healthy) {
            overallHealth.classList.add('success');
            overallHealth.textContent = 'All Systems Operational';
        } else {
            overallHealth.classList.add('error');
            overallHealth.textContent = 'Some Services Degraded';
        }
    }
}

// Create service health card
function createServiceHealthCard(service) {
    const card = document.createElement('div');
    card.className = `service-health-card ${service.status}`;

    const title = document.createElement('h4');
    title.textContent = service.service || 'Unknown Service';

    const statusDiv = document.createElement('div');
    statusDiv.className = 'service-status';

    let statusText = '';
    let statusIcon = '';

    switch (service.status) {
        case 'healthy':
            statusText = 'Healthy';
            statusIcon = '✓';
            break;
        case 'unhealthy':
            statusText = 'Unhealthy';
            statusIcon = '✗';
            break;
        case 'unreachable':
            statusText = 'Unreachable';
            statusIcon = '⚠';
            break;
        default:
            statusText = 'Unknown';
            statusIcon = '?';
    }

    statusDiv.innerHTML = `<span>${statusIcon}</span> ${statusText}`;

    // Add error message if present
    if (service.error) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'service-error';
        errorDiv.style.fontSize = '0.8rem';
        errorDiv.style.color = '#666';
        errorDiv.style.marginTop = '8px';
        errorDiv.textContent = `Error: ${service.error}`;
        card.appendChild(errorDiv);
    }

    card.appendChild(title);
    card.appendChild(statusDiv);

    return card;
}

// Update last updated timestamp
function updateLastUpdated() {
    const element = document.getElementById('last-updated');
    if (element) {
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        element.textContent = timeString;
    }
}

// Show error state
function showError() {
    const elements = [
        'total-orders', 'pending-orders', 'delivered-orders',
        'total-shipments', 'active-shipments', 'delivered-shipments',
        'total-inventory', 'low-stock-items',
        'notifications-sent'
    ];

    elements.forEach(id => {
        updateElement(id, 'Error');
    });

    const statusElements = [
        'order-status', 'shipment-status',
        'inventory-status', 'notification-status'
    ];

    statusElements.forEach(id => {
        updateStatusBadge(id, 'error');
    });

    const overallHealth = document.getElementById('overall-health');
    if (overallHealth) {
        overallHealth.classList.remove('success', 'warning', 'loading');
        overallHealth.classList.add('error');
        overallHealth.textContent = 'Dashboard Error';
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }
});
