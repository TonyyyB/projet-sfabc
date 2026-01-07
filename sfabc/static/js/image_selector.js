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
        this.previewComparison = null;
        this.currentImagePreview = null;
        this.newImagePreview = null;

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

                    <div class="image-preview-comparison" id="imagePreviewComparison" style="display: none;">
                        <h3>Aperçu avant/après</h3>
                        <div class="preview-container">
                            <div class="preview-item">
                                <h4>Image actuelle</h4>
                                <div class="preview-image" id="currentImagePreview">
                                    <span class="no-image">Aucune image</span>
                                </div>
                            </div>
                            <div class="preview-item">
                                <h4>Nouvelle image</h4>
                                <div class="preview-image" id="newImagePreview">
                                    <span class="no-image">Sélectionnez une image</span>
                                </div>
                            </div>
                        </div>
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
                        <button class="btn-cancel" id="cancelImageSelection">
                            <span class="material-symbols-outlined">cancel</span>
                            Annuler
                        </button>
                        <button class="btn-submit" id="confirmImageSelection" disabled>
                            <span class="material-symbols-outlined">check</span>
                            Sélectionner
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);

        this.modal = document.getElementById('imageModal');
        this.searchInput = this.modal.querySelector('.image-search-input');
        this.grid = document.getElementById('imageSelectionGrid');
        this.previewComparison = document.getElementById('imagePreviewComparison');
        this.currentImagePreview = document.getElementById('currentImagePreview');
        this.newImagePreview = document.getElementById('newImagePreview');
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

        // Confirmer la sélection
        document.getElementById('confirmImageSelection').addEventListener('click', () => {
            if (this.selectedImage && this.callback) {
                this.callback(this.selectedImage);
            }
            this.close();
        });

        // Échap pour fermer
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.style.display === 'block') {
                this.close();
            }
        });
    }

    async loadImages() {
        try {
            // Récupérer les images depuis l'API Django ou une URL
            const response = await fetch('/admin/images/api/');
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
                { id: 1, name: 'image1.jpg', url: '/media/images/site/image1.jpg' },
                { id: 2, name: 'image2.jpg', url: '/media/images/site/image2.jpg' },
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

        // Mettre à jour l'aperçu de la nouvelle image
        this.updateNewImagePreview(image);

        // Activer le bouton de confirmation
        document.getElementById('confirmImageSelection').disabled = false;
    }

    updateCurrentImagePreview(image) {
        if (image && image.url) {
            this.currentImagePreview.innerHTML = `<img src="${image.url}" alt="${image.name || 'Image actuelle'}" style="max-width: 100%; max-height: 200px; object-fit: contain; border-radius: 8px;">`;
        } else {
            this.currentImagePreview.innerHTML = '<span class="no-image">Aucune image</span>';
        }
    }

    updateNewImagePreview(image) {
        if (image && image.url) {
            this.newImagePreview.innerHTML = `<img src="${image.url}" alt="${image.name || 'Nouvelle image'}" style="max-width: 100%; max-height: 200px; object-fit: contain; border-radius: 8px;">`;
        } else {
            this.newImagePreview.innerHTML = '<span class="no-image">Sélectionnez une image</span>';
        }
    }

    open(callback, currentImage = null) {
        this.callback = callback;
        this.currentImage = currentImage;
        this.selectedImage = null;
        this.searchInput.value = '';
        this.filteredImages = [...this.images];

        // Mettre à jour l'aperçu de l'image actuelle
        this.updateCurrentImagePreview(currentImage);

        // Afficher ou masquer la section d'aperçu selon qu'il y a une image actuelle
        if (currentImage) {
            this.previewComparison.style.display = 'block';
        } else {
            this.previewComparison.style.display = 'none';
        }

        // Désactiver le bouton de confirmation
        document.getElementById('confirmImageSelection').disabled = true;

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
        this.updateCurrentImagePreview(null);
        this.updateNewImagePreview(null);
    }
}

// Initialiser le sélecteur d'images
const imageSelector = new ImageSelector();

// Fonction globale pour ouvrir le sélecteur
function openImageSelector(callback, currentImage = null) {
    imageSelector.open(callback, currentImage);
}

// Attacher les événements aux boutons de sélection d'images
document.addEventListener('DOMContentLoaded', function() {
    // Attacher aux boutons avec la classe image-select-btn
    document.addEventListener('click', function(e) {
        if (e.target.closest('.image-select-btn')) {
            e.preventDefault();
            const button = e.target.closest('.image-select-btn');
            const targetInput = document.getElementById(button.dataset.target);
            const container = button.closest('.image-selector-container');

            // Récupérer l'image actuelle depuis le select caché
            let currentImage = null;
            if (targetInput && targetInput.value) {
                const selectedOption = targetInput.querySelector(`option[value="${targetInput.value}"]`);
                if (selectedOption && selectedOption.textContent.trim()) {
                    // Essayer de récupérer l'URL de l'image depuis les données du bouton ou du formulaire
                    const container = button.closest('.image-select-container, .form-group');
                    const existingImage = container.querySelector('img');
                    if (existingImage) {
                        currentImage = {
                            id: targetInput.value,
                            name: selectedOption.textContent.trim(),
                            url: existingImage.src
                        };
                    }
                }
            }

            openImageSelector(function(selectedImage) {
                if (targetInput) {
                    targetInput.value = selectedImage.id;
                    // Mettre à jour l'aperçu si disponible
                    const previewContainer = container.querySelector('.image-preview-container');
                    if (previewContainer) {
                        previewContainer.style = "";
                        const preview = previewContainer.querySelector('.image-preview');
                        if (preview) {
                            preview.innerHTML = `<img src="${selectedImage.url}" alt="${selectedImage.name}" height="80">`;
                        }
                    }
                }
            }, currentImage);
        }
    });
});