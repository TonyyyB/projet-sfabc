(() => {
  function normalizeFamilyKey(value) {
    let v = (value || '').trim().toLowerCase();
    try {
      v = v.normalize('NFKD');
    } catch {
      // ignore
    }
    v = v.replace(/[\u0300-\u036f]/g, '');
    v = v.replace(/\s+/g, ' ').trim();
    return v;
  }

  function getAddedFamilies() {
    const el = document.getElementById('added_families_json');
    try {
      return JSON.parse(el?.value || '[]');
    } catch {
      return [];
    }
  }

  function setAddedFamilies(list) {
    const el = document.getElementById('added_families_json');
    if (!el) return;
    el.value = JSON.stringify(list);
  }

  function getAllFamilyKeys() {
    // IMPORTANT: only read keys from the family rows.
    // Both the row and its <select> carry data-family-key; querying all would duplicate each key.
    const keys = Array.from(document.querySelectorAll('.family-row[data-family-key]'))
      .map((el) => el.getAttribute('data-family-key'))
      .filter((k) => typeof k === 'string' && k.trim().length > 0);
    return Array.from(new Set(keys));
  }

  function getFamilyLabelByKey(key) {
    const row = document.querySelector('[data-family-key="' + CSS.escape(key) + '"]');
    if (!row) return key;

    const input = row.querySelector('input.family-final-input');
    const v = input ? String(input.value || '').trim() : '';
    if (v) return v;

    const title = row.querySelector('[data-role="family-title"]');
    return title ? title.textContent.trim() : key;
  }

  function getMergeMap() {
    const map = new Map();
    document.querySelectorAll('select.merge-select[data-family-key]').forEach((sel) => {
      const fromKey = String(sel.getAttribute('data-family-key') || '').trim();
      const toKey = String(sel.value || '').trim();
      if (!fromKey || !toKey || fromKey === toKey) return;
      map.set(fromKey, toKey);
    });
    return map;
  }

  function resolveFamilyKey(key, mergeMap) {
    let current = String(key || '').trim();
    const seen = new Set();
    while (mergeMap.has(current) && !seen.has(current)) {
      seen.add(current);
      current = String(mergeMap.get(current) || '').trim();
    }
    return current;
  }

  function getEffectiveFamilyKeys() {
    const allKeys = getAllFamilyKeys();
    const mergeMap = getMergeMap();
    return allKeys.filter((k) => resolveFamilyKey(k, mergeMap) === k);
  }

  function refreshMergeSelectOptions() {
    const keys = getEffectiveFamilyKeys();
    const selects = document.querySelectorAll('select.merge-select');

    selects.forEach((sel) => {
      const current = sel.value;
      const selfKey = sel.getAttribute('data-family-key');
      sel.innerHTML = '';

      const optEmpty = document.createElement('option');
      optEmpty.value = '';
      optEmpty.textContent = '(ne pas fusionner)';
      sel.appendChild(optEmpty);

      // If current selection points to a now-merged key, keep it visible to avoid losing the value.
      const ensureKey = (k) => {
        if (!k) return;
        if (keys.includes(k)) return;
        keys.push(k);
      };
      ensureKey(current);

      keys.forEach((k) => {
        const opt = document.createElement('option');
        opt.value = k;
        opt.textContent = getFamilyLabelByKey(k);
        if (k === selfKey) opt.disabled = true;
        if (k === current) opt.selected = true;
        sel.appendChild(opt);
      });
    });
  }

  function refreshFamilySelectOptions() {
    const keys = getEffectiveFamilyKeys();
    const selects = document.querySelectorAll('select.family-select');

    selects.forEach((sel) => {
      const selected = sel.value || sel.getAttribute('data-selected') || '';
      sel.innerHTML = '';

      const empty = document.createElement('option');
      empty.value = '';
      empty.textContent = '(non définie)';
      sel.appendChild(empty);

      keys.forEach((k) => {
        const opt = document.createElement('option');
        opt.value = k;
        opt.textContent = getFamilyLabelByKey(k);
        if (k === selected) opt.selected = true;
        sel.appendChild(opt);
      });
    });
  }

  function applyFamilyMergesRealtime() {
    const mergeMap = getMergeMap();

    // 1) Update product family selects to their effective key
    document.querySelectorAll('select.family-select').forEach((sel) => {
      const raw = sel.value || sel.getAttribute('data-selected') || '';
      if (!raw) return;
      const resolved = resolveFamilyKey(raw, mergeMap);
      if (!resolved) return;
      sel.setAttribute('data-selected', resolved);
      sel.value = resolved;
    });

    // 2) Add a small visual cue on family rows when a merge is selected
    document.querySelectorAll('.family-row[data-family-key]').forEach((row) => {
      const key = String(row.getAttribute('data-family-key') || '').trim();
      if (!key) return;

      const select = row.querySelector('select.merge-select');
      const toKey = String(select?.value || '').trim();
      const meta = row.querySelector('.family-meta');
      if (!meta) return;

      let pill = meta.querySelector('[data-role="merge-pill"]');
      if (!pill) {
        pill = document.createElement('span');
        pill.className = 'pill';
        pill.setAttribute('data-role', 'merge-pill');
        meta.appendChild(pill);
      }

      if (toKey) {
        pill.style.display = '';
        pill.textContent = 'Fusionnée → ' + getFamilyLabelByKey(toKey);
      } else {
        pill.style.display = 'none';
        pill.textContent = '';
      }
    });
  }

  function syncFamilyTitlesAndSelects() {
    document.querySelectorAll('input.family-final-input').forEach((input) => {
      const key = input.getAttribute('data-family-key');
      if (!key) return;
      const row = document.querySelector('[data-family-key="' + CSS.escape(key) + '"]');
      if (!row) return;
      const title = row.querySelector('[data-role="family-title"]');
      if (!title) return;

      const v = String(input.value || '').trim();
      if (v) title.textContent = v;
    });

    refreshMergeSelectOptions();
    refreshFamilySelectOptions();
    applyFamilyMergesRealtime();
  }

  function addFamily(name) {
    const trimmed = (name || '').trim();
    if (!trimmed) return;

    const key = normalizeFamilyKey(trimmed);
    if (!key) return;

    if (document.querySelector('[data-family-key="' + CSS.escape(key) + '"]')) {
      return;
    }

    const added = getAddedFamilies();
    added.push(trimmed);
    setAddedFamilies(added);

    const container = document.getElementById('familiesContainer');
    if (!container) return;

    const wrapper = document.createElement('div');
    wrapper.className = 'family-row';
    wrapper.setAttribute('data-family-key', key);

    const safe = (s) => String(s).replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const safeAttr = (s) => String(s).replace(/"/g, '&quot;');

    wrapper.innerHTML = `
      <div>
        <div class="family-title" data-role="family-title">${safe(trimmed)}</div>
        <div class="family-meta"><span class="pill">Ajoutée</span></div>
        <div class="family-help">Variantes détectées dans le CSV ↓</div>
      </div>
      <div>
        <label class="form-label">Nom final</label>
        <input type="text" class="family-final-input" data-family-key="${safeAttr(key)}" name="family-${safeAttr(key)}-final" value="${safeAttr(trimmed)}" />
      </div>
      <div>
        <label class="form-label">Fusionner dans</label>
        <select name="family-${safeAttr(key)}-merge_into" class="merge-select" data-family-key="${safeAttr(key)}"></select>
      </div>
    `;

    container.appendChild(wrapper);
    wrapper.querySelector('input.family-final-input')?.addEventListener('input', () => syncFamilyTitlesAndSelects());

    refreshMergeSelectOptions();
    refreshFamilySelectOptions();
    applyFamilyMergesRealtime();
  }

  function setupPhotoDuMomentCheckboxes() {
    const rowCards = document.querySelectorAll('.card[data-row-index]');
    rowCards.forEach((rowCard) => {
      const rowIndex = rowCard.getAttribute('data-row-index');
      if (rowIndex === null) return;

      const hidden = rowCard.querySelector('input[name="rows-' + rowIndex + '-photo_du_moment"]');
      const checkboxes = Array.from(rowCard.querySelectorAll('input.pdm-checkbox'));
      if (!hidden || checkboxes.length === 0) return;

      function setSelected(photoIndex) {
        const idxStr = String(photoIndex);
        checkboxes.forEach((cb) => {
          cb.checked = String(cb.getAttribute('data-photo-index')) === idxStr;
          const pill = cb.closest('.photo-item')?.querySelector('.pdm-pill');
          if (pill) pill.style.display = cb.checked ? 'inline-block' : 'none';
        });
        hidden.value = idxStr;
      }

      const checked = checkboxes.filter((cb) => cb.checked);
      if (checked.length >= 1) {
        setSelected(checked[0].getAttribute('data-photo-index') || '1');
      } else {
        setSelected('1');
      }

      checkboxes.forEach((cb) => {
        cb.addEventListener('change', () => {
          const idx = cb.getAttribute('data-photo-index') || '1';
          if (cb.checked) {
            setSelected(idx);
            return;
          }

          // Obligatoire: on ne laisse jamais aucun choix.
          const anyChecked = checkboxes.some((x) => x.checked);
          if (!anyChecked) {
            cb.checked = true;
            setSelected(idx);
          }
        });
      });
    });
  }

  function setupPhotoFilenameSync() {
    document.querySelectorAll('.photo-item').forEach((item) => {
      const select = item.querySelector('select[name$="-image_existing"]');
      const pill = item.querySelector('[data-role="photo-filename"]');
      if (!select || !pill) return;

      const apply = () => {
        const selectedId = String(select.value || '').trim();
        const requested = String(pill.getAttribute('data-requested') || '').trim();
        const missing = pill.getAttribute('data-missing') === '1';

        const basename = (s) => {
          const v = String(s || '').trim();
          if (!v) return '';
          const parts = v.split('/');
          return parts[parts.length - 1] || v;
        };

        if (selectedId) {
          const opt = select.querySelector(`option[value="${CSS.escape(selectedId)}"]`);
          const rawName = (opt?.textContent || '').trim();
          const name = basename(rawName) || requested || '(image sélectionnée)';
          pill.textContent = name;
          pill.classList.remove('warn');
          return;
        }

        // No selection: fallback to requested display
        if (requested) {
          pill.textContent = missing ? `Introuvable: ${requested}` : requested;
          pill.classList.toggle('warn', missing);
        } else {
          pill.textContent = '(vide)';
          pill.classList.remove('warn');
        }
      };

      select.addEventListener('change', apply);
      apply();
    });
  }

  function init() {
    // Familles: live updates
    document.querySelectorAll('input.family-final-input').forEach((input) => {
      input.addEventListener('input', () => syncFamilyTitlesAndSelects());
    });

    document.getElementById('addFamilyBtn')?.addEventListener('click', () => {
      const input = document.getElementById('newFamilyName');
      addFamily(input?.value);
      if (input) {
        input.value = '';
        input.focus();
      }
    });

    document.getElementById('newFamilyName')?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        document.getElementById('addFamilyBtn')?.click();
      }
    });

    document.querySelectorAll('.apply-merge').forEach((btn) => {
      btn.addEventListener('click', () => {
        const from = btn.getAttribute('data-from');
        const to = btn.getAttribute('data-to');
        if (!from || !to) return;

        const select = document.querySelector('select.merge-select[data-family-key="' + CSS.escape(from) + '"]');
        if (select) select.value = to;

        refreshMergeSelectOptions();
        refreshFamilySelectOptions();
        applyFamilyMergesRealtime();
      });
    });

    document.querySelectorAll('select.merge-select').forEach((sel) => {
      sel.addEventListener('change', () => {
        // Apply immediately so the user sees the impact in realtime
        refreshMergeSelectOptions();
        refreshFamilySelectOptions();
        applyFamilyMergesRealtime();
      });
    });

    refreshMergeSelectOptions();
    refreshFamilySelectOptions();
    syncFamilyTitlesAndSelects();
    applyFamilyMergesRealtime();

    // Photos: "du moment" checkbox logic
    setupPhotoDuMomentCheckboxes();
    setupPhotoFilenameSync();
  }

  document.addEventListener('DOMContentLoaded', init);
})();
