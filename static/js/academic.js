function filterEvents(type) {
    const cards = document.querySelectorAll('.event-card');
    const buttons = document.querySelectorAll('.calendar-sidebar li');

    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    cards.forEach(card => {
        if (type === 'all') {
            card.style.display = 'block';
        } else {
            card.style.display = card.classList.contains(type) ? 'block' : 'none';
        }
    });
}
