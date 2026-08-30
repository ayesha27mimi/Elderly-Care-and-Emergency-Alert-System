// Family Dashboard JavaScript - Notifications & Real-time Updates

// Check for new notifications every 30 seconds
let notificationCount = 0;

function checkNotifications() {
    fetch('/api/family/notifications')
        .then(response => response.json())
        .then(data => {
            if (data.notifications && data.notifications.length > 0) {
                notificationCount = data.notifications.length;
                updateNotificationBadge(notificationCount);
                
                // Show toast for new notifications
                data.notifications.forEach(notification => {
                    showNotificationToast(notification);
                });
            }
        })
        .catch(error => console.error('Error fetching notifications:', error));
}

function updateNotificationBadge(count) {
    const badge = document.getElementById('notificationCount');
    if (badge) {
        badge.textContent = count;
        if (count > 0) {
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
    }
}

function showNotificationToast(notification) {
    const toast = document.getElementById('notificationToast');
    const message = document.getElementById('toastMessage');
    
    if (toast && message) {
        message.textContent = `${notification.type}: ${notification.description}`;
        toast.classList.add('show');
        
        // Play notification sound (optional)
        playNotificationSound();
        
        // Hide after 5 seconds
        setTimeout(() => {
            toast.classList.remove('show');
        }, 5000);
    }
}

function playNotificationSound() {
    // Create a simple beep sound using Web Audio API
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
        console.log('Audio playback not supported');
    }
}

// Notification button click handler
document.addEventListener('DOMContentLoaded', function() {
    const notificationBtn = document.getElementById('notificationBtn');
    if (notificationBtn) {
        notificationBtn.addEventListener('click', function() {
            // You can implement a dropdown menu here to show notifications
            alert('Notification panel - Feature can be expanded!');
        });
    }
    
    // Start checking for notifications
    checkNotifications();
    setInterval(checkNotifications, 30000); // Check every 30 seconds
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
});

// Smooth scroll to top function
function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Add scroll to top button
window.addEventListener('scroll', function() {
    if (window.pageYOffset > 300) {
        if (!document.getElementById('scrollTopBtn')) {
            const btn = document.createElement('button');
            btn.id = 'scrollTopBtn';
            btn.innerHTML = '<i class="fas fa-arrow-up"></i>';
            btn.style.cssText = `
                position: fixed;
                bottom: 2rem;
                left: 2rem;
                width: 50px;
                height: 50px;
                background: linear-gradient(135deg, #9ADBCC 0%, #9EB2DB 100%);
                color: white;
                border: none;
                border-radius: 50%;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                z-index: 1000;
                transition: all 0.3s;
            `;
            btn.onclick = scrollToTop;
            document.body.appendChild(btn);
        }
    } else {
        const btn = document.getElementById('scrollTopBtn');
        if (btn) {
            btn.remove();
        }
    }
});