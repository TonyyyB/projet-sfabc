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

  const topSection = document.querySelector(".top-section");
  const searchToggle = document.querySelector(".search-toggle");
  const searchForm = document.querySelector(".search-form");
  const searchInput = document.querySelector(".search-form input[type='search']");

  if (topSection && searchToggle && searchForm && searchInput) {
    const searchToggleIcon = searchToggle.querySelector("i");

    const closeSearch = () => {
      topSection.classList.remove("search-open");
      searchToggle.setAttribute("aria-expanded", "false");
      searchToggle.setAttribute("aria-label", "Ouvrir la recherche");
      if (searchToggleIcon) {
        searchToggleIcon.classList.remove("bi-x-lg");
        searchToggleIcon.classList.add("bi-search");
      }
    };

    const openSearch = () => {
      topSection.classList.add("search-open");
      searchToggle.setAttribute("aria-expanded", "true");
      searchToggle.setAttribute("aria-label", "Fermer la recherche");
      if (searchToggleIcon) {
        searchToggleIcon.classList.remove("bi-search");
        searchToggleIcon.classList.add("bi-x-lg");
      }
      setTimeout(() => searchInput.focus(), 0);
    };

    searchToggle.addEventListener("click", (e) => {
      e.preventDefault();
      const isOpen = topSection.classList.contains("search-open");
      if (isOpen) {
        closeSearch();
      } else {
        openSearch();
      }
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && topSection.classList.contains("search-open")) {
        closeSearch();
      }
    });

    document.addEventListener("click", (e) => {
      if (!topSection.classList.contains("search-open")) return;
      if (topSection.contains(e.target)) return;
      closeSearch();
    });
  }
});
