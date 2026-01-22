(() => {
  document.addEventListener('DOMContentLoaded', () => {
    const bulkActions = document.getElementById('bulkActions');
    const bulkForm = document.getElementById('bulkDeleteForm');
    const selects = Array.from(document.querySelectorAll('.image-select'));
    const selectAllUnusedBtn = document.getElementById('selectAllUnusedBtn');

    if (!bulkActions || !bulkForm || selects.length === 0) return;

    function refreshBulkActions() {
      const checkedCount = selects.filter((c) => c.checked).length;
      bulkActions.style.display = checkedCount > 0 ? 'flex' : 'none';
    }

    selects.forEach((c) => c.addEventListener('change', refreshBulkActions));

    if (selectAllUnusedBtn) {
      selectAllUnusedBtn.addEventListener('click', () => {
        selects.forEach((c) => {
          // used images are disabled in the template
          if (!c.disabled) c.checked = true;
        });
        refreshBulkActions();
      });
    }

    refreshBulkActions();

    bulkForm.addEventListener('submit', (e) => {
      const checkedCount = selects.filter((c) => c.checked).length;
      if (checkedCount === 0) {
        e.preventDefault();
        return;
      }
      // eslint-disable-next-line no-alert
      if (!confirm(`Supprimer ${checkedCount} image(s) sélectionnée(s) ?`)) {
        e.preventDefault();
      }
    });
  });
})();
