const gejalaList = window.gejalaList || [];

const searchInput = document.getElementById('search-gejala');
const dropdown = document.getElementById('dropdown-gejala');
const selectedContainer = document.getElementById('selected-gejala');
const hiddenInputs = document.getElementById('hidden-inputs');

let selectedGejala = [];

function renderDropdown(filtered) {
  dropdown.innerHTML = '';
  filtered.forEach(item => {
    const element = document.createElement('a');
    element.href = '#';
    element.classList.add('list-group-item', 'list-group-item-action');
    element.textContent = item.nama;
    element.onclick = (e) => {
      e.preventDefault();
      if (!selectedGejala.find(g => g.id === item.id)) {
        selectedGejala.push(item);
        renderSelected();
      }
      dropdown.innerHTML = '';
      searchInput.value = '';
    };
    dropdown.appendChild(element);
  });
}

function renderSelected() {
  selectedContainer.innerHTML = '';
  hiddenInputs.innerHTML = '';
  selectedGejala.forEach(item => {
    const badge = document.createElement('span');
    badge.classList.add('badge-gejala', 'badge', 'badge-info', 'mr-2', 'mb-2', 'p-2');
    badge.textContent = item.nama;

    const removeIcon = document.createElement('i');
    removeIcon.classList.add('fas', 'fa-times-circle', 'ml-2');
    removeIcon.style.cursor = 'pointer';
    removeIcon.onclick = () => {
      selectedGejala = selectedGejala.filter(g => g.id !== item.id);
      renderSelected();
    };

    badge.appendChild(removeIcon);
    selectedContainer.appendChild(badge);

    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'gejala';
    input.value = item.id;
    hiddenInputs.appendChild(input);
  });
}

searchInput.addEventListener('input', function () {
  const keyword = this.value.toLowerCase();
  if (keyword.length > 0) {
    const filtered = gejalaList.filter(g => g.nama.toLowerCase().includes(keyword));
    renderDropdown(filtered);
  } else {
    dropdown.innerHTML = '';
  }
});
