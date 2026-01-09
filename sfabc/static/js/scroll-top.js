
const btn = document.getElementById("btnScrollTop");

window.addEventListener("scroll", () => {
if (window.scrollY > 300) {
    btn.classList.remove("d-none");
} else {
    btn.classList.add("d-none");
}
});

btn.addEventListener("click", () => {
window.scrollTo({
    top: 0,
    behavior: "smooth"
});
});

