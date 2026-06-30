window.YC = (function () {
    // ── Audio ──
    let audioCtx = null;
    function getAudioCtx() {
        if (!audioCtx) {
            const Ctx = window.AudioContext || window.webkitAudioContext;
            if (Ctx) audioCtx = new Ctx();
        }
        return audioCtx;
    }

    function playBeep(freq = 880, duration = 120) {
        try {
            const ctx = getAudioCtx();
            if (!ctx) return;
            if (ctx.state === 'suspended') ctx.resume();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.value = freq;
            gain.gain.setValueAtTime(0.12, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration / 1000);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + duration / 1000);
        } catch (e) {}
    }

    function playSuccessChime() {
        playBeep(880, 100);
        setTimeout(() => playBeep(1320, 140), 120);
    }

    function playGoalFanfare() {
        const notes = [523, 659, 784, 1046];
        notes.forEach((f, i) => setTimeout(() => playBeep(f, 250), i * 200));
    }

    function playScanSound() {
        playBeep(660, 80);
        setTimeout(() => playBeep(880, 80), 90);
    }

    function playCrowdCheer() {
        const ctx = getAudioCtx();
        if (!ctx) return;
        if (ctx.state === 'suspended') ctx.resume();
        const duration = 2.5;
        const bufferSize = ctx.sampleRate * duration;
        const buffer = ctx.createBuffer(2, bufferSize, ctx.sampleRate);
        for (let ch = 0; ch < 2; ch++) {
            const data = buffer.getChannelData(ch);
            for (let i = 0; i < bufferSize; i++) {
                const t = i / ctx.sampleRate;
                const env = Math.exp(-t * 1.5) * (0.5 + 0.5 * Math.sin(t * 6));
                data[i] = (Math.random() * 2 - 1) * env * 0.15;
            }
        }
        const source = ctx.createBufferSource();
        source.buffer = buffer;
        const filter = ctx.createBiquadFilter();
        filter.type = 'bandpass';
        filter.frequency.value = 800;
        filter.Q.value = 0.5;
        source.connect(filter);
        filter.connect(ctx.destination);
        source.start();
    }

    // ── Toast ──
    function showToast(msg, kind = 'success') {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = 'position:fixed;top:20px;left:50%;transform:translateX(-50%);z-index:9999;display:flex;flex-direction:column;gap:8px;align-items:center;';
            document.body.appendChild(container);
        }
        const el = document.createElement('div');
        el.className = `toast toast-${kind}`;
        el.textContent = msg;
        container.appendChild(el);
        setTimeout(() => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(-10px)';
            el.style.transition = 'all 0.3s ease';
            setTimeout(() => el.remove(), 300);
        }, 2500);
    }

    // ── Goal Popup ──
    function showGoalPopup(title, subtitle) {
        let container = document.getElementById('goal-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'goal-container';
            document.body.appendChild(container);
        }
        const overlay = document.createElement('div');
        overlay.className = 'goal-overlay';
        overlay.innerHTML = `
            <div class="goal-text">${title}</div>
            <div class="goal-sub">${subtitle || ''}</div>
        `;
        container.appendChild(overlay);

        try {
            if (typeof gsap !== 'undefined') {
                gsap.fromTo(overlay, { opacity: 0 }, { opacity: 1, duration: 0.4 });
                gsap.fromTo(overlay.querySelector('.goal-text'),
                    { scale: 0.3, rotation: -10 },
                    { scale: 1, rotation: 0, duration: 0.8, ease: 'elastic.out(1, 0.5)' }
                );
            }
        } catch(e) {}

        playGoalFanfare();
        playCrowdCheer();

        setTimeout(() => {
            try {
                if (typeof gsap !== 'undefined') {
                    gsap.to(overlay, { opacity: 0, duration: 0.5, onComplete: () => overlay.remove() });
                } else {
                    overlay.remove();
                }
            } catch(e) { try { overlay.remove(); } catch(e2) {} }
        }, 4500);
    }

    // ── CSRF ──
    function csrfToken() {
        if (typeof CSRF_TOKEN !== 'undefined') return CSRF_TOKEN;
        const m = document.cookie.match(/csrftoken=([^;]+)/);
        return m ? m[1] : '';
    }

    // ── WebSocket ──
    let ws = null;
    let wsCallbacks = [];
    let wsReconnectTimer = null;

    function connectWS() {
        if (ws && ws.readyState <= 1) return;
        const proto = location.protocol === 'https:' ? 'wss' : 'ws';
        ws = new WebSocket(`${proto}://${location.host}/ws/live/`);
        ws.onopen = () => { if (wsReconnectTimer) { clearTimeout(wsReconnectTimer); wsReconnectTimer = null; } };
        ws.onmessage = (e) => {
            try {
                const data = JSON.parse(e.data);
                wsCallbacks.forEach(cb => cb(data));
            } catch (err) {}
        };
        ws.onclose = () => {
            wsReconnectTimer = setTimeout(connectWS, 2000);
        };
        ws.onerror = () => { ws.close(); };
    }

    function onWSMessage(callback) {
        wsCallbacks.push(callback);
        connectWS();
    }

    // ── Three.js 3D Background ──
    function initThreeBackground() {
        const canvas = document.getElementById('three-bg');
        if (!canvas) return;
        if (typeof THREE === 'undefined') return;

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.z = 5;

        const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setClearColor(0x000000, 0);

        // Football (icosahedron with pentagon pattern)
        const ballGeo = new THREE.IcosahedronGeometry(0.8, 1);
        const ballMat = new THREE.MeshPhongMaterial({
            color: 0xffebcd,
            emissive: 0x0d3b1c,
            shininess: 80,
            wireframe: false,
            transparent: true,
            opacity: 0.15,
        });
        const ball = new THREE.Mesh(ballGeo, ballMat);
        ball.position.set(2.5, 0.5, -2);
        scene.add(ball);

        // Wireframe overlay for football effect
        const wireGeo = new THREE.IcosahedronGeometry(0.82, 1);
        const wireMat = new THREE.MeshBasicMaterial({
            color: 0xe7b443,
            wireframe: true,
            transparent: true,
            opacity: 0.08,
        });
        const wireframe = new THREE.Mesh(wireGeo, wireMat);
        wireframe.position.copy(ball.position);
        scene.add(wireframe);

        // Floating particles (stadium lights effect)
        const particleCount = 200;
        const particlesGeo = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        const colors = new Float32Array(particleCount * 3);
        const particleColors = [
            [0.05, 0.23, 0.11],  // dark green
            [0.91, 0.71, 0.26],  // orange
            [1.0, 0.92, 0.80],   // yellow/cream
            [0.13, 0.46, 0.22],  // medium green
        ];

        for (let i = 0; i < particleCount; i++) {
            positions[i * 3] = (Math.random() - 0.5) * 20;
            positions[i * 3 + 1] = (Math.random() - 0.5) * 20;
            positions[i * 3 + 2] = (Math.random() - 0.5) * 15 - 3;
            const c = particleColors[Math.floor(Math.random() * particleColors.length)];
            colors[i * 3] = c[0];
            colors[i * 3 + 1] = c[1];
            colors[i * 3 + 2] = c[2];
        }
        particlesGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        particlesGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

        const particlesMat = new THREE.PointsMaterial({
            size: 0.04,
            vertexColors: true,
            transparent: true,
            opacity: 0.6,
            blending: THREE.AdditiveBlending,
        });
        const particles = new THREE.Points(particlesGeo, particlesMat);
        scene.add(particles);

        // Stadium spotlight beams
        const spotGeo = new THREE.ConeGeometry(0.3, 6, 8, 1, true);
        const spotMat = new THREE.MeshBasicMaterial({
            color: 0xe7b443,
            transparent: true,
            opacity: 0.03,
            side: THREE.DoubleSide,
        });
        const spots = [];
        for (let i = 0; i < 4; i++) {
            const spot = new THREE.Mesh(spotGeo, spotMat.clone());
            spot.position.set(-6 + i * 4, 5, -4);
            spot.rotation.x = Math.PI * 0.15;
            spot.rotation.z = (Math.random() - 0.5) * 0.3;
            scene.add(spot);
            spots.push(spot);
        }

        // Ambient + directional light
        scene.add(new THREE.AmbientLight(0x0d3b1c, 0.5));
        const dirLight = new THREE.DirectionalLight(0xe7b443, 0.3);
        dirLight.position.set(5, 5, 5);
        scene.add(dirLight);

        // Mouse parallax
        let mouseX = 0, mouseY = 0;
        document.addEventListener('mousemove', (e) => {
            mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
            mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
        });

        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });

        function animate() {
            requestAnimationFrame(animate);
            const time = Date.now() * 0.001;

            ball.rotation.x += 0.003;
            ball.rotation.y += 0.005;
            wireframe.rotation.x = ball.rotation.x;
            wireframe.rotation.y = ball.rotation.y;

            ball.position.y = 0.5 + Math.sin(time * 0.8) * 0.3;
            wireframe.position.y = ball.position.y;

            particles.rotation.y += 0.0003;
            particles.rotation.x += 0.0001;

            const posArr = particlesGeo.attributes.position.array;
            for (let i = 0; i < particleCount; i++) {
                posArr[i * 3 + 1] += Math.sin(time + i) * 0.001;
            }
            particlesGeo.attributes.position.needsUpdate = true;

            spots.forEach((s, i) => {
                s.rotation.z = Math.sin(time * 0.5 + i * 1.5) * 0.2;
                s.material.opacity = 0.02 + Math.sin(time * 0.7 + i) * 0.01;
            });

            camera.position.x += (mouseX * 0.3 - camera.position.x) * 0.02;
            camera.position.y += (-mouseY * 0.3 - camera.position.y) * 0.02;
            camera.lookAt(0, 0, -2);

            renderer.render(scene, camera);
        }
        animate();
    }

    // ── Init ──
    document.addEventListener('DOMContentLoaded', () => {
        try { initThreeBackground(); } catch(e) {}
    });

    return {
        showToast,
        showGoalPopup,
        playBeep,
        playSuccessChime,
        playGoalFanfare,
        playScanSound,
        playCrowdCheer,
        csrfToken,
        connectWS,
        onWSMessage,
        initThreeBackground,
    };
})();
