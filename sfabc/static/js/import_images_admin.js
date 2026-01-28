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
  const uploadProgressEl = document.getElementById('uploadProgress');
  const uploadProgressBarEl = document.getElementById('uploadProgressBar');
  const uploadProgressTextEl = document.getElementById('uploadProgressText');

  if (!imagesInput || !desiredNamesInput || !dropzone || !listEl || !submitBtn || !importForm) {
    return;
  }

  let existingNamesLower = new Set();
  let files = [];
  let renameBases = [];

  function humanBytes(bytes) {
    const n = Number(bytes || 0);
    if (!Number.isFinite(n) || n <= 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    const idx = Math.min(units.length - 1, Math.floor(Math.log(n) / Math.log(1024)));
    const value = n / Math.pow(1024, idx);
    const rounded = idx === 0 ? Math.round(value) : Math.round(value * 10) / 10;
    return `${rounded} ${units[idx]}`;
  }

  function setUploadProgress(visible, percent, text) {
    if (!uploadProgressEl) return;
    uploadProgressEl.style.display = visible ? 'block' : 'none';
    if (uploadProgressBarEl && typeof percent === 'number' && Number.isFinite(percent)) {
      const clamped = Math.max(0, Math.min(100, percent));
      uploadProgressBarEl.style.width = `${clamped}%`;
    }
    if (uploadProgressTextEl && typeof text === 'string') {
      uploadProgressTextEl.textContent = text;
    }
  }

  function formatBaseName(value) {
    // Remplacer les espaces par des '_' (convention du projet).
    // On garde le champ éditable: l'utilisateur peut toujours modifier le texte.
    return String(value || '').replaceAll(' ', '_');
  }

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

  function isKnownImageExt(ext) {
    const e = String(ext || '').toLowerCase();
    return (
      e === '.jpg' ||
      e === '.jpeg' ||
      e === '.png' ||
      e === '.gif' ||
      e === '.webp' ||
      e === '.bmp' ||
      e === '.tif' ||
      e === '.tiff' ||
      e === '.svg' ||
      e === '.avif'
    );
  }

  function normalizeInput(text) {
    return formatBaseName((text || '').trim().replaceAll('\n', '').replaceAll('\r', ''));
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
    renameBases = [...renameBases, ...incoming.map((f) => formatBaseName(splitExt(f.name).base))];

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
    const original = formatBaseName(safeBaseName(file.name));
    const { ext } = splitExt(original);
    const userBase = normalizeInput(renameBases[index]);

    if (!userBase) return original;
    if (userBase.includes('/') || userBase.includes('\\')) return null;
    if (userBase === '.' || userBase === '..') return null;

    // allow user typing full name with extension; else preserve original ext
    const typed = safeBaseName(userBase);
    const typedExt = splitExt(typed).ext;
    // Important: a dot in the base name (e.g. "photo.v1") should NOT drop the original extension.
    // We only treat the last ".xxx" as an extension override if it looks like a real image extension.
    if (typedExt && isKnownImageExt(typedExt)) return typed;
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
      if (name && name.includes(' ')) errorsPerIndex[i].push('Espaces interdits : utilisez des "_".');
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
      const hasSomething = files.length > 0;
      submitDisabledNote.style.display = validation.ok || !hasSomething ? 'none' : 'block';
    }
  }

  function updateHiddenInput(wantedNames) {
    if (!files.length) {
      desiredNamesInput.value = '[]';
      return;
    }
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
      title.textContent = wantedFinalNameFor(index) || formatBaseName(safeBaseName(file.name));

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
        // Auto-format: espaces -> '_' tout en gardant un champ éditable.
        const before = input.value;
        const selStart = input.selectionStart;
        const selEnd = input.selectionEnd;
        const formatted = formatBaseName(before);
        if (formatted !== before) {
          input.value = formatted;
          if (typeof selStart === 'number' && typeof selEnd === 'number') {
            input.setSelectionRange(selStart, selEnd);
          }
        }
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
    renameBases = picked.map((f) => formatBaseName(splitExt(f.name).base));
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
      clientValidationEl.textContent = "Import en cours...";
    }

    const url = importForm.action || window.location.href;
    setUploadProgress(true, 0, 'Préparation...');

    const xhr = new XMLHttpRequest();
    xhr.open('POST', url);
    xhr.setRequestHeader('Accept', 'application/json');
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

    xhr.upload.onprogress = (evt) => {
      if (!evt) return;
      if (evt.lengthComputable) {
        const pct = evt.total > 0 ? (evt.loaded / evt.total) * 100 : 0;
        setUploadProgress(true, pct, `Envoi: ${Math.round(pct)}% (${humanBytes(evt.loaded)} / ${humanBytes(evt.total)})`);
        if (pct >= 99.5) {
          setUploadProgress(true, 100, 'Envoi terminé. Traitement...');
        }
      } else {
        setUploadProgress(true, undefined, `Envoi: ${humanBytes(evt.loaded)}...`);
      }
    };

    xhr.onload = () => {
      setUploadProgress(true, 100, 'Traitement terminé.');

      let payload = null;
      try {
        payload = JSON.parse(xhr.responseText || 'null');
      } catch {
        payload = null;
      }

      if (xhr.status >= 200 && xhr.status < 300 && payload?.ok && payload.redirect) {
        window.location.href = payload.redirect;
        return;
      }

      const conflicts = Array.isArray(payload?.conflicts) ? payload.conflicts : [];
      if (xhr.status === 409) {
        conflicts.forEach((c) => existingNamesLower.add(String(c).toLowerCase()));
      }

      if (clientValidationEl) {
        clientValidationEl.style.display = 'block';
        clientValidationEl.textContent =
          payload?.error || "Import refusé par le serveur. Corrigez puis réessayez.";
      }

      submitBtn.disabled = false;
      setUploadProgress(false, 0, '');
      revalidateAndPaint();
    };

    xhr.onerror = () => {
      submitBtn.disabled = false;
      setUploadProgress(false, 0, '');
      if (clientValidationEl) {
        clientValidationEl.style.display = 'block';
        clientValidationEl.textContent = "Erreur réseau pendant l'import. Réessayez.";
      }
    };

    xhr.send(formData);
  });

  // Init
  (async () => {
    await loadExistingNames();
    buildList();
    revalidateAndPaint();
  })();
})();
