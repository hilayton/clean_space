# Clean Space
The game will be similar to “Asteroids.” The player will control a spaceship using the W, A, S, and D keys and will be able to fly around the screen. Asteroids and garbage bags will enter from outside the screen and travel across the play area. The player will need to avoid the asteroids while collecting as many garbage bags as possible.

Each garbage bag collected will increase the player’s score. There will be no time limit or traditional win condition. Instead, the objective of the game will be to survive for as long as possible and earn the highest score. As the game continues, the asteroids and garbage bags will move faster and appear more frequently. This will make it harder for the player to avoid collisions while continuing to collect garbage.

The player will begin the game with three lives. If the spaceship collides with an asteroid, the ship will explode and the player will lose one life. An explosion animation, particle effects, and a sound effect will play when this happens. After losing a life, the spaceship will return to the center of the screen so the player can continue. The game will end once all three lives have been spent.

The player’s score and remaining lives will be displayed on the screen throughout the game. Collecting a garbage bag will play a sound and create a small visual effect so the player knows that it was collected successfully. When the player runs out of lives, a game-over screen will appear and display the player’s final score. The game-over screen will also allow the player to restart the game and try to earn a higher score.

## Goals
To be implemented in order, possibly. IDK. I've never made a game or a real program before. 

1. Be able to move a ship around the screen 
    - Should have inertial movement
2. Basic asteroids and garbage shapes appear and fly in from off screen, from all directions
3. Implement collision logic between asteroids and ship
    - Colliding with asteroids will cause ship destruction
    - Colliding with garbage causes garbage to dissapear
4. Implement scoring and lives logic
    - Score will probably be in increments of 100
        - May implement alternate trash bags worth more points
    - Limited to three lives per run
        - Game over screen will also be implemented
        - Game over screen will allow player to restart game
5. Implement SFX and VFX
    - SFX
        - Sound when player collects garbage
        - Sound when player collides with asteroid
        - Possible background music
    - VFX
        - Sparks/ explosion when colliding with asteroid
        - Something for when garbage is collected

## Backlog/ Stretch Goals
1. Player can fire laser to destroy asteroids + SFX/VFX for asteroid destruction
2. Score history/ high score tracking/ scoreboard