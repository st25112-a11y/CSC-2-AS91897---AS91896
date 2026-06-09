const modal = document.getElementById('myModal');
const modalTitle = document.getElementById('modalTitle');

function openModal(itemName) {
    modalTitle.textContent = itemName;
    modal.showModal();
}

function closeModal() {
    modal.close();
}

document.querySelectorAll('.order-btn').forEach(button => {
    button.addEventListener('click', () => {
        openModal(button.dataset.name);
    });
});