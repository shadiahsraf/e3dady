(function() {
    "use strict";

    var individualCard = document.getElementById('individual-card');
    var teamCard = document.getElementById('team-card');
    var manualInput = document.getElementById('manual-code');
    var startBtn = document.getElementById('btn-start');
    var stopBtn = document.getElementById('btn-stop');
    var btnManual = document.getElementById('btn-manual');

    var state = { code: null, scanType: null, lastScannedAt: 0 };
    var scanner = null;
    var scanning = false;

    function anim(target, from, to) {
        try { if (typeof gsap !== 'undefined') gsap.fromTo(target, from, to); } catch(e) {}
    }

    function showToast(msg, kind) {
        try {
            if (typeof YC !== 'undefined' && YC.showToast) {
                YC.showToast(msg, kind);
                return;
            }
        } catch(e) {}
        try {
            var container = document.getElementById('toast-container');
            if (!container) {
                container = document.createElement('div');
                container.id = 'toast-container';
                container.style.cssText = 'position:fixed;top:20px;left:50%;transform:translateX(-50%);z-index:9999;display:flex;flex-direction:column;gap:8px;align-items:center;';
                document.body.appendChild(container);
            }
            var el = document.createElement('div');
            el.className = 'toast toast-' + (kind || 'success');
            el.textContent = msg;
            el.style.cssText = 'padding:12px 28px;border-radius:12px;font-weight:700;font-size:0.95rem;min-width:200px;text-align:center;background:rgba(13,59,28,0.9);color:#ffebcd;border:1px solid rgba(231,180,67,0.2);';
            if (kind === 'error') el.style.borderColor = 'rgba(192,57,43,0.5)';
            if (kind === 'success') el.style.borderColor = 'rgba(231,180,67,0.5)';
            container.appendChild(el);
            setTimeout(function() { try { el.remove(); } catch(e2) {} }, 2500);
        } catch(e) {
            alert(msg);
        }
    }

    function csrfToken() {
        try { if (typeof CSRF_TOKEN !== 'undefined') return CSRF_TOKEN; } catch(e) {}
        try {
            var m = document.cookie.match(/csrftoken=([^;]+)/);
            if (m) return m[1];
        } catch(e) {}
        return '';
    }

    function extractCode(text) {
        if (!text) return '';
        text = String(text).trim();
        if (!text) return '';
        try {
            var url = new URL(text);
            var codeParam = url.searchParams.get('code');
            if (codeParam) return codeParam.toUpperCase();
        } catch (e) {}
        return text.toUpperCase();
    }

    // ── Camera scanner ──
    function startScanner() {
        if (scanning) return;
        if (typeof Html5Qrcode === 'undefined') { showToast('مكتبة الكاميرا مش محملة', 'error'); return; }
        scanner = new Html5Qrcode('qr-reader');
        scanner.start(
            { facingMode: 'environment' },
            { fps: 10, qrbox: { width: 220, height: 220 } },
            onScanSuccess, function() {}
        ).then(function() {
            scanning = true;
            startBtn.classList.add('hidden');
            stopBtn.classList.remove('hidden');
        }).catch(function() { showToast('فشل تشغيل الكاميرا', 'error'); });
    }

    function stopScanner() {
        if (!scanning || !scanner) return;
        scanner.stop().then(function() {
            scanner.clear(); scanning = false;
            startBtn.classList.remove('hidden');
            stopBtn.classList.add('hidden');
        }).catch(function() {});
    }

    function onScanSuccess(decodedText) {
        var code = extractCode(decodedText);
        var now = Date.now();
        if (state.code === code && now - state.lastScannedAt < 2500) return;
        state.lastScannedAt = now;
        lookup(code);
    }

    // ── Event listeners ──
    if (startBtn) startBtn.addEventListener('click', startScanner);
    if (stopBtn) stopBtn.addEventListener('click', stopScanner);

    function doManualSearch() {
        if (!manualInput) return;
        var v = extractCode(manualInput.value);
        if (!v) {
            showToast('اكتب الكود الأول', 'error');
            return;
        }
        lookup(v);
    }

    if (btnManual) {
        btnManual.addEventListener('click', doManualSearch);
    }
    if (manualInput) {
        manualInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') doManualSearch();
        });
    }

    window.scannerDoManualSearch = doManualSearch;

    // ── Lookup ──
    function lookup(code) {
        if (!code) { showToast('كود فاضي', 'error'); return; }

        if (btnManual) {
            btnManual.textContent = '...';
            btnManual.disabled = true;
        }

        fetch('/api/lookup/?code=' + encodeURIComponent(code))
            .then(function(r) {
                if (!r.ok) {
                    return r.json().then(function(d) {
                        throw new Error(d.error || 'خطأ ' + r.status);
                    });
                }
                return r.json();
            })
            .then(function(data) {
                if (btnManual) { btnManual.textContent = 'ابحث'; btnManual.disabled = false; }

                if (!data.ok) { showToast(data.error || 'مش لاقي الكود', 'error'); return; }
                hideAllCards();
                state.code = code;

                if (data.scan_type === 'team') {
                    showTeamCard(data.team);
                } else {
                    showIndividualCard(data.participant);
                }
                try { if (typeof YC !== 'undefined' && YC.playScanSound) YC.playScanSound(); } catch(e) {}
            })
            .catch(function(err) {
                if (btnManual) { btnManual.textContent = 'ابحث'; btnManual.disabled = false; }
                showToast(err.message || 'مشكلة في الشبكة', 'error');
            });
    }

    window.scannerLookup = lookup;

    function hideAllCards() {
        if (individualCard) individualCard.classList.add('hidden');
        if (teamCard) teamCard.classList.add('hidden');
        var pm = document.getElementById('p-message');
        var tm = document.getElementById('t-message');
        if (pm) pm.classList.add('hidden');
        if (tm) tm.classList.add('hidden');
    }

    // ── Show individual ──
    function showIndividualCard(p) {
        state.scanType = 'individual';
        var pName = document.getElementById('p-name');
        var pCode = document.getElementById('p-code');
        var pPoints = document.getElementById('p-points');
        var pFlag = document.getElementById('p-flag');
        var pBadge = document.getElementById('p-badge');

        if (pName) pName.textContent = p.name;
        if (pCode) pCode.textContent = p.unique_code;
        if (pPoints) pPoints.textContent = p.total_points;
        if (pFlag) pFlag.textContent = (p.team && p.team.flag) ? p.team.flag : '🏳️';
        if (pBadge) {
            pBadge.textContent = p.team ? p.team.name_ar : '';
            pBadge.style.background = p.team ? p.team.primary : '#333';
            pBadge.style.color = '#fff';
        }

        if (individualCard) {
            individualCard.classList.remove('hidden');
            anim(individualCard, { y: 30, opacity: 0 }, { y: 0, opacity: 1, duration: 0.4 });
            individualCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    // ── Show team ──
    function showTeamCard(t) {
        state.scanType = 'team';
        var tFlag = document.getElementById('t-flag');
        var tName = document.getElementById('t-name');
        var tCount = document.getElementById('t-count');
        var tPoints = document.getElementById('t-points');

        if (tFlag) tFlag.textContent = t.flag || '🏳️';
        if (tName) tName.textContent = t.name_ar;
        if (tCount) tCount.textContent = t.members_count;
        if (tPoints) tPoints.textContent = t.total_points;

        if (teamCard) {
            teamCard.classList.remove('hidden');
            anim(teamCard, { y: 30, opacity: 0 }, { y: 0, opacity: 1, duration: 0.4 });
            teamCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    // ── Adjust points (+ / - stepper buttons) ──
    window.adjustPoints = function(inputId, delta) {
        var input = document.getElementById(inputId);
        if (!input) return;
        var val = parseInt(input.value, 10) || 0;
        val += delta;
        if (val > 999) val = 999;
        if (val < -999) val = -999;
        input.value = val;
    };

    // ── Send custom points ──
    window.sendCustomPoints = function(type, negate) {
        if (!state.code) { showToast('امسح حد الأول', 'error'); return; }

        var inputId = (type === 'team') ? 'team-points' : 'individual-points';
        var input = document.getElementById(inputId);
        var pts = parseInt(input ? input.value : '1', 10) || 1;
        if (negate) pts = -Math.abs(pts);
        else pts = Math.abs(pts);

        var location = '';
        if (type === 'team') {
            var teamLoc = document.getElementById('team-location');
            location = teamLoc ? teamLoc.value : '';
        } else {
            var indLoc = document.getElementById('individual-location');
            location = indLoc ? indLoc.value : '';
        }

        var bodyStr = 'code=' + encodeURIComponent(state.code) +
                      '&points=' + encodeURIComponent(String(pts)) +
                      '&location=' + encodeURIComponent(location);

        fetch('/api/scan/', {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken(), 'Content-Type': 'application/x-www-form-urlencoded' },
            body: bodyStr,
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (!data.ok) { showToast(data.error || 'خطأ', 'error'); return; }

            if (data.scan_type === 'individual') {
                var pp = document.getElementById('p-points');
                if (pp) pp.textContent = data.participant.total_points;
                var msgEl = document.getElementById('p-message');
                if (msgEl) { msgEl.textContent = data.message; msgEl.classList.remove('hidden'); }
                anim(pp, { scale: 1.5 }, { scale: 1, duration: 0.4 });
            } else {
                var tp = document.getElementById('t-points');
                if (tp) tp.textContent = data.team.total_points;
                var msgEl2 = document.getElementById('t-message');
                if (msgEl2) { msgEl2.textContent = data.message; msgEl2.classList.remove('hidden'); }
                anim(tp, { scale: 1.5 }, { scale: 1, duration: 0.4 });
            }

            showToast(data.message, 'success');
            try { if (typeof YC !== 'undefined' && YC.playSuccessChime) YC.playSuccessChime(); } catch(e) {}
        })
        .catch(function() {
            showToast('مشكلة في الشبكة', 'error');
        });
    };

    // ── Auto-load from URL ?code= ──
    try {
        var urlParams = new URLSearchParams(window.location.search);
        var urlCode = urlParams.get('code');
        if (urlCode) {
            lookup(urlCode.toUpperCase());
        }
    } catch(e) {}
})();
