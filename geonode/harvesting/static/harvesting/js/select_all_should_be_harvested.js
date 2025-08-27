document.addEventListener('DOMContentLoaded', function() {
    const header = document.querySelector('th.column-should_be_harvested');
    if (!header) return;

    const checkboxes = document.querySelectorAll(
        'td.field-should_be_harvested input[type="checkbox"]'
    );

    const selectAll = document.createElement('input');
    selectAll.type = 'checkbox';
    selectAll.classList.add('select-all-header');
    selectAll.checked = Array.from(checkboxes).every(cb => cb.checked);

    // wrapper with flex
    const wrapper = document.createElement('div');
    wrapper.style.display = 'inline-flex';
    wrapper.style.alignItems = 'center';
    wrapper.style.gap = '1px';

    // move all header children (text) into wrapper
    while (header.firstChild) {
        wrapper.appendChild(header.firstChild);
    }

    // put the text on the right
    wrapper.appendChild(selectAll);
    header.appendChild(wrapper);

    // event listeners
    selectAll.addEventListener('change', () => {
        checkboxes.forEach(cb => cb.checked = selectAll.checked);
    });

    checkboxes.forEach(cb => {
        cb.addEventListener('change', () => {
            selectAll.checked = Array.from(checkboxes).every(c => c.checked);
        });
    });
});
