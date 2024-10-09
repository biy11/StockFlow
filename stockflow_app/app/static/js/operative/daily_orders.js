//daily_orders.js

document.addEventListener('DOMContentLoaded', function () {
    // Connect to Socket.IO server
    var socket = io.connect('http://167.99.193.9:5000');

    const pingSound = new Audio('/static/sound/ping.mp3')
    
    socket.on('connect', function () {
        console.log('Connected to Socket.IO server');
    });

    socket.on('disconnect', function () {
        console.log('Disconnected from Socket.IO server');
    });

    socket.on('new_pick_order', function (data) {
        console.log('New pick order event received:', data);
        appendOrderToTable(data);
        pingSound.play();
        speakMessage(`New order: ${data.order_no}, customer name: ${data.customer_name}, Delivery comment: ${data.delivery_comment}`);
    });

    socket.on('update_pick_order', function (data) {
        console.log('Update pick order event received:', data);
        updateOrderInTable(data);
        pingSound.play();
    
        let message = 'Order update: ';
        let updates = [];
    
        // Check which fields are updated and construct the message accordingly
        if (data.order_no) {
            updates.push(`Order Number: ${data.order_no}`);
        }
        if (data.customer_name) {
            updates.push(`Customer: ${data.customer_name}`);
        }
        if (data.delivery_comment) {
            updates.push(`Delivery comment: ${data.delivery_comment}`);
        }
    
        // Construct the final message with the updated information
        if (updates.length > 0) {
            message += updates.join(', ');
        } else {
            message += 'No changes detected.';
        }
    
        // Speak the message
        speakMessage(message);
    });
    

    socket.on('delete_pick_order', function (data) {
        console.log('Delete pick order event received:', data);
        pingSound.play();  // Play the sound
        speakMessage(`Order ${data.order_no} has been deleted.`);
        removeOrderFromTable(data.id);
    });

    function speakMessage(message){
        if('speechSynthesis' in window){
            var speach = new SpeechSynthesisUtterance(message);
            speach.lang = 'en-US';
            speechSynthesis.speak(speach);
        } else{
            console.warn('Text-to-speach is not supported in this browser.');
        }
    }

    // Delegated event listener for table rows
    const tableBody = document.querySelector('.orders-table tbody');
    tableBody.addEventListener('click', function (event) {
        let row = event.target.closest('tr');
        if (row) {
            const orderId = row.dataset.id;
            const status = row.dataset.status;
            showActionModal(orderId, status);
        }
    });

    function processOrder(orderId) {
        fetch(`/operative/process_order/${orderId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const row = document.querySelector(`tr[data-id="${orderId}"]`);
                row.querySelector('.order_status').innerText = 'in process';
                row.dataset.status = 'in process';
            } else {
                alert(data.error);
            }
        })
        .catch(error => console.error('Error:', error));
    }
    
    function confirmCompleteOrder(orderId) {
        fetch(`/operative/confirm_order_complete/${orderId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                removeOrderFromTable(orderId);
            } else {
                alert(data.error);
            }
        })
        .catch(error => console.error('Error:', error));
    }

    function raiseInquiry(orderId) {
        const comment = prompt('Please enter inquiry details:');
        if (comment) {
            fetch(`/operative/raise_inquiry/${orderId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ comment })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const row = document.querySelector(`tr[data-id="${orderId}"]`);
                        row.querySelector('.order_status').innerText = 'inquiry raised';
                        row.dataset.status = 'inquiry raised';
                    } else {
                        alert(data.error);
                    }
                })
                .catch(error => console.error('Error:', error));
        }
    }

    function showActionModal(orderId, status) {
        const modal = document.getElementById("actionModal");
        const modalMessage = document.getElementById("modalMessage");
        const closeBtn = document.querySelector(".close");
        const processOrderBtn = document.getElementById("processOrderBtn");
        const raiseInquiryBtn = document.getElementById("raiseInquiryBtn");

        if (status === 'pending') {
            modalMessage.textContent = 'Process Order or Raise Inquiry?';
            processOrderBtn.textContent = 'Process Order';
        } else if (status === 'in process') {
            modalMessage.textContent = 'Confirm Order Complete or Raise Inquiry?';
            processOrderBtn.textContent = 'Confirm Complete';
        }

        modal.style.display = "block";

        closeBtn.onclick = function () {
            modal.style.display = "none";
        };

        window.onclick = function (event) {
            if (event.target == modal) {
                modal.style.display = "none";
            }
        };

        processOrderBtn.onclick = function () {
            if (status === 'pending') {
                processOrder(orderId);
            } else if (status === 'in process') {
                confirmCompleteOrder(orderId);
            }
            modal.style.display = "none";
        };
        

        raiseInquiryBtn.onclick = function () {
            raiseInquiry(orderId);
            modal.style.display = "none";
        };
    }

    // Append a new order to the table
    function appendOrderToTable(data) {
        var tableBody = document.querySelector('.orders-table tbody');
        if (tableBody) {
            // Remove the 'no-orders' row if it exists
            var noOrdersRow = document.querySelector('.orders-table tbody .no-orders');
            if (noOrdersRow) {
                noOrdersRow.remove();
            }
    
            var newRow = document.createElement('tr');
            newRow.setAttribute('data-id', data.id);
            newRow.setAttribute('data-status', data.status);
    
            newRow.innerHTML = `
                <td>${data.order_no}</td>
                <td>${data.customer_name}</td>
                <td>${data.delivery_comment || 'No Comment'}</td>
                <td class="order_status">${data.status}</td>
            `;
    
            tableBody.appendChild(newRow);
            console.log('New pick order added to the operative table.');
    
            // Attach click event listener to the new row
            newRow.addEventListener('click', function () {
                const orderId = newRow.getAttribute('data-id');
                const status = newRow.getAttribute('data-status');
                showActionModal(orderId, status);
            });
        } else {
            console.warn('Table body element not found.');
        }
    }
    
    

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
