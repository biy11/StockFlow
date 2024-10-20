// pick_orders.js

document.addEventListener('DOMContentLoaded', function() {
    function toggleCustomCommentInput() {
        var deliveryCommentSelect = document.getElementById("delivery_comment");
        var customCommentGroup = document.getElementById("custom_comment_group");
        if (deliveryCommentSelect.value === "custom") {
            customCommentGroup.style.display = "block";
        } else {
            customCommentGroup.style.display = "none";
        }
    }

    // Connect to Socket.IO server
    var socket = io.connect('wss://stockflow.femutrade.com');

    // Add these event listeners
    socket.on('update_pick_order', function(data) {
        console.log('Update pick order event received:', data);
        updateOrderInTable(data);
    });


    socket.on('delete_pick_order', function(data) {
        console.log('Delete pick order event received:', data);
        removeOrderFromTable(data.id);
    });
    

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


    // Implement the updateOrderInTable function
    function updateOrderInTable(data) {
        var row = document.querySelector(`tr[data-id="${data.id}"]`);
        if (row) {
            row.querySelector('.order_status').innerText = data.status;
            row.dataset.status = data.status;  // Update data-status attribute
            console.log('Pick order updated in the admin table.');
        } else {
            console.warn('Order not found in the table for update.');
        }
    }

    // Implement the removeOrderFromTable function
    function removeOrderFromTable(orderId) {
        var row = document.querySelector(`tr[data-id="${orderId}"]`);
        if (row) {
            row.remove();
            console.log('Pick order removed from the admin table.');
        } else {
            console.warn('Order not found in the table for removal.');
        }
    }

    // Function to append a new order to the admin's table
    function appendOrderToTable(data) {
        var tableBody = document.querySelector('.orders-table tbody');
        if (tableBody) {
            var newRow = document.createElement('tr');
            newRow.setAttribute('data-id', data.id);
            newRow.setAttribute('data-status', data.status);

            newRow.innerHTML = `
                <td class="order_no">${data.order_no}</td>
                <td class="customer_name">${data.customer_name}</td>
                <td class="delivery_comment">${data.delivery_comment || 'No Comment'}</td>
                <td class="order_status">${data.status}</td>
            `;

            tableBody.appendChild(newRow);
            console.log('New pick order added to the admin table.');

            // Attach event listeners to the new row
            newRow.addEventListener('mouseenter', () => newRow.classList.add('highlight'));
            newRow.addEventListener('mouseleave', () => newRow.classList.remove('highlight'));

            // Attach click event for editing the order
            newRow.addEventListener('click', function() {
                const orderId = newRow.getAttribute('data-id');
                openEditModal(orderId);
            });
        } else {
            console.warn('Table body element not found.');
        }
    }


    // Add event listener for the delivery comment dropdown
    const deliveryCommentSelect = document.getElementById('delivery_comment');
    if (deliveryCommentSelect) {
        deliveryCommentSelect.addEventListener('change', toggleCustomCommentInput);
    }

    // Handle form submission via AJAX
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent the default form submission

            const formData = new FormData(form);
            const data = {
                order_no: formData.get('order_no'),
                customer_name: formData.get('customer_name'),
                delivery_comment: formData.get('delivery_comment'),
                custom_comment: formData.get('custom_comment')
            };

            if (data.delivery_comment === 'custom' && data.custom_comment) {
                data.delivery_comment = data.custom_comment;
            }

            fetch(form.action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    console.log('Order successfully submitted:', result);
                    form.reset();
                    toggleCustomCommentInput();
                } else {
                    throw new Error(result.error);
                }
            })
            .catch(error => {
                console.error('There was a problem with the submission:', error);
            });
        });
    }

    // Highlight row on hover and attach click event
    document.querySelectorAll('.orders-table tbody tr').forEach(row => {
        row.addEventListener('mouseenter', () => row.classList.add('highlight'));
        row.addEventListener('mouseleave', () => row.classList.remove('highlight'));

        // Attach click event for editing the order
        row.addEventListener('click', function() {
            const orderId = row.getAttribute('data-id');
            openEditModal(orderId);
        });
    });

    // Modal Elements
    const modal = document.getElementById("editOrderModal");
    const span = document.getElementsByClassName("close")[0];
    const editForm = document.getElementById("editOrderForm");
    const deleteOrderBtn = document.getElementById("deleteOrderBtn");

    // Close modal on click of 'x'
    span.onclick = function() {
        modal.style.display = "none";
    };

    // Close modal on outside click
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    };

    // Open modal and populate fields with order data
    function openEditModal(orderId) {
        fetch(`/admin/get_order/${orderId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById("edit_order_id").value = orderId;
                document.getElementById("edit_order_no").value = data.order.order_no;
                document.getElementById("edit_customer_name").value = data.order.customer_name;
                document.getElementById("edit_delivery_comment").value = data.order.delivery_comment;

                // Display modal
                modal.style.display = "block";
            } else {
                throw new Error(data.error);
            }
        })
        .catch(error => {
            console.error('Error fetching order data:', error);
        });
    }

    // Handle update order form submission
    editForm.addEventListener('submit', function(event) {
        event.preventDefault();
    
        const orderId = document.getElementById("edit_order_id").value;
        const updatedData = {
            order_no: document.getElementById("edit_order_no").value,
            customer_name: document.getElementById("edit_customer_name").value,
            delivery_comment: document.getElementById("edit_delivery_comment").value
        };
    
        fetch(`/admin/update_order/${orderId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(updatedData)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                console.log('Order successfully updated:', result);
                modal.style.display = "none";
                
                // Optionally update the row data here
                const row = document.querySelector(`tr[data-id="${orderId}"]`);
                if (row) {
                    row.querySelector('.order_no').innerText = updatedData.order_no;
                    row.querySelector('.customer_name').innerText = updatedData.customer_name;
                    row.querySelector('.delivery_comment').innerText = updatedData.delivery_comment;
                }
            } else {
                throw new Error(result.error);
            }
        })
        .catch(error => {
            console.error('There was a problem with updating the order:', error);
            alert('Failed to update the order. Please try again.');
        });
    });

    // Handle delete button click
    deleteOrderBtn.addEventListener('click', function() {
        const orderId = document.getElementById("edit_order_id").value;

        fetch(`/admin/delete_order/${orderId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                console.log('Order successfully deleted:', result);
                modal.style.display = "none";
                
                // Remove the row from the table
                const row = document.querySelector(`tr[data-id="${orderId}"]`);
                if (row) {
                    row.remove();
                }
            } else {
                throw new Error(result.error);
            }
        })
        .catch(error => {
            console.error('Error deleting order:', error);
            alert('Failed to delete the order. Please try again.');
        });
    });
});
