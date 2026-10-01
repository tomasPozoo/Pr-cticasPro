document.addEventListener("DOMContentLoaded", function () {
  initMobileMenu();
  initHeroCarousel();
  initFeatureTabs();
  initMap(); // <-- Llamada para inicializar el mapa
});


document.addEventListener("DOMContentLoaded", function () {
  initMobileMenu();
  initHeroCarousel();
  initFeatureTabs();
});

/* ==================== 1. MENÚ MÓVIL ==================== */
function initMobileMenu() {
  const btn = document.getElementById("mobileMenuBtn");
  const menu = document.getElementById("mobileMenu");
  const iconOpen = document.getElementById("menuIconOpen");
  const iconClose = document.getElementById("menuIconClose");

  if (btn && menu) {
    btn.addEventListener("click", function () {
      menu.classList.toggle("hidden");
      if (iconOpen) iconOpen.classList.toggle("hidden");
      if (iconClose) iconClose.classList.toggle("hidden");
    });
  }
}

/* ==================== 2. CARRUSEL HERO ==================== */
let currentHeroSlide = 0;
let heroTimer = null;
const totalHeroSlides = 3;

function goToHeroSlide(index) {
  const slides = document.querySelectorAll(".hero-slide");
  const dots = document.querySelectorAll(".hero-dot");

  if (!slides.length) return;

  currentHeroSlide = (index + totalHeroSlides) % totalHeroSlides;

  slides.forEach((slide, idx) => {
    if (idx === currentHeroSlide) {
      slide.classList.remove("opacity-0", "pointer-events-none");
      slide.classList.add("opacity-100");
    } else {
      slide.classList.remove("opacity-100");
      slide.classList.add("opacity-0", "pointer-events-none");
    }
  });

  dots.forEach((dot, idx) => {
    if (idx === currentHeroSlide) {
      dot.className = "hero-dot w-9 h-2.5 rounded-full bg-amber-400 transition-all duration-300";
    } else {
      dot.className = "hero-dot w-2.5 h-2.5 rounded-full bg-white/40 hover:bg-white/80 transition-all duration-300";
    }
  });

  resetHeroAutoplay();
}

function nextHeroSlide() {
  goToHeroSlide(currentHeroSlide + 1);
}

function prevHeroSlide() {
  goToHeroSlide(currentHeroSlide - 1);
}

function resetHeroAutoplay() {
  if (heroTimer) clearInterval(heroTimer);
  heroTimer = setInterval(nextHeroSlide, 6000);
}

function initHeroCarousel() {
  const prevBtn = document.getElementById("heroPrevBtn");
  const nextBtn = document.getElementById("heroNextBtn");
  const dots = document.querySelectorAll(".hero-dot");

  if (prevBtn) prevBtn.addEventListener("click", prevHeroSlide);
  if (nextBtn) nextBtn.addEventListener("click", nextHeroSlide);

  dots.forEach((dot) => {
    dot.addEventListener("click", function () {
      const slideIndex = parseInt(this.getAttribute("data-slide"), 10);
      goToHeroSlide(slideIndex);
    });
  });

  resetHeroAutoplay();
}

/* ==================== 3. PESTAÑAS DE HERRAMIENTAS ==================== */
function showFeatureSlide(index) {
  const slide0 = document.getElementById("featureSlide0");
  const slide1 = document.getElementById("featureSlide1");
  const tab0 = document.getElementById("tabFeature0");
  const tab1 = document.getElementById("tabFeature1");

  if (!slide0 || !slide1 || !tab0 || !tab1) return;

  if (index === 0) {
    slide0.classList.remove("hidden", "opacity-0", "scale-95", "absolute", "inset-0");
    slide0.classList.add("opacity-100", "scale-100");

    slide1.classList.add("hidden", "opacity-0", "scale-95", "absolute", "inset-0");
    slide1.classList.remove("opacity-100", "scale-100");

    tab0.className = "px-5 py-2.5 rounded-xl text-xs font-bold transition-all duration-300 bg-amber-400 text-brand-950 shadow-md";
    tab1.className = "px-5 py-2.5 rounded-xl text-xs font-bold transition-all duration-300 text-gray-300 hover:text-white";
  } else {
    slide1.classList.remove("hidden", "opacity-0", "scale-95", "absolute", "inset-0");
    slide1.classList.add("opacity-100", "scale-100");

    slide0.classList.add("hidden", "opacity-0", "scale-95", "absolute", "inset-0");
    slide0.classList.remove("opacity-100", "scale-100");

    tab1.className = "px-5 py-2.5 rounded-xl text-xs font-bold transition-all duration-300 bg-amber-400 text-brand-950 shadow-md";
    tab0.className = "px-5 py-2.5 rounded-xl text-xs font-bold transition-all duration-300 text-gray-300 hover:text-white";
  }
}

function initFeatureTabs() {
  const tab0 = document.getElementById("tabFeature0");
  const tab1 = document.getElementById("tabFeature1");

  if (tab0) tab0.addEventListener("click", () => showFeatureSlide(0));
  if (tab1) tab1.addEventListener("click", () => showFeatureSlide(1));
}


/* ==================== 4. MAPA DE OFERTAS (LEAFLET) ==================== */
function initMap() {
  const mapElement = document.getElementById("map");
  if (!mapElement) return;

  if (typeof L === "undefined") {
    console.error("Error: La librería Leaflet (L) no está cargada.");
    return;
  }

  // Coordenadas de Santiago de Chile
  const santiagoCoords = [-33.4489, -70.6693];

  const map = L.map("map", {
    center: santiagoCoords,
    zoom: 11,
    scrollWheelZoom: false
  });

  // Servidor Esri (Gratuito, estable y sin bloqueos 403 en localhost)
  L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}", {
    maxZoom: 19,
    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS, Intermap, iPC, NRCAN, Esri Japan, METI, Esri China, TomTom'
  }).addTo(map);

  // Marcador de prueba
  const marker = L.marker([-33.4489, -70.6693]).addTo(map);
  marker.bindPopup("<b>PrácticasPro</b><br>Sede Santiago Centro.").openPopup();

  // Reajustar dimensiones para evitar descalibres visuales
  setTimeout(function () {
    map.invalidateSize();
  }, 300);
}