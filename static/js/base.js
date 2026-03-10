document.addEventListener('DOMContentLoaded', function () {

    // Logout confirmation
    window.confirmLogout = function () {
        const modal = new bootstrap.Modal(document.getElementById('logoutModal'));
        modal.show();
    };

    // Auto-hide alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Load connected users count
    updateConnectedCount();
    setInterval(updateConnectedCount, 30000);

    // Add loading state to buttons
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function () {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="loading me-2"></span>Processing...';
                submitBtn.disabled = true;

                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 10000);
            }
        });
    });

});

// Update connected users count
function updateConnectedCount() {
    const badge = document.getElementById('connectedBadge');
    const countElement = document.getElementById('connectedCount');

    if (badge && countElement) {
        fetch('/sessions/api/statistics/')
            .then(response => response.json())
            .then(data => {
                countElement.textContent = data.total_connected || 0;
            })
            .catch(error => {
                console.error('Error fetching connected users count:', error);
                countElement.textContent = '?';
            });
    }
}