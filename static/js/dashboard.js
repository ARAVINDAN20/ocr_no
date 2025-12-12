/**
 * ANPR Dashboard - Real-time Vehicle Detection Dashboard
 * Handles WebSocket connections, data updates, filtering, and chart rendering
 */

// === State Management ===
const state = {
    vehicles: [],
    filteredVehicles: [],
    stats: {
        'Lane 1': { total: 0, Car: 0, Bike: 0, Bus: 0, Truck: 0 },
        'Lane 2': { total: 0, Car: 0, Bike: 0, Bus: 0, Truck: 0 }
    },
    filters: {
        type: 'all',
        lane: 'all',
        search: ''
    },
    charts: {},
    connected: false
};

// === DOM Elements ===
const elements = {
    connectionStatus: document.getElementById('connectionStatus'),
    currentTime: document.getElementById('currentTime'),
    totalVehicles: document.getElementById('totalVehicles'),
    lane1Count: document.getElementById('lane1Count'),
    lane2Count: document.getElementById('lane2Count'),
    avgSpeed: document.getElementById('avgSpeed'),
    overlayTotal: document.getElementById('overlayTotal'),
    vehicleTableBody: document.getElementById('vehicleTableBody'),
    recordCount: document.getElementById('recordCount'),
    typeFilter: document.getElementById('typeFilter'),
    laneFilter: document.getElementById('laneFilter'),
    plateSearch: document.getElementById('plateSearch'),
    resetFilters: document.getElementById('resetFilters'),
    clearBtn: document.getElementById('clearBtn'),
    toastContainer: document.getElementById('toastContainer')
};

// === Socket.IO Connection ===
const socket = io();

socket.on('connect', () => {
    state.connected = true;
    updateConnectionStatus(true);
    showToast('Connected to server', 'success');
});

socket.on('disconnect', () => {
    state.connected = false;
    updateConnectionStatus(false);
    showToast('Lost connection to server', 'error');
});

socket.on('initial_data', (data) => {
    state.vehicles = data.vehicles || [];
    state.stats = data.stats || state.stats;
    updateAllUI();
});

socket.on('vehicle_crossed', (data) => {
    state.vehicles.push(data.event);
    state.stats = data.stats;
    updateAllUI();
    addTableRow(data.event, true);
});

socket.on('plate_updated', (event) => {
    // Update vehicle in state
    const idx = state.vehicles.findIndex(v => v.id === event.id);
    if (idx !== -1) {
        state.vehicles[idx] = event;
        applyFilters();
        updateTable();
    }
});

socket.on('data_cleared', () => {
    state.vehicles = [];
    state.stats = {
        'Lane 1': { total: 0, Car: 0, Bike: 0, Bus: 0, Truck: 0 },
        'Lane 2': { total: 0, Car: 0, Bike: 0, Bus: 0, Truck: 0 }
    };
    updateAllUI();
    showToast('All data cleared', 'warning');
});

// === Connection Status ===
function updateConnectionStatus(connected) {
    const statusEl = elements.connectionStatus;
    const textEl = statusEl.querySelector('.status-text');

    if (connected) {
        statusEl.classList.remove('disconnected');
        statusEl.classList.add('connected');
        textEl.textContent = 'Connected';
    } else {
        statusEl.classList.remove('connected');
        statusEl.classList.add('disconnected');
        textEl.textContent = 'Disconnected';
    }
}

// === Time Display ===
function updateCurrentTime() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    elements.currentTime.textContent = timeStr;
}

setInterval(updateCurrentTime, 1000);
updateCurrentTime();

