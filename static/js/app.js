/**
 * Hospital Management System - Front-end Interactivity & Chart Initialization
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Mobile & Desktop Sidebar Toggle
    const hamburgerBtn = document.getElementById('hamburgerToggle');
    const sidebar = document.getElementById('appSidebar');

    if (hamburgerBtn && sidebar) {
        hamburgerBtn.addEventListener('click', function () {
            sidebar.classList.toggle('sidebar-collapsed');
            if (sidebar.style.display === 'none' || sidebar.style.display === '') {
                sidebar.style.display = 'flex';
            } else {
                sidebar.style.display = 'none';
            }
        });
    }

    // 2. Tab Navigation (Settings page)
    const tabButtons = document.querySelectorAll('.settings-tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const targetTab = this.getAttribute('data-tab');

            tabButtons.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            this.classList.add('active');
            const targetPane = document.getElementById(targetTab);
            if (targetPane) {
                targetPane.classList.add('active');
            }
        });
    });

    // 3. Client-side Real-time Search Filtering for Tables
    const liveSearchInput = document.getElementById('clientTableSearch');
    if (liveSearchInput) {
        liveSearchInput.addEventListener('keyup', function () {
            const filter = this.value.toLowerCase();
            const table = document.querySelector('.custom-table tbody');
            if (table) {
                const rows = table.getElementsByTagName('tr');
                for (let i = 0; i < rows.length; i++) {
                    const text = rows[i].textContent.toLowerCase();
                    rows[i].style.display = text.indexOf(filter) > -1 ? '' : 'none';
                }
            }
        });
    }

    // 4. Quick Auto-fill for Login Demo Credentials
    const autoFillBtn = document.getElementById('btnAutoFillDemo');
    if (autoFillBtn) {
        autoFillBtn.addEventListener('click', function () {
            const usernameInput = document.getElementById('username');
            const passwordInput = document.getElementById('password');
            if (usernameInput && passwordInput) {
                usernameInput.value = 'admin';
                passwordInput.value = 'admin123';
                usernameInput.focus();
            }
        });
    }

    // 5. Test AWS S3 Connection AJAX
    const testS3Btn = document.getElementById('btnTestS3');
    const testS3Result = document.getElementById('testS3Result');

    if (testS3Btn && testS3Result) {
        testS3Btn.addEventListener('click', function () {
            testS3Btn.disabled = true;
            testS3Btn.innerHTML = `
                <svg class="spin" style="width:16px;height:16px;animation:spin 1s linear infinite;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
                    <path d="M12 2a10 10 0 0 1 10 10"></path>
                </svg> Testing AWS S3...
            `;
            testS3Result.style.display = 'block';
            testS3Result.className = 'alert alert-info';
            testS3Result.innerHTML = 'Connecting to AWS S3 endpoint and verifying credentials...';

            fetch('/settings/test-s3', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(res => res.json())
            .then(data => {
                testS3Btn.disabled = false;
                testS3Btn.innerHTML = 'Test S3 Connection';

                if (data.connected) {
                    testS3Result.className = 'alert alert-success';
                    testS3Result.innerHTML = `<strong>S3 Connection Active!</strong> ${data.message}`;
                } else {
                    testS3Result.className = 'alert alert-warning';
                    testS3Result.innerHTML = `<strong>Status: ${data.status}</strong><br>${data.message}`;
                }
            })
            .catch(err => {
                testS3Btn.disabled = false;
                testS3Btn.innerHTML = 'Test S3 Connection';
                testS3Result.className = 'alert alert-danger';
                testS3Result.innerHTML = `<strong>Network Error:</strong> ${err.message}`;
            });
        });
    }

    // 6. Doctor quick-select in Book Appointment page
    const doctorCards = document.querySelectorAll('.available-doctor-item');
    const doctorSelect = document.getElementById('doctor_id');

    doctorCards.forEach(card => {
        card.addEventListener('click', function () {
            const docId = this.getAttribute('data-doctor-id');
            if (doctorSelect && docId) {
                doctorSelect.value = docId;
                // Highlight selected card
                doctorCards.forEach(c => c.style.borderColor = 'var(--border-color)');
                this.style.borderColor = 'var(--teal-primary)';
                this.style.backgroundColor = '#f0fdfa';
            }
        });
    });

    // 7. Auto dismiss alert messages after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });
});

// CSS Animation for spinner
const style = document.createElement('style');
style.textContent = `
@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
`;
document.head.appendChild(style);
