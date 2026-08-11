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

deliverySelect.addEventListener("change", toggleAddress);

toggleAddress();