// Named crops of the real app screenshots (945x2048 source px): [screen, x, y, w, h].
// Posts refer to these names so every visual stays a real piece of the product.
window.SCREENS = ['takip', 'bakiye', 'analiz', 'planlar', 'onboarding', 'giris'];
window.CROPS = {
  'takip.ozet':      ['takip', 40, 245, 870, 125],   // Ev Ortak Giderleri, ₺4.460 ödendi
  'takip.butonlar':  ['takip', 51, 389, 840, 226],   // Gider Ekle, Bakiyeler, Ekstre Aktar
  'takip.filtre':    ['takip', 97, 885, 760, 230],   // arama, Filtre, Tümü/Ödenenler/Planlananlar
  'takip.gider':     ['takip', 102, 1142, 743, 445], // Temizlik malzemesi kartı, Onur/Ece payı
  'takip.gider2':    ['takip', 102, 1613, 743, 230], // Uber / taksi kartı
  'bakiye.baslik':   ['bakiye', 56, 343, 794, 328],  // Bakiyeler & Mahsuplaşma
  'bakiye.net':      ['bakiye', 61, 722, 824, 712],  // Net bakiyeler kartı
  'bakiye.kisiler':  ['bakiye', 100, 1092, 770, 296],// Onur alacaklı / Ece borçlu
  'bakiye.transfer': ['bakiye', 61, 1497, 824, 356], // Transfer (mahsup)
  'analiz.ekstre':   ['analiz', 61, 258, 824, 282],  // Ekstrelerim, PDF · 73 işlem
  'analiz.nabiz':    ['analiz', 61, 724, 824, 423],  // Ekstre nabzı
  'analiz.toplam':   ['analiz', 60, 1183, 400, 271], // Toplam harcama
  'analiz.kartlar':  ['analiz', 61, 1185, 824, 633], // 4 özet kartı
  'planlar.baslik':  ['planlar', 61, 276, 789, 236], // Tüm Planlar
  'planlar.sayac':   ['planlar', 63, 701, 818, 170], // Aktif plan / Bekleyen davet
  'planlar.sekme':   ['planlar', 61, 930, 824, 140], // Planlarım / Hazır Şablonlar
  'planlar.kart':    ['planlar', 100, 1244, 744, 527],// Ev Ortak Giderleri plan kartı
  'onboarding.plan': ['onboarding', 67, 792, 812, 425], // 120 Aylık Konut Planı, Eren/Yusuf Ödedi
  'onboarding.metin':['onboarding', 179, 1254, 589, 128],// FuzulEv, Eminevim...
  'giris.google':    ['giris', 41, 1602, 865, 118],  // Google ile devam et
  'giris.ssl':       ['giris', 220, 1905, 510, 52],  // 256-bit SSL
};

// Text markup: "\n" breaks a line, **text** is bold, *text* gets the brand gradient. Everything else is escaped.
window.markup = s => String(s || '')
  .replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]))
  .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  .replace(/\*([^*]+)\*/g, '<span class="grad">$1</span>')
  .replace(/\n/g, '<br>');

// Same markup, but every word in its own span so it can animate on its own.
window.wordsMarkup = s => String(s || '').split('\n').map(line =>
  line.split(/(\*[^*]+\*)/).filter(Boolean).map(seg => {
    const g = /^\*.*\*$/.test(seg);
    return (g ? seg.slice(1, -1) : seg).split(/\s+/).filter(Boolean)
      .map(w => `<span class="w${g ? ' grad' : ''}">${markup(w)}</span>`).join(' ');
  }).join(' ')).join('<br>');

// Crop element scaled to fit inside maxW x maxH.
window.cropEl = (name, maxW, maxH, cls = '') => {
  const c = CROPS[name];
  if (!c) throw new Error('unknown crop: ' + name);
  const [scr, x, y, w, h] = c;
  const s = Math.min(maxW / w, (maxH || 1e9) / h);
  const el = document.createElement('div');
  el.className = 'crop ' + cls;
  el.style.cssText = `--img:url(assets/${scr}.jpg);--x:${x};--y:${y};--cw:${w};--ch:${h};--s:${s};background-color:#0f1424`;
  el.dataset.w = w * s; el.dataset.h = h * s;
  return el;
};

const SB_ICONS = `<svg viewBox="0 0 18 12"><path fill="#fff" d="M0 9h3v3H0zM5 6h3v6H5zM10 3h3v9h-3zM15 0h3v12h-3z"/></svg>
<svg viewBox="0 0 16 12"><path fill="#fff" d="M8 12 0 3.5a11.5 11.5 0 0 1 16 0z"/></svg>
<svg viewBox="0 0 24 12"><rect x=".75" y=".75" width="20" height="10.5" rx="3" fill="none" stroke="#fff" stroke-width="1.5" opacity=".6"/><rect x="2.5" y="2.5" width="14" height="7" rx="1.5" fill="#fff"/><rect x="22" y="4" width="1.8" height="4" rx=".9" fill="#fff" opacity=".6"/></svg>`;

window.phoneEl = (screen, w, cls = '') => {
  if (!SCREENS.includes(screen)) throw new Error('unknown screen: ' + screen);
  const el = document.createElement('div');
  el.className = 'phone ' + cls;
  el.style.setProperty('--w', w + 'px');
  el.innerHTML = `<div class="screen"><img src="assets/${screen}.jpg" alt="">
    <div class="sb" style="background-image:url(assets/${screen}.jpg)"><span>9:41</span><span class="ic">${SB_ICONS}</span></div>
    <div class="cam"></div><div class="glare"></div></div>`;
  return el;
};

window.preload = () => Promise.all([...SCREENS.map(s => `assets/${s}.jpg`), 'assets/logo.png', 'assets/google-play-badge-tr.png']
  .map(src => new Promise((ok, no) => { const i = new Image(); i.onload = ok; i.onerror = () => no(new Error('missing ' + src)); i.src = src; })))
  .then(() => document.fonts.ready);