// === Stats Updates ===
function updateStats() {
    const totalLane1 = state.stats['Lane 1']?.total || 0;
    const totalLane2 = state.stats['Lane 2']?.total || 0;
    const total = totalLane1 + totalLane2;

    animateValue(elements.totalVehicles, parseInt(elements.totalVehicles.textContent) || 0, total);
    animateValue(elements.lane1Count, parseInt(elements.lane1Count.textContent) || 0, totalLane1);
    animateValue(elements.lane2Count, parseInt(elements.lane2Count.textContent) || 0, totalLane2);
    elements.overlayTotal.textContent = total;

    // Calculate average speed
    if (state.vehicles.length > 0) {
        const speeds = state.vehicles.map(v => v.speed).filter(s => s > 0);
        const avgSpeed = speeds.length > 0 ? Math.round(speeds.reduce((a, b) => a + b, 0) / speeds.length) : 0;
        animateValue(elements.avgSpeed, parseInt(elements.avgSpeed.textContent) || 0, avgSpeed);
    }
}

function animateValue(element, start, end) {
    if (start === end) return;

    const duration = 300;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        const easeOutQuad = 1 - (1 - progress) * (1 - progress);
        const current = Math.round(start + (end - start) * easeOutQuad);

        element.textContent = current;

        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            element.classList.add('updated');
            setTimeout(() => element.classList.remove('updated'), 300);
        }
    }

    requestAnimationFrame(update);
}

