document.querySelectorAll('.filter').forEach(button => button.addEventListener('click', () => {
  document.querySelectorAll('.filter').forEach(item => {
    const selected = item === button;
    item.classList.toggle('active', selected);
    item.setAttribute('aria-pressed', String(selected));
  });
  filterFiles();
}));
document.querySelector('#fileSearch')?.addEventListener('input', filterFiles);
function filterFiles() {
  const category = document.querySelector('.filter.active')?.dataset.category || 'all';
  const query = (document.querySelector('#fileSearch')?.value || '').trim().toLocaleLowerCase('ru');
  let count = 0;
  document.querySelectorAll('.file-row').forEach(row => {
    const visible = (category === 'all' || row.dataset.category === category) && row.dataset.search.toLocaleLowerCase('ru').includes(query);
    row.hidden = !visible;
    if (visible) count++;
  });
  if (document.querySelector('#fileCount')) document.querySelector('#fileCount').textContent = count;
  if (document.querySelector('#noResults')) document.querySelector('#noResults').hidden = count > 0;
}
