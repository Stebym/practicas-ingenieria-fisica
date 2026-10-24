/* ==========================================================================
   MOTOR CÓSMICO Y DE FÍSICA AVANZADA: 3D MULTIDIMENSIONAL
   - Gran Galaxia Espiral de Fondo (Espacio Profundo)
   - Telescopio Espacial James Webb (JWST) 3D con Espejos de Oro y Parasol
   - Estación Espacial Internacional (ISS) 3D con Paneles Solares Rotativos
   - Procesador Cuántico QPU 3D con Qubits Transmon y Resonadores CPW
   - Átomo Cuántico 3D con Orbitales Electrónicos en Precesión
   - Planeta Gaseoso 3D (Saturno) con División de Cassini y Luna
   - Púlsar Relativista con Haz Doppler y Conos Magnéticos
   - Paquete de Ondas ψ(x,t), Bandas E(k), Cometas y Fórmulas Flotantes
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

  // Medición de corredores laterales
  let leftMarginWidth = 260;
  let rightMarginStart = 1660;
  let isWidescreen = true;

  // --- 1. BANCO DE FÓRMULAS LATERALES ---
  const LEFT_FORMULAS = [
    { text: "iℏ ∂ψ/∂t = Ĥψ", size: 16, color: "cyan", speed: 0.22, y: 110, xOffset: 0.5 },
    { text: "E² = (pc)² + (m₀c²)²", size: 15, color: "amber", speed: 0.18, y: 240, xOffset: 0.4 },
    { text: "Δx · Δp ≥ ℏ/2", size: 16, color: "emerald", speed: 0.24, y: 530, xOffset: 0.6 },
    { text: "Ĥ = -(ℏ²/2m)∇² + V", size: 15, color: "cyan", speed: 0.20, y: 680, xOffset: 0.45 },
    { text: "R_μν - ½Rg_μν = κT_μν", size: 14, color: "violet", speed: 0.16, y: 990, xOffset: 0.55 },
    { text: "λ_dB = h / p", size: 15, color: "cyan", speed: 0.19, y: 1120, xOffset: 0.35 },
    { text: "S = k_B ln(Ω)", size: 15, color: "emerald", speed: 0.21, y: 1380, xOffset: 0.5 },
    { text: "E_n = (n + ½)ℏω", size: 15, color: "amber", speed: 0.17, y: 1540, xOffset: 0.42 },
    { text: "∇ × E = -∂B/∂t", size: 15, color: "cyan", speed: 0.23, y: 1710, xOffset: 0.58 },
    { text: "ψ(x) ∝ e^{ikx}", size: 15, color: "emerald", speed: 0.19, y: 1890, xOffset: 0.48 }
  ];

  const RIGHT_FORMULAS = [
    { text: "∇ × B = μ₀J + μ₀ε₀∂E/∂t", size: 15, color: "cyan", speed: 0.20, y: 140, xOffset: 0.5 },
    { text: "2d sin(θ) = nλ", size: 16, color: "amber", speed: 0.22, y: 460, xOffset: 0.45 },
    { text: "n₁ sin(θ₁) = n₂ sin(θ₂)", size: 15, color: "emerald", speed: 0.19, y: 600, xOffset: 0.55 },
    { text: "σ = n e² τ / m*", size: 15, color: "cyan", speed: 0.17, y: 920, xOffset: 0.4 },
    { text: "F = q(E + v × B)", size: 16, color: "amber", speed: 0.25, y: 1040, xOffset: 0.6 },
    { text: "∇ · D = ρ_f", size: 15, color: "cyan", speed: 0.18, y: 1320, xOffset: 0.48 },
    { text: "ρ(E) ∝ √E", size: 15, color: "emerald", speed: 0.16, y: 1460, xOffset: 0.52 },
    { text: "∮ B · dA = 0", size: 15, color: "cyan", speed: 0.21, y: 1620, xOffset: 0.42 },
    { text: "μ = qτ / m*", size: 15, color: "violet", speed: 0.18, y: 1780, xOffset: 0.56 },
    { text: "v_g = dω / dk", size: 15, color: "amber", speed: 0.22, y: 1960, xOffset: 0.46 }
  ];

  let leftFormulasState = [];
  let rightFormulasState = [];
  let stars = [];
  let backgroundGalaxyParticles = [];
  let comets = [];
  let nextCometTime = 2500;

  // Variables de rotación continua 3D
  let globalTime = 0;
  let jwstAngle = 0;
  let issAngle = 0;
  let planetAngle = 0;
  let pulsarAngle = 0;
  let waveTime = 0;
  let qpuPulse = 0;
  let atomAngle = 0;
  let galaxyRotation = 0;

  // --- 2. GESTIÓN DE MÁRGENES Y REDIMENSIÓN ---
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

    // Estrellas del firmamento profundo
    const starCount = Math.min(110, Math.max(45, Math.round((width * height) / 14000)));
    stars = Array.from({ length: starCount }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      radius: 0.6 + Math.random() * 1.3,
      phase: Math.random() * Math.PI * 2,
      drift: 0.08 + Math.random() * 0.22
    }));

    // Gran Galaxia Cósmica de Fondo (300 estrellas en 4 brazos espirales)
    backgroundGalaxyParticles = [];
    const galaxyArms = 4;
    const particlesPerArm = 75;
    for (let arm = 0; arm < galaxyArms; arm++) {
      const armOffset = arm * (Math.PI / 2);
      for (let i = 0; i < particlesPerArm; i++) {
        const distRatio = (i + 1) / particlesPerArm;
        const radius = Math.pow(distRatio, 0.75) * 190;
        const angle = armOffset + distRatio * 4.2 + (Math.random() - 0.5) * 0.35;
        const isCore = distRatio < 0.28;
        backgroundGalaxyParticles.push({
          radiusBase: radius,
          angleBase: angle,
          speed: 0.0016 + (1 - distRatio) * 0.0022,
          currentAngle: angle,
          size: 0.8 + Math.random() * 1.6,
          colorType: isCore ? 'amber' : (Math.random() > 0.4 ? 'cyan' : 'violet'),
          brightness: 0.35 + Math.random() * 0.65
        });
      }
    }
  }

  // --- 3. GRAN GALAXIA CÓSMICA DE FONDO (ESPACIO PROFUNDO) ---
  function drawBackgroundGalaxy(cx, cy, isDark) {
    ctx.save();
    ctx.translate(cx, cy);
    galaxyRotation += 0.0015;

    const tiltScaleY = 0.52; // Proyección elíptica 3D

    // Núcleo galáctico difuso hiperbrillante
    const coreGrad = ctx.createRadialGradient(0, 0, 0, 0, 0, 65);
    if (isDark) {
      coreGrad.addColorStop(0, 'rgba(255, 255, 255, 0.50)');
      coreGrad.addColorStop(0.20, 'rgba(255, 183, 3, 0.32)');
      coreGrad.addColorStop(0.50, 'rgba(0, 229, 255, 0.16)');
      coreGrad.addColorStop(0.80, 'rgba(168, 85, 247, 0.08)');
      coreGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    } else {
      coreGrad.addColorStop(0, 'rgba(15, 23, 42, 0.30)');
      coreGrad.addColorStop(0.25, 'rgba(217, 119, 6, 0.22)');
      coreGrad.addColorStop(0.60, 'rgba(2, 132, 199, 0.12)');
      coreGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    }

    ctx.save();
    ctx.scale(1, tiltScaleY);
    ctx.beginPath();
    ctx.arc(0, 0, 65, 0, Math.PI * 2);
    ctx.fillStyle = coreGrad;
    ctx.fill();
    ctx.restore();

    // Partículas de los 4 brazos espirales en rotación dinámica
    for (let i = 0; i < backgroundGalaxyParticles.length; i++) {
      const p = backgroundGalaxyParticles[i];
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
      ctx.fillStyle = `rgba(${pColor}, ${p.brightness * (isDark ? 0.70 : 0.40)})`;
      ctx.fill();
    }

    ctx.restore();
  }

  // --- 4. MODELO 3D: TELESCOPIO ESPACIAL JAMES WEBB (JWST) ---
  // Representación del parasol de 5 capas, 18 espejos hexagonales de berilio-oro y trípode secundario
  function drawJamesWebbSatellite(cx, cy, isDark) {
    ctx.save();
    ctx.translate(cx, cy);
    jwstAngle += 0.012;

    const pitch = Math.sin(jwstAngle * 0.7) * 0.18;
    const yaw = Math.cos(jwstAngle * 0.5) * 0.22;
    ctx.rotate(0.25 + yaw);

    // A) Parasol Térmico multicapa Kapton (forma de cometa romboidal 3D)
    const layers = 5;
    for (let l = 0; l < layers; l++) {
      const offsetZ = (l - 2) * 2.2;
      ctx.beginPath();
      ctx.moveTo(-42 + l * 0.5, 0 + offsetZ * pitch);
      ctx.lineTo(0, -22 + l * 0.8 + offsetZ);
      ctx.lineTo(42 - l * 0.5, 0 + offsetZ * pitch);
      ctx.lineTo(0, 22 - l * 0.8 + offsetZ);
      ctx.closePath();

      if (isDark) {
        ctx.fillStyle = `rgba(${168 - l * 15}, ${85 + l * 20}, ${247 - l * 10}, ${0.18 + l * 0.05})`;
        ctx.strokeStyle = `rgba(203, 213, 225, ${0.30 + l * 0.10})`;
      } else {
        ctx.fillStyle = `rgba(147, 51, 234, ${0.12 + l * 0.04})`;
        ctx.strokeStyle = `rgba(71, 85, 105, ${0.25 + l * 0.08})`;
      }
      ctx.lineWidth = 0.9;
      ctx.fill();
      ctx.stroke();
    }

    // B) Mástil central y bus de servicio espacial
    ctx.save();
    ctx.translate(0, -4);
    ctx.fillStyle = isDark ? '#1e293b' : '#64748b';
    ctx.fillRect(-6, -6, 12, 12);
    ctx.strokeStyle = isDark ? '#00e5ff' : '#0284c7';
    ctx.lineWidth = 1;
    ctx.strokeRect(-6, -6, 12, 12);

    // C) Espejo Primario de Oro (Matriz de 18 hexágonos)
    function drawHexagon(hx, hy, r) {
      ctx.beginPath();
      for (let i = 0; i < 6; i++) {
        const a = (Math.PI / 3) * i;
        const px = hx + Math.cos(a) * r;
        const py = hy + Math.sin(a) * r;
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.closePath();
      ctx.fillStyle = isDark ? '#ffb703' : '#d97706';
      ctx.fill();
      ctx.strokeStyle = isDark ? '#fff275' : '#b45309';
      ctx.lineWidth = 0.7;
      ctx.stroke();
    }

    const hexR = 4.2;
    const stepX = hexR * 1.55;
    const stepY = hexR * 1.73;

    // Anillo interno y medio de espejos hexagonales
    const hexCoords = [
      [-stepX, -stepY], [0, -stepY * 1.1], [stepX, -stepY],
      [-stepX * 1.3, 0], [0, 0], [stepX * 1.3, 0],
      [-stepX, stepY], [0, stepY * 1.1], [stepX, stepY],
      [-stepX * 2, -stepY * 0.5], [stepX * 2, -stepY * 0.5],
      [-stepX * 2, stepY * 0.5], [stepX * 2, stepY * 0.5]
    ];

    ctx.save();
    ctx.scale(1, 0.88); // Perspectiva visual
    hexCoords.forEach(([hx, hy]) => drawHexagon(hx, hy - 4, hexR));

    // D) Trípode de soporte del espejo secundario en 3D
    ctx.strokeStyle = isDark ? 'rgba(255, 255, 255, 0.7)' : 'rgba(15, 23, 42, 0.7)';
    ctx.lineWidth = 1.1;
    const secZ = -18;
    ctx.beginPath();
    ctx.moveTo(-stepX * 1.5, -4);
    ctx.lineTo(0, secZ);
    ctx.moveTo(stepX * 1.5, -4);
    ctx.lineTo(0, secZ);
    ctx.moveTo(0, stepY * 1.2 - 4);
    ctx.lineTo(0, secZ);
    ctx.stroke();

    // Espejo secundario circular
    ctx.beginPath();
    ctx.arc(0, secZ, 2.5, 0, Math.PI * 2);
    ctx.fillStyle = isDark ? '#ffffff' : '#f8fafc';
    ctx.fill();
    ctx.restore();

    // E) Panel Solar Trasero del JWST
    ctx.fillStyle = isDark ? '#0284c7' : '#0369a1';
    ctx.fillRect(-14, 18, 28, 6);
    ctx.strokeStyle = isDark ? '#38bdf8' : '#bae6fd';
    ctx.strokeRect(-14, 18, 28, 6);

    ctx.restore();
    ctx.restore();
  }

  // --- 5. MODELO 3D: ESTACIÓN ESPACIAL INTERNACIONAL (ISS) ---
  // Representación del módulo central presurizado, viga truss y paneles solares dorados rotativos
  function drawSpaceStationISS(cx, cy, isDark) {
    ctx.save();
    ctx.translate(cx, cy);
    issAngle += 0.015;

    ctx.rotate(-0.30 + Math.sin(issAngle * 0.4) * 0.08);

    const solarAngle = issAngle * 0.8;
    const solarTilt = Math.sin(solarAngle);

    // A) Viga Principal Central (Integrated Truss Structure)
    ctx.strokeStyle = isDark ? '#94a3b8' : '#475569';
    ctx.lineWidth = 2.2;
    ctx.beginPath();
    ctx.moveTo(-60, 0);
    ctx.lineTo(60, 0);
    ctx.stroke();

    // Reticulado truss
    ctx.lineWidth = 0.8;
    for (let x = -56; x <= 56; x += 8) {
      ctx.beginPath();
      ctx.moveTo(x, -3);
      ctx.lineTo(x + 4, 3);
      ctx.stroke();
    }

    // B) Módulos Habitacionales Cilíndricos Centrales (Destiny, Kibo, Zvezda)
    ctx.fillStyle = isDark ? '#cbd5e1' : '#64748b';
    ctx.fillRect(-8, -14, 16, 28);
    ctx.strokeStyle = isDark ? '#00e5ff' : '#0284c7';
    ctx.lineWidth = 1;
    ctx.strokeRect(-8, -14, 16, 28);

    // Módulos transversales
    ctx.fillStyle = isDark ? '#94a3b8' : '#94a3b8';
    ctx.fillRect(-18, -4, 10, 8);
    ctx.fillRect(8, -4, 10, 8);

    // Cúpula de observación / docking ring
    ctx.beginPath();
    ctx.arc(0, 15, 3.5, 0, Math.PI * 2);
    ctx.fillStyle = isDark ? '#00e5ff' : '#0284c7';
    ctx.fill();

    // C) Radiadores Térmicos Blancos Disipadores
    ctx.fillStyle = isDark ? '#f8fafc' : '#e2e8f0';
    ctx.fillRect(-22, -18, 6, 12);
    ctx.fillRect(16, -18, 6, 12);

    // D) 4 Alas Dobles de Paneles Solares Fotovoltaicos (SAW)
    function drawSolarWing(wx, wy, w, h) {
      ctx.save();
      ctx.translate(wx, wy);
      ctx.scale(1, Math.max(0.20, Math.abs(solarTilt))); // Rotación 3D hacia el sol

      // Panel solar dorado/celeste
      const panelGrad = ctx.createLinearGradient(0, -h / 2, 0, h / 2);
      if (isDark) {
        panelGrad.addColorStop(0, '#ffb703');
        panelGrad.addColorStop(0.5, '#f59e0b');
        panelGrad.addColorStop(1, '#d97706');
      } else {
        panelGrad.addColorStop(0, '#0284c7');
        panelGrad.addColorStop(0.5, '#0369a1');
        panelGrad.addColorStop(1, '#075985');
      }

      ctx.fillStyle = panelGrad;
      ctx.fillRect(-w / 2, -h / 2, w, h);
      ctx.strokeStyle = isDark ? '#fef08a' : '#7dd3fc';
      ctx.lineWidth = 0.8;
      ctx.strokeRect(-w / 2, -h / 2, w, h);

      // Rejilla de celdas fotovoltaicas
      ctx.strokeStyle = isDark ? 'rgba(0, 0, 0, 0.45)' : 'rgba(255, 255, 255, 0.45)';
      ctx.lineWidth = 0.5;
      for (let y = -h / 2 + 5; y < h / 2; y += 5) {
        ctx.beginPath();
        ctx.moveTo(-w / 2, y);
        ctx.lineTo(w / 2, y);
        ctx.stroke();
      }
      ctx.restore();
    }

    const wingW = 12;
    const wingH = 34;
    // Alas de estribor y babor
    drawSolarWing(-52, -20, wingW, wingH);
    drawSolarWing(-52, 20, wingW, wingH);
    drawSolarWing(-34, -20, wingW, wingH);
    drawSolarWing(-34, 20, wingW, wingH);

    drawSolarWing(34, -20, wingW, wingH);
    drawSolarWing(34, 20, wingW, wingH);
    drawSolarWing(52, -20, wingW, wingH);
    drawSolarWing(52, 20, wingW, wingH);

    ctx.restore();
  }

  // --- 6. MODELO 3D: CHIP DE COMPUTACIÓN CUÁNTICA (QPU) ---
  // Sustrato criogénico isométrico 3D, matriz de qubits transmon y líneas de meandro CPW
  function drawQuantumProcessor(cx, cy, isDark) {
    ctx.save();
    ctx.translate(cx, cy);
    qpuPulse += 0.04;

    // Perspectiva Isométrica
    const cos30 = 0.866;
    const sin30 = 0.5;
    const size = 38;

    function isoProject(x, y, z) {
      return {
        px: (x - y) * cos30,
        py: (x + y) * sin30 - z
      };
    }

    // A) Sustrato de Silicio / Zafiro (Bloque 3D)
    const thickness = 7;
    const p1 = isoProject(-size, -size, 0);
    const p2 = isoProject(size, -size, 0);
    const p3 = isoProject(size, size, 0);
    const p4 = isoProject(-size, size, 0);

    // Caras laterales inferiores
    const p2B = isoProject(size, -size, -thickness);
    const p3B = isoProject(size, size, -thickness);
    const p4B = isoProject(-size, size, -thickness);

    // Lado frontal derecho
    ctx.beginPath();
    ctx.moveTo(p2.px, p2.py);
    ctx.lineTo(p3.px, p3.py);
    ctx.lineTo(p3B.px, p3B.py);
    ctx.lineTo(p2B.px, p2B.py);
    ctx.closePath();
    ctx.fillStyle = isDark ? '#09101d' : '#94a3b8';
    ctx.fill();

    // Lado frontal izquierdo
    ctx.beginPath();
    ctx.moveTo(p3.px, p3.py);
    ctx.lineTo(p4.px, p4.py);
    ctx.lineTo(p4B.px, p4B.py);
    ctx.lineTo(p3B.px, p3B.py);
    ctx.closePath();
    ctx.fillStyle = isDark ? '#050a12' : '#64748b';
    ctx.fill();

    // Cara superior del chip
    ctx.beginPath();
    ctx.moveTo(p1.px, p1.py);
    ctx.lineTo(p2.px, p2.py);
    ctx.lineTo(p3.px, p3.py);
    ctx.lineTo(p4.px, p4.py);
    ctx.closePath();
    ctx.fillStyle = isDark ? '#0d1829' : '#e2e8f0';
    ctx.fill();
    ctx.strokeStyle = isDark ? '#00e5ff' : '#0284c7';
    ctx.lineWidth = 1.2;
    ctx.stroke();

    // B) Rejilla de 9 Qubits Transmon superconductores
    const gridSpacing = 18;
    for (let gx = -1; gx <= 1; gx++) {
      for (let gy = -1; gy <= 1; gy++) {
        const qx = gx * gridSpacing;
        const qy = gy * gridSpacing;
        const pt = isoProject(qx, qy, 1);

        // Qubit en cruz
        const qArm = 4.5;
        const ptT = isoProject(qx, qy - qArm, 1);
        const ptB = isoProject(qx, qy + qArm, 1);
        const ptL = isoProject(qx - qArm, qy, 1);
        const ptR = isoProject(qx + qArm, qy, 1);

        ctx.strokeStyle = isDark ? '#ffb703' : '#d97706';
        ctx.lineWidth = 1.4;
        ctx.beginPath();
        ctx.moveTo(ptT.px, ptT.py);
        ctx.lineTo(ptB.px, ptB.py);
        ctx.moveTo(ptL.px, ptL.py);
        ctx.lineTo(ptR.px, ptR.py);
        ctx.stroke();

        // Pulso cuántico de coherencia |ψ⟩
        const pulsePhase = qpuPulse + (gx + 1) * 0.8 + (gy + 1) * 0.5;
        const pulseIntensity = 0.3 + Math.sin(pulsePhase) * 0.3;

        ctx.beginPath();
        ctx.arc(pt.px, pt.py, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = isDark
          ? `rgba(0, 229, 255, ${0.5 + pulseIntensity})`
          : `rgba(2, 132, 199, ${0.4 + pulseIntensity})`;
        ctx.fill();
      }
    }

    // C) Pistas superconductoras en meandro CPW
    ctx.strokeStyle = isDark ? 'rgba(0, 240, 160, 0.45)' : 'rgba(5, 150, 105, 0.40)';
    ctx.lineWidth = 0.9;
    for (let i = -1; i <= 1; i++) {
      const startP = isoProject(-size * 0.85, i * gridSpacing, 1);
      const endP = isoProject(size * 0.85, i * gridSpacing, 1);
      ctx.beginPath();
      ctx.moveTo(startP.px, startP.py);
      ctx.lineTo(endP.px, endP.py);
      ctx.stroke();
    }

    // Etiqueta técnica QPU
    ctx.font = '600 9px "JetBrains Mono", monospace';
    ctx.fillStyle = isDark ? 'rgba(0, 229, 255, 0.6)' : 'rgba(2, 132, 199, 0.6)';
    ctx.textAlign = 'center';
    const tagPos = isoProject(0, size * 0.85, 1);
    ctx.fillText("QPU 9-QUBIT LATTICE", tagPos.px, tagPos.py + 12);

    ctx.restore();
  }

  // --- 7. MODELO 3D: ÁTOMO CUÁNTICO & NANOTECNOLOGÍA ---
  // Núcleo brillante y 3 orbitales electrónicos precesando en 3 dimensiones
  function drawQuantumAtom(cx, cy, isDark) {
    ctx.save();
    ctx.translate(cx, cy);
    atomAngle += 0.022;

    const r = 36;

    // A) 3 Orbitales elípticos inclinados en 3D
    const orbits = [
      { rx: r, ry: r * 0.38, rot: atomAngle * 0.5, speed: 1.8, phase: 0 },
      { rx: r, ry: r * 0.38, rot: atomAngle * 0.5 + Math.PI / 3, speed: 2.2, phase: 1.5 },
      { rx: r, ry: r * 0.38, rot: atomAngle * 0.5 + (Math.PI * 2) / 3, speed: 2.6, phase: 3.0 }
    ];

    orbits.forEach((orb, idx) => {
      ctx.save();
      ctx.rotate(orb.rot);

      // Anillo orbital punteado
      ctx.beginPath();
      ctx.ellipse(0, 0, orb.rx, orb.ry, 0, 0, Math.PI * 2);
      ctx.strokeStyle = isDark
        ? `rgba(0, 229, 255, ${0.22 + idx * 0.05})`
        : `rgba(2, 132, 199, ${0.18 + idx * 0.05})`;
      ctx.lineWidth = 1.1;
      ctx.stroke();

      // Electrón viajero en fase
      const eAngle = globalTime * orb.speed + orb.phase;
      const ex = Math.cos(eAngle) * orb.rx;
      const ey = Math.sin(eAngle) * orb.ry;
      const ez = Math.sin(eAngle); // Profundidad 3D

      // Electrón
      ctx.beginPath();
      const eSize = 2.4 + ez * 0.8;
      ctx.arc(ex, ey, Math.max(1.2, eSize), 0, Math.PI * 2);
      ctx.fillStyle = isDark ? '#ffffff' : '#0284c7';
      ctx.shadowBlur = isDark ? 8 : 4;
      ctx.shadowColor = isDark ? '#00e5ff' : '#0284c7';
      ctx.fill();
      ctx.shadowBlur = 0;

      ctx.restore();
    });

    // B) Núcleo denso cuántico (protones y neutrones en racimo)
    const nucleusGrad = ctx.createRadialGradient(0, 0, 0, 0, 0, 8);
    nucleusGrad.addColorStop(0, isDark ? '#ffffff' : '#ffb703');
    nucleusGrad.addColorStop(0.4, isDark ? '#ffb703' : '#d97706');
    nucleusGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');

    ctx.beginPath();
    ctx.arc(0, 0, 8, 0, Math.PI * 2);
    ctx.fillStyle = nucleusGrad;
    ctx.fill();

    // Etiqueta
    ctx.font = '600 9px "JetBrains Mono", monospace';
    ctx.fillStyle = isDark ? 'rgba(255, 183, 3, 0.6)' : 'rgba(217, 119, 6, 0.6)';
    ctx.textAlign = 'center';
    ctx.fillText("BOHR-DE BROGLIE", 0, 48);

    ctx.restore();
  }

  // --- 8. PLANETA GASEOSO 3D CON ANILLOS (SATURNO & LUNA) ---
  function drawPlanetWithRings(cx, cy, radius, isDark) {
    ctx.save();
    ctx.translate(cx, cy);
    planetAngle += 0.0035;

    const ringTilt = 0.32;
    const ringAngle = -0.36;
    const ringInnerR = radius * 1.35;
    const ringCassiniR = radius * 1.85;
    const ringOuterR = radius * 2.35;

    ctx.rotate(ringAngle);

    // A) Anillos traseros (detrás de la esfera)
    ctx.save();
    ctx.scale(1, ringTilt);

    // Anillo A exterior
    ctx.beginPath();
    ctx.arc(0, 0, ringOuterR, Math.PI, Math.PI * 2, false);
    ctx.arc(0, 0, ringCassiniR + 2, Math.PI * 2, Math.PI, true);
    ctx.closePath();
    ctx.fillStyle = isDark ? 'rgba(0, 229, 255, 0.16)' : 'rgba(2, 132, 199, 0.13)';
    ctx.fill();

    // División de Cassini (espacio oscuro libre de materia)
    // Anillo B interior
    ctx.beginPath();
    ctx.arc(0, 0, ringCassiniR - 3, Math.PI, Math.PI * 2, false);
    ctx.arc(0, 0, ringInnerR, Math.PI * 2, Math.PI, true);
    ctx.closePath();
    ctx.fillStyle = isDark ? 'rgba(0, 229, 255, 0.22)' : 'rgba(2, 132, 199, 0.18)';
    ctx.fill();

    ctx.restore();
    ctx.rotate(-ringAngle);

    // B) Esfera Planetaria 3D sombreada con bandas de nubes
    const grad = ctx.createRadialGradient(
      -radius * 0.35, -radius * 0.35, radius * 0.10,
      0, 0, radius
    );
    if (isDark) {
      grad.addColorStop(0, '#00f0a0');
      grad.addColorStop(0.35, '#0891b2');
      grad.addColorStop(0.75, '#0f172a');
      grad.addColorStop(1, '#020617');
    } else {
      grad.addColorStop(0, '#38bdf8');
      grad.addColorStop(0.45, '#0284c7');
      grad.addColorStop(1, '#64748b');
    }

    ctx.beginPath();
    ctx.arc(0, 0, radius, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();

    // Bandas atmosféricas
    ctx.save();
    ctx.clip();
    ctx.strokeStyle = isDark ? 'rgba(0, 229, 255, 0.22)' : 'rgba(2, 132, 199, 0.18)';
    ctx.lineWidth = 2.2;
    for (let b = -radius + 8; b < radius; b += 10) {
      ctx.beginPath();
      ctx.ellipse(0, b, radius * 1.05, radius * 0.24, 0, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.restore();

    ctx.rotate(ringAngle);

    // C) Anillos frontales (delante de la esfera)
    ctx.save();
    ctx.scale(1, ringTilt);

    // Anillo A frontal
    ctx.beginPath();
    ctx.arc(0, 0, ringOuterR, 0, Math.PI, false);
    ctx.arc(0, 0, ringCassiniR + 2, Math.PI, 0, true);
    ctx.closePath();
    ctx.fillStyle = isDark ? 'rgba(0, 229, 255, 0.24)' : 'rgba(2, 132, 199, 0.19)';
    ctx.fill();
    ctx.strokeStyle = isDark ? 'rgba(0, 229, 255, 0.50)' : 'rgba(2, 132, 199, 0.35)';
    ctx.lineWidth = 1;
    ctx.stroke();

    // Anillo B frontal
    ctx.beginPath();
    ctx.arc(0, 0, ringCassiniR - 3, 0, Math.PI, false);
    ctx.arc(0, 0, ringInnerR, Math.PI, 0, true);
    ctx.closePath();
    ctx.fillStyle = isDark ? 'rgba(0, 229, 255, 0.32)' : 'rgba(2, 132, 199, 0.26)';
    ctx.fill();
    ctx.strokeStyle = isDark ? 'rgba(0, 229, 255, 0.65)' : 'rgba(2, 132, 199, 0.45)';
    ctx.stroke();

    ctx.restore();

    // D) Luna orbital 3D
    const moonDist = radius * 2.8;
    const moonA = planetAngle * 2.2;
    const moonX = Math.cos(moonA) * moonDist;
    const moonY = Math.sin(moonA) * (moonDist * ringTilt);
    const moonZ = Math.sin(moonA);

    ctx.beginPath();
    ctx.arc(moonX, moonY, 3.8, 0, Math.PI * 2);
    ctx.fillStyle = isDark
      ? (moonZ > 0 ? '#00e5ff' : 'rgba(0, 229, 255, 0.35)')
      : (moonZ > 0 ? '#0284c7' : 'rgba(2, 132, 199, 0.35)');
    ctx.fill();

    ctx.restore();
  }

  // --- 9. PÚLSAR RELATIVISTA CON HAZ DOPPLER ---
  function drawPulsar(cx, cy, isDark) {
    ctx.save();
    ctx.translate(cx, cy);
    pulsarAngle += 0.045;

    const coreColor = isDark ? '#ffffff' : '#0f172a';
    const beamColor = isDark ? '0, 229, 255' : '2, 132, 199';

    // Conos de haz de radiación relativista
    ctx.save();
    ctx.rotate(pulsarAngle);

    const beamLen = 65;
    const beamWidth = 14;

    const gradTop = ctx.createLinearGradient(0, 0, 0, -beamLen);
    gradTop.addColorStop(0, `rgba(${beamColor}, 0.85)`);
    gradTop.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.beginPath();
    ctx.moveTo(-beamWidth / 2, -beamLen);
    ctx.lineTo(beamWidth / 2, -beamLen);
    ctx.lineTo(0, 0);
    ctx.closePath();
    ctx.fillStyle = gradTop;
    ctx.fill();

    const gradBottom = ctx.createLinearGradient(0, 0, 0, beamLen);
    gradBottom.addColorStop(0, `rgba(${beamColor}, 0.85)`);
    gradBottom.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.beginPath();
    ctx.moveTo(-beamWidth / 2, beamLen);
    ctx.lineTo(beamWidth / 2, beamLen);
    ctx.lineTo(0, 0);
    ctx.closePath();
    ctx.fillStyle = gradBottom;
    ctx.fill();

    ctx.restore();

    // Líneas de campo magnético dipolar
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

    // Núcleo denso
    ctx.beginPath();
    ctx.arc(0, 0, 8, 0, Math.PI * 2);
    ctx.fillStyle = coreColor;
    ctx.fill();
    ctx.shadowBlur = 12;
    ctx.shadowColor = isDark ? '#00e5ff' : '#0284c7';
    ctx.stroke();

    ctx.restore();
  }

  // --- 10. PAQUETE DE ONDAS CUÁNTICO ψ(x,t) ---
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
    ctx.stroke();

    ctx.strokeStyle = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(-halfW, 0);
    ctx.lineTo(halfW, 0);
    ctx.stroke();

    ctx.restore();
  }

  // --- 11. DIAGRAMA DE BANDAS E(k) ---
  function drawBandStructure(cx, cy, widthLimit, isDark) {
    ctx.save();
    ctx.translate(cx, cy);

    const w = Math.min(160, widthLimit - 20);
    const halfW = w / 2;

    // Conducción
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

    // Valencia
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

    ctx.font = '600 11px "JetBrains Mono", monospace';
    ctx.fillStyle = isDark ? 'rgba(255, 255, 255, 0.4)' : 'rgba(15, 23, 42, 0.4)';
    ctx.textAlign = 'center';
    ctx.fillText("Eg (Bandgap)", 0, 0);

    ctx.restore();
  }

  // --- 12. GESTOR DE COMETAS ---
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

  // --- 13. FÓRMULAS LATERALES FLOTANTES ---
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

    if (!isWidescreen) {
      for (let i = 0; i < 6; i++) {
        const f = leftFormulasState[i];
        f.phase += 0.012;
        f.currentY -= f.speed * 0.6;
        if (f.currentY < -40) f.currentY = height + 40;
        const posX = ((i + 1) / 7) * width + Math.sin(f.phase) * 8;
        ctx.fillStyle = isDark ? 'rgba(0, 229, 255, 0.10)' : 'rgba(2, 132, 199, 0.08)';
        ctx.fillText(f.text, posX, f.currentY);
      }
    }

    ctx.restore();
  }

  // --- 14. MALLA DE ESTRELLAS CUÁNTICAS ---
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

  // --- 15. CICLO PRINCIPAL DE RENDERIZADO 60 FPS ---
  function render(timestamp) {
    if (!lastTime) lastTime = timestamp;
    const delta = timestamp - lastTime;
    lastTime = timestamp;
    globalTime += 0.016;

    ctx.clearRect(0, 0, width, height);

    const isDark = document.documentElement.dataset.theme !== 'light';
    updateMargins();

    // 1. CAPA PROFUNDA: GRAN GALAXIA ESPIRAL DE FONDO (Espacio celestial)
    drawBackgroundGalaxy(width * 0.72, height * 0.28, isDark);

    const leftCenter = isWidescreen ? leftMarginWidth * 0.5 : width * 0.15;
    const rightCenter = isWidescreen ? rightMarginStart + (width - rightMarginStart) * 0.5 : width * 0.85;

    // Los modelos 3D solo se dibujan si hay corredores laterales libres: en
    // pantallas más angostas quedaban encima del texto y los filtros.
    if (isWidescreen) {
      // 2. ELEMENTOS DEL CORREDOR IZQUIERDO:
      // A) Telescopio Espacial James Webb (JWST) 3D con parasol y espejos dorados
      drawJamesWebbSatellite(leftCenter, Math.min(height * 0.25, 230), isDark);

      // B) Procesador Cuántico QPU 3D con Qubits Transmon
      if (height > 550) {
        drawQuantumProcessor(leftCenter, Math.min(height * 0.62, 590), isDark);
      }

      // C) Planeta Gaseoso Gigante 3D (Saturno con Cassini y luna)
      if (height > 850) {
        const pRadius = Math.min(46, Math.max(28, leftMarginWidth * 0.22));
        drawPlanetWithRings(leftCenter, Math.min(height * 1.05, 960), pRadius, isDark);
      }

      // D) Paquete de Ondas ψ(x,t)
      if (isWidescreen && leftMarginWidth > 130 && height > 1150) {
        drawQuantumWave(leftCenter, Math.min(height * 1.35, 1280), leftMarginWidth, isDark);
      }

      // 3. ELEMENTOS DEL CORREDOR DERECHO:
      // A) Estación Espacial Internacional (ISS) 3D con paneles rotativos
      drawSpaceStationISS(rightCenter, Math.min(height * 0.26, 240), isDark);

      // B) Átomo Cuántico 3D / Nanotecnología con orbitales en precesión
      if (height > 550) {
        drawQuantumAtom(rightCenter, Math.min(height * 0.60, 580), isDark);
      }

      // C) Púlsar Relativista con haces Doppler
      if (height > 850) {
        drawPulsar(rightCenter, Math.min(height * 0.98, 940), isDark);
      }

      // D) Diagrama de bandas E(k)
      if (isWidescreen && (width - rightMarginStart) > 130 && height > 1150) {
        drawBandStructure(rightCenter, Math.min(height * 1.32, 1260), width - rightMarginStart, isDark);
      }

    }

    // 4. FÓRMULAS CIENTÍFICAS FLOTANTES
    updateAndDrawSideFormulas(isDark);

    // 5. MALLA DE ESTRELLAS CUÁNTICAS
    updateAndDrawStars(isDark);

    // 6. COMETAS PERIÓDICOS
    nextCometTime -= delta;
    if (nextCometTime <= 0) {
      spawnComet();
      nextCometTime = 3500 + Math.random() * 4000;
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
