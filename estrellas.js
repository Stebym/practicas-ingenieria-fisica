/* ==========================================================================
   MOTOR DE FÍSICA AVANZADA: LATERALES REPOTENCIADOS
   Planetas 3D, Púlsar, Galaxia Espiral, Paquete de Ondas, Bandas E(k),
   Cometas y Fórmulas Científicas en Movimiento Continuo
   Autor: Jimmy Stebym Rosero Barrera • Universidad Nacional de Colombia
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

  // Medición de corredores laterales (márgenes libres de la pantalla)
  let leftMarginWidth = 260;
  let rightMarginStart = 1660;
  let isWidescreen = true;

  // --- 1. BANCO DE FÓRMULAS PARA EL CORREDOR IZQUIERDO (CUÁNTICA & RELATIVIDAD) ---
  const LEFT_FORMULAS = [
    { text: "iℏ ∂ψ/∂t = Ĥψ", size: 16, color: "cyan", speed: 0.22, y: 120, xOffset: 0.5 },
    { text: "E² = (pc)² + (m₀c²)²", size: 15, color: "amber", speed: 0.18, y: 260, xOffset: 0.4 },
    { text: "Δx · Δp ≥ ℏ/2", size: 16, color: "emerald", speed: 0.24, y: 560, xOffset: 0.6 },
    { text: "Ĥ = -(ℏ²/2m)∇² + V", size: 15, color: "cyan", speed: 0.20, y: 700, xOffset: 0.45 },
    { text: "R_μν - ½Rg_μν = κT_μν", size: 14, color: "violet", speed: 0.16, y: 1020, xOffset: 0.55 },
    { text: "λ_dB = h / p", size: 15, color: "cyan", speed: 0.19, y: 1140, xOffset: 0.35 },
    { text: "S = k_B ln(Ω)", size: 15, color: "emerald", speed: 0.21, y: 1400, xOffset: 0.5 },
    { text: "E_n = (n + ½)ℏω", size: 15, color: "amber", speed: 0.17, y: 1560, xOffset: 0.42 },
    { text: "∇ × E = -∂B/∂t", size: 15, color: "cyan", speed: 0.23, y: 1720, xOffset: 0.58 },
    { text: "ψ(x) ∝ e^{ikx}", size: 15, color: "emerald", speed: 0.19, y: 1900, xOffset: 0.48 }
  ];

  // --- 2. BANCO DE FÓRMULAS PARA EL CORREDOR DERECHO (ELECTROMAGNETISMO, ÓPTICA & MATERIALES) ---
  const RIGHT_FORMULAS = [
    { text: "∇ × B = μ₀J + μ₀ε₀∂E/∂t", size: 15, color: "cyan", speed: 0.20, y: 150, xOffset: 0.5 },
    { text: "2d sin(θ) = nλ", size: 16, color: "amber", speed: 0.22, y: 480, xOffset: 0.45 },
    { text: "n₁ sin(θ₁) = n₂ sin(θ₂)", size: 15, color: "emerald", speed: 0.19, y: 620, xOffset: 0.55 },
    { text: "σ = n e² τ / m*", size: 15, color: "cyan", speed: 0.17, y: 940, xOffset: 0.4 },
    { text: "F = q(E + v × B)", size: 16, color: "amber", speed: 0.25, y: 1060, xOffset: 0.6 },
    { text: "∇ · D = ρ_f", size: 15, color: "cyan", speed: 0.18, y: 1340, xOffset: 0.48 },
    { text: "ρ(E) ∝ √E", size: 15, color: "emerald", speed: 0.16, y: 1480, xOffset: 0.52 },
    { text: "∮ B · dA = 0", size: 15, color: "cyan", speed: 0.21, y: 1640, xOffset: 0.42 },
    { text: "μ = qτ / m*", size: 15, color: "violet", speed: 0.18, y: 1800, xOffset: 0.56 },
    { text: "v_g = dω / dk", size: 15, color: "amber", speed: 0.22, y: 1980, xOffset: 0.46 }
  ];

  let leftFormulasState = [];
  let rightFormulasState = [];
  let stars = [];
  let galaxyParticles = [];
  let comets = [];
  let nextCometTime = 3000;

  // Variables de animación temporal
  let planetAngle = 0;
  let pulsarAngle = 0;
  let waveTime = 0;
  let binaryAngle = 0;

  // --- 3. REDIMENSIONAMIENTO Y CÁLCULO DE MÁRGENES ---
  function updateMargins() {
    const mainEl = document.querySelector('main.main-content');
    if (mainEl) {
      const rect = mainEl.getBoundingClientRect();
      leftMarginWidth = Math.max(0, rect.left);
      rightMarginStart = Math.min(width, rect.right);
      isWidescreen = rect.left > 130;
    } else {
      leftMarginWidth = Math.max(0, (width - 1400) / 2);
      rightMarginStart = width - leftMarginWidth;
      isWidescreen = leftMarginWidth > 130;
    }
  }

  function resize() {
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);

    updateMargins();

    // Inicializar fórmulas laterales
    leftFormulasState = LEFT_FORMULAS.map((f, i) => ({
      ...f,
      phase: i * 0.7,
      currentY: f.y % (height * 1.5)
    }));

    rightFormulasState = RIGHT_FORMULAS.map((f, i) => ({
      ...f,
      phase: i * 0.8 + 1.5,
      currentY: f.y % (height * 1.5)
    }));

    // Estrellas de fondo
    const starCount = Math.min(90, Math.max(35, Math.round((width * height) / 16000)));
    stars = Array.from({ length: starCount }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      radius: 0.6 + Math.random() * 1.3,
      phase: Math.random() * Math.PI * 2,
      drift: 0.08 + Math.random() * 0.22
    }));

    // Partículas de Galaxia Espiral (180 estrellas multicolores)
    galaxyParticles = [];
    const galaxyArms = 2;
    const particlesPerArm = 90;
    for (let arm = 0; arm < galaxyArms; arm++) {
      const armOffset = arm * Math.PI;
      for (let i = 0; i < particlesPerArm; i++) {
        const distRatio = (i + 1) / particlesPerArm;
        const radius = Math.pow(distRatio, 0.78) * 88;
        const angle = armOffset + distRatio * 3.6 + (Math.random() - 0.5) * 0.32;
        const isCore = distRatio < 0.3;
        galaxyParticles.push({
          radiusBase: radius,
          angleBase: angle,
          speed: 0.0020 + (1 - distRatio) * 0.0028,
          currentAngle: angle,
          size: 0.7 + Math.random() * 1.5,
          colorType: isCore ? 'amber' : (Math.random() > 0.4 ? 'cyan' : 'violet'),
          brightness: 0.35 + Math.random() * 0.65
        });
      }
    }
  }

  // --- 4. RENDERIZADO: PLANETA GASEOSO 3D CON ANILLOS (LATERAL IZQUIERDO) ---
  function drawPlanetWithRings(cx, cy, radius, isDark) {
    ctx.save();
    ctx.translate(cx, cy);
    planetAngle += 0.0035;

    const ringTilt = 0.32;
    const ringAngle = -0.36;
    const ringInnerR = radius * 1.40;
    const ringOuterR = radius * 2.30;

    ctx.rotate(ringAngle);

    // A) MITAD TRASERA DE ANILLOS (Detrás de la esfera)
    ctx.save();
    ctx.scale(1, ringTilt);
    ctx.beginPath();
    ctx.arc(0, 0, ringOuterR, Math.PI, Math.PI * 2, false);
    ctx.arc(0, 0, ringInnerR, Math.PI * 2, Math.PI, true);
    ctx.closePath();
    ctx.fillStyle = isDark ? 'rgba(0, 229, 255, 0.18)' : 'rgba(2, 132, 199, 0.14)';
    ctx.fill();
    ctx.strokeStyle = isDark ? 'rgba(0, 229, 255, 0.45)' : 'rgba(2, 132, 199, 0.30)';
    ctx.lineWidth = 1.2;
    ctx.stroke();
    ctx.restore();

    ctx.rotate(-ringAngle);

    // B) ESFERA PLANETARIA 3D CON SOMBREADO ILUMINADO
    const grad = ctx.createRadialGradient(
      -radius * 0.35, -radius * 0.35, radius * 0.12,
      0, 0, radius
    );
    if (isDark) {
      grad.addColorStop(0, 'rgba(0, 240, 160, 0.75)');
      grad.addColorStop(0.40, 'rgba(14, 116, 144, 0.65)');
      grad.addColorStop(0.80, 'rgba(15, 23, 42, 0.92)');
      grad.addColorStop(1, 'rgba(8, 12, 20, 0.98)');
    } else {
      grad.addColorStop(0, 'rgba(56, 189, 248, 0.65)');
      grad.addColorStop(0.50, 'rgba(2, 132, 199, 0.45)');
      grad.addColorStop(1, 'rgba(148, 163, 184, 0.85)');
    }

    ctx.beginPath();
    ctx.arc(0, 0, radius, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();

    // Bandas de nubes atmosféricas
    ctx.save();
    ctx.clip();
    ctx.strokeStyle = isDark ? 'rgba(0, 229, 255, 0.22)' : 'rgba(2, 132, 199, 0.18)';
    ctx.lineWidth = 2.4;
    for (let b = -radius + 8; b < radius; b += 11) {
      ctx.beginPath();
      ctx.ellipse(0, b, radius * 1.05, radius * 0.24, 0, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.restore();

    ctx.rotate(ringAngle);

    // C) MITAD FRONTAL DE ANILLOS (Delante de la esfera)
    ctx.save();
    ctx.scale(1, ringTilt);
    ctx.beginPath();
    ctx.arc(0, 0, ringOuterR, 0, Math.PI, false);
    ctx.arc(0, 0, ringInnerR, Math.PI, 0, true);
    ctx.closePath();
    ctx.fillStyle = isDark ? 'rgba(0, 229, 255, 0.25)' : 'rgba(2, 132, 199, 0.20)';
    ctx.fill();
    ctx.strokeStyle = isDark ? 'rgba(0, 229, 255, 0.60)' : 'rgba(2, 132, 199, 0.40)';
    ctx.lineWidth = 1.4;
    ctx.stroke();
    ctx.restore();

    // D) LUNA ORBITAL EN PERSPECTIVA 3D
    const moonDist = radius * 2.75;
    const moonAngle = planetAngle * 2.4;
    const moonX = Math.cos(moonAngle) * moonDist;
    const moonY = Math.sin(moonAngle) * (moonDist * ringTilt);
    const moonZ = Math.sin(moonAngle);

    ctx.beginPath();
    ctx.arc(moonX, moonY, 4.2, 0, Math.PI * 2);
    ctx.fillStyle = isDark
      ? (moonZ > 0 ? '#00e5ff' : 'rgba(0, 229, 255, 0.35)')
      : (moonZ > 0 ? '#0284c7' : 'rgba(2, 132, 199, 0.35)');
    ctx.fill();

    ctx.restore();
  }

  // --- 5. RENDERIZADO: PÚLSAR / ESTRELLA DE NEUTRONES (LATERAL IZQUIERDO) ---
  function drawPulsar(cx, cy, isDark) {
    ctx.save();
    ctx.translate(cx, cy);
    pulsarAngle += 0.045;

    const coreColor = isDark ? '#ffffff' : '#0f172a';
    const beamColor = isDark ? '0, 229, 255' : '2, 132, 199';

    // Haz de radiación relativista giratorio (Conos opuestos 3D)
    ctx.save();
    ctx.rotate(pulsarAngle);

    const beamLen = 65;
    const beamWidth = 14;

    const gradTop = ctx.createLinearGradient(0, 0, 0, -beamLen);
    gradTop.addColorStop(0, `rgba(${beamColor}, 0.8)`);
    gradTop.addColorStop(1, 'rgba(0, 0, 0, 0)');

    ctx.beginPath();
    ctx.moveTo(-beamWidth / 2, -beamLen);
    ctx.lineTo(beamWidth / 2, -beamLen);
    ctx.lineTo(0, 0);
    ctx.closePath();
    ctx.fillStyle = gradTop;
    ctx.fill();

    const gradBottom = ctx.createLinearGradient(0, 0, 0, beamLen);
    gradBottom.addColorStop(0, `rgba(${beamColor}, 0.8)`);
    gradBottom.addColorStop(1, 'rgba(0, 0, 0, 0)');

    ctx.beginPath();
    ctx.moveTo(-beamWidth / 2, beamLen);
    ctx.lineTo(beamWidth / 2, beamLen);
    ctx.lineTo(0, 0);
    ctx.closePath();
    ctx.fillStyle = gradBottom;
    ctx.fill();

    ctx.restore();

    // Líneas del campo magnético dipolar
    ctx.strokeStyle = isDark ? 'rgba(0, 240, 160, 0.25)' : 'rgba(5, 150, 105, 0.22)';
    ctx.lineWidth = 1;
    for (let r = 18; r <= 38; r += 10) {
      ctx.beginPath();
      ctx.ellipse(-r * 0.4, 0, r * 0.7, r, 0, 0, Math.PI * 2);
      ctx.stroke();
      ctx.beginPath();
      ctx.ellipse(r * 0.4, 0, r * 0.7, r, 0, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Núcleo ultradenso del púlsar
    ctx.beginPath();
    ctx.arc(0, 0, 8, 0, Math.PI * 2);
    ctx.fillStyle = coreColor;
    ctx.fill();
    ctx.shadowBlur = 12;
    ctx.shadowColor = isDark ? '#00e5ff' : '#0284c7';
    ctx.stroke();

    ctx.restore();
  }

  // --- 6. RENDERIZADO: PAQUETE DE ONDAS CUÁNTICO EN TIEMPO REAL (LATERAL IZQUIERDO) ---
  function drawQuantumWave(cx, cy, widthLimit, isDark) {
    ctx.save();
    ctx.translate(cx, cy);
    waveTime += 0.035;

    const w = Math.min(180, widthLimit - 20);
    const halfW = w / 2;
    const sigma = w * 0.22;
    const k = 0.18;
    const amp = 24;

    ctx.beginPath();
    for (let x = -halfW; x <= halfW; x += 2) {
      const envelope = Math.exp(-(x * x) / (2 * sigma * sigma));
      const osc = Math.cos(k * x - waveTime);
      const y = -envelope * osc * amp;

      if (x === -halfW) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }

    ctx.strokeStyle = isDark ? '#00e5ff' : '#0284c7';
    ctx.lineWidth = 1.8;
    ctx.shadowBlur = isDark ? 8 : 4;
    ctx.shadowColor = isDark ? '#00e5ff' : '#0284c7';
    ctx.stroke();

    // Línea base del eje de propagación
    ctx.shadowBlur = 0;
    ctx.strokeStyle = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(-halfW, 0);
    ctx.lineTo(halfW, 0);
    ctx.stroke();

    ctx.restore();
  }

  // --- 7. RENDERIZADO: GALAXIA ESPIRAL GIRATORIA 3D (LATERAL DERECHO) ---
  function drawGalaxy(cx, cy, isDark) {
    ctx.save();
    ctx.translate(cx, cy);

    const tiltScaleY = 0.50; // Inclinación elíptica 3D
    const coreGrad = ctx.createRadialGradient(0, 0, 0, 0, 0, 32);
    coreGrad.addColorStop(0, isDark ? 'rgba(255, 255, 255, 0.55)' : 'rgba(15, 23, 42, 0.35)');
    coreGrad.addColorStop(0.35, isDark ? 'rgba(255, 183, 3, 0.35)' : 'rgba(217, 119, 6, 0.25)');
    coreGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.fillStyle = coreGrad;
    ctx.beginPath();
    ctx.arc(0, 0, 32, 0, Math.PI * 2);
    ctx.fill();

    // Partículas de los brazos espirales
    for (let i = 0; i < galaxyParticles.length; i++) {
      const p = galaxyParticles[i];
      p.currentAngle += p.speed;
      const x = Math.cos(p.currentAngle) * p.radiusBase;
      const y = Math.sin(p.currentAngle) * p.radiusBase * tiltScaleY;

      let pColor = '0, 229, 255';
      if (p.colorType === 'amber') pColor = '255, 183, 3';
      else if (p.colorType === 'violet') pColor = '168, 85, 247';

      if (!isDark) {
        if (p.colorType === 'amber') pColor = '217, 119, 6';
        else if (p.colorType === 'violet') pColor = '124, 58, 237';
        else pColor = '2, 132, 199';
      }

      ctx.beginPath();
      ctx.arc(x, y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${pColor}, ${p.brightness * (isDark ? 0.75 : 0.45)})`;
      ctx.fill();
    }
    ctx.restore();
  }

  // --- 8. RENDERIZADO: SISTEMA BINARIO DE EXOPLANETAS (LATERAL DERECHO) ---
  function drawBinaryPlanets(cx, cy, isDark) {
    ctx.save();
    ctx.translate(cx, cy);
    binaryAngle += 0.018;

    const orbitR = 38;
    const p1X = Math.cos(binaryAngle) * orbitR;
    const p1Y = Math.sin(binaryAngle) * (orbitR * 0.45);
    const p1Z = Math.sin(binaryAngle);

    const p2X = -p1X * 0.75;
    const p2Y = -p1Y * 0.75;
    const p2Z = -p1Z;

    // Órbita punteada
    ctx.beginPath();
    ctx.ellipse(0, 0, orbitR, orbitR * 0.45, 0, 0, Math.PI * 2);
    ctx.strokeStyle = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)';
    ctx.lineWidth = 1;
    ctx.stroke();

    // Dibujar primero el que está detrás (Z < 0)
    function drawSinglePlanet(x, y, r, colorPrimary, colorSecondary) {
      const g = ctx.createRadialGradient(x - r * 0.3, y - r * 0.3, r * 0.1, x, y, r);
      g.addColorStop(0, colorPrimary);
      g.addColorStop(1, colorSecondary);
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = g;
      ctx.fill();
    }

    if (p1Z < 0) {
      drawSinglePlanet(p1X, p1Y, 18, isDark ? '#ffb703' : '#d97706', isDark ? '#1e293b' : '#94a3b8');
      drawSinglePlanet(p2X, p2Y, 13, isDark ? '#00f0a0' : '#059669', isDark ? '#0f172a' : '#64748b');
    } else {
      drawSinglePlanet(p2X, p2Y, 13, isDark ? '#00f0a0' : '#059669', isDark ? '#0f172a' : '#64748b');
      drawSinglePlanet(p1X, p1Y, 18, isDark ? '#ffb703' : '#d97706', isDark ? '#1e293b' : '#94a3b8');
    }

    ctx.restore();
  }

  // --- 9. RENDERIZADO: DIAGRAMA DE BANDAS E(k) (LATERAL DERECHO) ---
  function drawBandStructure(cx, cy, widthLimit, isDark) {
    ctx.save();
    ctx.translate(cx, cy);

    const w = Math.min(160, widthLimit - 20);
    const halfW = w / 2;

    // Banda de Conducción
    ctx.beginPath();
    for (let k = -halfW; k <= halfW; k += 2) {
      const normK = k / halfW;
      const energy = -22 + normK * normK * 18;
      if (k === -halfW) ctx.moveTo(k, energy);
      else ctx.lineTo(k, energy);
    }
    ctx.strokeStyle = isDark ? '#00e5ff' : '#0284c7';
    ctx.lineWidth = 1.8;
    ctx.stroke();

    // Banda de Valencia
    ctx.beginPath();
    for (let k = -halfW; k <= halfW; k += 2) {
      const normK = k / halfW;
      const energy = 18 - normK * normK * 16;
      if (k === -halfW) ctx.moveTo(k, energy);
      else ctx.lineTo(k, energy);
    }
    ctx.strokeStyle = isDark ? '#ffb703' : '#d97706';
    ctx.lineWidth = 1.8;
    ctx.stroke();

    // Brecha Prohibida Eg
    ctx.font = '600 11px "JetBrains Mono", monospace';
    ctx.fillStyle = isDark ? 'rgba(255, 255, 255, 0.4)' : 'rgba(15, 23, 42, 0.4)';
    ctx.textAlign = 'center';
    ctx.fillText("Eg (Bandgap)", 0, 0);

    ctx.restore();
  }

  // --- 10. GESTOR DE COMETAS ---
  function spawnComet() {
    const fromLeft = Math.random() > 0.5;
    const startX = fromLeft ? -60 : width + 60;
    const startY = Math.random() * height * 0.55;
    const targetX = fromLeft ? width + 60 : -60;
    const targetY = startY + (Math.random() * 260 + 120);

    const angle = Math.atan2(targetY - startY, targetX - startX);
    const speed = 8 + Math.random() * 4.5;

    comets.push({
      x: startX,
      y: startY,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      length: 90 + Math.random() * 70,
      opacity: 0.95
    });
  }

  function updateAndDrawComets(isDark) {
    for (let i = comets.length - 1; i >= 0; i--) {
      const c = comets[i];
      c.x += c.vx;
      c.y += c.vy;
      c.opacity -= 0.0075;

      if (c.opacity <= 0 || c.x < -120 || c.x > width + 120 || c.y > height + 120) {
        comets.splice(i, 1);
        continue;
      }

      const dist = Math.hypot(c.vx, c.vy);
      const tailX = c.x - (c.vx / dist) * c.length;
      const tailY = c.y - (c.vy / dist) * c.length;

      const grad = ctx.createLinearGradient(c.x, c.y, tailX, tailY);
      const color = isDark ? '0, 229, 255' : '2, 132, 199';
      grad.addColorStop(0, `rgba(${color}, ${c.opacity})`);
      grad.addColorStop(1, 'rgba(0, 0, 0, 0)');

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(c.x, c.y);
      ctx.lineTo(tailX, tailY);
      ctx.strokeStyle = grad;
      ctx.lineWidth = 2.4;
      ctx.lineCap = 'round';
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(c.x, c.y, 3, 0, Math.PI * 2);
      ctx.fillStyle = isDark ? '#ffffff' : '#0f172a';
      ctx.fill();
      ctx.restore();
    }
  }

  // --- 11. GESTOR DE FÓRMULAS LATERALES FLOTANTES ---
  function updateAndDrawSideFormulas(isDark) {
    ctx.save();
    ctx.font = '600 15px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';

    const colorMap = {
      cyan: isDark ? '0, 229, 255' : '2, 132, 199',
      amber: isDark ? '255, 183, 3' : '217, 119, 6',
      emerald: isDark ? '0, 240, 160' : '5, 150, 105',
      violet: isDark ? '168, 85, 247' : '124, 58, 237'
    };

    // Fórmulas en el corredor lateral izquierdo
    if (isWidescreen && leftMarginWidth > 120) {
      for (let i = 0; i < leftFormulasState.length; i++) {
        const f = leftFormulasState[i];
        f.phase += 0.012;
        f.currentY -= f.speed;
        if (f.currentY < -40) f.currentY = height + 40;

        const posX = leftMarginWidth * f.xOffset + Math.sin(f.phase) * 12;
        const opacity = 0.40 + Math.sin(f.phase * 0.9) * 0.22;
        const c = colorMap[f.color] || colorMap.cyan;

        ctx.fillStyle = `rgba(${c}, ${opacity})`;
        ctx.fillText(f.text, posX, f.currentY);
      }
    }

    // Fórmulas en el corredor lateral derecho
    if (isWidescreen && (width - rightMarginStart) > 120) {
      const rightWidth = width - rightMarginStart;
      for (let i = 0; i < rightFormulasState.length; i++) {
        const f = rightFormulasState[i];
        f.phase += 0.013;
        f.currentY -= f.speed;
        if (f.currentY < -40) f.currentY = height + 40;

        const posX = rightMarginStart + rightWidth * f.xOffset + Math.sin(f.phase) * 12;
        const opacity = 0.40 + Math.sin(f.phase * 0.9) * 0.22;
        const c = colorMap[f.color] || colorMap.cyan;

        ctx.fillStyle = `rgba(${c}, ${opacity})`;
        ctx.fillText(f.text, posX, f.currentY);
      }
    }

    // Si la pantalla no es suficientemente ancha (móviles/tablets), dispersarlas suavemente
    if (!isWidescreen) {
      for (let i = 0; i < 6; i++) {
        const f = leftFormulasState[i];
        f.phase += 0.012;
        f.currentY -= f.speed * 0.6;
        if (f.currentY < -40) f.currentY = height + 40;
        const posX = ((i + 1) / 7) * width + Math.sin(f.phase) * 8;
        ctx.fillStyle = isDark ? 'rgba(0, 229, 255, 0.20)' : 'rgba(2, 132, 199, 0.16)';
        ctx.fillText(f.text, posX, f.currentY);
      }
    }

    ctx.restore();
  }

  // --- 12. MALLA DE ESTRELLAS CUÁNTICAS ---
  function updateAndDrawStars(isDark) {
    const tint = isDark ? '0, 229, 255' : '2, 132, 199';
    const reach = Math.min(130, Math.max(75, width * 0.09));

    for (let i = 0; i < stars.length; i++) {
      const s = stars[i];
      s.phase += 0.014;
      s.x += Math.sin(s.phase * 0.6) * s.drift;
      s.y -= s.drift * 0.3;

      if (s.y < -5) s.y = height + 5;
      if (s.x < -5) s.x = width + 5;
      if (s.x > width + 5) s.x = -5;

      const glow = 0.35 + Math.sin(s.phase) * 0.25;
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.radius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${tint}, ${glow * (isDark ? 0.65 : 0.35)})`;
      ctx.fill();

      for (let j = i + 1; j < stars.length; j++) {
        const other = stars[j];
        const dx = s.x - other.x;
        const dy = s.y - other.y;
        const dist = Math.hypot(dx, dy);

        if (dist < reach) {
          ctx.beginPath();
          ctx.moveTo(s.x, s.y);
          ctx.lineTo(other.x, other.y);
          const lineAlpha = (1 - dist / reach) * (isDark ? 0.09 : 0.05);
          ctx.strokeStyle = `rgba(${tint}, ${lineAlpha})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }
    }
  }

  // --- 13. CICLO DE RENDERIZADO 60 FPS ---
  function render(timestamp) {
    if (!lastTime) lastTime = timestamp;
    const delta = timestamp - lastTime;
    lastTime = timestamp;

    ctx.clearRect(0, 0, width, height);

    const isDark = document.documentElement.dataset.theme !== 'light';
    updateMargins();

    const leftCenter = isWidescreen ? leftMarginWidth * 0.5 : width * 0.15;
    const rightCenter = isWidescreen ? rightMarginStart + (width - rightMarginStart) * 0.5 : width * 0.85;

    // A) ELEMENTOS DEL LATERAL IZQUIERDO:
    // 1. Planeta con anillos
    const pRadius = Math.min(48, Math.max(30, leftMarginWidth * 0.22));
    drawPlanetWithRings(leftCenter, Math.min(height * 0.42, 420), pRadius, isDark);

    // 2. Púlsar rotativo con haces relativistas
    if (height > 600) {
      drawPulsar(leftCenter, Math.min(height * 0.82, 820), isDark);
    }

    // 3. Paquete de ondas cuántico
    if (isWidescreen && leftMarginWidth > 130 && height > 900) {
      drawQuantumWave(leftCenter, Math.min(height * 1.15, 1180), leftMarginWidth, isDark);
    }

    // B) ELEMENTOS DEL LATERAL DERECHO:
    // 1. Galaxia espiral giratoria en 3D
    drawGalaxy(rightCenter, Math.min(height * 0.32, 320), isDark);

    // 2. Sistema binario de planetas
    if (height > 650) {
      drawBinaryPlanets(rightCenter, Math.min(height * 0.76, 760), isDark);
    }

    // 3. Diagrama de bandas E(k)
    if (isWidescreen && (width - rightMarginStart) > 130 && height > 950) {
      drawBandStructure(rightCenter, Math.min(height * 1.12, 1140), width - rightMarginStart, isDark);
    }

    // C) FÓRMULAS LATERALES EN MOVIMIENTO CONTINUO
    updateAndDrawSideFormulas(isDark);

    // D) MALLA DE ESTRELLAS
    updateAndDrawStars(isDark);

    // E) COMETAS PERIÓDICOS
    nextCometTime -= delta;
    if (nextCometTime <= 0) {
      spawnComet();
      nextCometTime = 4000 + Math.random() * 4500;
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
  window.addEventListener('scroll', updateMargins, { passive: true });
  document.addEventListener('visibilitychange', start);
  reduceMotion.addEventListener?.('change', start);
  document.getElementById('themeToggle')?.addEventListener('click', () => {
    setTimeout(() => { if (!frame) start(); }, 50);
  });
})();
