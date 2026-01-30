(function () {
    'use strict';
    window.SYNEX_THEME_READY = true;

    // Configurações
    const config = window.SYNEX_CONFIG || {};
    const urls = config.urls || {};
    const userConfig = config.user || {};

    // Helper de carregamento
    function onReady(fn) {
        if (document.readyState !== 'loading') {
            fn();
        } else {
            document.addEventListener('DOMContentLoaded', fn);
        }
    }

    function getCookie(name) {
        var value = "; " + document.cookie;
        var parts = value.split("; " + name + "=");
        if (parts.length === 2) return parts.pop().split(";").shift();
        return "";
    }

    function showGlobalToast(message, isError) {
        var toast = document.getElementById('global-toast');
        if (!toast) return;
        toast.textContent = message;
        toast.classList.toggle('border-rose-200', !!isError);
        toast.classList.toggle('bg-rose-50', !!isError);
        toast.classList.toggle('text-rose-700', !!isError);
        toast.classList.toggle('border-emerald-200', !isError);
        toast.classList.toggle('bg-emerald-50', !isError);
        toast.classList.toggle('text-emerald-700', !isError);
        toast.classList.remove('hidden');
        setTimeout(function () { toast.classList.add('hidden'); }, 2800);
    }

    // --- TEMA ---
    function initThemeToggle() {
        const buttons = document.querySelectorAll('[data-theme-toggle]');
        if (!buttons.length) return;

        const updateIcons = () => {
            const darkIcon = document.getElementById('theme-toggle-dark-icon');
            const lightIcon = document.getElementById('theme-toggle-light-icon');
            const themeText = document.getElementById('theme-text');
            const isDark = document.documentElement.classList.contains('dark');
            if (darkIcon) darkIcon.classList.toggle('hidden', isDark);
            if (lightIcon) lightIcon.classList.toggle('hidden', !isDark);
            if (themeText) themeText.textContent = isDark ? 'Tema Claro' : 'Tema Escuro';
        };

        buttons.forEach((btn) => {
            btn.addEventListener('click', () => {
            if (document.documentElement.classList.contains('dark')) {
                document.documentElement.classList.remove('dark');
                localStorage.setItem('color-theme', 'light');
            } else {
                document.documentElement.classList.add('dark');
                localStorage.setItem('color-theme', 'dark');
            }
            updateIcons();
        });
        });

        updateIcons();
    }

    // =================================================================
    // ONBOARDING V10 (LIMPO E SEGURO)
    // =================================================================


    function initProfileMenu() {
        const toggle = document.getElementById('profile-menu-toggle');
        const menu = document.getElementById('profile-menu');
        if (!toggle || !menu) return;

        function closeMenu() {
            menu.classList.add('hidden');
            toggle.setAttribute('aria-expanded', 'false');
        }

        function openMenu() {
            menu.classList.remove('hidden');
            toggle.setAttribute('aria-expanded', 'true');
        }

        toggle.addEventListener('click', function (event) {
            event.preventDefault();
            event.stopPropagation();
            if (menu.classList.contains('hidden')) {
                openMenu();
            } else {
                closeMenu();
            }
        });

        document.addEventListener('click', function (event) {
            if (!menu.classList.contains('hidden') && !menu.contains(event.target) && !toggle.contains(event.target)) {
                closeMenu();
            }
        });

        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape') {
                closeMenu();
            }
        });
    }

    function initSidebarToggle() {
        const toggle = document.getElementById('sidebar-toggle');
        const body = document.body;
        if (!toggle || !body) return;
        const key = 'synex_sidebar_collapsed';

        function applyState(collapsed) {
            body.classList.toggle('sidebar-collapsed', collapsed);
        }

        const saved = localStorage.getItem(key) === '1';
        applyState(saved);

        toggle.addEventListener('click', function () {
            const next = !body.classList.contains('sidebar-collapsed');
            applyState(next);
            localStorage.setItem(key, next ? '1' : '0');
        });
    }

    function initOnboarding() {
        const userId = userConfig.id ? String(userConfig.id) : 'anon';
        const PREFIX = `synex_v10_${userId}_`; // Prefixo V10 para ignorar caches antigos

        const keys = {
            done: `${PREFIX}done`,
            step: `${PREFIX}step`,
            active: `${PREFIX}active`,
            pending: `${PREFIX}pending`,
            name: `${PREFIX}name`,
            pause: `${PREFIX}pause`
        };

        // --- DETECÇÃO SEGURA ---
        const currentUrl = window.location.href.toLowerCase();
        // Verifica se é página de matéria (URL ou Título)
        const isMateriaPage = currentUrl.indexOf('materia') > -1 || document.title.toLowerCase().indexOf('materia') > -1;
        const isPending = localStorage.getItem(keys.pending) === '1';

        // REGRA 1: ESTOU CRIANDO MATÉRIA -> PARE TUDO
        if (isPending && isMateriaPage) {
            return; 
        }

        // REGRA 2: VOLTEI DA CRIAÇÃO -> AVANÇA
        let initialIndex = parseInt(localStorage.getItem(keys.step) || '0', 10);
        if (isPending && !isMateriaPage) {
            localStorage.removeItem(keys.pending); 
            initialIndex = 2; // Pula para o Tema
            localStorage.setItem(keys.step, '2');
            localStorage.setItem(keys.active, '1');
        }

        // Verificações finais
        if (localStorage.getItem(keys.done) === '1') return;
        if (localStorage.getItem(keys.pause) === '1') return;
        
        const shouldShow = (!!userConfig.id || localStorage.getItem(keys.active) === '1');
        if (!shouldShow) return;

        // --- UI ---
        function buildOverlay() {
            const overlay = document.createElement('div');
            Object.assign(overlay.style, {
                position: 'fixed', inset: '0', zIndex: '99999', display: 'flex',
                alignItems: 'center', justifyContent: 'center', background: 'rgba(15, 23, 42, 0.95)',
                backdropFilter: 'blur(5px)'
            });
            overlay.id = 'synex-onboarding';

            const card = document.createElement('div');
            Object.assign(card.style, {
                maxWidth: '550px', width: '90%', background: '#1e293b',
                border: '1px solid #334155', borderRadius: '16px', padding: '30px',
                color: '#f8fafc', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)'
            });

            card.innerHTML = `
                <div style="margin-bottom: 20px;">
                     <span id="ob-badge" style="background:#334155; color:#94a3b8; padding:4px 8px; border-radius:4px; font-size:11px; font-weight:700; text-transform:uppercase;">Passo 1</span>
                </div>
                <h2 id="ob-title" style="font-size: 22px; font-weight: 700; margin-bottom: 10px; color: #fff;"></h2>
                <p id="ob-subtitle" style="font-size: 15px; color: #cbd5e1; line-height: 1.5; margin-bottom: 25px;"></p>
                <div id="ob-content" style="margin-bottom: 30px; min-height: 80px;"></div>
                <div style="display:flex; justify-content:flex-end; gap:12px; border-top: 1px solid #334155; padding-top: 20px;">
                    <button id="ob-skip" style="margin-right:auto; background:transparent; border:none; color:#64748b; font-size:13px; cursor:pointer;">Pular</button>
                    <button id="ob-next" style="background:#6366f1; color:#fff; font-weight:600; border:none; border-radius:8px; padding:10px 24px; font-size:14px; cursor:pointer;">Continuar</button>
                </div>
            `;
            overlay.appendChild(card);
            return {
                overlay, badge: card.querySelector('#ob-badge'), title: card.querySelector('#ob-title'),
                subtitle: card.querySelector('#ob-subtitle'), content: card.querySelector('#ob-content'),
                nextBtn: card.querySelector('#ob-next'), skip: card.querySelector('#ob-skip')
            };
        }

        function startOnboarding(startIndex) {
            if (document.getElementById('synex-onboarding')) return;

            const steps = [
                {
                    title: 'Bem-vindo ao Synex!',
                    subtitle: 'Vamos configurar seu ambiente.',
                    render: (wrap) => { wrap.innerHTML = `<div style="text-align:center; font-size: 50px;">🚀</div>`; }
                },
                {
                    title: 'Crie sua primeira Matéria',
                    subtitle: 'Para usar o cronograma, precisamos de uma matéria.',
                    render: (wrap) => {
                        const btn = document.createElement('a');
                        btn.href = urls.materias || '/materias/';
                        btn.innerHTML = `Ir para cadastro de Matéria`;
                        Object.assign(btn.style, {
                            display: 'block', width: '100%', padding: '16px', borderRadius: '10px', 
                            background: '#0ea5e9', color: '#fff', textAlign: 'center',
                            textDecoration: 'none', fontWeight: 'bold'
                        });
                        btn.addEventListener('click', () => { localStorage.setItem(keys.pending, '1'); });
                        wrap.appendChild(btn);
                    }
                },
                {
                    title: 'Personalize o Tema',
                    subtitle: 'Escolha o visual.',
                    render: (wrap) => {
                        const grid = document.createElement('div');
                        Object.assign(grid.style, { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' });
                        
                        const makeBtn = (label, isDarkOption) => {
                            const b = document.createElement('div');
                            Object.assign(b.style, { padding:'15px', borderRadius:'10px', border:'1px solid #475569', background:'#0f172a', color:'#fff', textAlign:'center', cursor:'pointer' });
                            b.innerText = label;
                            b.onclick = () => {
                                if(isDarkOption) { document.documentElement.classList.add('dark'); localStorage.setItem('color-theme', 'dark'); }
                                else { document.documentElement.classList.remove('dark'); localStorage.setItem('color-theme', 'light'); }
                            };
                            return b;
                        };
                        grid.appendChild(makeBtn('☀️ Claro', false));
                        grid.appendChild(makeBtn('🌙 Escuro', true));
                        wrap.appendChild(grid);
                    }
                },
                {
                    title: 'Seu Nome',
                    subtitle: 'Como devemos te chamar?',
                    render: (wrap) => {
                        const input = document.createElement('input');
                        input.type = 'text'; input.placeholder = 'Nome...';
                        input.value = localStorage.getItem(keys.name) || '';
                        Object.assign(input.style, { width:'100%', padding:'12px', borderRadius:'8px', background:'#0f172a', border:'1px solid #475569', color:'#fff' });
                        input.oninput = (e) => localStorage.setItem(keys.name, e.target.value);
                        wrap.appendChild(input);
                    }
                },
                {
                    title: 'Pronto!',
                    subtitle: 'Configuração concluída.',
                    render: (wrap) => { wrap.innerHTML = `<div style="text-align:center; padding: 20px; color: #4ade80; font-weight: bold;">Vamos lá!</div>`; }
                }
            ];

            const ui = buildOverlay();
            document.body.appendChild(ui.overlay);

            let index = Math.min(Math.max(startIndex, 0), steps.length - 1);

            const updateUI = () => {
                const step = steps[index];
                ui.badge.textContent = `PASSO ${index + 1} DE ${steps.length}`;
                ui.title.textContent = step.title;
                ui.subtitle.textContent = step.subtitle;
                ui.content.innerHTML = '';
                step.render(ui.content);

                if (index === 1) ui.nextBtn.textContent = 'Já criei (Avançar)';
                else if (index === steps.length - 1) { ui.nextBtn.textContent = 'Concluir'; ui.nextBtn.style.background = '#10b981'; }
                else { ui.nextBtn.textContent = 'Continuar'; ui.nextBtn.style.background = '#6366f1'; }
                
                localStorage.setItem(keys.step, String(index));
                localStorage.setItem(keys.active, '1');
            };

            function launchConfetti() {
                var colors = ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#a855f7', '#14b8a6', '#f97316'];
                var bursts = 5;
                var perBurst = 140;
                for (var b = 0; b < bursts; b++) {
                    (function (delay) {
                        setTimeout(function () {
                            var originX = Math.random() * window.innerWidth;
                            var originY = Math.random() * window.innerHeight * 0.6 + window.innerHeight * 0.1;
                            for (var i = 0; i < perBurst; i++) {
                                var piece = document.createElement('div');
                                piece.className = 'confetti-piece';
                                var size = 6 + Math.random() * 8;
                                piece.style.width = size + 'px';
                                piece.style.height = (size * 0.6) + 'px';
                                piece.style.left = originX + 'px';
                                piece.style.top = originY + 'px';
                                piece.style.setProperty('--color', colors[i % colors.length]);
                                var angle = Math.random() * Math.PI * 2;
                                var distance = 180 + Math.random() * 360;
                                var dx = Math.cos(angle) * distance;
                                var dy = Math.sin(angle) * distance;
                                piece.style.setProperty('--dx', dx + 'px');
                                piece.style.setProperty('--dy', dy + 'px');
                                piece.style.setProperty('--dur', (1.4 + Math.random() * 0.9) + 's');
                                document.body.appendChild(piece);
                                (function (el) {
                                    setTimeout(function () { el.remove(); }, 2600);
                                })(piece);
                            }
                        }, delay);
                    })(b * 220);
                }
            }

            const finish = () => {
                localStorage.setItem(keys.done, '1');
                localStorage.removeItem(keys.active);
                localStorage.removeItem(keys.step);
                localStorage.removeItem(keys.pause);
                localStorage.removeItem(keys.pending);
                if (ui.overlay) ui.overlay.remove();
                launchConfetti();
            };

            ui.skip.onclick = finish;
            ui.nextBtn.onclick = () => { if (index < steps.length - 1) { index++; updateUI(); } else { finish(); } };
            updateUI();
        }

        startOnboarding(initialIndex);
    }


    function initCmdk() {
        const cmdk = document.getElementById('cmdk');
        const cmdkBackdrop = document.getElementById('cmdk-backdrop');
        const cmdkInput = document.getElementById('cmdk-input');
        const cmdkList = document.getElementById('cmdk-list');
        if (!cmdk || !cmdkBackdrop || !cmdkList) return;

        const cfg = window.SYNEX_CONFIG || {};
        const urls = cfg.urls || {};
        const selectors = cfg.selectors || {};

        const commands = [
            { section: 'Criar', label: 'Nova tarefa', href: urls.kanbanNewTask },
            { section: 'Criar', label: 'Nova meta', href: urls.metas },
            { section: 'Criar', label: 'Nova materia', href: urls.materias },
            { section: 'Criar', label: 'Nova anotacao', href: urls.anotacaoCreate },
            { section: 'Navegacao', label: 'Dashboard', href: urls.dashboard },
            { section: 'Navegacao', label: 'Cronograma', href: urls.cronograma },
            { section: 'Navegacao', label: 'Kanban', href: urls.kanban },
            { section: 'Navegacao', label: 'Metas', href: urls.metas },
            { section: 'Navegacao', label: 'Materias', href: urls.materias },
            { section: 'Navegacao', label: 'Cadernos', href: urls.anotacoes },
            { section: 'Navegacao', label: 'Modo foco', href: urls.foco },
            { section: 'Conta', label: 'Perfil', href: urls.perfil },
            { section: 'Conta', label: 'Configuracoes', href: urls.configuracoes },
            { section: 'Acoes', label: 'Alternar tema', action: 'toggle-theme' },
            { section: 'Acoes', label: 'Sair', action: 'logout' }
        ].filter(function (cmd) { return !!(cmd.href || cmd.action); });

        function clearList() {
            while (cmdkList.firstChild) {
                cmdkList.removeChild(cmdkList.firstChild);
            }
        }

        function renderList(filter) {
            clearList();
            const text = (filter || '').toLowerCase();
            const filtered = commands.filter(function (cmd) {
                return cmd.label.toLowerCase().indexOf(text) !== -1;
            });
            let currentSection = null;
            filtered.forEach(function (cmd) {
                if (cmd.section !== currentSection) {
                    currentSection = cmd.section;
                    const header = document.createElement('div');
                    header.className = 'px-3 py-2 text-xs uppercase tracking-wider text-slate-400';
                    header.textContent = currentSection;
                    cmdkList.appendChild(header);
                }
                const item = document.createElement(cmd.href ? 'a' : 'button');
                item.className = 'w-full text-left px-3 py-2 rounded-lg hover:bg-slate-800 text-sm text-slate-100 flex items-center justify-between';
                item.textContent = cmd.label;
                if (cmd.href) {
                    item.href = cmd.href;
                } else {
                    item.type = 'button';
                    item.dataset.action = cmd.action;
                }
                cmdkList.appendChild(item);
            });
        }

        function openCmdk() {
            cmdk.classList.remove('hidden');
            cmdk.classList.add('flex');
            cmdkBackdrop.classList.remove('hidden');
            if (cmdkInput) {
                cmdkInput.value = '';
                cmdkInput.focus();
            }
            renderList('');
        }

        function closeCmdk() {
            cmdk.classList.add('hidden');
            cmdk.classList.remove('flex');
            cmdkBackdrop.classList.add('hidden');
        }

        document.addEventListener('keydown', function (event) {
            if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
                event.preventDefault();
                openCmdk();
            }
            if (event.key === 'Escape') {
                closeCmdk();
            }
        });

        if (cmdkBackdrop) {
            cmdkBackdrop.addEventListener('click', closeCmdk);
        }

        if (cmdkInput) {
            cmdkInput.addEventListener('input', function (event) {
                renderList(event.target.value || '');
            });
            cmdkInput.addEventListener('keydown', function (event) {
                if (event.key === 'Enter') {
                    const first = cmdkList.querySelector('a,button');
                    if (first) first.click();
                }
            });
        }

        cmdkList.addEventListener('click', function (event) {
            const target = event.target;
            if (!target || !target.dataset) return;
            if (target.dataset.action === 'toggle-theme') {
                const btn = document.querySelector('[data-theme-toggle]');
                if (btn) btn.click();
                closeCmdk();
            }
            if (target.dataset.action === 'logout') {
                const form = document.querySelector(selectors.logoutForm || '#logout-form');
                if (form) form.submit();
            }
        });
    }

    function initFocusClock() {
        const clock = document.getElementById('focus-clock');
        const timeEl = document.getElementById('focus-clock-time');
        const toggleBtn = document.getElementById('focus-clock-toggle');
        const resetBtn = document.getElementById('focus-clock-reset');
        if (!clock || !timeEl || !toggleBtn || !resetBtn) return;

        const KEY_RUNNING = 'synex_focus_running';
        const KEY_START = 'synex_focus_start';
        const KEY_ELAPSED = 'synex_focus_elapsed';
        const KEY_POS = 'synex_focus_pos';
        let intervalId = null;
        let dragging = false;
        let startX = 0;
        let startY = 0;
        let originLeft = 0;
        let originTop = 0;

        function formatTime(totalSeconds) {
            const hours = Math.floor(totalSeconds / 3600);
            const minutes = Math.floor((totalSeconds % 3600) / 60);
            const seconds = Math.floor(totalSeconds % 60);
            const mm = String(minutes).padStart(2, '0');
            const ss = String(seconds).padStart(2, '0');
            if (hours > 0) {
                return String(hours).padStart(2, '0') + ':' + mm + ':' + ss;
            }
            return mm + ':' + ss;
        }

        function getElapsedSeconds() {
            const elapsed = parseInt(localStorage.getItem(KEY_ELAPSED) || '0', 10);
            const running = localStorage.getItem(KEY_RUNNING) === '1';
            const start = parseInt(localStorage.getItem(KEY_START) || '0', 10);
            if (!running || !start) return elapsed;
            const delta = Math.floor((Date.now() - start) / 1000);
            return elapsed + Math.max(0, delta);
        }

        function updateDisplay() {
            timeEl.textContent = formatTime(getElapsedSeconds());
        }

        function setRunning(running) {
            localStorage.setItem(KEY_RUNNING, running ? '1' : '0');
            toggleBtn.textContent = running ? 'Pause' : 'Start';
            toggleBtn.classList.toggle('bg-slate-800', running);
            if (intervalId) {
                clearInterval(intervalId);
                intervalId = null;
            }
            if (running) {
                intervalId = setInterval(updateDisplay, 1000);
            }
            updateDisplay();
        }

        function start() {
            if (localStorage.getItem(KEY_RUNNING) === '1') return;
            localStorage.setItem(KEY_START, String(Date.now()));
            setRunning(true);
        }

        function pause() {
            if (localStorage.getItem(KEY_RUNNING) !== '1') return;
            const total = getElapsedSeconds();
            localStorage.setItem(KEY_ELAPSED, String(total));
            localStorage.removeItem(KEY_START);
            setRunning(false);
        }

        function reset() {
            localStorage.setItem(KEY_ELAPSED, '0');
            localStorage.removeItem(KEY_START);
            setRunning(false);
        }

        function applySavedPosition() {
            try {
                const raw = localStorage.getItem(KEY_POS);
                if (!raw) return;
                const data = JSON.parse(raw);
                if (typeof data.left === 'number' && typeof data.top === 'number') {
                    clock.style.left = data.left + 'px';
                    clock.style.top = data.top + 'px';
                    clock.style.right = 'auto';
                    clock.style.bottom = 'auto';
                }
            } catch (e) {
                // ignore invalid data
            }
        }

        function clamp(value, min, max) {
            return Math.min(Math.max(value, min), max);
        }

        function onDragStart(event) {
            if (event.target === toggleBtn || event.target === resetBtn || event.target.closest('button')) {
                return;
            }
            dragging = true;
            const rect = clock.getBoundingClientRect();
            startX = (event.touches ? event.touches[0].clientX : event.clientX);
            startY = (event.touches ? event.touches[0].clientY : event.clientY);
            originLeft = rect.left;
            originTop = rect.top;
            clock.style.right = 'auto';
            clock.style.bottom = 'auto';
            clock.classList.add('cursor-grabbing');
            event.preventDefault();
        }

        function onDragMove(event) {
            if (!dragging) return;
            const currentX = (event.touches ? event.touches[0].clientX : event.clientX);
            const currentY = (event.touches ? event.touches[0].clientY : event.clientY);
            const dx = currentX - startX;
            const dy = currentY - startY;
            const newLeft = originLeft + dx;
            const newTop = originTop + dy;
            const maxLeft = window.innerWidth - clock.offsetWidth - 8;
            const maxTop = window.innerHeight - clock.offsetHeight - 8;
            const clampedLeft = clamp(newLeft, 8, maxLeft);
            const clampedTop = clamp(newTop, 8, maxTop);
            clock.style.left = clampedLeft + 'px';
            clock.style.top = clampedTop + 'px';
        }

        function onDragEnd() {
            if (!dragging) return;
            dragging = false;
            clock.classList.remove('cursor-grabbing');
            const rect = clock.getBoundingClientRect();
            localStorage.setItem(KEY_POS, JSON.stringify({ left: rect.left, top: rect.top }));
        }

        toggleBtn.addEventListener('click', function () {
            if (localStorage.getItem(KEY_RUNNING) === '1') {
                pause();
            } else {
                start();
            }
        });

        resetBtn.addEventListener('click', function () {
            reset();
        });

        setRunning(localStorage.getItem(KEY_RUNNING) === '1');
        applySavedPosition();

        clock.classList.add('cursor-grab');
        clock.addEventListener('mousedown', onDragStart);
        clock.addEventListener('touchstart', onDragStart, { passive: false });
        document.addEventListener('mousemove', onDragMove);
        document.addEventListener('touchmove', onDragMove, { passive: false });
        document.addEventListener('mouseup', onDragEnd);
        document.addEventListener('touchend', onDragEnd);
    }

    function initFeedbackModal() {
        const openBtn = document.getElementById('feedback-open');
        const modal = document.getElementById('feedback-modal');
        const backdrop = document.getElementById('feedback-backdrop');
        const closeBtn = document.getElementById('feedback-close');
        const cancelBtn = document.getElementById('feedback-cancel');
        const form = document.getElementById('feedback-form');
        const starsWrap = document.getElementById('feedback-stars');
        const ratingInput = document.getElementById('feedback-rating');
        const comment = document.getElementById('feedback-comment');
        const count = document.getElementById('feedback-count');
        const submitBtn = document.getElementById('feedback-submit');

        if (!openBtn || !modal || !backdrop || !form || !starsWrap) return;

        function open() {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            backdrop.classList.remove('hidden');
        }

        function close() {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            backdrop.classList.add('hidden');
        }

        function updateStars(value) {
            const stars = starsWrap.querySelectorAll('.feedback-star');
            stars.forEach(function (btn) {
                const v = parseInt(btn.dataset.value || '0', 10);
                btn.classList.toggle('text-amber-400', v <= value);
                btn.classList.toggle('text-slate-600', v > value);
            });
            ratingInput.value = value ? String(value) : '';
            submitBtn.disabled = !value;
        }

        function updateCount() {
            if (!comment || !count) return;
            count.textContent = String(comment.value.length);
        }

        openBtn.addEventListener('click', open);
        if (closeBtn) closeBtn.addEventListener('click', close);
        if (cancelBtn) cancelBtn.addEventListener('click', close);
        backdrop.addEventListener('click', close);
        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape') close();
        });

        starsWrap.addEventListener('click', function (event) {
            const target = event.target.closest('.feedback-star');
            if (!target) return;
            const value = parseInt(target.dataset.value || '0', 10);
            updateStars(value);
        });

        if (comment) comment.addEventListener('input', updateCount);

        form.addEventListener('submit', function (event) {
            event.preventDefault();
            var feedbackUrl = urls.feedback;
            if (!feedbackUrl) {
                showGlobalToast('Endpoint de feedback nao configurado.', true);
                return;
            }
            var payload = {
                rating: ratingInput.value,
                comment: comment ? comment.value.trim() : '',
                page: window.location.pathname
            };
            var originalText = submitBtn ? submitBtn.textContent : '';
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Enviando...';
            }
            fetch(feedbackUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(payload)
            })
                .then(function (res) {
                    if (!res.ok) {
                        return res.json().then(function (data) {
                            throw new Error((data && data.error) || 'Erro ao enviar feedback.');
                        });
                    }
                    return res.json();
                })
                .then(function () {
                    close();
                    if (comment) comment.value = '';
                    updateStars(0);
                    updateCount();
                    showGlobalToast('Feedback enviado. Obrigado!', false);
                })
                .catch(function (err) {
                    showGlobalToast(err.message || 'Erro ao enviar feedback.', true);
                })
                .finally(function () {
                    if (submitBtn) {
                        submitBtn.disabled = !ratingInput.value;
                        submitBtn.textContent = originalText || 'Enviar';
                    }
                });
        });

        updateStars(0);
        updateCount();
    }

    onReady(function () {
        initThemeToggle();
        initOnboarding();
        initSidebarToggle();
        initProfileMenu();
        initCmdk();
        initFocusClock();
        initFeedbackModal();
    });
})();
