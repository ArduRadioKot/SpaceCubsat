document.addEventListener('DOMContentLoaded', function() {
    loadSatellites();
    setupEventListeners();
});

function setupEventListeners() {
    const toggleBtn = document.getElementById('toggleSidebar');
    const sidebar = document.getElementById('sidebar');
    
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
    }
}

async function loadSatellites() {
    try {
        const response = await fetch('/api/satellites');
        const satellites = await response.json();
        renderSatellites(satellites);
    } catch (error) {
        console.error('Error loading satellites:', error);
        showError('Ошибка загрузки данных спутников');
    }
}

function renderSatellites(satellites) {
    const grid = document.getElementById('satellitesGrid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    satellites.forEach(satellite => {
        const card = createSatelliteCard(satellite);
        grid.appendChild(card);
    });
}

function createSatelliteCard(satellite) {
    const card = document.createElement('div');
    card.className = 'satellite-card';
    card.onclick = () => viewSatellite(satellite.id);
    
    const statusClass = getStatusClass(satellite.status);
    
    card.innerHTML = `
        <div class="satellite-header">
            <h3 class="satellite-name">${satellite.name}</h3>
            <span class="satellite-status ${statusClass}">${satellite.status}</span>
        </div>
        <img src="/static/images/${satellite.image}" alt="${satellite.name}" class="satellite-image">
        <div class="satellite-info">
            <div class="info-item">
                <span class="info-label">Орбита:</span>
                <span class="info-value">${satellite.altitude}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Запуск:</span>
                <span class="info-value">${satellite.launch_date}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Последний контакт:</span>
                <span class="info-value">${satellite.last_contact}</span>
            </div>
        </div>
        <div class="satellite-actions">
            <button class="btn btn-small btn-primary" onclick="event.stopPropagation(); viewSatellite(${satellite.id})">
                <i class="fas fa-eye"></i> Детали
            </button>
        </div>
    `;
    
    return card;
}

function getStatusClass(status) {
    switch(status.toLowerCase()) {
        case 'active': return 'status-active';
        case 'maintenance': return 'status-maintenance';
        case 'inactive': return 'status-inactive';
        default: return 'status-inactive';
    }
}

function viewSatellite(id) {
    window.location.href = `/satellite/${id}`;
}

function openConfigModal() {
    const modal = document.getElementById('configModal');
    if (modal) {
        modal.style.display = 'block';
    }
}

function closeConfigModal() {
    const modal = document.getElementById('configModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

async function applyConfiguration() {
    const satelliteId = document.getElementById('satelliteSelect').value;
    const rotationX = document.getElementById('rotationX').value;
    const rotationY = document.getElementById('rotationY').value;
    const rotationZ = document.getElementById('rotationZ').value;
    
    try {
        const response = await fetch('/api/configure-satellite', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                satellite_id: satelliteId,
                rotation_x: rotationX,
                rotation_y: rotationY,
                rotation_z: rotationZ
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Конфигурация успешно применена!');
            closeConfigModal();
        } else {
            alert('Ошибка: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка при отправке конфигурации');
    }
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
        z-index: 1001;
    `;
    
    document.body.appendChild(errorDiv);
    
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.parentNode.removeChild(errorDiv);
        }
    }, 5000);
}

window.onclick = function(event) {
    const modal = document.getElementById('configModal');
    if (modal && event.target == modal) {
        closeConfigModal();
    }
}
