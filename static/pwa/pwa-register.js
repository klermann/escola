// pwa-register.js
if ('serviceWorker' in navigator) {
  window.addEventListener('load', async () => {
    try {
    const reg = await navigator.serviceWorker.register("{% url 'service_worker' %}", {
        scope: "{% url 'index' %}"
    });
    if (reg.waiting) showRefreshUI(reg.waiting);
      reg.addEventListener('updatefound', () => {
        const nw = reg.installing;
        nw?.addEventListener('statechange', () => {
          if (nw.state === 'installed' && navigator.serviceWorker.controller) showRefreshUI(nw);
        });
      });

      let refreshing = false;
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (!refreshing) { refreshing = true; window.location.reload(); }
      });
    } catch (e) { console.error('Falha ao registrar SW:', e); }
  });
}

function showRefreshUI(worker){
  const btn = document.getElementById('btnRefresh');
  if (btn) { btn.hidden = false; btn.onclick = () => worker.postMessage({type:'SKIP_WAITING'}); }
}

// beforeinstallprompt (Chromium)
let deferredPrompt;
const installBtn = document.getElementById('btnInstall');
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault(); deferredPrompt = e; installBtn && (installBtn.hidden = false);
});
installBtn?.addEventListener('click', async () => {
  installBtn.hidden = true;
  deferredPrompt?.prompt();
  await deferredPrompt?.userChoice;
  deferredPrompt = null;
});
