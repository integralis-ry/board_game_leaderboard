let funnyComments = [];
let currentCommentIndex = 0;

function createGameEntry(game) {
    return `
        <div class="game-entry">
            <div class="game-type">${game.game}</div>
            <div class="winner">Winner: ${game.winner}</div>
            <div class="time">${new Date(game.timestamp).toLocaleTimeString()}</div>
        </div>
    `;
}

function createLeaderboardEntry(winner, index) {
    const medal = index < 3 ? ['🥇', '🥈', '🥉'][index] : '';
    
    // Create game breakdown HTML
    const gameBreakdown = Object.entries(winner.game_breakdown)
        .map(([game, wins]) => `
            <div class="game-stat">
                <span class="game-name">${game}:</span>
                <span class="game-wins">${wins}</span>
            </div>
        `).join('');
    
    return `
        <div class="leaderboard-entry ${index < 3 ? 'top-three' : ''}">
            <div class="player-info">
                <span class="player-name">${medal} ${winner.name}</span>
                <span class="total-wins">${winner.wins} total win${winner.wins !== 1 ? 's' : ''}</span>
            </div>
            <div class="game-breakdown">
                ${gameBreakdown}
            </div>
        </div>
    `;
}

function updateData() {
    fetch('/get_data')
        .then(response => response.json())
        .then(data => {
            document.getElementById('today-date').textContent = data.today;
            document.getElementById('yesterday-date').textContent = data.yesterday;
            
            // Update today's games
            document.getElementById('today-games').innerHTML = 
                data.today_games.length > 0 
                    ? data.today_games.map(createGameEntry).join('') 
                    : '<p>No games played today yet!</p>';
            
            // Update yesterday's games
            document.getElementById('yesterday-games').innerHTML = 
                data.yesterday_games.length > 0 
                    ? data.yesterday_games.map(createGameEntry).join('') 
                    : '<p>No games played yesterday!</p>';
            
            // Update leaderboard with proper object access
            const leaderboardHtml = data.winner_counts
                .map((winner, index) => createLeaderboardEntry(winner, index))
                .join('');
            document.getElementById('winner-counts').innerHTML = leaderboardHtml;
            
            // Update funny comments
            funnyComments = data.funny_comments;
            if (funnyComments.length > 0) {
                document.getElementById('comment-display').textContent = funnyComments[0];
            }
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            document.getElementById('winner-counts').innerHTML = '<p>Error loading leaderboard</p>';
        });
}

function rotateComments() {
    if (funnyComments.length === 0) return;
    
    const commentDiv = document.getElementById('comment-display');
    commentDiv.style.opacity = 0;
    
    setTimeout(() => {
        currentCommentIndex = (currentCommentIndex + 1) % funnyComments.length;
        commentDiv.textContent = funnyComments[currentCommentIndex];
        commentDiv.style.opacity = 1;
    }, 500);
}



// Initial update
updateData();

// Update data every minute
setInterval(updateData, 60000);

// Rotate comments every 5 seconds
setInterval(rotateComments, 5000);
