(() => {
  document.addEventListener('DOMContentLoaded', () => {
    const bulkActions = document.getElementById('bulkActions');
    const bulkForm = document.getElementById('bulkDeleteForm');
    const selects = Array.from(document.querySelectorAll('.image-select'));
    const selectAllUnusedBtn = document.getElementById('selectAllUnusedBtn');
    const selectAllUnusedFlag = document.getElementById('selectAllUnusedFlag');

    if (!bulkActions || !bulkForm || selects.length === 0) return;

    function refreshBulkActions() {
      const checkedCount = selects.filter((c) => c.checked).length;
      const allUnusedMode = selectAllUnusedFlag && selectAllUnusedFlag.value === '1';
      bulkActions.style.display = checkedCount > 0 || allUnusedMode ? 'flex' : 'none';
    }

    selects.forEach((c) =>
      c.addEventListener('change', () => {
        // If user changes selection manually, leave "all unused" mode.
        if (selectAllUnusedFlag) selectAllUnusedFlag.value = '0';
        refreshBulkActions();
      }),
    );

    if (selectAllUnusedBtn) {
      selectAllUnusedBtn.addEventListener('click', () => {
        if (selectAllUnusedFlag) selectAllUnusedFlag.value = '1';
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
      const allUnusedMode = selectAllUnusedFlag && selectAllUnusedFlag.value === '1';
      if (checkedCount === 0 && !allUnusedMode) {
        e.preventDefault();
        return;
      }
      // eslint-disable-next-line no-alert
      if (
        !confirm(
          allUnusedMode
            ? 'Supprimer TOUTES les images non utilisées (toutes pages) ?'
            : `Supprimer ${checkedCount} image(s) sélectionnée(s) ?`,
        )
      ) {
        e.preventDefault();
      }
    });
  });
})();
