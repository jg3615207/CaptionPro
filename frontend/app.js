document.addEventListener('DOMContentLoaded', () => {
    
    // Core Elements
    const engineSelect = document.getElementById('engine');
    const modelSelect = document.getElementById('model');
    const langSelect = document.getElementById('language');
    const computeSelect = document.getElementById('computeType');
    const denoiseLevel = document.getElementById('denoiseLevel');
    const denoiseValue = document.getElementById('denoiseValue');
    const highlightWords = document.getElementById('highlightWords');
    
    // Post-Proc Elements
    const convertToTraditional = document.getElementById('convertToTraditional');
    
    // AI Translation Elements
    const autoTranslate = document.getElementById('autoTranslate');
    const aiApiUrl = document.getElementById('aiApiUrl');
    const aiModelName = document.getElementById('aiModelName');
    const aiTargetLang = document.getElementById('aiTargetLang');

    // Sidebar Tab Switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(btn.getAttribute('data-tab')).classList.add('active');
        });
    });

    // Main Area Tab Switching
    const mainTabBtns = document.querySelectorAll('.main-tab-btn');
    const mainTabContents = document.querySelectorAll('.main-tab-content');
    mainTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            mainTabBtns.forEach(b => b.classList.remove('active'));
            mainTabContents.forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            
            const targetTab = btn.getAttribute('data-tab');
            document.getElementById(targetTab).classList.add('active');
            
            // Sync sidebar tabs
            if (targetTab === 'view-transcription') {
                const coreBtn = document.querySelector('.tab-btn[data-tab="core-settings"]');
                if (coreBtn && !coreBtn.classList.contains('active')) coreBtn.click();
            } else if (targetTab === 'view-translation') {
                const aiBtn = document.querySelector('.tab-btn[data-tab="ai-settings"]');
                if (aiBtn && !aiBtn.classList.contains('active')) aiBtn.click();
            }
            
            // Hide results when switching tabs
            document.getElementById('resultsArea').classList.add('hidden');
        });
    });
    
    const loadingState = document.getElementById('loadingState');
    const resultsArea = document.getElementById('resultsArea');
    const srtOutput = document.getElementById('srtOutput');
    const copyBtn = document.getElementById('copyBtn');

    let selectedMediaFile = null;
    let selectedSrtFile = null;

    // Initialize Config
    async function fetchConfig() {
        try {
            const res = await fetch('/api/config');
            const config = await res.json();
            
            config.engines.forEach(e => {
                const opt = document.createElement('option');
                opt.value = e; opt.textContent = e;
                engineSelect.appendChild(opt);
            });

            config.models.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m; opt.textContent = m;
                modelSelect.appendChild(opt);
            });

            const langOpt = document.createElement('option');
            langOpt.value = 'english'; langOpt.textContent = 'English';
            langSelect.appendChild(langOpt);
            config.languages.forEach(l => {
                if(l !== 'english') {
                    const opt = document.createElement('option');
                    opt.value = l; opt.textContent = l;
                    langSelect.appendChild(opt);
                }
            });

            config.compute_types.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c; opt.textContent = c;
                computeSelect.appendChild(opt);
            });
        } catch (err) {
            console.error("Error fetching config:", err);
        }
    }
    fetchConfig();

    denoiseLevel.addEventListener('input', (e) => {
        const vals = ["0 (None)", "1 (HTDemucs)", "2 (HTDemucs FT)"];
        denoiseValue.textContent = vals[e.target.value];
    });

    // Transcription File Handling
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const fileNameDisplay = document.getElementById('fileName');
    const startBtn = document.getElementById('startBtn');

    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) handleMediaFile(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleMediaFile(e.target.files[0]);
    });

    function handleMediaFile(file) {
        selectedMediaFile = file;
        fileNameDisplay.textContent = file.name;
        startBtn.disabled = false;
        resultsArea.classList.add('hidden');
        srtOutput.value = '';
    }

    // SRT Translation File Handling
    const srtDropZone = document.getElementById('srtDropZone');
    const srtFileInput = document.getElementById('srtFileInput');
    const srtFileNameDisplay = document.getElementById('srtFileName');
    const startTranslationBtn = document.getElementById('startTranslationBtn');

    srtDropZone.addEventListener('click', () => srtFileInput.click());
    srtDropZone.addEventListener('dragover', (e) => { e.preventDefault(); srtDropZone.classList.add('dragover'); });
    srtDropZone.addEventListener('dragleave', () => srtDropZone.classList.remove('dragover'));
    srtDropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        srtDropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) handleSrtFile(e.dataTransfer.files[0]);
    });
    srtFileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleSrtFile(e.target.files[0]);
    });

    function handleSrtFile(file) {
        if (!file.name.toLowerCase().endsWith('.srt')) {
            alert('Please select an SRT file.');
            return;
        }
        selectedSrtFile = file;
        srtFileNameDisplay.textContent = file.name;
        startTranslationBtn.disabled = false;
        resultsArea.classList.add('hidden');
        srtOutput.value = '';
    }

    // Open Workspace
    const openWorkspaceBtn = document.getElementById('openWorkspaceBtn');
    if (openWorkspaceBtn) {
        openWorkspaceBtn.addEventListener('click', async () => {
            try { await fetch('/api/open-workspace', { method: 'POST' }); } 
            catch (err) { console.error(err); }
        });
    }

    // Start Transcription
    startBtn.addEventListener('click', async () => {
        if (!selectedMediaFile) return;

        startBtn.disabled = true;
        loadingState.classList.remove('hidden');
        resultsArea.classList.add('hidden');
        
        const formData = new FormData();
        formData.append('file', selectedMediaFile);
        formData.append('engine', engineSelect.value);
        formData.append('model', modelSelect.value);
        formData.append('language', langSelect.value);
        formData.append('compute_type', computeSelect.value);
        formData.append('denoise_level', denoiseLevel.value);
        formData.append('highlight_words', highlightWords.checked ? 'true' : 'false');
        formData.append('convert_to_traditional', convertToTraditional.checked ? 'true' : 'false');
        
        // AI Auto-translate parameters
        formData.append('auto_translate', autoTranslate.checked ? 'true' : 'false');
        formData.append('ai_api_url', aiApiUrl.value);
        formData.append('ai_model_name', aiModelName.value);
        formData.append('ai_target_lang', aiTargetLang.value);

        try {
            const res = await fetch('/api/transcribe', { method: 'POST', body: formData });
            const data = await res.json();
            
            if (data.success) {
                srtOutput.value = data.srt_content || 'No subtitles returned.';
                resultsArea.classList.remove('hidden');
            } else {
                alert('Transcription Failed: ' + data.error);
            }
        } catch (err) {
            console.error(err);
            alert('Error during transcription.');
        } finally {
            startBtn.disabled = false;
            loadingState.classList.add('hidden');
        }
    });

    // Start standalone SRT translation
    startTranslationBtn.addEventListener('click', async () => {
        if (!selectedSrtFile) return;

        startTranslationBtn.disabled = true;
        loadingState.classList.remove('hidden');
        resultsArea.classList.add('hidden');

        const formData = new FormData();
        formData.append('file', selectedSrtFile);
        formData.append('ai_api_url', aiApiUrl.value);
        formData.append('ai_model_name', aiModelName.value);
        formData.append('ai_target_lang', aiTargetLang.value);

        try {
            const res = await fetch('/api/translate-srt', { method: 'POST', body: formData });
            const data = await res.json();
            
            if (data.success) {
                srtOutput.value = data.srt_content || 'No subtitles returned.';
                resultsArea.classList.remove('hidden');
            } else {
                alert('Translation Failed: ' + data.error);
            }
        } catch (err) {
            console.error(err);
            alert('Error during translation.');
        } finally {
            startTranslationBtn.disabled = false;
            loadingState.classList.add('hidden');
        }
    });

    // Copy to clipboard
    copyBtn.addEventListener('click', () => {
        srtOutput.select();
        document.execCommand('copy');
        const icon = copyBtn.querySelector('i');
        icon.className = 'fa-solid fa-check';
        setTimeout(() => { icon.className = 'fa-regular fa-copy'; }, 2000);
    });
});
