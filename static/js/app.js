let map;

document.addEventListener('DOMContentLoaded', () => {
  initMap();
});

function initMap() {
  const mapElement = document.getElementById('map');
  
  // Evitar error si el elemento #map no existe en la plantilla actual
  if (!mapElement) return;

  // Coordenadas iniciales (Sede Puente Alto)
  map = L.map('map').setView([-33.6117, -70.5758], 12);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map);

  // Marcadores de ofertas de muestra
  L.marker([-33.6117, -70.5758]).addTo(map)
    .bindPopup('<b>Tech Solutions Chile</b><br>Practicante Desarrollo TI<br><i>Cerca de Sede Puente Alto</i>');

  L.marker([-33.6200, -70.5800]).addTo(map)
    .bindPopup('<b>Transportes Fregosi</b><br>Soporte TI y Redes<br><i>Cerca de Sede Puente Alto</i>');
}

// Abrir / Cerrar el Chat usando la clase 'hidden' de Tailwind CSS
function toggleChat() {
  const chat = document.getElementById('chatBox');
  if (chat) {
    chat.classList.toggle('hidden');
  }
}

// Enviar mensaje del usuario y respuesta simulada
function sendMessage() {
  const input = document.getElementById('userInput');
  const messages = document.getElementById('chatMessages');

  if (input && messages && input.value.trim() !== '') {
    // 1. Mensaje del usuario
    const userMsg = document.createElement('div');
    userMsg.className = 'bg-blue-900 text-white p-3 rounded-lg max-w-[85%] ml-auto text-sm text-right';
    userMsg.textContent = input.value;
    messages.appendChild(userMsg);

    const promptText = input.value;
    input.value = '';
    messages.scrollTop = messages.scrollHeight;

    // 2. Respuesta simulada del asistente
    setTimeout(() => {
      const aiMsg = document.createElement('div');
      aiMsg.className = 'bg-blue-100 text-blue-900 border border-blue-200 p-3 rounded-lg max-w-[85%] text-sm';
      aiMsg.textContent = "¡Hola! Como asistente de DuocPrácticas, puedo orientarte sobre las vacantes disponibles para tu sede, filtrar por tu carrera o explicarte cómo ampliar tu cobertura con el Plan Premium.";
      messages.appendChild(aiMsg);
      messages.scrollTop = messages.scrollHeight;
    }, 800);
  }
}