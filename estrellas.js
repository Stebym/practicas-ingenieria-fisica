(() => {
  const canvas = document.getElementById('constellationCanvas');
  if (!canvas) return;
  const context = canvas.getContext('2d');
  if (!context) return;

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let width = 0;
  let height = 0;
  let stars = [];
  let frame = 0;

  function resize() {
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    const count = Math.min(90, Math.max(34, Math.round(width * height / 15000)));
    stars = Array.from({ length: count }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      radius: 0.7 + Math.random() * 1.3,
      phase: Math.random() * Math.PI * 2,
      drift: 0.08 + Math.random() * 0.2
    }));
    draw();
  }

  function draw() {
    context.clearRect(0, 0, width, height);
    const tint = document.documentElement.dataset.theme === 'dark' ? '190, 226, 220' : '61, 111, 103';
    const reach = Math.min(150, Math.max(90, width * 0.12));
    for (let i = 0; i < stars.length; i += 1) {
      const star = stars[i];
      const glow = 0.48 + Math.sin(star.phase) * 0.2;
      context.beginPath();
      context.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
      context.fillStyle = `rgba(${tint}, ${glow})`;
      context.fill();
      if (star.radius > 1.65) {
        context.strokeStyle = `rgba(${tint}, ${glow * 0.52})`;
        context.lineWidth = 0.7;
        context.beginPath();
        context.moveTo(star.x - star.radius * 2.2, star.y);
        context.lineTo(star.x + star.radius * 2.2, star.y);
        context.moveTo(star.x, star.y - star.radius * 2.2);
        context.lineTo(star.x, star.y + star.radius * 2.2);
        context.stroke();
      }
      for (let j = i + 1; j < stars.length; j += 1) {
        const other = stars[j];
        const dx = star.x - other.x;
        const dy = star.y - other.y;
        const distance = Math.hypot(dx, dy);
        if (distance < reach) {
          context.beginPath();
          context.moveTo(star.x, star.y);
          context.lineTo(other.x, other.y);
          context.strokeStyle = `rgba(${tint}, ${(1 - distance / reach) * (document.documentElement.dataset.theme === 'dark' ? 0.16 : 0.12)})`;
          context.lineWidth = 0.7;
          context.stroke();
        }
      }
    }
  }

  function animate() {
    if (reduceMotion.matches || document.hidden) {
      cancelAnimationFrame(frame);
      return;
    }
    stars.forEach((star) => {
      star.phase += 0.012;
      star.x += Math.sin(star.phase * 0.65) * star.drift;
      star.y -= star.drift * 0.32;
      if (star.y < -4) star.y = height + 4;
      if (star.x < -4) star.x = width + 4;
      if (star.x > width + 4) star.x = -4;
    });
    draw();
    frame = requestAnimationFrame(animate);
  }

  function start() {
    cancelAnimationFrame(frame);
    if (!reduceMotion.matches && !document.hidden) animate();
  }

  resize();
  start();
  window.addEventListener('resize', resize, { passive: true });
  document.addEventListener('visibilitychange', start);
  reduceMotion.addEventListener?.('change', start);
  document.getElementById('themeToggle')?.addEventListener('click', draw);
})();
