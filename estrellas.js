/* ==========================================================================
   CANVAS DE FÍSICA AVANZADA: FÓRMULAS, PLANETAS 3D, GALAXIA Y COMETAS
   Portal de Prácticas & Becas • Ingeniería Física UNAL Medellín
   Autor: Jimmy Stebym Rosero Barrera
   ========================================================================== */

(() => {
  const canvas = document.getElementById('constellationCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let width = 0;
  let height = 0;
  let frame = 0;
  let lastTime = 0;

  // --- 1. BANCO DE FÓRMULAS CLAVE DE INGENIERÍA FÍSICA ---
  const FORMULAS_DATA = [
    { text: "iℏ ∂ψ/∂t = Ĥψ", size: 17, speed: 0.18, phase: 0.1 },
    { text: "∇ × B = μ₀J + μ₀ε₀ ∂E/∂t", size: 16, speed: 0.22, phase: 1.2 },
    { text: "E² = (pc)² + (m₀c²)²", size: 16, speed: 0.15, phase: 2.3 },
    { text: "Δx · Δp ≥ ℏ/2", size: 17, speed: 0.24, phase: 3.4 },
    { text: "Ĥ = -(ℏ²/2m)∇² + V(r)", size: 16, speed: 0.20, phase: 4.5 },
    { text: "2d sin(θ) = nλ", size: 16, speed: 0.19, phase: 0.8 },
    { text: "R_μν - ½Rg_μν = (8πG/c⁴)T_μν", size: 15, speed: 0.14, phase: 5.1 },
    { text: "S = k_B ln(Ω)", size: 16, speed: 0.21, phase: 1.9 },
    { text: "∇ × E = -∂B/∂t", size: 16, speed: 0.23, phase: 2.8 },
    { text: "∇ · D = ρ_f", size: 16, speed: 0.17, phase: 3.7 },
    { text: "E_n = (n + ½)ℏω", size: 16, speed: 0.19, phase: 4.2 },
    { text: "σ = n e² τ / m*", size: 16, speed: 0.16, phase: 5.6 },
    { text: "n₁ sin(θ₁) = n₂ sin(θ₂)", size: 15, speed: 0.21, phase: 0.4 },
    { text: "F = q(E + v × B)", size: 16, speed: 0.25, phase: 1.7 },
    { text: "λ_dB = h / p", size: 16, speed: 0.18, phase: 3.1 },
    { text: "ρ(E) ∝ √E", size: 16, speed: 0.15, phase: 4.9 }
  ];

  let formulas = [];
  let stars = [];
  let galaxyParticles = [];
  let comets = [];
  let nextCometTime = 2000;

  // --- 2. CONFIGURACIÓN Y REDIMENSIONAMIENTO ---
  function resize() {
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);

    // Inicializar estrellas cuánticas
    const starCount = Math.min(85, Math.max(30, Math.round((width * height) / 16000)));
    stars = Array.from({ length: starCount }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      radius: 0.6 + Math.random() * 1.4,
      phase: Math.random() * Math.PI * 2,
      drift: 0.08 + Math.random() * 0.22
    }));

    // Inicializar fórmulas flotantes en posiciones dispersas
    formulas = FORMULAS_DATA.map((f, i) => {
      const col = i % 4;
      const row = Math.floor(i / 4);
      return {
        ...f,
        x: (col * 0.25 + 0.08 + Math.random() * 0.12) * width,
        y: (row * 0.24 + 0.06 + Math.random() * 0.14) * height,
        driftX: (Math.random() - 0.5) * 0.35,
        driftY: -(0.15 + Math.random() * 0.25),
        oscPhase: f.phase
      };
    });

    // Inicializar partículas de Galaxia Espiral (160 partículas en espiral logarítmica)
    galaxyParticles = [];
    const galaxyArms = 2;
    const particlesPerArm = 80;
    for (let arm = 0; arm < galaxyArms; arm++) {
      const armOffset = arm * Math.PI;
      for (let i = 0; i < particlesPerArm; i++) {
        const distRatio = (i + 1) / particlesPerArm;
        const radius = Math.pow(distRatio, 0.8) * Math.min(width, height) * 0.22;
        const angle = armOffset + distRatio * 3.4 + (Math.random() - 0.5) * 0.35;
        galaxyParticles.push({
          radiusBase: radius,
          angleBase: angle,
          speed: 0.0018 + (1 - distRatio) * 0.0025,
          currentAngle: angle,
          size: 0.8 + Math.random() * 1.6,
          brightness: 0.25 + Math.random() * 0.65
        });
      }
    }
  }

  // --- 3. DIBUJAR GALAXIA ESPIRAL 3D GIRATORIA ---
  function drawGalaxy(centerX, centerY, isDark) {
    ctx.save();
    ctx.translate(centerX, centerY);

    // Inclinación 3D en el plano
    const tiltScaleY = 0.52; // Proyección elíptica inclinada
    const baseColor = isDark ? '0, 229, 255' : '2, 132, 199';
    const coreColor = isDark ? '255, 255, 255' : '15, 23, 42';

    // Núcleo galáctico luminoso
    const coreGrad = ctx.createRadialGradient(0, 0, 0, 0, 0, 28);
    coreGrad.addColorStop(0, `rgba(${coreColor}, ${isDark ? 0.35 : 0.18})`);
    coreGrad.addColorStop(0.5, `rgba(${baseColor}, ${isDark ? 0.15 : 0.08})`);
    coreGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.fillStyle = coreGrad;
    ctx.beginPath();
    ctx.arc(0, 0, 28, 0, Math.PI * 2);
    ctx.fill();

    // Partículas espirales
    for (let i = 0; i < galaxyParticles.length; i++) {
      const p = galaxyParticles[i];
      p.currentAngle += p.speed;
      const x = Math.cos(p.currentAngle) * p.radiusBase;
      const y = Math.sin(p.currentAngle) * p.radiusBase * tiltScaleY;

      ctx.beginPath();
      ctx.arc(x, y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${baseColor}, ${p.brightness * (isDark ? 0.45 : 0.25)})`;
      ctx.fill();
    }
    ctx.restore();
  }

  // --- 4. DIBUJAR PLANETA 3D CON ANILLOS GIRATORIOS ---
  let planetAngle = 0;
  function drawPlanetWithRings(px, py, radius, isDark) {
    ctx.save();
    ctx.translate(px, py);
    planetAngle += 0.003;

    const ringTilt = 0.35; // Perspectiva 3D inclinada
    const ringAngle = -0.38; // Ángulo de rotación del plano ecuatorial
    const ringInnerR = radius * 1.45;
    const ringOuterR = radius * 2.35;

    ctx.rotate(ringAngle);

    // A) MITAD TRASERA DE LOS ANILLOS (Detrás del planeta)
    ctx.save();
    ctx.scale(1, ringTilt);
    ctx.beginPath();
    ctx.arc(0, 0, ringOuterR, Math.PI, Math.PI * 2, false);
    ctx.arc(0, 0, ringInnerR, Math.PI * 2, Math.PI, true);
    ctx.closePath();
    ctx.fillStyle = isDark ? 'rgba(0, 229, 255, 0.12)' : 'rgba(2, 132, 199, 0.10)';
    ctx.fill();
    ctx.strokeStyle = isDark ? 'rgba(0, 229, 255, 0.28)' : 'rgba(2, 132, 199, 0.20)';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.restore();

    // B) ESFERA PLANETARIA 3D CON SOMBREADO RADIAL REAL
    // Deshacer rotación para que la luz provenga siempre de arriba a la izquierda
    ctx.rotate(-ringAngle);

    const grad = ctx.createRadialGradient(
      -radius * 0.35, -radius * 0.35, radius * 0.15,
      0, 0, radius
    );
    if (isDark) {
      grad.addColorStop(0, 'rgba(0, 240, 160, 0.55)');
      grad.addColorStop(0.45, 'rgba(14, 116, 144, 0.45)');
      grad.addColorStop(0.85, 'rgba(15, 23, 42, 0.85)');
      grad.addColorStop(1, 'rgba(8, 12, 20, 0.95)');
    } else {
      grad.addColorStop(0, 'rgba(56, 189, 248, 0.45)');
      grad.addColorStop(0.55, 'rgba(2, 132, 199, 0.30)');
      grad.addColorStop(1, 'rgba(203, 213, 225, 0.70)');
    }

    ctx.beginPath();
    ctx.arc(0, 0, radius, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();

    // Bandas de latitud atmosféricas
    ctx.save();
    ctx.clip();
    ctx.strokeStyle = isDark ? 'rgba(0, 229, 255, 0.15)' : 'rgba(2, 132, 199, 0.12)';
    ctx.lineWidth = 2.5;
    for (let b = -radius + 8; b < radius; b += 12) {
      ctx.beginPath();
      ctx.ellipse(0, b, radius * 1.1, radius * 0.25, 0, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.restore();

    ctx.rotate(ringAngle);

    // C) MITAD FRONTAL DE LOS ANILLOS (Pasan por delante del planeta)
    ctx.save();
    ctx.scale(1, ringTilt);
    ctx.beginPath();
    ctx.arc(0, 0, ringOuterR, 0, Math.PI, false);
    ctx.arc(0, 0, ringInnerR, Math.PI, 0, true);
    ctx.closePath();
    ctx.fillStyle = isDark ? 'rgba(0, 229, 255, 0.18)' : 'rgba(2, 132, 199, 0.14)';
    ctx.fill();
    ctx.strokeStyle = isDark ? 'rgba(0, 229, 255, 0.40)' : 'rgba(2, 132, 199, 0.28)';
    ctx.lineWidth = 1.2;
    ctx.stroke();
    ctx.restore();

    // D) LUNA ORBITAL 3D
    const moonDist = radius * 2.8;
    const moonAngle = planetAngle * 2.2;
    const moonX = Math.cos(moonAngle) * moonDist;
    const moonY = Math.sin(moonAngle) * (moonDist * ringTilt);
    const moonZ = Math.sin(moonAngle);

    ctx.beginPath();
    ctx.arc(moonX, moonY, 4, 0, Math.PI * 2);
    ctx.fillStyle = isDark ? (moonZ > 0 ? '#00e5ff' : 'rgba(0, 229, 255, 0.3)') : (moonZ > 0 ? '#0284c7' : 'rgba(2, 132, 199, 0.3)');
    ctx.fill();

    ctx.restore();
  }

  // --- 5. COMETAS PERIÓDICOS CON COLA LUMINOSA ---
  function spawnComet() {
    const startFromLeft = Math.random() > 0.5;
    const startX = startFromLeft ? -50 : width + 50;
    const startY = Math.random() * height * 0.6;
    const targetX = startFromLeft ? width + 50 : -50;
    const targetY = startY + (Math.random() * 250 + 100);

    const angle = Math.atan2(targetY - startY, targetX - startX);
    const speed = 7.5 + Math.random() * 4.5;

    comets.push({
      x: startX,
      y: startY,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      length: 85 + Math.random() * 60,
      opacity: 0.85
    });
  }

  function updateAndDrawComets(isDark) {
    for (let i = comets.length - 1; i >= 0; i--) {
      const c = comets[i];
      c.x += c.vx;
      c.y += c.vy;
      c.opacity -= 0.007;

      if (c.opacity <= 0 || c.x < -100 || c.x > width + 100 || c.y > height + 100) {
        comets.splice(i, 1);
        continue;
      }

      // Dibujar cola del cometa
      const tailX = c.x - (c.vx / Math.hypot(c.vx, c.vy)) * c.length;
      const tailY = c.y - (c.vy / Math.hypot(c.vx, c.vy)) * c.length;

      const grad = ctx.createLinearGradient(c.x, c.y, tailX, tailY);
      const color = isDark ? '0, 229, 255' : '2, 132, 199';
      grad.addColorStop(0, `rgba(${color}, ${c.opacity})`);
      grad.addColorStop(1, 'rgba(0, 0, 0, 0)');

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(c.x, c.y);
      ctx.lineTo(tailX, tailY);
      ctx.strokeStyle = grad;
      ctx.lineWidth = 2.2;
      ctx.lineCap = 'round';
      ctx.stroke();

      // Cabeza del cometa
      ctx.beginPath();
      ctx.arc(c.x, c.y, 2.8, 0, Math.PI * 2);
      ctx.fillStyle = isDark ? '#ffffff' : '#0f172a';
      ctx.fill();
      ctx.restore();
    }
  }

  // --- 6. FÓRMULAS DE FÍSICA FLOTANTES Y EN MOVIMIENTO ---
  function updateAndDrawFormulas(isDark) {
    ctx.save();
    ctx.font = '600 15px "JetBrains Mono", monospace';
    const textColor = isDark ? '0, 229, 255' : '2, 132, 199';

    for (let i = 0; i < formulas.length; i++) {
      const f = formulas[i];
      f.oscPhase += 0.012;
      f.x += f.driftX + Math.sin(f.oscPhase) * 0.25;
      f.y += f.driftY;

      // Reingreso continuo cuando salen de pantalla
      if (f.y < -30) {
        f.y = height + 30;
        f.x = Math.random() * width;
      }
      if (f.x < -150) f.x = width + 50;
      if (f.x > width + 150) f.x = -50;

      const opacity = 0.20 + Math.sin(f.oscPhase * 0.8) * 0.12;
      ctx.fillStyle = `rgba(${textColor}, ${isDark ? opacity : opacity * 0.85})`;
      ctx.fillText(f.text, f.x, f.y);
    }
    ctx.restore();
  }

  // --- 7. ESTRELLAS Y MALLA CUÁNTICA INTERACTIVA ---
  function updateAndDrawStars(isDark) {
    const tint = isDark ? '0, 229, 255' : '2, 132, 199';
    const reach = Math.min(140, Math.max(80, width * 0.10));

    for (let i = 0; i < stars.length; i++) {
      const s = stars[i];
      s.phase += 0.015;
      s.x += Math.sin(s.phase * 0.7) * s.drift;
      s.y -= s.drift * 0.35;

      if (s.y < -5) s.y = height + 5;
      if (s.x < -5) s.x = width + 5;
      if (s.x > width + 5) s.x = -5;

      const glow = 0.35 + Math.sin(s.phase) * 0.25;
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.radius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${tint}, ${glow * (isDark ? 0.7 : 0.4)})`;
      ctx.fill();

      // Enlaces cuánticos de proximidad
      for (let j = i + 1; j < stars.length; j++) {
        const other = stars[j];
        const dx = s.x - other.x;
        const dy = s.y - other.y;
        const dist = Math.hypot(dx, dy);

        if (dist < reach) {
          ctx.beginPath();
          ctx.moveTo(s.x, s.y);
          ctx.lineTo(other.x, other.y);
          const lineAlpha = (1 - dist / reach) * (isDark ? 0.10 : 0.06);
          ctx.strokeStyle = `rgba(${tint}, ${lineAlpha})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }
    }
  }

  // --- 8. CICLO PRINCIPAL DE RENDERIZADO (60 FPS) ---
  function render(timestamp) {
    if (!lastTime) lastTime = timestamp;
    const delta = timestamp - lastTime;
    lastTime = timestamp;

    ctx.clearRect(0, 0, width, height);

    const isDark = document.documentElement.dataset.theme !== 'light';

    // A) Galaxia Espiral giratoria en cuadrante superior derecho
    drawGalaxy(width * 0.76, height * 0.28, isDark);

    // B) Planeta gaseoso gigante 3D con anillos en cuadrante inferior izquierdo
    const planetRadius = Math.min(width, height) * 0.052 + 18;
    drawPlanetWithRings(width * 0.18, height * 0.72, planetRadius, isDark);

    // C) Segundo exoplaneta rocoso en cuadrante inferior derecho
    ctx.save();
    const p2Grad = ctx.createRadialGradient(
      width * 0.88 - 8, height * 0.84 - 8, 4,
      width * 0.88, height * 0.84, 22
    );
    p2Grad.addColorStop(0, isDark ? 'rgba(255, 183, 3, 0.45)' : 'rgba(217, 119, 6, 0.35)');
    p2Grad.addColorStop(1, isDark ? 'rgba(15, 23, 42, 0.8)' : 'rgba(203, 213, 225, 0.6)');
    ctx.beginPath();
    ctx.arc(width * 0.88, height * 0.84, 22, 0, Math.PI * 2);
    ctx.fillStyle = p2Grad;
    ctx.fill();
    ctx.restore();

    // D) Fórmulas de Física volando suavemente
    updateAndDrawFormulas(isDark);

    // E) Malla de estrellas cuánticas
    updateAndDrawStars(isDark);

    // F) Generador periódico de cometas
    nextCometTime -= delta;
    if (nextCometTime <= 0) {
      spawnComet();
      nextCometTime = 4000 + Math.random() * 5000;
    }
    updateAndDrawComets(isDark);

    frame = requestAnimationFrame(render);
  }

  function start() {
    cancelAnimationFrame(frame);
    if (!reduceMotion.matches && !document.hidden) {
      frame = requestAnimationFrame(render);
    }
  }

  resize();
  start();
  window.addEventListener('resize', resize, { passive: true });
  document.addEventListener('visibilitychange', start);
  reduceMotion.addEventListener?.('change', start);
  document.getElementById('themeToggle')?.addEventListener('click', () => {
    // Redibujar con los colores del nuevo tema
    setTimeout(() => {
      if (!frame) start();
    }, 50);
  });
})();
