document.addEventListener('DOMContentLoaded', function () {
    var socket = io();  // Connect to the WebSocket server
    const notificationCountElement = document.getElementById('notification-count');
    const notificationList = document.getElementById('notification-list');
    let notificationCount = 0;

    // Function to add a new notification
    function addNotification(message) {
        const li = document.createElement('li');
        li.textContent = `${message} - ${new Date().toLocaleString()}`; // Adds timestamp
        notificationList.appendChild(li);
        notificationCount++;
        notificationCountElement.textContent = notificationCount;
        notificationCountElement.style.display = 'block';
    }

    // Listen for inquiries raised
    socket.on('inquiry_raised', function (data) {
        const message = `Inquiry raised for order ${data.order_no} by ${data.raised_by}: ${data.inquiry_comment}`;
        addNotification(message);
    });

    // Listen for completed orders
    socket.on('order_completed', function (data) {
        const message = `Order ${data.order_no} has been completed.`;
        addNotification(message);
    });

    // Reset notification count when dropdown is opened
    document.querySelector('.bell-icon').addEventListener('click', function () {
        notificationCount = 0;
        notificationCountElement.textContent = notificationCount;
        notificationCountElement.style.display = 'none';

        // Show 'No new notifications' if list is empty
        if (notificationList.children.length === 0) {
            const li = document.createElement('li');
            li.textContent = 'No new notifications';
            notificationList.appendChild(li);
        }
    });
});
