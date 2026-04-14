// Animal Health System - Main JavaScript File

$(document).ready(function() {
    const loader = document.getElementById('page-loader');
    const showPageLoader = () => {
        if (loader) {
            loader.classList.add('is-visible');
        }
    };
    const hidePageLoader = () => {
        if (loader) {
            loader.classList.remove('is-visible');
        }
    };

    hidePageLoader();

    // Initialize tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // Initialize popovers
    $('[data-bs-toggle="popover"]').popover();
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        $('.alert:not(.alert-permanent)').fadeTo(500, 0).slideUp(500, function() {
            $(this).remove();
        });
    }, 5000);
    
    // Form validation enhancement
    $('form').on('submit', function() {
        const $submitButton = $(this).find('button[type="submit"]');
        const originalText = $submitButton.html();
        $submitButton.data('original-text', originalText).prop('disabled', true).html(
            '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...'
        );
        showPageLoader();
    });

    $('a[href]:not([href^="#"]):not([target="_blank"])').on('click', function(event) {
        const href = $(this).attr('href');
        if (!href || href.startsWith('javascript:') || $(this).attr('download') !== undefined || event.ctrlKey || event.metaKey || event.shiftKey) {
            return;
        }
        showPageLoader();
    });
    
    // Table row click for details
    $('.clickable-row').on('click', function() {
        window.location = $(this).data('href');
    });
    
    // Print functionality
    $('.print-btn').on('click', function() {
        window.print();
    });
    
    // Refresh data buttons
    $('.refresh-btn').on('click', function() {
        const $btn = $(this);
        const originalText = $btn.html();
        
        $btn.prop('disabled', true).html(
            '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Refreshing...'
        );
        
        setTimeout(function() {
            location.reload();
        }, 1000);
    });
    
    // Dynamic form field handling
    $('.dynamic-field-add').on('click', function() {
        const $template = $($(this).data('template'));
        const $container = $($(this).data('container'));
        const newField = $template.clone().removeClass('d-none');
        newField.find('input, select, textarea').val('');
        $container.append(newField);
        updateFieldIndexes();
    });
    
    $(document).on('click', '.dynamic-field-remove', function() {
        if ($(this).closest('.dynamic-field').siblings('.dynamic-field').length > 0) {
            $(this).closest('.dynamic-field').remove();
            updateFieldIndexes();
        }
    });
    
    function updateFieldIndexes() {
        $('.dynamic-field').each(function(index) {
            $(this).find('input, select, textarea, label').each(function() {
                const $el = $(this);
                const name = $el.attr('name');
                const id = $el.attr('id');
                const forAttr = $el.attr('for');
                
                if (name) $el.attr('name', name.replace(/\[\d+\]/, '[' + index + ']'));
                if (id) $el.attr('id', id.replace(/\d+/, index));
                if (forAttr) $el.attr('for', forAttr.replace(/\d+/, index));
            });
        });
    }
    
    // Real-time data updates (for dashboards)
    if ($('.real-time-update').length) {
        setInterval(updateDashboardData, 30000); // Update every 30 seconds
    }
    
    function updateDashboardData() {
        $.ajax({
            url: '/api/dashboard/stats',
            method: 'GET',
            success: function(data) {
                // Update counters
                $('[data-stat="total-reports"]').text(data.total_reports);
                $('[data-stat="pending-predictions"]').text(data.pending_predictions);
                $('[data-stat="active-treatments"]').text(data.active_treatments);
                $('[data-stat="assigned-farmers"]').text(data.assigned_farmers);
                
                // Show update notification
                showToast('Data updated', 'info');
            }
        });
    }
    
    // Toast notifications
    function showToast(message, type = 'info') {
        const toast = `
            <div class="toast align-items-center text-bg-${type} border-0 fade-in" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        $('.toast-container').append(toast);
        const toastEl = $('.toast-container .toast:last');
        const bsToast = new bootstrap.Toast(toastEl[0]);
        bsToast.show();
        
        toastEl.on('hidden.bs.toast', function() {
            $(this).remove();
        });
    }
    
    // Chart initialization (if Chart.js is included)
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
    
    function initializeCharts() {
        // Disease distribution chart
        const diseaseCtx = document.getElementById('diseaseChart');
        if (diseaseCtx) {
            new Chart(diseaseCtx, {
                type: 'pie',
                data: {
                    labels: ['Respiratory', 'Parasitic', 'Nutritional', 'Other'],
                    datasets: [{
                        data: [35, 28, 20, 17],
                        backgroundColor: [
                            '#dc3545',
                            '#ffc107',
                            '#17a2b8',
                            '#6c757d'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
        
        // Performance trend chart
        const performanceCtx = document.getElementById('performanceChart');
        if (performanceCtx) {
            new Chart(performanceCtx, {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Accuracy %',
                        data: [85, 86, 87, 88, 89, 89.2],
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: false,
                            min: 80,
                            max: 100
                        }
                    }
                }
            });
        }
    }
    
    // File upload preview
    $('input[type="file"]').on('change', function() {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                $('#file-preview').html(`
                    <div class="alert alert-info">
                        <i class="bi bi-file-earmark"></i>
                        <strong>${file.name}</strong> (${(file.size / 1024).toFixed(1)} KB)
                    </div>
                `);
            };
            reader.readAsDataURL(file);
        }
    });
    
    // Confirmation dialogs
    $('.confirm-action').on('click', function(e) {
        if (!confirm($(this).data('confirm') || 'Are you sure?')) {
            e.preventDefault();
            return false;
        }
    });
    
    // Auto-save forms (for longer forms)
    let autoSaveTimeout;
    $('.autosave-form').on('input', function() {
        clearTimeout(autoSaveTimeout);
        autoSaveTimeout = setTimeout(function() {
            saveFormDraft();
        }, 2000);
    });
    
    function saveFormDraft() {
        // Implement form draft saving logic here
        console.log('Auto-saving form...');
    }
    
    // Initialize datepickers
    if ($.fn.datepicker) {
        $('.datepicker').datepicker({
            format: 'yyyy-mm-dd',
            autoclose: true,
            todayHighlight: true
        });
    }
    
    // Initialize timepickers
    if ($.fn.timepicker) {
        $('.timepicker').timepicker({
            showMeridian: false,
            minuteStep: 15
        });
    }
});

// Cattle and Goat specific calculations
function calculateDosage(weight, medication) {
    // Simple dosage calculator for cattle and goats
    const dosages = {
        'oxytetracycline': 20, // mg/kg
        'penicillin': 10, // mg/kg
        'ivermectin': 0.2 // mg/kg
    };
    
    const dosagePerKg = dosages[medication] || 10;
    return (weight * dosagePerKg).toFixed(1);
}

function predictDisease(symptoms) {
    // Simple disease prediction based on symptoms
    const diseaseRules = {
        'respiratory': ['coughing', 'fever', 'nasal_discharge', 'labored_breathing'],
        'parasitic': ['diarrhea', 'weight_loss', 'lethargy', 'poor_coat'],
        'nutritional': ['weight_loss', 'poor_growth', 'weakness', 'reduced_appetite']
    };
    
    let scores = {};
    for (const [disease, indicators] of Object.entries(diseaseRules)) {
        scores[disease] = symptoms.filter(s => indicators.includes(s)).length / indicators.length;
    }
    
    return Object.entries(scores).sort((a, b) => b[1] - a[1])[0];
}

// Export data functions
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll('tr');
    const csv = [];
    
    for (const row of rows) {
        const rowData = [];
        const cols = row.querySelectorAll('td, th');
        
        for (const col of cols) {
            rowData.push('"' + col.innerText.replace(/"/g, '""') + '"');
        }
        
        csv.push(rowData.join(','));
    }
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (navigator.msSaveBlob) {
        navigator.msSaveBlob(blob, filename);
    } else {
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

function exportTableToPDF(tableId, filename) {
    // This would require a PDF library like jsPDF
    console.log('PDF export would require additional library');
}

// API helper functions
function apiCall(endpoint, method = 'GET', data = null) {
    return $.ajax({
        url: endpoint,
        method: method,
        data: data,
        contentType: 'application/json',
        dataType: 'json'
    });
}

// Notification functions
function markNotificationAsRead(notificationId) {
    return apiCall(`/api/notifications/${notificationId}/read`, 'POST');
}

function getUnreadNotifications() {
    return apiCall('/api/notifications/unread');
}
