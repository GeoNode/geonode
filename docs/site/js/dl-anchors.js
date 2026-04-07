function slugify(s) {
  return s.toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "")
    .replace(/\s+/g, "-");
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("dl > dt").forEach(dt => {
    if (!dt.id) dt.id = slugify(dt.textContent);
    if (dt.querySelector(".dl-permalink")) return;

    const a = document.createElement("a");
    a.className = "dl-permalink";
    a.href = `#${dt.id}`;
    a.setAttribute("aria-label", "Permalink");
    a.textContent = "¶"; // or "🔗"

    dt.appendChild(a);
  });
});