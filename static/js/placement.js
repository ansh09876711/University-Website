console.log("Internship & Placement Page Loaded");
const ctx = document.getElementById('placementChart');

if (ctx) {
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['2022', '2023', '2024'],
            datasets: [
                {
                    label: 'Students Placed',
                    data: [180, 230, 310],
                    backgroundColor: '#f4b400'
                },
                {
                    label: 'Average Package (LPA)',
                    data: [4.5, 5.8, 6.5],
                    backgroundColor: '#1a73e8'
                }
            ]
        }
    });
}
