function showPhoto() {
    viewer.innerText = "Фото спутника";
}

function showOrbit() {
    viewer.innerText = "Симуляция орбиты";
}

const photos = ["Снимок 1","Снимок 2","Снимок 3","Снимок 4","Снимок 5","Снимок 6","Снимок 7"];
let index = 0;
const photo = document.getElementById("photo");

function changePhoto(newIndex) {
    photo.classList.add("fade-out");

    setTimeout(() => {
        index = (newIndex + photos.length) % photos.length;
        photo.innerText = photos[index];
        photo.classList.remove("fade-out");
        photo.classList.add("fade-in");
    }, 400);
}

function nextPhoto() { 
    changePhoto(index + 1); 
}

function prevPhoto() { 
    changePhoto(index - 1); 
}

function createChart(id, label, data) {
    new Chart(document.getElementById(id), {
        type: 'line',
        data: {
            labels: ['00','01','02','03','04','05','06'],
            datasets: [{
                label: label,
                data: data,
                borderColor: '#7c3aed',
                backgroundColor: 'rgba(124,58,237,0.2)',
                fill: true
            }]
        }
    });
}

createChart('tempIn', 'Температура внутри °C', [20,21,22,23,22,21,20]);
createChart('tempOut', 'Температура снаружи °C', [-40,-42,-41,-39,-38,-40,-41]);
createChart('voltage', 'Напряжение батареи В', [28,28.2,28.1,28.3,28.4,28.2,28.1]);
createChart('radiation', 'Радиация мЗв', [0.12,0.14,0.13,0.15,0.16,0.14,0.13]);