// === Table Management ===
function updateTable() {
    elements.recordCount.textContent = `${state.filteredVehicles.length} records`;

    if (state.filteredVehicles.length === 0) {
        elements.vehicleTableBody.innerHTML = `
            <tr class="empty-row">
                <td colspan="5">
                    <div class="empty-state">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9L18 10.5V5a2 2 0 00-2-2H8a2 2 0 00-2 2v5.5l-2.5.6C2.7 11.3 2 12.1 2 13v3c0 .6.4 1 1 1h2"/>
                            <circle cx="7" cy="17" r="2"/>
                            <circle cx="17" cy="17" r="2"/>
                        </svg>
                        <p>No vehicles match filters</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    // Show most recent first
    const reversed = [...state.filteredVehicles].reverse();
    elements.vehicleTableBody.innerHTML = reversed.map(v => createTableRowHTML(v)).join('');
}

function addTableRow(vehicle, animate = false) {
    // Check if vehicle matches current filters
    if (!matchesFilters(vehicle)) return;

    // Remove empty state if exists
    const emptyRow = elements.vehicleTableBody.querySelector('.empty-row');
    if (emptyRow) {
        emptyRow.remove();
    }

    const row = document.createElement('tr');
    row.innerHTML = createTableRowContent(vehicle);
    if (animate) {
        row.classList.add('new-entry');
    }

    // Insert at beginning (most recent first)
    elements.vehicleTableBody.insertBefore(row, elements.vehicleTableBody.firstChild);

    // Update record count
    elements.recordCount.textContent = `${state.filteredVehicles.length} records`;
}

function createTableRowHTML(vehicle) {
    return `<tr>${createTableRowContent(vehicle)}</tr>`;
}

function createTableRowContent(vehicle) {
    const typeClass = vehicle.type.toLowerCase();
    const laneClass = vehicle.lane === 'Lane 1' ? 'lane1' : 'lane2';

    let speedClass = 'low';
    if (vehicle.speed > 80) speedClass = 'high';
    else if (vehicle.speed > 50) speedClass = 'medium';

    return `
        <td>${vehicle.timestamp_display || '--:--:--'}</td>
        <td><span class="type-badge ${typeClass}">${vehicle.type}</span></td>
        <td><span class="plate-number">${vehicle.plate || 'N/A'}</span></td>
        <td><span class="speed-value ${speedClass}">${vehicle.speed} km/h</span></td>
        <td><span class="lane-badge ${laneClass}">${vehicle.lane}</span></td>
    `;
}

// === Filtering ===
function matchesFilters(vehicle) {
    const { type, lane, search } = state.filters;

    if (type !== 'all' && vehicle.type !== type) return false;
    if (lane !== 'all' && vehicle.lane !== lane) return false;
    if (search && !vehicle.plate.toLowerCase().includes(search.toLowerCase())) return false;

    return true;
}

function applyFilters() {
    state.filteredVehicles = state.vehicles.filter(matchesFilters);
}

// Filter event listeners
elements.typeFilter.addEventListener('click', (e) => {
    if (!e.target.classList.contains('filter-btn')) return;

    elements.typeFilter.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    e.target.classList.add('active');
    state.filters.type = e.target.dataset.value;

    applyFilters();
    updateTable();
    updateCharts();
});

elements.laneFilter.addEventListener('click', (e) => {
    if (!e.target.classList.contains('filter-btn')) return;

    elements.laneFilter.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    e.target.classList.add('active');
    state.filters.lane = e.target.dataset.value;

    applyFilters();
    updateTable();
    updateCharts();
});

elements.plateSearch.addEventListener('input', (e) => {
    state.filters.search = e.target.value;
    applyFilters();
    updateTable();
});

elements.resetFilters.addEventListener('click', () => {
    state.filters = { type: 'all', lane: 'all', search: '' };

    elements.typeFilter.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.value === 'all');
    });
    elements.laneFilter.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.value === 'all');
    });
    elements.plateSearch.value = '';

    applyFilters();
    updateTable();
    updateCharts();
});

// Clear all data
elements.clearBtn.addEventListener('click', async () => {
    if (confirm('Are you sure you want to clear all vehicle data?')) {
        try {
            await fetch('/api/clear');
        } catch (err) {
            showToast('Failed to clear data', 'error');
        }
    }
});

// === Charts ===
const chartColors = {
    car: '#3b82f6',
    bike: '#8b5cf6',
    bus: '#10b981',
    truck: '#f97316',
    lane1: '#f97316',
    lane2: '#3b82f6'
};

function initCharts() {
    const chartDefaults = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: {
                    color: '#94a3b8',
                    font: { family: 'Inter' }
                }
            }
        }
    };

    // Type Distribution (Doughnut)
    state.charts.type = new Chart(document.getElementById('typeChart'), {
        type: 'doughnut',
        data: {
            labels: ['Car', 'Bike', 'Bus', 'Truck'],
            datasets: [{
                data: [0, 0, 0, 0],
                backgroundColor: [chartColors.car, chartColors.bike, chartColors.bus, chartColors.truck],
                borderWidth: 0,
                hoverOffset: 10
            }]
        },
        options: {
            ...chartDefaults,
            cutout: '60%',
            plugins: {
                ...chartDefaults.plugins,
                legend: { position: 'bottom', labels: { color: '#94a3b8', padding: 10 } }
            }
        }
    });

    // Lane Comparison (Bar)
    state.charts.lane = new Chart(document.getElementById('laneChart'), {
        type: 'bar',
        data: {
            labels: ['Lane 1', 'Lane 2'],
            datasets: [{
                label: 'Vehicles',
                data: [0, 0],
                backgroundColor: [chartColors.lane1, chartColors.lane2],
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            ...chartDefaults,
            plugins: { ...chartDefaults.plugins, legend: { display: false } },
            scales: {
                x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
                y: { grid: { color: 'rgba(148, 163, 184, 0.1)' }, ticks: { color: '#94a3b8' } }
            }
        }
    });

    // Speed Distribution (Histogram)
    state.charts.speed = new Chart(document.getElementById('speedChart'), {
        type: 'bar',
        data: {
            labels: ['0-20', '20-40', '40-60', '60-80', '80-100', '100+'],
            datasets: [{
                label: 'Vehicles',
                data: [0, 0, 0, 0, 0, 0],
                backgroundColor: 'rgba(59, 130, 246, 0.6)',
                borderColor: '#3b82f6',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            ...chartDefaults,
            plugins: { ...chartDefaults.plugins, legend: { display: false } },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' },
                    title: { display: true, text: 'Speed (km/h)', color: '#64748b' }
                },
                y: {
                    grid: { color: 'rgba(148, 163, 184, 0.1)' },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });

    // Timeline (Line)
    state.charts.timeline = new Chart(document.getElementById('timelineChart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Lane 1',
                    data: [],
                    borderColor: chartColors.lane1,
                    backgroundColor: 'rgba(249, 115, 22, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 6
                },
                {
                    label: 'Lane 2',
                    data: [],
                    borderColor: chartColors.lane2,
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 6
                }
            ]
        },
        options: {
            ...chartDefaults,
            plugins: {
                ...chartDefaults.plugins,
                legend: { position: 'top', labels: { color: '#94a3b8' } }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8', maxTicksLimit: 10 }
                },
                y: {
                    grid: { color: 'rgba(148, 163, 184, 0.1)' },
                    ticks: { color: '#94a3b8' },
                    beginAtZero: true
                }
            }
        }
    });
}

function updateCharts() {
    // Type chart
    const typeData = state.filteredVehicles.reduce((acc, v) => {
        acc[v.type] = (acc[v.type] || 0) + 1;
        return acc;
    }, {});

    state.charts.type.data.datasets[0].data = [
        typeData['Car'] || 0,
        typeData['Bike'] || 0,
        typeData['Bus'] || 0,
        typeData['Truck'] || 0
    ];
    state.charts.type.update('none');

    // Lane chart
    const laneData = state.filteredVehicles.reduce((acc, v) => {
        acc[v.lane] = (acc[v.lane] || 0) + 1;
        return acc;
    }, {});

    state.charts.lane.data.datasets[0].data = [
        laneData['Lane 1'] || 0,
        laneData['Lane 2'] || 0
    ];
    state.charts.lane.update('none');

    // Speed histogram
    const speedBuckets = [0, 0, 0, 0, 0, 0];
    state.filteredVehicles.forEach(v => {
        const speed = v.speed || 0;
        if (speed < 20) speedBuckets[0]++;
        else if (speed < 40) speedBuckets[1]++;
        else if (speed < 60) speedBuckets[2]++;
        else if (speed < 80) speedBuckets[3]++;
        else if (speed < 100) speedBuckets[4]++;
        else speedBuckets[5]++;
    });

    state.charts.speed.data.datasets[0].data = speedBuckets;
    state.charts.speed.update('none');

    // Timeline - group by minute
    const timeGroups = {};
    state.filteredVehicles.forEach(v => {
        if (!v.timestamp) return;
        const time = v.timestamp.slice(11, 16); // HH:MM
        if (!timeGroups[time]) {
            timeGroups[time] = { 'Lane 1': 0, 'Lane 2': 0 };
        }
        timeGroups[time][v.lane]++;
    });

    const sortedTimes = Object.keys(timeGroups).sort();
    state.charts.timeline.data.labels = sortedTimes;
    state.charts.timeline.data.datasets[0].data = sortedTimes.map(t => timeGroups[t]['Lane 1']);
    state.charts.timeline.data.datasets[1].data = sortedTimes.map(t => timeGroups[t]['Lane 2']);
    state.charts.timeline.update('none');
}

// === Toast Notifications ===
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    let icon = '';
    switch (type) {
        case 'success':
            icon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/></svg>';
            break;
        case 'error':
            icon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/></svg>';
            break;
        case 'warning':
            icon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><path d="M12 9v4M12 17h.01"/></svg>';
            break;
        default:
            icon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>';
    }

    toast.innerHTML = `
        <div class="toast-icon">${icon}</div>
        <span class="toast-message">${message}</span>
    `;

    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// === Master Update Function ===
function updateAllUI() {
    applyFilters();
    updateStats();
    updateTable();
    updateCharts();
}

// === Initialize ===
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    initDownloadButtons();

    // Fetch initial data via API as backup
    fetch('/api/vehicles')
        .then(res => res.json())
        .then(data => {
            if (data.length > 0 && state.vehicles.length === 0) {
                state.vehicles = data;
                return fetch('/api/stats');
            }
        })
        .then(res => res?.json())
        .then(data => {
            if (data) {
                state.stats = data.lane_stats;
                updateAllUI();
            }
        })
        .catch(err => console.log('Initial data fetch skipped'));
});

// === Download Functions ===
function initDownloadButtons() {
    // Header download buttons
    const downloadCSV = document.getElementById('downloadCSV');
    const downloadJSON = document.getElementById('downloadJSON');

    // Table dropdown buttons
    const exportCSVBtn = document.getElementById('exportCSVBtn');
    const exportJSONBtn = document.getElementById('exportJSONBtn');
    const exportBtn = document.getElementById('exportBtn');
    const exportDropdown = document.getElementById('exportDropdown');

    // Header buttons - download directly
    if (downloadCSV) {
        downloadCSV.addEventListener('click', () => downloadData('csv'));
    }

    if (downloadJSON) {
        downloadJSON.addEventListener('click', () => downloadData('json'));
    }

    // Table dropdown buttons
    if (exportCSVBtn) {
        exportCSVBtn.addEventListener('click', () => {
            downloadData('csv');
            closeDropdown();
        });
    }

    if (exportJSONBtn) {
        exportJSONBtn.addEventListener('click', () => {
            downloadData('json');
            closeDropdown();
        });
    }

    // Toggle dropdown on button click
    if (exportBtn && exportDropdown) {
        exportBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            exportDropdown.parentElement.classList.toggle('open');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.export-dropdown')) {
                closeDropdown();
            }
        });
    }

    function closeDropdown() {
        const dropdown = document.querySelector('.export-dropdown');
        if (dropdown) {
            dropdown.classList.remove('open');
        }
    }
}

function downloadData(format) {
    const endpoint = format === 'csv' ? '/api/download/csv' : '/api/download/json';

    // Show loading toast
    showToast(`Preparing ${format.toUpperCase()} download...`, 'info');

    fetch(endpoint)
        .then(response => {
            if (!response.ok) {
                throw new Error('Download failed');
            }

            // Get filename from Content-Disposition header
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `vehicle_data.${format}`;
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename=(.+)/);
                if (filenameMatch) {
                    filename = filenameMatch[1];
                }
            }

            return response.blob().then(blob => ({ blob, filename }));
        })
        .then(({ blob, filename }) => {
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();

            // Cleanup
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            showToast(`${format.toUpperCase()} downloaded successfully!`, 'success');
        })
        .catch(error => {
            console.error('Download error:', error);
            showToast(`Failed to download ${format.toUpperCase()}`, 'error');
        });
}

// Alternative: Generate CSV/JSON from client-side data
function downloadLocalCSV() {
    const headers = ['ID', 'Vehicle ID', 'Type', 'Number Plate', 'Speed (km/h)', 'Lane', 'Timestamp'];
    const rows = state.vehicles.map(v => [
        v.id,
        v.vehicle_id,
        v.type,
        v.plate,
        v.speed,
        v.lane,
        v.timestamp
    ]);

    const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    downloadFile(csvContent, 'vehicle_data.csv', 'text/csv');
}

function downloadLocalJSON() {
    const data = {
        export_timestamp: new Date().toISOString(),
        summary: {
            total_vehicles: state.vehicles.length,
            lane_1_total: state.stats['Lane 1']?.total || 0,
            lane_2_total: state.stats['Lane 2']?.total || 0,
            type_breakdown: {
                Car: (state.stats['Lane 1']?.Car || 0) + (state.stats['Lane 2']?.Car || 0),
                Bike: (state.stats['Lane 1']?.Bike || 0) + (state.stats['Lane 2']?.Bike || 0),
                Bus: (state.stats['Lane 1']?.Bus || 0) + (state.stats['Lane 2']?.Bus || 0),
                Truck: (state.stats['Lane 1']?.Truck || 0) + (state.stats['Lane 2']?.Truck || 0)
            }
        },
        lane_stats: state.stats,
        vehicles: state.vehicles
    };

    const jsonContent = JSON.stringify(data, null, 2);
    downloadFile(jsonContent, 'vehicle_data.json', 'application/json');
}

function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    showToast(`${filename} downloaded!`, 'success');
}

