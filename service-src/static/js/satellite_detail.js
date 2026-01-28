function openConfigModal() {
    document.getElementById('configModal').style.display = 'block';
}

function closeConfigModal() {
    document.getElementById('configModal').style.display = 'none';
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

window.onclick = function(event) {
    const modal = document.getElementById('configModal');
    if (event.target == modal) {
        closeConfigModal();
    }
}
