(() => {
  const scriptEl = document.currentScript;
  const existingNamesUrl = scriptEl?.dataset?.existingNamesUrl;

  const imagesInput = document.getElementById('imagesInput');
  const desiredNamesInput = document.getElementById('desiredNamesInput');
  const dropzone = document.getElementById('dropzone');
  const listEl = document.getElementById('selectedFiles');
  const clientValidationEl = document.getElementById('clientValidation');
  const submitBtn = document.getElementById('submitBtn');
  const submitDisabledNote = document.getElementById('submitDisabledNote');
  const importForm = document.getElementById('importForm');

  if (!imagesInput || !desiredNamesInput || !dropzone || !listEl || !submitBtn || !importForm) {
    return;
  }

  let existingNamesLower = new Set();
  let files = [];
  let renameBases = [];

  function safeBaseName(filename) {
    const normalized = String(filename || '').replaceAll('\\', '/');
    const parts = normalized.split('/');
    return parts[parts.length - 1];
  }

  function splitExt(filename) {
    const name = safeBaseName(filename);
    const dot = name.lastIndexOf('.');
    if (dot <= 0) return { base: name, ext: '' };
    return { base: name.slice(0, dot), ext: name.slice(dot) };
  }

  function normalizeInput(text) {
    return (text || '').trim().replaceAll('\n', '').replaceAll('\r', '');
  }

  function isImageFile(file) {
    return file && typeof file.type === 'string' && file.type.startsWith('image/');
  }

  async function loadExistingNames() {
    if (!existingNamesUrl) {
      existingNamesLower = new Set();
      return;
    }
    try {
      const res = await fetch(existingNamesUrl, { headers: { Accept: 'application/json' } });
      if (!res.ok) {
        existingNamesLower = new Set();
        return;
      }
      const data = await res.json();
      const names = (data.names || []).map(safeBaseName).map((n) => n.toLowerCase());
      existingNamesLower = new Set(names);
    } catch {
      existingNamesLower = new Set();
    }
  }

  function setInputFilesFromArray(nextFiles) {
    const dt = new DataTransfer();
    nextFiles.forEach((f) => dt.items.add(f));
    imagesInput.files = dt.files;
  }

  function addFiles(newFiles) {
    const incoming = Array.from(newFiles || []).filter(isImageFile);
    if (!incoming.length) return;

    files = [...files, ...incoming];
    renameBases = [...renameBases, ...incoming.map((f) => splitExt(f.name).base)];

    setInputFilesFromArray(files);
    buildList();
    loadExistingNames().then(() => revalidateAndPaint());
  }

  function removeFileAt(index) {
    files = files.filter((_, i) => i !== index);
    renameBases = renameBases.filter((_, i) => i !== index);
    setInputFilesFromArray(files);
    buildList();
    loadExistingNames().then(() => revalidateAndPaint());
  }

  function wantedFinalNameFor(index) {
    const file = files[index];
    const original = safeBaseName(file.name);
    const { ext } = splitExt(original);
    const userBase = normalizeInput(renameBases[index]);

    if (!userBase) return original;
    if (userBase.includes('/') || userBase.includes('\\')) return null;
    if (userBase === '.' || userBase === '..') return null;

    // allow user typing full name with extension; else preserve original ext
    const typed = safeBaseName(userBase);
    const typedExt = splitExt(typed).ext;
    if (typedExt) return typed;
    return `${typed}${ext}`;
  }

  function validateAll() {
    const errorsPerIndex = files.map(() => []);

    if (!files.length) {
      return { ok: false, errorsPerIndex, globalErrors: ['Veuillez ajouter au moins une image.'], wantedNames: [] };
    }

    const wantedNames = files.map((_, i) => wantedFinalNameFor(i));
    wantedNames.forEach((name, i) => {
      if (!name) errorsPerIndex[i].push('Nom invalide (pas de / ou \\).');
    });

    // duplicates in selection (case-insensitive)
    const counts = new Map();
    wantedNames.forEach((name) => {
      if (!name) return;
      const key = name.toLowerCase();
      counts.set(key, (counts.get(key) || 0) + 1);
    });
    wantedNames.forEach((name, i) => {
      if (!name) return;
      const key = name.toLowerCase();
      if ((counts.get(key) || 0) > 1) {
        errorsPerIndex[i].push('Doublon dans la sélection (un autre fichier a le même nom).');
      }
    });

    // duplicates with existing (case-insensitive)
    wantedNames.forEach((name, i) => {
      if (!name) return;
      if (existingNamesLower.has(name.toLowerCase())) {
        errorsPerIndex[i].push('Ce nom existe déjà (déjà importé).');
      }
    });

    const globalErrors = [];

    const ok = errorsPerIndex.every((arr) => arr.length === 0) && files.length > 0;
    return { ok, errorsPerIndex, globalErrors, wantedNames };
  }

  function updateSubmitState(validation) {
    submitBtn.disabled = !validation.ok;
    if (submitDisabledNote) {
      const hasFiles = files.length > 0;
      submitDisabledNote.style.display = validation.ok || !hasFiles ? 'none' : 'block';
    }
  }

  function updateHiddenInput(wantedNames) {
    const payload = wantedNames.map((n, i) => n || safeBaseName(files[i].name));
    desiredNamesInput.value = JSON.stringify(payload);
  }

  function renderValidationBanner(validation) {
    if (!clientValidationEl) return;

    // Tant qu'aucune image n'est sélectionnée, on ne montre pas d'erreur.
    if (files.length === 0) {
      clientValidationEl.style.display = 'none';
      clientValidationEl.textContent = '';
      return;
    }

    const hasBlocking = !validation.ok;
    const messages = [];
    if (hasBlocking) messages.push('Import bloqué : corrigez les noms en rouge.');
    validation.globalErrors.forEach((m) => messages.push(m));

    if (!messages.length) {
      clientValidationEl.style.display = 'none';
      clientValidationEl.textContent = '';
      return;
    }

    clientValidationEl.style.display = 'block';
    clientValidationEl.textContent = messages.join(' ');
  }

  function buildList() {
    listEl.innerHTML = '';
    listEl.style.display = files.length ? 'block' : 'none';
    listEl.classList.add('import-list');

    files.forEach((file, index) => {
      const { ext } = splitExt(file.name);

      const item = document.createElement('div');
      item.className = 'import-item';
      item.dataset.index = String(index);

      const thumb = document.createElement('div');
      thumb.className = 'import-thumb';
      const img = document.createElement('img');
      img.alt = '';
      img.src = URL.createObjectURL(file);
      img.onload = () => URL.revokeObjectURL(img.src);
      thumb.appendChild(img);

      const meta = document.createElement('div');
      meta.className = 'import-meta';

      const topRow = document.createElement('div');
      topRow.className = 'import-row';

      const left = document.createElement('div');
      const title = document.createElement('div');
      title.className = 'import-filename';
      title.dataset.role = 'title';
      title.textContent = safeBaseName(file.name);

      const hint = document.createElement('div');
      hint.className = 'hint';
      hint.textContent = `Original: ${safeBaseName(file.name)} • ${Math.round(file.size / 1024)} KB`;
      left.appendChild(title);
      left.appendChild(hint);

      const actions = document.createElement('div');
      actions.className = 'import-actions';
      const removeBtn = document.createElement('button');
      removeBtn.type = 'button';
      removeBtn.className = 'btn-icon';
      removeBtn.textContent = 'Retirer';
      removeBtn.addEventListener('click', () => removeFileAt(index));
      actions.appendChild(removeBtn);

      topRow.appendChild(left);
      topRow.appendChild(actions);

      const editor = document.createElement('div');
      editor.className = 'name-editor';

      const input = document.createElement('input');
      input.type = 'text';
      input.value = renameBases[index] ?? '';
      input.placeholder = "Nom (sans changer l'extension)";
      input.dataset.role = 'name-input';
      input.addEventListener('input', () => {
        renameBases[index] = input.value;
        revalidateAndPaint();
      });

      const extPill = document.createElement('span');
      extPill.className = 'ext-pill';
      extPill.textContent = ext || '(sans extension)';

      editor.appendChild(input);
      editor.appendChild(extPill);

      const errorsContainer = document.createElement('div');
      errorsContainer.dataset.role = 'errors';

      meta.appendChild(topRow);
      meta.appendChild(editor);
      meta.appendChild(errorsContainer);

      item.appendChild(thumb);
      item.appendChild(meta);
      listEl.appendChild(item);
    });
  }

  function revalidateAndPaint() {
    const validation = validateAll();
    updateHiddenInput(validation.wantedNames);
    updateSubmitState(validation);
    renderValidationBanner(validation);

    const items = Array.from(listEl.querySelectorAll('.import-item'));
    items.forEach((item) => {
      const index = Number(item.dataset.index);
      const file = files[index];
      if (!file) return;

      const wanted = validation.wantedNames[index] || safeBaseName(file.name);
      const errors = validation.errorsPerIndex[index] || [];

      const titleEl = item.querySelector('[data-role="title"]');
      if (titleEl) titleEl.textContent = wanted;

      const inputEl = item.querySelector('[data-role="name-input"]');
      if (inputEl) {
        if (document.activeElement !== inputEl) {
          inputEl.value = renameBases[index] ?? '';
        }
        inputEl.classList.toggle('is-invalid', errors.length > 0);
      }

      item.classList.toggle('is-invalid', errors.length > 0);

      const errorsContainer = item.querySelector('[data-role="errors"]');
      if (errorsContainer) {
        errorsContainer.innerHTML = '';
        if (errors.length) {
          const ul = document.createElement('ul');
          ul.className = 'import-errors';
          errors.forEach((e) => {
            const li = document.createElement('li');
            li.textContent = e;
            ul.appendChild(li);
          });
          errorsContainer.appendChild(ul);
        }
      }
    });
  }

  // Dropzone events
  dropzone.addEventListener('click', () => imagesInput.click());
  dropzone.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      imagesInput.click();
    }
  });

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('is-dragover');
  });
  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('is-dragover'));
  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('is-dragover');
    addFiles(e.dataTransfer?.files);
  });

  imagesInput.addEventListener('change', () => {
    // If user picks from file dialog, replace selection (consistent with typical UX)
    const picked = Array.from(imagesInput.files || []).filter(isImageFile);
    files = picked;
    renameBases = picked.map((f) => splitExt(f.name).base);
    setInputFilesFromArray(files);
    buildList();
    loadExistingNames().then(() => revalidateAndPaint());
  });

  importForm.addEventListener('submit', (e) => {
    const validation = validateAll();
    updateHiddenInput(validation.wantedNames);

    if (!validation.ok) {
      e.preventDefault();
      revalidateAndPaint();
      return;
    }

    // AJAX submit so we can keep files/names on server-side conflict
    e.preventDefault();

    const formData = new FormData(importForm);
    submitBtn.disabled = true;
    if (submitDisabledNote) submitDisabledNote.style.display = 'none';
    if (clientValidationEl) {
      clientValidationEl.style.display = 'block';
      clientValidationEl.textContent = 'Import en cours...';
    }

    fetch(importForm.action || window.location.href, {
      method: 'POST',
      body: formData,
      credentials: 'same-origin',
      headers: {
        Accept: 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
      },
    })
      .then(async (res) => {
        let payload = null;
        try {
          payload = await res.json();
        } catch {
          payload = null;
        }

        if (res.ok && payload?.ok && payload.redirect) {
          window.location.href = payload.redirect;
          return;
        }

        // Conflict or error: keep selection, show error, and re-enable submit.
        const conflicts = Array.isArray(payload?.conflicts) ? payload.conflicts : [];
        conflicts.forEach((c) => existingNamesLower.add(String(c).toLowerCase()));

        if (clientValidationEl) {
          clientValidationEl.style.display = 'block';
          clientValidationEl.textContent = payload?.error || "Import refusé par le serveur. Corrigez puis réessayez.";
        }

        submitBtn.disabled = false;
        revalidateAndPaint();
      })
      .catch(() => {
        submitBtn.disabled = false;
        if (clientValidationEl) {
          clientValidationEl.style.display = 'block';
          clientValidationEl.textContent = "Erreur réseau pendant l'import. Réessayez.";
        }
      });
  });

  // Init
  (async () => {
    await loadExistingNames();
    buildList();
    revalidateAndPaint();
  })();
})();
