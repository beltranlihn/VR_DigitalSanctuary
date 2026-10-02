/* Icons: ISP's ICO() (Immersive Studio Pro index.html:1458, stroke 1.8, viewBox 24) + the editor's own, same stroke. */
(function (root) {
  'use strict';
  const P = {
    folder: '<path d="M3 7h6l2 2h10v9H3z"/>', plus: '<path d="M12 5v14M5 12h14"/>',
    panelL: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/>', panel: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M15 4v16"/>',
    fit: '<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>', zoomOut: '<circle cx="11" cy="11" r="7"/><path d="M8 11h6M20 20l-3.5-3.5"/>',
    zoomIn: '<circle cx="11" cy="11" r="7"/><path d="M11 8v6M8 11h6M20 20l-3.5-3.5"/>', chevDown: '<path d="M6 9l6 6 6-6"/>', chevR: '<path d="M9 6l6 6-6 6"/>',
    toStart: '<path d="M6 5v14M18 5l-9 7 9 7z"/>', toEnd: '<path d="M18 5v14M6 5l9 7-9 7z"/>',
    play: '<path d="M7 5l12 7-12 7z" fill="currentColor" stroke="none"/>', pause: '<rect x="7" y="5" width="3.5" height="14" fill="currentColor" stroke="none"/><rect x="13.5" y="5" width="3.5" height="14" fill="currentColor" stroke="none"/>',
    flag: '<path d="M6 3v18"/><path d="M6 4h11l-2.5 3.5L17 11H6"/>', curves: '<path d="M3 17C7 17 8 7 12 7s5 10 9 10"/>',
    follow: '<circle cx="12" cy="12" r="6.5"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3"/><circle cx="12" cy="12" r="1.6" fill="currentColor" stroke="none"/>',
    viewer: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="2.5"/>',
    popout: '<rect x="3" y="5" width="11" height="11" rx="1.5"/><path d="M15 4h5v5"/><path d="M20 4l-7 7"/>',
    hourglass: '<path d="M7 3h10M7 21h10"/><path d="M8 3c0 5 8 5 8 9s-8 4-8 9"/><path d="M16 3c0 5-8 5-8 9s8 4 8 9"/>',
    anchor: '<circle cx="12" cy="5" r="2"/><path d="M12 7v13"/><path d="M5 13a7 7 0 0 0 14 0"/><path d="M8 11h8"/>',
    person: '<circle cx="12" cy="7" r="3"/><path d="M5 20a7 7 0 0 1 14 0"/>', note: '<path d="M5 4h14v12l-4 4H5z"/><path d="M15 20v-4h4"/>',
    lock: '<rect x="5" y="11" width="14" height="9" rx="1.5"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    wave: '<path d="M3 12h2M7 8v8M11 5v14M15 9v6M19 11v2"/>', text: '<path d="M5 6h14"/><path d="M12 6v13"/>',
    obj: '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M12 12l8-4.5M12 12v9M12 12L4 7.5"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>', ghost: '<path d="M6 20V10a6 6 0 0 1 12 0v10l-3-2-3 2-3-2z"/>',
    haptic: '<path d="M4 12h3l2-5 3 10 2-5h6"/>', walk: '<circle cx="13" cy="4" r="2"/><path d="M9 21l3-7 3 3v5M8 12l3-4 4 3 3 1"/>',
    alma: '<circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="9" stroke-dasharray="2 3"/>', sound: '<path d="M4 9v6h4l5 4V5L8 9z"/><path d="M16 8a5 5 0 0 1 0 8"/>',
    upload: '<path d="M12 16V5"/><path d="M8 9l4-4 4 4"/><path d="M5 19h14"/>', wire: '<path d="M9 3v5M15 3v5"/><path d="M7 8h10v3a5 5 0 0 1-10 0z"/><path d="M12 16v5"/>',
    logic: '<rect x="3" y="5" width="6" height="5" rx="1"/><rect x="15" y="14" width="6" height="5" rx="1"/><path d="M9 7.5h3a2 2 0 0 1 2 2v5a2 2 0 0 0 2 2"/>',
    world: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    save: '<path d="M5 4h11l3 3v13H5z"/><path d="M8 4v5h7"/><rect x="8" y="13" width="8" height="6"/>',
    trash: '<path d="M5 7h14M9 7V5h6v2M6 7l1 13h10l1-13"/>', warn: '<path d="M12 3l9 16H3z"/><path d="M12 10v4M12 17v.5"/>',
  };
  root.ICO = function (n, s) {
    s = s || 13;
    return `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${P[n] || ''}</svg>`;
  };
})(window);
