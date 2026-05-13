// === DOM Elements ===
// Navigation
const navItems = document.querySelectorAll('.nav-item');
const tabContents = document.querySelectorAll('.tab-content');

// Camera & WS (Kiosk)
const video = document.getElementById('videoElement');
const overlayCanvas = document.getElementById('overlayCanvas');
const captureCanvas = document.getElementById('captureCanvas');
const overlayCtx = overlayCanvas.getContext('2d');
const captureCtx = captureCanvas.getContext('2d');
const btnStart = document.getElementById('btn-start');
const btnStop = document.getElementById('btn-stop');
const wsStatus = document.getElementById('ws-status');

// Kiosk Card
const kioskCard = document.getElementById('kiosk-card');
const kioskImgReg = document.getElementById('kiosk-img-reg');
const kioskImgCap = document.getElementById('kiosk-img-cap');
const kioskName = document.getElementById('kiosk-name');
const kioskId = document.getElementById('kiosk-id');
const kioskStatus = document.getElementById('kiosk-status');
const kioskTime = document.getElementById('kiosk-time');

// Dashboard
const dashTotalUsers = document.getElementById('dash-total-users');
const dashCheckins = document.getElementById('dash-checkins');
const dashCheckouts = document.getElementById('dash-checkouts');
const dashRecentLogs = document.getElementById('dash-recent-logs');

// User Management & Profile Modal
const usersTableBody = document.getElementById('users-table-body');
const btnShowRegister = document.getElementById('btn-show-register');
const registerModal = document.getElementById('registerModal');
const profileModal = document.getElementById('profileModal');
const spanCloseReg = document.getElementsByClassName('close')[0];
const spanCloseProf = document.getElementsByClassName('close-profile')[0];
const registerForm = document.getElementById('registerForm');
const registerMsg = document.getElementById('register-msg');

// All Logs
const allLogsBody = document.getElementById('all-logs-body');
const btnRefreshLogs = document.getElementById('btn-refresh-logs');

// === Global State ===
let stream = null;
let ws = null;
let captureInterval = null;
let isStreaming = false;
let activeTab = 'dashboard';
const FPS = 10;
let kioskTimer = null;

// === Initialization ===
function init() {
    setupNavigation();
    setupModals();
    fetchDashboardStats();
    
    setInterval(() => {
        if (activeTab === 'dashboard') fetchDashboardStats();
        if (activeTab === 'users') fetchUsers();
        if (activeTab === 'logs') fetchAllLogs();
    }, 10000);
}

// === Navigation Logic ===
function setupNavigation() {
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navItems.forEach(nav => nav.classList.remove('active'));
            tabContents.forEach(tab => tab.classList.remove('active'));
            
            item.classList.add('active');
            const targetId = `tab-${item.dataset.tab}`;
            document.getElementById(targetId).classList.add('active');
            
            activeTab = item.dataset.tab;
            
            if (activeTab === 'dashboard') fetchDashboardStats();
            if (activeTab === 'users') fetchUsers();
            if (activeTab === 'logs') fetchAllLogs();
            
            if (activeTab !== 'camera' && isStreaming) {
                stopCamera();
            }
        });
    });
}

// === API Fetchers ===
async function fetchDashboardStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        
        dashTotalUsers.textContent = data.total_users;
        const checkins = data.today_logs.filter(log => log.status === 'Check-in').length;
        const checkouts = data.today_logs.filter(log => log.status === 'Check-out').length;
        dashCheckins.textContent = checkins;
        dashCheckouts.textContent = checkouts;
        
        dashRecentLogs.innerHTML = '';
        data.today_logs.slice(0, 10).forEach(log => {
            const capImg = log.captured_image_path ? `<img src="${log.captured_image_path}" class="log-img-preview" alt="Captured">` : '-';
            dashRecentLogs.innerHTML += `
                <tr style="cursor:pointer" onclick="viewProfile(${log.user_id})">
                    <td><strong>${log.name}</strong></td>
                    <td>${log.student_id}</td>
                    <td><span class="status-badge status-${log.status}">${log.status}</span></td>
                    <td>${log.time}</td>
                    <td>${log.score}</td>
                    <td>${capImg}</td>
                </tr>
            `;
        });
    } catch (e) { console.error("Error fetching stats:", e); }
}

