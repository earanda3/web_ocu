/* ================================================================
 * Info Viewer  –  js/ui/info-viewer.js
 * Interactive information window for the ocu universe.
 * Exposes: openInfoViewer(anchorEl?), closeInfoViewer()
 * ================================================================ */

(function () {
    'use strict';

    // ── Load extra fonts (Google Fonts, async) ───────────────────
    if (!document.getElementById('info-viewer-fonts')) {
        const link = document.createElement('link');
        link.id   = 'info-viewer-fonts';
        link.rel  = 'stylesheet';
        link.href = 'https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500&family=Playfair+Display:ital@0;1&family=Courier+Prime&display=swap';
        document.head.appendChild(link);
    }

    // ── Translations ─────────────────────────────────────────────
    const TRANSLATIONS = {
        ca: `Aquest és l'univers ocu, una plataforma d'art digital
On cada paraula és un món.

Per descobrir-los has de clicar les paraules
Així, trobaràs el que hi ha a l'interior.

Pots interactuar amb els elements que apareixen
Clica els objectes 3D per canviar-los el color
Manipula les Imatges
Descarrega documents
Afegeix paraules
Afegeix arxius
Investiga-ho!

Pots crear una serp amb la lletra "N" per navegar i descobrir l'univers.
Es mou amb les fletxetes.
Pots interactuar amb les paraules xocant-hi
I menjar els elements que hi neixen
per anar més de pressa i créixer.

Pots crear una altra serp amb la lletra "M"
Que es mou amb les lletres W-A-S-D
I jugar amb algú altre al laberint o a veure qui va més de pressa.

Pots jugar al pong amb la lletra "P"
I interactuar amb les paraules
I xocar amb els elements per accelerar la pilota.

Espero que ho gaudeixis
gràcies per la visita <3`,
        es: `Este es el universo ocu, una plataforma de arte digital
Donde cada palabra es un mundo.

Para descubrirlos tienes que hacer clic en las palabras
Así, encontrarás lo que hay en el interior.

Puedes interactuar con los elementos que aparecen
Haz clic en los objetos 3D para cambiarles el color
Manipula las imágenes
Descarga documentos
Añade palabras
Añade archivos
¡Investígalo!

Puedes crear una serpiente con la letra "N" para navegar y descubrir el universo.
Se mueve con las flechas.
Puedes interactuar con las palabras chocando con ellas
Y comer los elementos que nacen
para ir más rápido y crecer.

Puedes crear otra serpiente con la letra "M"
Que se mueve con las letras W-A-S-D
Y jugar con alguien más en el laberinto o ver quién va más rápido.

Puedes jugar al pong con la letra "P"
E interactuar con las palabras
Y chocar con los elementos para acelerar la pelota.

Espero que lo disfrutes
gracias por la visita <3`,
        en: `This is the ocu universe, a digital art platform
Where each word is a world.

To discover them you have to click on the words
That way, you'll find what's inside.

You can interact with the elements that appear
Click on 3D objects to change their color
Manipulate images
Download documents
Add words
Add files
Explore it!

You can create a snake with the letter "N" to navigate and discover the universe.
It moves with the arrow keys.
You can interact with words by colliding with them
And eat the elements that are born
to go faster and grow.

You can create another snake with the letter "M"
That moves with the W-A-S-D keys
And play with someone else in the maze or see who goes faster.

You can play pong with the letter "P"
And interact with the words
And collide with elements to accelerate the ball.

I hope you enjoy it
thank you for your visit <3`,
        fr: `Ceci est l'univers ocu, une plateforme d'art numérique
Où chaque mot est un monde.

Pour les découvrir vous devez cliquer sur les mots
Ainsi, vous trouverez ce qu'il y a à l'intérieur.

Vous pouvez interagir avec les éléments qui apparaissent
Cliquez sur les objets 3D pour en changer la couleur
Manipulez les images
Téléchargez des documents
Ajoutez des mots
Ajoutez des fichiers
Explorez !

Vous pouvez créer un serpent avec la lettre "N" pour naviguer et découvrir l'univers.
Il se déplace avec les flèches.
Vous pouvez interagir avec les mots en les percutant
Et manger les éléments qui naissent
pour aller plus vite et grandir.

Vous pouvez créer un autre serpent avec la lettre "M"
Qui se déplace avec les touches W-A-S-D
Et jouer avec quelqu'un d'autre dans le labyrinthe ou voir qui va le plus vite.

Vous pouvez jouer au pong avec la lettre "P"
Et interagir avec les mots
Et percuter les éléments pour accélérer la balle.

J'espère que vous l'apprécierez
merci pour votre visite <3`,
        de: `Dies ist das ocu-Universum, eine digitale Kunstplattform
Wo jedes Wort eine Welt ist.

Um sie zu entdecken, musst du auf die Wörter klicken
So findest du heraus, was sich darin verbirgt.

Du kannst mit den Elementen interagieren, die erscheinen
Klicke auf 3D-Objekte, um ihre Farbe zu ändern
Bilder manipulieren
Dokumente herunterladen
Wörter hinzufügen
Dateien hinzufügen
Erkunde es!

Du kannst eine Schlange mit der Taste "N" erstellen, um das Universum zu navigieren.
Sie bewegt sich mit den Pfeiltasten.
Du kannst mit Wörtern interagieren, indem du mit ihnen kollidierst
Und die entstehenden Elemente fressen
um schneller zu werden und zu wachsen.

Du kannst eine weitere Schlange mit der Taste "M" erstellen
Die sich mit den Tasten W-A-S-D bewegt
Und mit jemand anderem im Labyrinth spielen.

Du kannst mit der Taste "P" Pong spielen
Und mit den Wörtern interagieren
Und mit Elementen kollidieren, um den Ball zu beschleunigen.

Ich hoffe, du genießt es
Danke für deinen Besuch <3`,
        ja: `ここはocuの宇宙、デジタルアートのプラットフォームです
すべての言葉がひとつの世界。

発見するには、言葉をクリックしてください
そうすれば、中にあるものが見えてきます。

現れる要素と交流できます
3Dオブジェクトをクリックして色を変えましょう
画像を操作する
ドキュメントをダウンロード
言葉を追加
ファイルを追加
探索してみよう！

「N」キーで蛇を作り、宇宙を旅することができます。
矢印キーで動きます。
言葉と衝突して交流できます
生まれた要素を食べて
もっと速く動いて成長できます。

「M」キーでもう一匹の蛇を作れます
W-A-S-Dキーで動きます
迷路で誰が速いか競いましょう。

「P」キーでポンを遊べます
言葉と交流して
要素に衝突してボールを加速させましょう。

楽しんでもらえたら嬉しいです
ご訪問ありがとうございます <3`,
        zh: `这是ocu宇宙，一个数字艺术平台
每一个词都是一个世界。

要发现它们，你需要点击这些词
这样，你会找到里面的内容。

你可以与出现的元素互动
点击3D物体来改变颜色
操控图像
下载文档
添加词语
添加文件
探索吧！

你可以用「N」键创建一条蛇来探索宇宙。
用方向键移动。
你可以与词语碰撞来互动
吃掉诞生的元素
来加速移动和成长。

你可以用「M」键创建另一条蛇
用W-A-S-D键移动
和别人在迷宫里比赛。

你可以用「P」键玩乒乓
与词语互动
碰撞元素来加速球。

希望你喜欢
感谢你的到来 <3`,
        ko: `이것은 ocu 우주, 디지털 아트 플랫폼입니다
모든 단어가 하나의 세계입니다.

발견하려면 단어를 클릭하세요
그렇게 하면 안에 무엇이 있는지 알 수 있습니다.

나타나는 요소들과 상호작용할 수 있습니다
3D 오브젝트를 클릭하여 색상을 바꿔보세요
이미지를 조작하세요
문서를 다운로드하세요
단어 추가하기
파일 추가하기
탐험해보세요！

「N」키로 뱀을 만들어 우주를 탐험할 수 있습니다.
화살표 키로 이동합니다.
단어와 충돌하여 상호작용할 수 있습니다
생겨나는 요소를 먹어서
더 빠르게 이동하고 성장할 수 있습니다.

「M」키로 또 다른 뱀을 만들 수 있습니다
W-A-S-D 키로 이동합니다
미로에서 누가 더 빠른지 경쟁해보세요.

「P」키로 퐁을 플레이할 수 있습니다
단어와 상호작용하세요
요소와 충돌하여 공을 가속시키세요.

즐거운 시간 되시길 바랍니다
방문해주셔서 감사합니다 <3`,
    };

    // ── CSS ──────────────────────────────────────────────────────
    const CSS = `
#info-modal {
    position: absolute;
    z-index: 620;
    width: 520px;
    height: 580px;
    min-width: 320px;
    min-height: 280px;
    background: var(--info-bg, #ffffff);
    color: var(--info-el, #222222);
    border: 1px solid rgba(128,128,128,0.18);
    box-shadow: 0 12px 48px rgba(0,0,0,0.13), 0 2px 8px rgba(0,0,0,0.05);
    border-radius: 14px;
    overflow: hidden;
    display: none;
    flex-direction: column;
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    resize: both;
    transition: background 0.3s, color 0.3s;
}
#info-modal.show { display: flex; }

.info-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 11px 16px;
    background: rgba(128,128,128,0.06);
    border-bottom: 1px solid rgba(128,128,128,0.1);
    cursor: move;
    user-select: none;
    touch-action: none;
    flex-shrink: 0;
}
.info-header-title {
    font-size: 10px;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: var(--info-el, #222);
    opacity: 0.4;
    font-weight: 400;
}
.info-header-close {
    width: 22px;
    height: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    border: none;
    background: rgba(128,128,128,0.12);
    color: var(--info-el, #222);
    font-size: 15px;
    cursor: pointer;
    line-height: 1;
    padding: 0;
    transition: background 0.15s;
    flex-shrink: 0;
}
.info-header-close:hover { background: rgba(128,128,128,0.22); }

.info-body {
    flex: 1;
    overflow-y: auto;
    padding: 28px 32px 20px 32px;
    scrollbar-width: thin;
    scrollbar-color: rgba(128,128,128,0.25) transparent;
}
.info-body::-webkit-scrollbar { width: 5px; }
.info-body::-webkit-scrollbar-track { background: transparent; }
.info-body::-webkit-scrollbar-thumb { background: rgba(128,128,128,0.2); border-radius: 3px; }

.info-text {
    outline: none;
    line-height: 1.75;
    color: var(--info-el, #222);
    min-height: 140px;
    white-space: pre-wrap;
    word-break: break-word;
    cursor: text;
    border-radius: 4px;
    transition: background 0.15s;
}
.info-text:focus { background: rgba(128,128,128,0.04); }
.info-text:empty:before {
    content: attr(data-placeholder);
    color: var(--info-el, #ccc);
    opacity: 0.3;
    pointer-events: none;
}

/* ── Vida: letters ── */
.info-text.vida-on {
    white-space: normal;
    cursor: default;
    word-break: break-word;
}
#info-modal .letter {
    display: inline-block;
    transition: transform 0.05s ease;
    transform-origin: center bottom;
}

.info-toolbar {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 16px;
    background: rgba(128,128,128,0.06);
    border-top: 1px solid rgba(128,128,128,0.1);
    flex-shrink: 0;
    flex-wrap: wrap;
}

.info-toolbar select {
    appearance: none;
    -webkit-appearance: none;
    border: 1px solid rgba(128,128,128,0.22);
    border-radius: 7px;
    padding: 4px 26px 4px 10px;
    font-size: 11.5px;
    color: var(--info-el, #555);
    background: var(--info-bg, #fff) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='8' height='5'%3E%3Cpath d='M0 0l4 5 4-5z' fill='%23999'/%3E%3C/svg%3E") no-repeat right 9px center;
    cursor: pointer;
    height: 28px;
    min-width: 120px;
    transition: border-color 0.15s;
}
.info-toolbar select:focus { outline: none; border-color: rgba(128,128,128,0.4); }

.info-size-wrap {
    display: flex;
    align-items: center;
    gap: 7px;
}
.info-size-wrap label {
    font-size: 10.5px;
    color: var(--info-el, #aaa);
    opacity: 0.5;
    letter-spacing: 0.5px;
    white-space: nowrap;
}
.info-size-wrap input[type=range] {
    -webkit-appearance: none;
    width: 76px;
    height: 2px;
    background: rgba(128,128,128,0.22);
    border-radius: 2px;
    outline: none;
    cursor: pointer;
}
.info-size-wrap input[type=range]::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 13px;
    height: 13px;
    background: var(--info-el, #444);
    border-radius: 50%;
    cursor: pointer;
    transition: opacity 0.15s;
}
.info-size-wrap input[type=range]::-webkit-slider-thumb:hover { opacity: 0.7; }
.info-size-val {
    font-size: 10.5px;
    color: var(--info-el, #888);
    opacity: 0.55;
    min-width: 28px;
    font-variant-numeric: tabular-nums;
}

.info-slot-wrap {
    display: flex;
    align-items: center;
    gap: 7px;
    margin-left: auto;
}
.info-slot-label {
    font-size: 10.5px;
    color: var(--info-el, #aaa);
    opacity: 0.5;
    user-select: none;
    cursor: pointer;
    letter-spacing: 0.5px;
}

/* iOS-style toggle */
.info-toggle {
    position: relative;
    width: 38px;
    height: 21px;
    cursor: pointer;
    flex-shrink: 0;
}
.info-toggle input {
    opacity: 0;
    width: 0;
    height: 0;
    position: absolute;
}
.info-toggle-track {
    position: absolute;
    inset: 0;
    background: rgba(128,128,128,0.28);
    border-radius: 10.5px;
    transition: background 0.2s;
}
.info-toggle input:checked + .info-toggle-track {
    background: var(--info-el, #3a3a3a);
    opacity: 0.8;
}
.info-toggle-thumb {
    position: absolute;
    top: 2.5px;
    left: 2.5px;
    width: 16px;
    height: 16px;
    background: var(--info-bg, #fff);
    border-radius: 50%;
    box-shadow: 0 1px 4px rgba(0,0,0,0.22);
    transition: transform 0.2s;
    pointer-events: none;
}
.info-toggle input:checked ~ .info-toggle-thumb { transform: translateX(17px); }

.info-reset {
    font-size: 10.5px;
    color: var(--info-el, #aaa);
    opacity: 0.3;
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
    text-decoration: underline;
    text-underline-offset: 2px;
    transition: opacity 0.15s;
    white-space: nowrap;
}
.info-reset:hover { opacity: 0.6; }
`;

    // Inject CSS once
    if (!document.getElementById('info-viewer-style')) {
        const style = document.createElement('style');
        style.id = 'info-viewer-style';
        style.textContent = CSS;
        document.head.appendChild(style);
    }

    // ── State ─────────────────────────────────────────────────────
    let _currentLang  = 'ca';
    let _currentText  = TRANSLATIONS.ca;
    let _vidaActive   = false;
    let _vidaInterval = null;

    // ── Color adaptation ─────────────────────────────────────────
    function _applyColors(bg, el) {
        document.documentElement.style.setProperty('--info-bg', bg || '#ffffff');
        document.documentElement.style.setProperty('--info-el', el || '#222222');
    }

    function _readSiteColors() {
        const bg = document.body.style.backgroundColor || '#ffffff';
        const elEl = document.querySelector('#canvas a');
        const el = elEl ? (elEl.style.color || '#222222') : '#222222';
        return { bg: bg || '#ffffff', el };
    }

    // ── Vida helpers (mirrors createWordSlotMachine from interactions.js) ───
    function _enableVida() {
        if (!textEl) return;
        _currentText = _getPlainText();

        // Build span tree
        const fontsArr = window.fonts || ['font-minecraft', 'font-oregular', 'font-helvetica', 'font-courier'];
        textEl.innerHTML = '';
        textEl.contentEditable = 'false';
        textEl.classList.add('vida-on');

        const frag = document.createDocumentFragment();
        Array.from(_currentText).forEach(ch => {
            if (ch === '\n') {
                frag.appendChild(document.createElement('br'));
                return;
            }
            const span = document.createElement('span');
            span.className = 'letter';
            span.textContent = (ch === ' ') ? '\u00A0' : ch;
            span.classList.add(fontsArr[Math.floor(Math.random() * fontsArr.length)]);
            frag.appendChild(span);
        });
        textEl.appendChild(frag);
        _vidaActive = true;

        // Single master interval — updates ~7% of letters per tick (like the canvas words)
        _vidaInterval = setInterval(() => {
            const spans = textEl.querySelectorAll('span.letter');
            if (!spans.length) return;
            const f = window.fonts || ['font-minecraft', 'font-oregular', 'font-helvetica', 'font-courier'];
            const count = Math.max(1, Math.ceil(spans.length * 0.07));
            for (let k = 0; k < count; k++) {
                const span = spans[Math.floor(Math.random() * spans.length)];
                f.forEach(cls => span.classList.remove(cls));
                span.classList.add(f[Math.floor(Math.random() * f.length)]);
                span.style.transform = 'scaleY(0.8)';
                setTimeout(() => { span.style.transform = 'scaleY(1)'; }, 55);
            }
        }, 180);
    }

    function _disableVida() {
        if (!textEl) return;
        if (_vidaInterval) { clearInterval(_vidaInterval); _vidaInterval = null; }
        textEl.classList.remove('vida-on');
        textEl.contentEditable = 'true';
        textEl.textContent = _currentText;
        _vidaActive = false;
    }

    function _getPlainText() {
        if (!textEl) return '';
        if (_vidaActive) return _currentText;
        return textEl.textContent;
    }

    function _setLang(lang) {
        _currentLang = lang;
        const text = TRANSLATIONS[lang] || TRANSLATIONS.ca;
        _currentText = text;
        if (_vidaActive) {
            // Rebuild with new text
            if (_vidaInterval) { clearInterval(_vidaInterval); _vidaInterval = null; }
            _vidaActive = false;
            _enableVida();
        } else {
            textEl.textContent = text;
        }
    }

    // ── Font catalogue ───────────────────────────────────────────
    const FONTS = [
        { label: 'Helvetica',        value: "'Helvetica Neue', Helvetica, Arial, sans-serif" },
        { label: 'Space Grotesk',    value: "'Space Grotesk', sans-serif" },
        { label: 'Playfair Display', value: "'Playfair Display', Georgia, serif" },
        { label: 'Georgia',          value: "Georgia, 'Times New Roman', serif" },
        { label: 'Courier Prime',    value: "'Courier Prime', 'Courier New', monospace" },
        { label: 'O-Regular',        value: "'O-Regular', Helvetica, sans-serif" },
    ];

    // ── DOM refs (set after buildModal) ──────────────────────────
    let modal      = null;
    let textEl     = null;
    let sizeRange  = null;
    let sizeVal    = null;
    let fontSelect = null;
    let slotToggle = null;
    let langSelect = null;

    // ── Build modal (idempotent) ─────────────────────────────────
    function buildModal() {
        if (document.getElementById('info-modal')) {
            modal      = document.getElementById('info-modal');
            textEl     = modal.querySelector('.info-text');
            sizeRange  = modal.querySelector('input[type=range]');
            sizeVal    = modal.querySelector('.info-size-val');
            fontSelect = modal.querySelector('.info-font-select');
            langSelect = modal.querySelector('.info-lang-select');
            slotToggle = modal.querySelector('.info-toggle input');
            return;
        }

        modal = document.createElement('div');
        modal.id = 'info-modal';

        // ── Header ───────────────────────────────────────────────
        const header = document.createElement('div');
        header.className = 'info-header';

        const titleSpan = document.createElement('span');
        titleSpan.className = 'info-header-title';
        titleSpan.textContent = '· ocu · info ·';

        const closeBtn = document.createElement('button');
        closeBtn.className = 'info-header-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.title = 'Tancar';
        closeBtn.onclick = closeInfoViewer;

        header.appendChild(titleSpan);
        header.appendChild(closeBtn);

        // ── Body (editable text) ─────────────────────────────────
        const body = document.createElement('div');
        body.className = 'info-body';

        textEl = document.createElement('div');
        textEl.className = 'info-text';
        textEl.contentEditable = 'true';
        textEl.setAttribute('data-placeholder', 'Escriu aquí…');
        textEl.spellcheck = false;
        textEl.textContent = TRANSLATIONS.ca;
        textEl.style.fontSize = '17px';

        // Sync _currentText on edit
        textEl.addEventListener('input', () => {
            if (!_vidaActive) _currentText = textEl.textContent;
        });
        // Prevent drag events from bubbling to canvas pan
        textEl.addEventListener('mousedown', e => e.stopPropagation());
        textEl.addEventListener('touchstart', e => e.stopPropagation(), { passive: true });

        body.appendChild(textEl);

        // ── Toolbar ──────────────────────────────────────────────
        const toolbar = document.createElement('div');
        toolbar.className = 'info-toolbar';

        // Font selector
        fontSelect = document.createElement('select');
        fontSelect.className = 'info-font-select';
        fontSelect.title = 'Tipografia';
        FONTS.forEach(f => {
            const opt = document.createElement('option');
            opt.value = f.value;
            opt.textContent = f.label;
            fontSelect.appendChild(opt);
        });
        fontSelect.oninput = () => { textEl.style.fontFamily = fontSelect.value; };

        // Size wrap
        const sizeWrap = document.createElement('div');
        sizeWrap.className = 'info-size-wrap';

        const sizeLbl = document.createElement('label');
        sizeLbl.textContent = 'Mida';

        sizeRange = document.createElement('input');
        sizeRange.type  = 'range';
        sizeRange.min   = '10';
        sizeRange.max   = '48';
        sizeRange.value = '17';
        sizeRange.oninput = () => {
            textEl.style.fontSize = sizeRange.value + 'px';
            sizeVal.textContent   = sizeRange.value + 'px';
        };

        sizeVal = document.createElement('span');
        sizeVal.className   = 'info-size-val';
        sizeVal.textContent = '17px';

        sizeWrap.appendChild(sizeLbl);
        sizeWrap.appendChild(sizeRange);
        sizeWrap.appendChild(sizeVal);

        // Language selector
        langSelect = document.createElement('select');
        langSelect.className = 'info-lang-select';
        langSelect.title = 'Idioma';
        [['ca','Català'], ['es','Castellano'], ['en','English'], ['fr','Français'], ['de','Deutsch'], ['ja','日本語'], ['zh','中文'], ['ko','한국어']]
            .forEach(([code, label]) => {
                const opt = document.createElement('option');
                opt.value = code; opt.textContent = label;
                langSelect.appendChild(opt);
            });
        langSelect.onchange = () => _setLang(langSelect.value);

        // Vida toggle (slot machine inside the window)
        const slotWrap = document.createElement('div');
        slotWrap.className = 'info-slot-wrap';

        const slotLbl = document.createElement('span');
        slotLbl.className   = 'info-slot-label';
        slotLbl.textContent = 'vida';

        const toggleLabel = document.createElement('label');
        toggleLabel.className = 'info-toggle';
        toggleLabel.title     = 'Activar/desactivar vida';

        slotToggle = document.createElement('input');
        slotToggle.type    = 'checkbox';
        slotToggle.checked = false;
        slotToggle.onchange = () => {
            if (slotToggle.checked) { _enableVida(); }
            else                    { _disableVida(); }
        };

        const toggleTrack = document.createElement('span');
        toggleTrack.className = 'info-toggle-track';
        const toggleThumb = document.createElement('span');
        toggleThumb.className = 'info-toggle-thumb';

        toggleLabel.appendChild(slotToggle);
        toggleLabel.appendChild(toggleTrack);
        toggleLabel.appendChild(toggleThumb);

        slotWrap.appendChild(slotLbl);
        slotWrap.appendChild(toggleLabel);

        // Reset button
        const resetBtn = document.createElement('button');
        resetBtn.className   = 'info-reset';
        resetBtn.textContent = 'reset';
        resetBtn.title       = 'Restaurar valors per defecte';
        resetBtn.onclick = () => {
            // Turn off vida first
            if (_vidaActive) { slotToggle.checked = false; _disableVida(); }
            // Reset lang
            _currentLang = 'ca';
            langSelect.value = 'ca';
            _currentText = TRANSLATIONS.ca;
            textEl.textContent      = TRANSLATIONS.ca;
            sizeRange.value         = '17';
            sizeVal.textContent     = '17px';
            textEl.style.fontSize   = '17px';
            fontSelect.selectedIndex = 0;
            textEl.style.fontFamily = FONTS[0].value;
        };

        toolbar.appendChild(fontSelect);
        toolbar.appendChild(sizeWrap);
        toolbar.appendChild(langSelect);
        toolbar.appendChild(slotWrap);
        toolbar.appendChild(resetBtn);

        modal.appendChild(header);
        modal.appendChild(body);
        modal.appendChild(toolbar);
        document.body.appendChild(modal);

        setupDrag(modal, header);

        // Keyboard close
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape' && modal.classList.contains('show')) {
                closeInfoViewer();
            }
        });
    }

    // ── Drag ─────────────────────────────────────────────────────
    function setupDrag(el, handle) {
        let dragging = false;
        let ox = 0, oy = 0;

        const onStart = (cx, cy) => {
            dragging = true;
            const r = el.getBoundingClientRect();
            ox = cx - r.left;
            oy = cy - r.top;
        };
        const onMove = (cx, cy) => {
            if (!dragging) return;
            const maxX = window.innerWidth  - el.offsetWidth;
            const maxY = window.innerHeight - el.offsetHeight;
            el.style.left = Math.max(0, Math.min(cx - ox, maxX)) + 'px';
            el.style.top  = Math.max(0, Math.min(cy - oy, maxY)) + 'px';
        };
        const onEnd = () => { dragging = false; };

        handle.addEventListener('mousedown', e => {
            if (e.target.closest('.info-header-close')) return;
            onStart(e.clientX, e.clientY);
            e.preventDefault();
        });
        document.addEventListener('mousemove', e => onMove(e.clientX, e.clientY));
        document.addEventListener('mouseup', onEnd);

        handle.addEventListener('touchstart', e => {
            if (e.target.closest('.info-header-close')) return;
            onStart(e.touches[0].clientX, e.touches[0].clientY);
        }, { passive: true });
        document.addEventListener('touchmove', e => {
            if (!dragging) return;
            onMove(e.touches[0].clientX, e.touches[0].clientY);
            e.preventDefault();
        }, { passive: false });
        document.addEventListener('touchend', onEnd);
    }

    // ── Public API ───────────────────────────────────────────────
    function openInfoViewer(anchorEl) {
        buildModal();

        // Sync colors from current site palette
        const { bg, el } = _readSiteColors();
        _applyColors(bg, el);

        // Position near anchor, or centered
        if (anchorEl && anchorEl.getBoundingClientRect) {
            const r = anchorEl.getBoundingClientRect();
            modal.style.left = Math.max(0, Math.min(r.left + 40, window.innerWidth  - 540)) + 'px';
            modal.style.top  = Math.max(0, Math.min(r.top  + 20, window.innerHeight - 600)) + 'px';
        } else {
            modal.style.left = Math.max(0, Math.round((window.innerWidth  - 520) / 2)) + 'px';
            modal.style.top  = Math.max(0, Math.round((window.innerHeight - 560) / 4)) + 'px';
        }

        modal.classList.add('show');
    }

    function closeInfoViewer() {
        if (modal) {
            modal.classList.remove('show');
            if (_vidaActive) _disableVida();
        }
    }

    // Called from applyColors() in index.html
    window.infoViewerApplyColors = function(bg, el) {
        _applyColors(bg, el);
    };

    window.openInfoViewer  = openInfoViewer;
    window.closeInfoViewer = closeInfoViewer;

})();
