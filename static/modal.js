const modal = document.getElementById('myModal');
const modalTitle = document.getElementById('modalTitle');
const modalItemName = document.getElementById('modalItemName');

document.querySelectorAll('.order-btn').forEach(button => {
    button.addEventListener('click', () => {
        const itemName = button.getAttribute('data-name');
        
        modalTitle.textContent = `Order ${itemName}`;
        modalItemName.value = itemName;
        
        modal.showModal();
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

deliverySelect.addEventListener("change", toggleAddress);

toggleAddress();