async function fetchUsers() {
    try {
        const res = await fetch('/api/users');
        const users = await res.json();
        
        usersTableBody.innerHTML = '';
        users.forEach(u => {
            usersTableBody.innerHTML += `
                <tr>
                    <td>#${u.id}</td>
                    <td><strong>${u.student_id}</strong></td>
                    <td>${u.name}</td>
                    <td>
                        <button class="btn secondary-btn btn-sm" onclick="viewProfile(${u.id})">
                            <i class="fa-solid fa-id-card"></i> Profile
                        </button>
                        <button class="btn danger-btn btn-sm" style="margin-left:0.5rem" onclick="deleteUser(${u.id}, '${u.name}')">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
    } catch (e) { console.error("Error fetching users:", e); }
}

async function fetchAllLogs() {
    try {
        const res = await fetch('/api/logs/all');
        const logs = await res.json();
        
        allLogsBody.innerHTML = '';
        logs.forEach(log => {
            const capImg = log.captured_image_path ? `<img src="${log.captured_image_path}" class="log-img-preview" alt="Captured">` : '-';
            allLogsBody.innerHTML += `
                <tr>
                    <td>#${log.id}</td>
                    <td><strong>${log.name}</strong></td>
                    <td>${log.student_id}</td>
                    <td>${log.date}</td>
                    <td>${log.time}</td>
                    <td><span class="status-badge status-${log.status}">${log.status}</span></td>
                    <td>${log.score}</td>
                    <td>${capImg}</td>
                </tr>
            `;
        });
    } catch (e) { console.error("Error fetching logs:", e); }
}

async function deleteUser(id, name) {
    if(!confirm(`Are you sure you want to delete user: ${name}?`)) return;
    try {
        const res = await fetch(`/api/users/${id}`, { method: 'DELETE' });
        if (res.ok) fetchUsers();
        else alert("Failed to delete user.");
    } catch (e) { console.error("Delete error:", e); }
}

async function viewProfile(id) {
    profileModal.style.display = 'flex';
    document.getElementById('prof-logs-body').innerHTML = '<tr><td colspan="4">Loading...</td></tr>';
    
    try {
        const res = await fetch(`/api/users/${id}/logs`);
        if(!res.ok) return;
        const data = await res.json();
        
        document.getElementById('prof-img').src = data.user.image_path || '/ui/default-avatar.png';
        document.getElementById('prof-name').textContent = data.user.name;
        document.getElementById('prof-id').textContent = data.user.student_id;
        
        document.getElementById('prof-checkins').textContent = data.stats.checkins;
        document.getElementById('prof-checkouts').textContent = data.stats.checkouts;
        document.getElementById('prof-status').textContent = data.stats.current_status;
        
        const tbody = document.getElementById('prof-logs-body');
        tbody.innerHTML = '';
        data.logs.forEach(log => {
            const imgHtml = log.captured_image_path ? `<img src="${log.captured_image_path}" class="log-img-preview" alt="Log Image">` : 'N/A';
            tbody.innerHTML += `
                <tr>
                    <td>${log.date}</td>
                    <td>${log.time}</td>
                    <td><span class="status-badge status-${log.status}">${log.status}</span></td>
                    <td>${imgHtml}</td>
                </tr>
            `;
        });
        
    } catch (e) { console.error("Profile error:", e); }
}

// === Modal & Form Logic ===
function setupModals() {
    btnShowRegister.onclick = () => registerModal.style.display = 'flex';
    spanCloseReg.onclick = () => { registerModal.style.display = 'none'; registerMsg.textContent = ''; }
    spanCloseProf.onclick = () => { profileModal.style.display = 'none'; }
    window.onclick = (e) => {
        if (e.target == registerModal) { registerModal.style.display = 'none'; registerMsg.textContent = ''; }
        if (e.target == profileModal) { profileModal.style.display = 'none'; }
    }
    
    registerForm.onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(registerForm);
        const btn = registerForm.querySelector('button');
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
        registerMsg.textContent = '';
        
        try {
            const res = await fetch('/api/register', { method: 'POST', body: formData });
            const data = await res.json();
            if (res.ok) {
                registerMsg.innerHTML = `<span style="color:var(--success-color)"><i class="fa-solid fa-check"></i> ${data.message}</span>`;
                registerForm.reset();
                fetchUsers(); 
                setTimeout(() => { registerModal.style.display = 'none'; registerMsg.textContent = ''; }, 1500);
            } else {
                registerMsg.innerHTML = `<span style="color:var(--danger-color)"><i class="fa-solid fa-triangle-exclamation"></i> ${data.detail || 'Error'}</span>`;
            }
        } catch (err) { registerMsg.innerHTML = `<span style="color:var(--danger-color)">Connection error</span>`; } 
        finally { btn.disabled = false; btn.innerHTML = 'Submit & Extract Face'; }
    }
}

btnRefreshLogs.onclick = fetchAllLogs;

// === Camera & WebSocket Logic ===
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
    
    ws.onopen = () => { wsStatus.textContent = 'WS Connected'; wsStatus.className = 'status-badge connected'; };
    ws.onclose = () => { wsStatus.textContent = 'WS Disconnected'; wsStatus.className = 'status-badge disconnected'; if (isStreaming) setTimeout(connectWebSocket, 2000); };
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.results) {
            drawOverlay(data.results);
            updateKioskCard(data.results);
        }
    };
}

async function startCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } });
        video.srcObject = stream;
        
        video.onloadedmetadata = () => {
            overlayCanvas.width = video.videoWidth;
            overlayCanvas.height = video.videoHeight;
            captureCanvas.width = video.videoWidth;
            captureCanvas.height = video.videoHeight;
            
            isStreaming = true;
            connectWebSocket();
            captureInterval = setInterval(sendFrame, 1000 / FPS);
            
            btnStart.disabled = true;
            btnStop.disabled = false;
        };
    } catch (err) { alert("Webcam access denied or unavailable."); }
}

function stopCamera() {
    if (stream) { stream.getTracks().forEach(t => t.stop()); video.srcObject = null; }
    isStreaming = false;
    clearInterval(captureInterval);
    if (ws) ws.close();
    
    overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
    btnStart.disabled = false;
    btnStop.disabled = true;
    kioskCard.classList.add('empty'); // Hide card content
}

function sendFrame() {
    if (!isStreaming || !ws || ws.readyState !== WebSocket.OPEN) return;
    captureCtx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);
    ws.send(captureCanvas.toDataURL('image/jpeg', 0.8));
}

function drawOverlay(results) {
    overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
    results.forEach(res => {
        const [x1, y1, x2, y2] = res.box;
        let color = '#ef4444'; 
        if (res.status === 'Check-in') color = '#10b981';
        else if (res.status === 'Check-out') color = '#f59e0b';
        else if (res.status === 'Cooldown') color = '#3b82f6';
        
        overlayCtx.strokeStyle = color;
        overlayCtx.lineWidth = 4;
        overlayCtx.strokeRect(x1, y1, x2 - x1, y2 - y1);
    });
}

function updateKioskCard(results) {
    // Find the first valid Check-in or Check-out to display
    const validLog = results.find(r => r.status === 'Check-in' || r.status === 'Check-out');
    
    if (validLog) {
        // Show card content
        kioskCard.classList.remove('empty');
        
        kioskImgReg.src = validLog.registered_image || '';
        kioskImgCap.src = validLog.captured_image || '';
        kioskName.textContent = validLog.name;
        kioskId.textContent = validLog.student_id;
        
        kioskStatus.textContent = validLog.status;
        kioskStatus.className = `status-badge kiosk-badge status-${validLog.status}`;
        kioskTime.textContent = new Date().toLocaleTimeString();
        
        // Auto hide after 8 seconds - enough time to read info
        clearTimeout(kioskTimer);
        kioskTimer = setTimeout(() => {
            kioskCard.classList.add('empty');
        }, 8000);
    }
}

btnStart.onclick = startCamera;
btnStop.onclick = stopCamera;

// Run
init();
