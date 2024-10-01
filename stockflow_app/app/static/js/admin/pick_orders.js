/* static/js/admin/pick_orders.js */

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
        var tableBody = document.querySelector('.orders-table tbody');
        if (tableBody) {
            var newRow = document.createElement('tr');
            newRow.setAttribute('data-order-id', data.id);
            newRow.innerHTML = `
                <td>${data.order_no}</td>
                <td>${data.customer_name}</td>
                <td>${data.delivery_comment || 'No Comment'}</td>
                <td>${data.status}</td>
                <td>
                    <button class="edit-btn">Edit</button>
                    <button class="delete-btn">Delete</button>
                </td>
            `;
            tableBody.appendChild(newRow);
            console.log('New pick order added to the table.');
        } else {
            console.warn('Table body element not found.');
        }
    });

    // Add event listener for the delivery comment dropdown
    const deliveryCommentSelect = document.getElementById('delivery_comment');
    if (deliveryCommentSelect) {
        deliveryCommentSelect.addEventListener('change', toggleCustomCommentInput);
    }

    // Handle form submission via AJAX
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
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

            console.log('Submitting form data:', data);

            fetch(form.action, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(response => {
                console.log('Response received:', response);
                if (!response.ok) {
                    return response.json().then(errorData => {
                        throw new Error('Network response was not ok: ' + errorData.error);
                    });
                }
                return response.json();
            })
            .then(result => {
                console.log('Order successfully submitted:', result);
                form.reset();
                toggleCustomCommentInput();
            })
            .catch(error => {
                console.error('There was a problem with the submission:', error);
            });
        });
    }

    // Event delegation for edit and delete buttons
    document.querySelector('.orders-table').addEventListener('click', function(event) {
        const target = event.target;
        const row = target.closest('tr');
        const orderId = row.dataset.orderId;

        if (target.classList.contains('delete-btn')) {
            // Handle delete
            fetch(`/admin/delete_order/${orderId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    row.remove();
                    console.log('Order deleted successfully.');
                }
            })
            .catch(error => {
                console.error('There was a problem deleting the order:', error);
            });
        } else if (target.classList.contains('edit-btn')) {
            // Handle edit
            const orderNo = row.children[0].innerText;
            const customerName = row.children[1].innerText;
            const deliveryComment = row.children[2].innerText;

            document.getElementById('order_no').value = orderNo;
            document.getElementById('customer_name').value = customerName;
            document.getElementById('delivery_comment').value = deliveryComment;

            if (deliveryComment === 'custom') {
                document.getElementById('custom_comment_group').style.display = 'block';
            }
        }
    });
});
