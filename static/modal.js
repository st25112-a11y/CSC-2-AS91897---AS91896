const modal = document.getElementById('myModal');
const modalTitle = document.getElementById('modalTitle');
const modalItemName = document.getElementById('modalItemName');

function openModal(itemName) {
    modalTitle.textContent = `${itemName}`;
    modalItemName.value = itemName;
    modal.showModal();
}

document.querySelectorAll('.order-btn').forEach(button => {
    button.addEventListener('click', () => {
        openModal(button.getAttribute('data-name'));
    });
});

function closeModal() {
    modal.close();
}

const deliverySelect = document.getElementById("del_or_pickup");
const addressContainer = document.getElementById("addressField");

function toggleAddress() {
    if (deliverySelect.value === "delivery") {
        addressContainer.style.display = "block";
    } else {
        addressContainer.style.display = "none";
    }
}

let countdownInterval;

function startTimer(expiresAt) {
    clearInterval(countdownInterval);
    const timerDisplay = document.getElementById('deal-timer');

    countdownInterval = setInterval(() => {
        const now = Math.floor(Date.now() / 1000);
        const secondsRemaining = expiresAt - now;

        if (secondsRemaining > 0) {
            timerDisplay.textContent = `(Ends in ${secondsRemaining}s)`;
        } else {
            clearInterval(countdownInterval);
            timerDisplay.textContent = "(Loading new deal...)";
            fetchNewDeal();
        }
    }, 1000);
}

async function fetchNewDeal() {
    try {
        const response = await fetch('/api/get_deal');
        const newDeal = await response.json();

        document.getElementById('deal-pizza-size').textContent = newDeal.pizza_size;
        document.getElementById('deal-pizza').textContent = newDeal.pizza;
        document.getElementById('deal-side-size').textContent = newDeal.side_size;
        document.getElementById('deal-side').textContent = newDeal.side;
        document.getElementById('deal-price').textContent = newDeal.price.toFixed(2);

        document.getElementById('input-pizza').value = newDeal.pizza;
        document.getElementById('input-pizza-size').value = newDeal.pizza_size;
        document.getElementById('input-side').value = newDeal.side;
        document.getElementById('input-side-size').value = newDeal.side_size;

        startTimer(newDeal.expires_at);
        
    } catch (error) {
        console.error("Failed to load new deal:", error);
    }
}

const dealContainer = document.getElementById('deal-container');
if (dealContainer) {
    const initialExpires = parseInt(dealContainer.getAttribute('data-expires'), 10);
    startTimer(initialExpires);
}

deliverySelect.addEventListener("change", toggleAddress);

toggleAddress();