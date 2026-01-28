// === POPUP DE SÉLECTION D'IMAGES ===

class ImageSelector {
    constructor() {
        this.modal = null;
        this.searchInput = null;
        this.grid = null;
        this.selectedImage = null;
        this.currentImage = null;
        this.callback = null;
        this.images = [];
        this.filteredImages = [];
        this.currentImagePreview = null;
        this.newImagePreview = null;
        this.uploadInput = null;

        // Pagination / recherche côté serveur
        this.page = 1;
        this.pageSize = 60;
        this.numPages = 1;
        this.totalCount = 0;
        this.query = '';
        this.isLoading = false;
        this.paginationEl = null;
        this.prevBtn = null;
        this.nextBtn = null;
        this.pageInfoEl = null;
        this.pageSizeSelect = null;
        this._searchDebounceTimer = null;
        this._abortController = null;

        this.init();
    }

    init() {
        this.createModal();
        this.bindEvents();
    }

    createModal() {
        // Créer le HTML du modal
        const modalHTML = `
            <div id="imageModal" class="image-modal">
                <div class="image-modal-content">
                    <div class="image-modal-header">
                        <h2>
                            <span class="material-symbols-outlined">image</span>
                            Sélectionner une image
                        </h2>
                        <button class="image-modal-close">&times;</button>
                    </div>

                    <div class="image-search-container">
                        <input type="text" class="image-search-input" placeholder="Rechercher une image...">
                    </div>

                    <div class="image-pagination" aria-label="Pagination images">
                        <button type="button" class="image-page-btn" id="imagePrevPage" aria-label="Page précédente">
                            <span class="material-symbols-outlined">chevron_left</span>
                        </button>
                        <div class="image-page-info" id="imagePageInfo">Page 1 / 1</div>
                        <button type="button" class="image-page-btn" id="imageNextPage" aria-label="Page suivante">
                            <span class="material-symbols-outlined">chevron_right</span>
                        </button>
                        <div class="image-page-size">
                            <label for="imagePageSizeSelect">/ page</label>
                            <select id="imagePageSizeSelect">
                                <option value="30">30</option>
                                <option value="60" selected>60</option>
                                <option value="120">120</option>
                            </select>
                        </div>
                    </div>

                    <div class="image-modal-body">
                        <div class="image-selection-grid" id="imageSelectionGrid">
                            <!-- Les images seront chargées ici -->
                        </div>
                    </div>

                    <div class="image-modal-footer">
                        <button class="btn-upload btn-submit" id="uploadImageBtn">
                            <span class="material-symbols-outlined">upload</span>
                            Importer une image
                        </button>
                        <input type="file" id="imageUploadInput" accept="image/*" hidden>
                        <button class="btn-cancel" id="cancelImageSelection">
                            <span class="material-symbols-outlined">cancel</span>
                            Annuler
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);

        this.modal = document.getElementById('imageModal');
        this.searchInput = this.modal.querySelector('.image-search-input');
        this.grid = document.getElementById('imageSelectionGrid');
        this.uploadInput = document.getElementById('imageUploadInput');
        this.previewComparison = document.getElementById('imagePreviewComparison');
        this.currentImagePreview = document.getElementById('currentImagePreview');
        this.newImagePreview = document.getElementById('newImagePreview');

        this.paginationEl = this.modal.querySelector('.image-pagination');
        this.prevBtn = document.getElementById('imagePrevPage');
        this.nextBtn = document.getElementById('imageNextPage');
        this.pageInfoEl = document.getElementById('imagePageInfo');
        this.pageSizeSelect = document.getElementById('imagePageSizeSelect');
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    bindEvents() {
        // Fermer le modal
        this.modal.querySelector('.image-modal-close').addEventListener('click', () => this.close());
        document.getElementById('cancelImageSelection').addEventListener('click', () => this.close());

        // Cliquer en dehors du modal pour fermer
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });

        // Recherche en temps réel
        this.searchInput.addEventListener('input', (e) => {
            this.filterImages(e.target.value);
        });

        // Pagination
        this.prevBtn?.addEventListener('click', () => {
            if (this.page > 1 && !this.isLoading) {
                this.page -= 1;
                this.loadImages();
            }
        });
        this.nextBtn?.addEventListener('click', () => {
            if (this.page < this.numPages && !this.isLoading) {
                this.page += 1;
                this.loadImages();
            }
        });
        this.pageSizeSelect?.addEventListener('change', () => {
            const v = parseInt(this.pageSizeSelect.value, 10);
            if (!Number.isNaN(v) && v > 0) {
                this.pageSize = v;
                this.page = 1;
                this.loadImages();
            }
        });

        // Échap pour fermer
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.style.display === 'block') {
                this.close();
            }
        });

        document.getElementById('uploadImageBtn').addEventListener('click', () => {
            this.uploadInput?.click();
        });

        this.uploadInput?.addEventListener('change', async (e) => {
            const file = e.target.files && e.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('image', file);
            formData.append('type', this.imageType);
            formData.append('product_id', this.productId || '');

            try {
                const response = await fetch('/admin/images/upload/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': this.getCSRFToken()
                    }
                });

                if (!response.ok) {
                    throw new Error("Erreur lors de l'upload de l'image");
                }

                const data = await response.json();
                const uploadedImage = data?.image;
                if (!uploadedImage) {
                    throw new Error("Réponse d'upload invalide");
                }

                // Sélectionner immédiatement l'image uploadée et fermer le modal.
                if (this.callback) {
                    this.callback(uploadedImage);
                }
                this.close();
            } catch (error) {
                console.error("Erreur lors de l'upload:", error);
            } finally {
                // Permet de re-sélectionner le même fichier (sinon l'event change peut ne pas se déclencher)
                if (this.uploadInput) {
                    this.uploadInput.value = '';
                }
            }
        });
    }

    setLoading(isLoading) {
        this.isLoading = isLoading;
        if (this.prevBtn) this.prevBtn.disabled = isLoading || this.page <= 1;
        if (this.nextBtn) this.nextBtn.disabled = isLoading || this.page >= this.numPages;
        // Important: ne pas désactiver l'input de recherche, sinon le navigateur retire le focus.
        if (this.pageSizeSelect) this.pageSizeSelect.disabled = isLoading;
        if (this.grid) {
            this.grid.classList.toggle('is-loading', isLoading);
        }
    }

    updatePaginationUI() {
        if (this.pageInfoEl) {
            const countTxt = this.totalCount ? ` • ${this.totalCount} image(s)` : '';
            this.pageInfoEl.textContent = `Page ${this.page} / ${this.numPages}${countTxt}`;
        }
        if (this.prevBtn) this.prevBtn.disabled = this.isLoading || this.page <= 1;
        if (this.nextBtn) this.nextBtn.disabled = this.isLoading || this.page >= this.numPages;
        if (this.pageSizeSelect) {
            this.pageSizeSelect.value = String(this.pageSize);
        }
    }

    async loadImages() {
        try {
            const keepSearchFocus = document.activeElement === this.searchInput;
            this.setLoading(true);

            // Annuler la requête précédente si nécessaire (utile quand on tape vite dans la recherche)
            try {
                this._abortController?.abort();
            } catch (e) {
                // ignore
            }
            this._abortController = new AbortController();

            // Récupérer les images depuis l'API Django (pagination + recherche)
            const baseUrl = this.imageType === 'site' ? '/admin/images/api/' : '/admin/produits/images/api/';
            const params = new URLSearchParams();
            params.set('page', String(this.page || 1));
            params.set('page_size', String(this.pageSize || 60));
            if (this.query) params.set('q', this.query);

            const url = `${baseUrl}?${params.toString()}`;

            const response = await fetch(url, { signal: this._abortController.signal });
            if (!response.ok) {
                throw new Error('Erreur lors du chargement des images');
            }
            const data = await response.json();
            this.images = data.images || [];
            this.filteredImages = [...this.images];

            const p = data.pagination || {};
            this.page = parseInt(p.page || this.page || 1, 10) || 1;
            this.numPages = parseInt(p.num_pages || 1, 10) || 1;
            this.totalCount = parseInt(p.count || 0, 10) || 0;
            this.renderImages();
            this.updatePaginationUI();

            // Restaurer le focus sur la recherche si elle l'avait avant le refresh.
            if (keepSearchFocus && this.searchInput && this.modal?.style?.display === 'block') {
                this.searchInput.focus({ preventScroll: true });
                try {
                    const len = this.searchInput.value.length;
                    this.searchInput.setSelectionRange(len, len);
                } catch (e) {
                    // ignore
                }
            }
        } catch (error) {
            // Ignore les annulations (ex: utilisateur qui retape avant la fin)
            if (error && (error.name === 'AbortError' || String(error).includes('AbortError'))) {
                return;
            }

            console.error('Erreur lors du chargement des images:', error);
            this.images = [];
            this.filteredImages = [];
            this.numPages = 1;
            this.totalCount = 0;
            this.renderImages();
            this.updatePaginationUI();
        } finally {
            this.setLoading(false);
        }
    }

    renderImages() {
        this.grid.innerHTML = '';

        if (this.filteredImages.length === 0) {
            this.grid.innerHTML = '<p style="text-align: center; color: #666; padding: 40px;">Aucune image trouvée</p>';
            return;
        }

        this.filteredImages.forEach(image => {
            const item = document.createElement('div');
            item.className = 'image-selection-item';
            item.dataset.imageId = image.id;

            item.innerHTML = `
                <img src="${image.url}" alt="${image.name}" loading="lazy">
                <div class="image-name">${image.name}</div>
            `;

            item.addEventListener('click', () => this.selectImage(image, item));
            this.grid.appendChild(item);
        });
    }

    filterImages(query) {
        // Recherche côté serveur (debounce)
        this.query = String(query || '').trim();
        this.page = 1;

        if (this._searchDebounceTimer) {
            clearTimeout(this._searchDebounceTimer);
        }
        this._searchDebounceTimer = setTimeout(() => {
            this.loadImages();
        }, 250);
    }

    selectImage(image, element) {
        // Désélectionner l'ancienne image
        const previouslySelected = this.modal.querySelector('.image-selection-item.selected');
        if (previouslySelected) {
            previouslySelected.classList.remove('selected');
        }

        // Sélectionner la nouvelle image
        element.classList.add('selected');
        this.selectedImage = image;

        // Validation immédiate (plus de bouton "Sélectionner")
        if (this.callback) {
            this.callback(image);
        }
        this.close();
    }

    updateNewImagePreview(image) {
        if (!this.newImagePreview) return;
        if (image && image.url) {
            this.newImagePreview.innerHTML = `<img src="${image.url}" alt="${image.name || 'Nouvelle image'}" style="max-width: 100%; max-height: 200px; object-fit: contain; border-radius: 8px;">`;
        } else {
            this.newImagePreview.innerHTML = '<span class="no-image">Sélectionnez une image</span>';
        }
    }

    open(callback, currentImage = null, imageType = 'site', productId = null) {
        this.callback = callback;
        this.imageType = imageType;
        this.productId = productId;
        this.currentImage = currentImage;
        this.selectedImage = null;
        this.searchInput.value = '';
        this.query = '';
        this.page = 1;
        this.filteredImages = [];

        // Mettre à jour l'aperçu de l'image actuelle
        //this.updateCurrentImagePreview(currentImage);

        // Charger la première page (toujours serveur)
        this.loadImages();

        // Afficher le modal
        this.modal.style.display = 'block';
        document.body.style.overflow = 'hidden';

        // Focus sur la recherche
        setTimeout(() => this.searchInput.focus(), 100);
    }

    close() {
        this.modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        this.selectedImage = null;
        this.currentImage = null;
        this.callback = null;

        // Réinitialiser les aperçus
        //this.updateCurrentImagePreview(null);
        this.updateNewImagePreview(null);
    }
}

// Initialiser le sélecteur d'images
const imageSelector = new ImageSelector();

// Fonction globale pour ouvrir le sélecteur
function openImageSelector(callback, currentImage = null, imageType = 'site', productId = null) {
    imageSelector.open(callback, currentImage, imageType, productId);
}

// Attacher les événements aux boutons de sélection d'images
document.addEventListener('DOMContentLoaded', function () {
    const displayName = (name) => {
        const s = String(name || '').trim();
        if (!s) return '';
        const parts = s.split('/');
        return parts[parts.length - 1] || s;
    };

    const updateClosestPhotoPill = (buttonEl, newName) => {
        try {
            const photoItem = buttonEl?.closest?.('.photo-item');
            if (!photoItem) return;
            const pill = photoItem.querySelector('[data-role="photo-filename"]') || photoItem.querySelector('.photo-title .pill');
            if (!pill) return;
            pill.textContent = newName || pill.textContent;
            pill.classList.remove('warn');
            if (pill.getAttribute('data-missing') === '1') {
                pill.setAttribute('data-missing', '0');
            }
        } catch (e) {
            // ignore
        }
    };

    // Attacher aux boutons avec la classe image-select-btn
    document.addEventListener('click', function (e) {
        if (e.target.closest('.image-select-btn')) {
            e.preventDefault();
            const button = e.target.closest('.image-select-btn');
            const container = button.closest('.image-selector-container');
            const card = button.closest('.image-card') || container;
            const imageType = button.dataset.imageType || 'site';
            const productId = button.dataset.productId || null;
            
            // Chercher le select de manière relative au conteneur
            // - services : ...-image
            // - produits : ...-image_existing
            if (!container) return;
            const targetInput = container.querySelector('select[name$="-image"], select[name$="-image_existing"]');
            
            console.log(button.dataset);
            console.log(imageType);

            // Récupérer l'image actuelle depuis le select caché
            let currentImage = null;
            if (targetInput && targetInput.value) {
                const selectedOption = targetInput.querySelector(`option[value="${targetInput.value}"]`);
                if (selectedOption && selectedOption.textContent.trim()) {
                    // Essayer de récupérer l'URL de l'image depuis les données du bouton ou du formulaire
                    const existingImage = card ? card.querySelector('.image-preview-container img') : null;
                    if (existingImage) {
                        currentImage = {
                            id: targetInput.value,
                            name: selectedOption.textContent.trim(),
                            url: existingImage.src
                        };
                    }
                }
            }

            openImageSelector(function (selectedImage) {
                if (targetInput) {
                    const prettyName = displayName(selectedImage?.name);
                    let option = targetInput.querySelector(
                        `option[value="${selectedImage.id}"]`
                    );
                    console.log(targetInput);

                    // Si l'option n'existe pas encore (image uploadée)
                    if (!option) {
                        option = document.createElement("option");
                        option.value = selectedImage.id;
                        option.textContent = prettyName || selectedImage.name;
                        targetInput.appendChild(option);
                    } else {
                        // Keep text in sync (useful after upload)
                        option.textContent = prettyName || selectedImage.name;
                    }
                    targetInput.value = selectedImage.id;
                    try {
                        targetInput.dispatchEvent(new Event('change', { bubbles: true }));
                    } catch (e) {
                        // ignore
                    }

                    // Import produits page: update the filename pill immediately
                    updateClosestPhotoPill(button, prettyName || selectedImage.name);

                    // Mettre à jour l'aperçu si disponible
                    if (card) {
                        const previewContainers = card.querySelectorAll('.image-preview-container');
                        const previewContainer = previewContainers[previewContainers.length - 1];
                        if (previewContainer) {
                            previewContainer.style.display = "block";
                            previewContainer.querySelector('.image-preview').innerHTML =
                                `<img src="${selectedImage.url}" alt="${prettyName || selectedImage.name}" height="80">`;
                        }
                    }
                }
            }, currentImage, imageType, productId);
        }
    });
});