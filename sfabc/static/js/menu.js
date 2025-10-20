document.addEventListener("DOMContentLoaded", () => {
  const toggles = document.querySelectorAll("[data-bs-toggle='collapse']");
  toggles.forEach(btn => {
    const icon = btn.querySelector("i");
    const target = document.querySelector(btn.dataset.bsTarget);

    target.addEventListener("show.bs.collapse", () => {
      icon.classList.remove("bi-chevron-right");
      icon.classList.add("bi-chevron-down");
    });
    target.addEventListener("hide.bs.collapse", () => {
      icon.classList.remove("bi-chevron-down");
      icon.classList.add("bi-chevron-right");
    });
  });
});
