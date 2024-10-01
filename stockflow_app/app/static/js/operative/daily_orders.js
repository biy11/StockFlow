/* static/js/operative/daiy_orders.js */


document.addEventListener('DOMContentLoaded', function() {
    // Connect to Socket.IO server
    var socket = io.connect('http://' + document.domain + ':' + location.port);

    // Log connection status
    socket.on('connect', function() {
        console.log('Connected to Socket.IO server');
    });

    socket.on('disconnect', function() {
        console.log('Disconnected from Socket.IO server');
    });

    // Listen for 'new_pick_order' events
    socket.on('new_pick_order', function(data) {
        console.log('New pick order event received:', data);
        // Append the new pick order to the current orders table
        var tableBody = document.querySelector('.orders-table tbody');
        if (tableBody) {
            var newRow = document.createElement('tr');

            newRow.innerHTML = `
                <td>${data.order_no}</td>
                <td>${data.customer_name}</td>
                <td>${data.delivery_comment || 'No Comment'}</td>
                <td>${data.status}</td>
            `;

            tableBody.appendChild(newRow);
            console.log('New pick order added to the operative table.');
        } else {
            console.warn('Table body element not found.');
        }
    });
});
