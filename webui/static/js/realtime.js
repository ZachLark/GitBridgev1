// Initialize Socket.IO connection
const socket = io();

// Task counters
let totalTasks = 0;
let pendingTasks = 0;
let completedTasks = 0;
let processingRate = 0;

// Charts
let taskDistributionChart;
let processingTimelineChart;

// Initialize charts
function initializeCharts() {
    // Task Distribution Chart
    const taskDistCtx = document.getElementById('taskDistributionChart').getContext('2d');
    taskDistributionChart = new Chart(taskDistCtx, {
        type: 'doughnut',
        data: {
            labels: ['Pending', 'Processing', 'Completed', 'Failed'],
            datasets: [{
                data: [0, 0, 0, 0],
                backgroundColor: [
                    '#60A5FA', // blue-400
                    '#F59E0B', // yellow-500
                    '#10B981', // green-500
                    '#EF4444'  // red-500
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    // Processing Timeline Chart
    const timelineCtx = document.getElementById('processingTimelineChart').getContext('2d');
    processingTimelineChart = new Chart(timelineCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Tasks/Second',
                data: [],
                borderColor: '#6366F1', // indigo-500
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Update task list
function updateTaskList(tasks) {
    const taskList = document.getElementById('task-list');
    const fragment = document.createDocumentFragment();

    tasks.forEach(task => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">${task.task_id}</div>
            </td>
            <td class="px-6 py-4">
                <div class="text-sm text-gray-900">${task.description}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusClass(task.status)}">
                    ${task.status}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                ${new Date(task.created_at).toLocaleString()}
            </td>
        `;
        fragment.appendChild(row);
    });

    taskList.innerHTML = '';
    taskList.appendChild(fragment);
}

// Get status class for styling
function getStatusClass(status) {
    const classes = {
        'pending': 'bg-blue-100 text-blue-800',
        'processing': 'bg-yellow-100 text-yellow-800',
        'completed': 'bg-green-100 text-green-800',
        'failed': 'bg-red-100 text-red-800'
    };
    return classes[status.toLowerCase()] || 'bg-gray-100 text-gray-800';
}

// Update metrics
function updateMetrics(metrics) {
    document.getElementById('total-tasks').textContent = metrics.total;
    document.getElementById('pending-tasks').textContent = metrics.pending;
    document.getElementById('completed-tasks').textContent = metrics.completed;
    document.getElementById('processing-rate').textContent = `${metrics.rate}/s`;

    // Update distribution chart
    taskDistributionChart.data.datasets[0].data = [
        metrics.pending,
        metrics.processing,
        metrics.completed,
        metrics.failed
    ];
    taskDistributionChart.update();

    // Update timeline chart
    const now = new Date().toLocaleTimeString();
    processingTimelineChart.data.labels.push(now);
    processingTimelineChart.data.datasets[0].data.push(metrics.rate);

    // Keep last 10 data points
    if (processingTimelineChart.data.labels.length > 10) {
        processingTimelineChart.data.labels.shift();
        processingTimelineChart.data.datasets[0].data.shift();
    }
    processingTimelineChart.update();
}

// Socket event handlers
socket.on('connect', () => {
    console.log('Connected to server');
    initializeCharts();
});

socket.on('task_update', (data) => {
    updateTaskList(data.tasks);
    updateMetrics(data.metrics);
});

socket.on('error', (error) => {
    console.error('Socket error:', error);
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    
    // Request initial data
    socket.emit('request_initial_data');
}); 