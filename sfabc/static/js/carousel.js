/**
 * Carrousel custom simple avec transition slide
 * Usage: Ajouter la classe 'custom-carousel' sur un conteneur
 * avec des images à l'intérieur et des boutons avec data-carousel-prev/next
 */
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('.custom-carousel').forEach(carousel => {
    const slidesContainer = carousel.querySelector('.carousel-slides');
    const slides = Array.from(carousel.querySelectorAll('.carousel-slide'));
    const prevBtn = carousel.querySelector('[data-carousel-prev]');
    const nextBtn = carousel.querySelector('[data-carousel-next]');
    
    if (slides.length === 0 || !slidesContainer) return;
    
    let currentIndex = 0;
    
    const updateCarousel = () => {
      slidesContainer.style.transform = `translateX(-${currentIndex * 100}%)`;
    };
    
    const goToSlide = (index) => {
      currentIndex = (index + slides.length) % slides.length;
      updateCarousel();
    };
    
    if (prevBtn) {
      prevBtn.addEventListener('click', () => goToSlide(currentIndex - 1));
    }
    
    if (nextBtn) {
      nextBtn.addEventListener('click', () => goToSlide(currentIndex + 1));
    }
    
    // Initialisation
    updateCarousel();
  });
});
