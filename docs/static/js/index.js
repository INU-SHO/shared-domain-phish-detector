// SHS Phishing Detector Project Page - JavaScript

// ===== Scroll to Top Button =====
const scrollToTopButton = document.querySelector(".scroll-to-top");

window.addEventListener("scroll", () => {
  if (window.pageYOffset > 300) {
    scrollToTopButton.classList.add("visible");
  } else {
    scrollToTopButton.classList.remove("visible");
  }
});

function scrollToTop() {
  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
}

// ===== Copy BibTeX to Clipboard =====
function copyBibtex() {
  const bibtexText = document.getElementById("bibtex-text").innerText;
  const copyButton = document.querySelector(".copy-button");

  navigator.clipboard
    .writeText(bibtexText)
    .then(() => {
      const originalHTML = copyButton.innerHTML;
      copyButton.innerHTML =
        '<span class="icon"><i class="fas fa-check"></i></span><span>Copied!</span>';
      copyButton.classList.add("copied");

      setTimeout(() => {
        copyButton.innerHTML = originalHTML;
        copyButton.classList.remove("copied");
      }, 2000);
    })
    .catch((err) => {
      console.error("Failed to copy text: ", err);
      // Fallback for older browsers
      const textArea = document.createElement("textarea");
      textArea.value = bibtexText;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand("copy");
      document.body.removeChild(textArea);

      const originalHTML = copyButton.innerHTML;
      copyButton.innerHTML =
        '<span class="icon"><i class="fas fa-check"></i></span><span>Copied!</span>';
      copyButton.classList.add("copied");

      setTimeout(() => {
        copyButton.innerHTML = originalHTML;
        copyButton.classList.remove("copied");
      }, 2000);
    });
}

// ===== Smooth Scroll for Anchor Links =====
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute("href"));
    if (target) {
      target.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  });
});

// ===== Console Message =====
console.log(
  "%cDetecting Phishing on Shared-Domain Hosting Services",
  "color: #3273dc; font-size: 16px; font-weight: bold;"
);
console.log(
  "%cPaper: ARES 2026 | Code: https://github.com/INU-SHO/shared-domain-phish-detector",
  "color: #666; font-size: 12px;"
);
