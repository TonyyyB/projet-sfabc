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

                this.images.unshift(uploadedImage);
                this.filteredImages = [...this.images];
                this.renderImages();

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

    async loadImages() {
        try {
            // Récupérer les images depuis l'API Django ou une URL
            const url = this.imageType === 'site' ? '/admin/images/api/' : '/admin/produits/images/api/';
            console.log(url);
            console.log(this.imageType);
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error('Erreur lors du chargement des images');
            }
            const data = await response.json();
            this.images = data.images || [];
            this.filteredImages = [...this.images];
            this.renderImages();
        } catch (error) {
            console.error('Erreur lors du chargement des images:', error);
            // Fallback: utiliser des données statiques si l'API n'est pas disponible
            this.images = [

            ];
            this.filteredImages = [...this.images];
            this.renderImages();
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
        this.filteredImages = [...this.images];

        // Mettre à jour l'aperçu de l'image actuelle
        //this.updateCurrentImagePreview(currentImage);

        // Charger les images si ce n'est pas déjà fait
        if (this.images.length === 0) {
            this.loadImages();
        } else {
            this.renderImages();
        }

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
                    let option = targetInput.querySelector(
                        `option[value="${selectedImage.id}"]`
                    );
                    console.log(targetInput);

                    // Si l'option n'existe pas encore (image uploadée)
                    if (!option) {
                        option = document.createElement("option");
                        option.value = selectedImage.id;
                        option.textContent = selectedImage.name;
                        targetInput.appendChild(option);
                    }
                    targetInput.value = selectedImage.id;
                    // Mettre à jour l'aperçu si disponible
                    if (card) {
                        const previewContainers = card.querySelectorAll('.image-preview-container');
                        const previewContainer = previewContainers[previewContainers.length - 1];
                        if (previewContainer) {
                            previewContainer.style.display = "block";
                            previewContainer.querySelector('.image-preview').innerHTML =
                                `<img src="${selectedImage.url}" alt="${selectedImage.name}" height="80">`;
                        }
                    }
                }
            }, currentImage, imageType, productId);
        }
    });
});