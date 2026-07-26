document.addEventListener("DOMContentLoaded", function () {
  var toggle = document.querySelector("[data-ag-menu-toggle]");
  var mobileNav = document.querySelector("[data-ag-mobile-nav]");

  if (toggle && mobileNav) {
    toggle.addEventListener("click", function () {
      var isOpen = !mobileNav.hidden;
      mobileNav.hidden = isOpen;
      toggle.setAttribute("aria-expanded", String(!isOpen));
    });
  }

  var slides = document.querySelectorAll(".ag-hero-slide");
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (slides.length > 1 && !reduceMotion) {
    var current = 0;
    setInterval(function () {
      slides[current].classList.remove("active");
      current = (current + 1) % slides.length;
      slides[current].classList.add("active");
    }, 5000);
  }
});
