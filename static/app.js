function createGameEntry(game) {
    return `
        <div class="game-entry">
            <div class="game-type">${game.game}</div>
            <div class="winner">Winner: ${game.winner}</div>
            <div class="time">${new Date(game.timestamp).toLocaleTimeString()}</div>
        </div>
    `;
}

function updateGames() {
    fetch('/get_winners')
        .then(response => response.json())
        .then(data => {
            // Update dates
            document.getElementById('today-date').textContent = data.today;
            document.getElementById('yesterday-date').textContent = data.yesterday;
            
            // Update today's games
            const todayGames = document.getElementById('today-games');
            todayGames.innerHTML = data.today_games.length > 0
                ? data.today_games.map(createGameEntry).join('')
                : '<p>No games played today yet!</p>';
            
            // Update yesterday's games
            const yesterdayGames = document.getElementById('yesterday-games');
            yesterdayGames.innerHTML = data.yesterday_games.length > 0
                ? data.yesterday_games.map(createGameEntry).join('')
                : '<p>No games played yesterday!</p>';
        })
        .catch(error => console.error('Error fetching winners:', error));
}

// Update immediately and then every minute
updateGames();
setInterval(updateGames, 60000);