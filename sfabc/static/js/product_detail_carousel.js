document.addEventListener("DOMContentLoaded", () => {
  const carousel = document.getElementById("carousel");
  if (!carousel) return;

  const carouselInner = carousel.querySelector(".carousel-inner");
  const images = Array.from(carousel.querySelectorAll("img.carousel-img"));

  if (!carouselInner || images.length === 0) return;

  const computeMaxHeight = () => {
    const width = carouselInner.clientWidth;
    if (!width) return;

    let maxHeight = 0;

    for (const img of images) {
      if (!img.naturalWidth || !img.naturalHeight) continue;

      const scale = width / img.naturalWidth;
      const scaledHeight = img.naturalHeight * scale;
      if (scaledHeight > maxHeight) maxHeight = scaledHeight;
    }

    if (maxHeight > 0) {
      carouselInner.style.height = `${Math.ceil(maxHeight)}px`;
    }
  };

  const waitForImagesThenCompute = () => {
    const unloaded = images.filter((img) => !img.complete || img.naturalWidth === 0);
    if (unloaded.length === 0) {
      computeMaxHeight();
      return;
    }

    let remaining = unloaded.length;
    const onDone = () => {
      remaining -= 1;
      if (remaining <= 0) {
        computeMaxHeight();
      }
    };

    for (const img of unloaded) {
      img.addEventListener("load", onDone, { once: true });
      img.addEventListener("error", onDone, { once: true });
    }
  };

  let resizeTimeout;
  const onResize = () => {
    window.clearTimeout(resizeTimeout);
    resizeTimeout = window.setTimeout(computeMaxHeight, 100);
  };

  waitForImagesThenCompute();
  window.addEventListener("resize", onResize);

  // Recalcule après un slide (utile si scrollbar/largeur change, ou fonts/layout).
  carousel.addEventListener("slid.bs.carousel", computeMaxHeight);
});
