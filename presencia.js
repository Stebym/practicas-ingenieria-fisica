/*
 * =============================================================================
 * PRESENCIA EN LÍNEA Y VISITAS REALES (PORTAL IPF)
 * Autor: Jimmy Stebym Rosero Barrera <jiroserob@unal.edu.co>
 * Licencia: MIT con descargo de responsabilidad (ver LICENSE)
 * =============================================================================
 * Cada pestaña abierta registra un nodo en /presencia de Firebase Realtime
 * Database. Firebase lo borra solo cuando la pestaña se cierra o pierde la
 * conexión (onDisconnect), así que el número mostrado es la cantidad real de
 * pestañas conectadas. Un latido cada 60 s descarta nodos huérfanos.
 * /visitas suma 1 por sesión del navegador.
 *
 * Si firebase_config.json está vacío, el contador no se muestra: nunca se
 * inventan cifras.
 */

const FIREBASE_SDK = 'https://www.gstatic.com/firebasejs/10.12.2';
const LATIDO_MS = 60000;
const VENCIMIENTO_MS = 150000;

function leerConfig() {
  try {
    const cfg = JSON.parse(document.getElementById('ipfFirebaseConfig')?.textContent || '{}');
    return cfg && cfg.databaseURL ? cfg : null;
  } catch {
    return null;
  }
}

async function iniciarPresencia() {
  const cfg = leerConfig();
  if (!cfg) return;

  const [{ initializeApp }, db] = await Promise.all([
    import(`${FIREBASE_SDK}/firebase-app.js`),
    import(`${FIREBASE_SDK}/firebase-database.js`),
  ]);
  const { getDatabase, ref, push, set, update, onValue, onDisconnect, serverTimestamp, runTransaction } = db;

  const database = getDatabase(initializeApp(cfg));
  const chip = document.getElementById('liveOnlineBadge');
  const contador = document.getElementById('liveOnlineCount');
  const visitasBox = document.getElementById('totalViewsCounter');
  const visitasTxt = document.getElementById('totalViewsText');

  let desfaseServidor = 0;
  onValue(ref(database, '.info/serverTimeOffset'), snap => { desfaseServidor = snap.val() || 0; });

  // 1. Registrar esta pestaña mientras esté conectada.
  const miNodo = push(ref(database, 'presencia'));
  onValue(ref(database, '.info/connected'), snap => {
    if (snap.val() !== true) return;
    onDisconnect(miNodo).remove().then(() => set(miNodo, { t: serverTimestamp() }));
  });
  setInterval(() => { update(miNodo, { t: serverTimestamp() }).catch(() => {}); }, LATIDO_MS);

  // 2. Contar las pestañas conectadas con latido reciente.
  onValue(ref(database, 'presencia'), snap => {
    const ahora = Date.now() + desfaseServidor;
    let enLinea = 0;
    snap.forEach(hijo => {
      const t = hijo.val()?.t;
      if (typeof t === 'number' && ahora - t < VENCIMIENTO_MS) enLinea += 1;
    });
    enLinea = Math.max(enLinea, 1);
    if (contador) contador.textContent = `${enLinea} en línea`;
    if (chip) chip.hidden = false;
  });

  // 3. Visitas: +1 por sesión del navegador.
  const visitasRef = ref(database, 'visitas');
  let nuevaSesion = true;
  try {
    nuevaSesion = !sessionStorage.getItem('ipf_visita_contada');
    sessionStorage.setItem('ipf_visita_contada', '1');
  } catch {}
  if (nuevaSesion) runTransaction(visitasRef, v => (typeof v === 'number' ? v : 0) + 1).catch(() => {});
  onValue(visitasRef, snap => {
    const total = snap.val();
    if (typeof total !== 'number') return;
    if (visitasTxt) visitasTxt.textContent = total.toLocaleString('es-CO');
    if (visitasBox) visitasBox.hidden = false;
  });
}

iniciarPresencia().catch(() => {
  // Sin conexión con Firebase: se deja oculto el contador.
});
