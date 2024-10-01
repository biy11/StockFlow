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
        appendOrderToTable(data);
    });

    // Listen for 'update_pick_order' events
    socket.on('update_pick_order', function(data) {
        console.log('Update pick order event received:', data);
        updateOrderInTable(data);
    });

    // Listen for 'delete_pick_order' events
    socket.on('delete_pick_order', function(data) {
        console.log('Delete pick order event received:', data);
        removeOrderFromTable(data.id);
    });

    // Append a new order to the table
    function appendOrderToTable(data) {
        var tableBody = document.querySelector('.orders-table tbody');
        if (tableBody) {
            var newRow = document.createElement('tr');
            newRow.setAttribute('data-id', data.id);

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
    }

    // Update an existing order in the table
    function updateOrderInTable(data) {
        var row = document.querySelector(`tr[data-id="${data.id}"]`);
        if (row) {
            var cells = row.children;
            cells[0].innerText = data.order_no;
            cells[1].innerText = data.customer_name;
            cells[2].innerText = data.delivery_comment || 'No Comment';
            cells[3].innerText = data.status;
            console.log('Pick order updated in the operative table.');
        } else {
            console.warn('Order not found in the table for update.');
        }
    }

    // Remove an order from the table
    function removeOrderFromTable(orderId) {
        var row = document.querySelector(`tr[data-id="${orderId}"]`);
        if (row) {
            row.remove();
            console.log('Pick order removed from the operative table.');
        } else {
            console.warn('Order not found in the table for removal.');
        }
    }
});
