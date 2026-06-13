document.addEventListener('DOMContentLoaded', () => {
    
    // Elements
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const fileNameDisplay = document.getElementById('fileName');
    const transcribeBtn = document.getElementById('transcribeBtn');
    
    const engineSelect = document.getElementById('engine');
    const modelSelect = document.getElementById('model');
    const langSelect = document.getElementById('language');
    const computeSelect = document.getElementById('computeType');
    const denoiseLevel = document.getElementById('denoiseLevel');
    const denoiseValue = document.getElementById('denoiseValue');
    const highlightWords = document.getElementById('highlightWords');
    const convertToTraditional = document.getElementById('convertToTraditional');
    
    // Tab Switching Logic
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked
            btn.classList.add('active');
            const tabId = btn.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    const loadingState = document.getElementById('loadingState');
    const resultsArea = document.getElementById('resultsArea');
    const srtOutput = document.getElementById('srtOutput');
    const copyBtn = document.getElementById('copyBtn');

    let selectedFile = null;

    // Initialize Config
    async function fetchConfig() {
        try {
            const res = await fetch('/api/config');
            const config = await res.json();
            
            // Populate Engines
            config.engines.forEach(e => {
                const opt = document.createElement('option');
                opt.value = e; opt.textContent = e;
                engineSelect.appendChild(opt);
            });

            // Populate Models (restricted to large-v3, large-v3-turbo)
            config.models.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m; opt.textContent = m;
                modelSelect.appendChild(opt);
            });

            // Populate Languages
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

            // Populate Compute Types
            config.compute_types.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c; opt.textContent = c;
                computeSelect.appendChild(opt);
            });

        } catch (err) {
            console.error("Error fetching config:", err);
            alert("Failed to load backend config. Is the server running?");
        }
    }

    fetchConfig();

    // Denoise Label update
    denoiseLevel.addEventListener('input', (e) => {
        const vals = ["0 (None)", "1 (HTDemucs)", "2 (HTDemucs FT)"];
        denoiseValue.textContent = vals[e.target.value];
    });

    // File Drag & Drop
    dropzone.addEventListener('click', () => fileInput.click());
    
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });
    
    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });
    
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    function handleFile(file) {
        selectedFile = file;
        fileNameDisplay.textContent = file.name;
        transcribeBtn.disabled = false;
        
        // Hide previous results
        resultsArea.classList.add('hidden');
        srtOutput.value = '';
    }

    // Transcribe
    const openWorkspaceBtn = document.getElementById('openWorkspaceBtn');
    openWorkspaceBtn.addEventListener('click', async () => {
        try {
            await fetch('/api/open-workspace', { method: 'POST' });
        } catch (err) {
            console.error('Failed to open workspace', err);
        }
    });

    transcribeBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        // UI Updates
        transcribeBtn.disabled = true;
        loadingState.classList.remove('hidden');
        resultsArea.classList.add('hidden');
        
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('engine', engineSelect.value);
        formData.append('model', modelSelect.value);
        formData.append('language', langSelect.value);
        formData.append('compute_type', computeSelect.value);
        formData.append('denoise_level', denoiseLevel.value);
        formData.append('highlight_words', highlightWords.checked ? 'true' : 'false');
        formData.append('convert_to_traditional', convertToTraditional.checked ? 'true' : 'false');

        try {
            const res = await fetch('/api/transcribe', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            
            if (data.success) {
                srtOutput.value = data.srt_content || 'No subtitles returned. Check server logs.';
                resultsArea.classList.remove('hidden');
            } else {
                alert('Transcription Failed: ' + data.error);
            }
        } catch (err) {
            console.error('Transcription Error:', err);
            alert('An error occurred during transcription. See console.');
        } finally {
            transcribeBtn.disabled = false;
            loadingState.classList.add('hidden');
        }
    });

    // Copy to clipboard
    copyBtn.addEventListener('click', () => {
        srtOutput.select();
        document.execCommand('copy');
        
        // Brief visual feedback
        const icon = copyBtn.querySelector('i');
        icon.className = 'fa-solid fa-check';
        setTimeout(() => {
            icon.className = 'fa-regular fa-copy';
        }, 2000);
    });
});
