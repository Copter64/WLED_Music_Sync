"""PyGame-based music player GUI."""
import logging
import os
import time
from typing import List, Optional, Tuple

import pygame

LOGGER = logging.getLogger(__name__)

class MusicPlayer:
    """Lightweight pygame-based player with keyboard controls and song selection."""
    def __init__(self):
        pygame.mixer.init()
        pygame.init()  # Initialize pygame for event handling
        
        # Create a larger control window
        self._window = pygame.display.set_mode((800, 400))
        pygame.display.set_caption("WLED Music Sync")
        
        # Force the window to be focused and centered
        info = pygame.display.Info()
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{(info.current_w - 800) // 2},{(info.current_w - 400) // 2}"
        pygame.display.set_allow_screensaver(False)  # Prevent screensaver during playback
        pygame.event.clear()  # Clear any pending events
        pygame.display.flip()  # Update the display
        
        # Initialize fonts for display
        self._font = pygame.font.Font(None, 48)  # Larger main font
        self._small_font = pygame.font.Font(None, 36)  # Smaller font for status
        self._title_font = pygame.font.Font(None, 60)  # Large font for titles
        
        self._start_time = None
        self._paused = False
        self._current_pos = 0.0
        self._file_path = None
        self._volume = 1.0
        self._song_finished = False
        self._in_song_select = True  # Start in song selection mode
        self._available_songs = []   # Will be populated with song list
        self._song_buttons = []      # List of (rect, song_name) tuples
        self._hover_index = -1       # Index of button being hovered
        pygame.mixer.music.set_volume(self._volume)
        
        # Set up the end of song event
        pygame.mixer.music.set_endevent(pygame.USEREVENT + 1)
        
        # Draw initial menu
        self._draw_song_select()

    def play(self, file_path: str) -> None:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(file_path)
        self._file_path = file_path
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        self._start_time = time.perf_counter()
        self._paused = False
        LOGGER.info("Started music: %s", file_path)

    def stop(self) -> None:
        pygame.mixer.music.stop()
        self._start_time = None
        self._paused = False

    def is_playing(self) -> bool:
        return pygame.mixer.music.get_busy() or self._paused

    def playback_elapsed(self) -> Optional[float]:
        if not self._start_time:
            return None
        if self._paused:
            return self._current_pos
        return time.perf_counter() - self._start_time

    def _draw_controls(self):
        """Draw the control interface"""
        self._window.fill((0, 0, 0))  # Black background
        
        # Draw controls text
        controls = [
            "SPACE: Play/Pause",
            "LEFT/RIGHT: Seek ±5s",
            "PGUP/PGDN: Seek ±30s",
            "UP/DOWN: Volume",
            "R: Restart",
            "Q: Quit"
        ]
        
        # Draw title
        title = self._font.render("Music Controls", True, (255, 255, 255))
        title_rect = title.get_rect(centerx=self._window.get_width() // 2, y=20)
        self._window.blit(title, title_rect)
        
        # Draw controls in two columns
        y = 100
        col_width = self._window.get_width() // 2
        for i, text in enumerate(controls):
            surface = self._font.render(text, True, (255, 255, 255))
            if i < len(controls) // 2:
                x = 40
            else:
                x = col_width + 40
                y = 100 + (i - len(controls) // 2) * 60
            self._window.blit(surface, (x, y))
            if i < len(controls) // 2:
                y += 60
        
        # Draw status bar at bottom
        if self._start_time is not None:
            # Status bar background
            pygame.draw.rect(self._window, (40, 40, 40), (20, 320, 760, 60))
            
            # Current time
            time_text = f"Time: {self.playback_elapsed():.1f}s"
            time_surface = self._font.render(time_text, True, (0, 255, 0))
            self._window.blit(time_surface, (30, 330))
            
            # Volume
            vol_text = f"Volume: {int(self._volume * 100)}%"
            vol_surface = self._font.render(vol_text, True, (0, 255, 0))
            vol_rect = vol_surface.get_rect(midright=(780, 350))
            self._window.blit(vol_surface, vol_rect)
            
            # Playback status
            if self._song_finished:
                status = "FINISHED - Press 'R' to replay or 'Q' to quit"
                status_surface = self._font.render(status, True, (0, 255, 0))
            else:
                status = "PAUSED" if self._paused else "PLAYING"
                status_surface = self._font.render(status, True, (255, 165, 0))
            status_rect = status_surface.get_rect(center=(self._window.get_width() // 2, 350))
            self._window.blit(status_surface, status_rect)
        
        pygame.display.flip()

    def handle_events(self) -> bool:
        """Handle keyboard and mouse events. Returns False if should quit, None if song finished."""
        for event in pygame.event.get():
            if event.type == pygame.USEREVENT + 1:  # End of song
                self._song_finished = True
                self._current_pos = time.perf_counter() - self._start_time  # Save final position
                self._start_time = None  # Stop the timer
                self._in_song_select = True  # Return to song selection
                return None

            # Handle mouse events for song selection
            if self._in_song_select:
                if event.type == pygame.MOUSEMOTION:
                    # Update hover state
                    mouse_pos = pygame.mouse.get_pos()
                    self._hover_index = -1
                    for i, (rect, _) in enumerate(self._song_buttons):
                        if rect.collidepoint(mouse_pos):
                            self._hover_index = i
                            break

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Handle song selection click
                    mouse_pos = pygame.mouse.get_pos()
                    for rect, song in self._song_buttons:
                        if rect.collidepoint(mouse_pos):
                            self._in_song_select = False
                            return song  # Return selected song name
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:  # Play/Pause
                    if self._paused:
                        pygame.mixer.music.unpause()
                        self._start_time = time.perf_counter() - self._current_pos
                        self._paused = False
                        LOGGER.info("Resumed at %.2fs", self._current_pos)
                    else:
                        pygame.mixer.music.pause()
                        self._current_pos = time.perf_counter() - self._start_time
                        self._paused = True
                        LOGGER.info("Paused at %.2fs", self._current_pos)
                
                elif event.key == pygame.K_LEFT:  # Rewind 5 seconds
                    current = self.playback_elapsed() or 0
                    new_pos = max(0, current - 5)
                    self._current_pos = new_pos
                    pygame.mixer.music.rewind()
                    pygame.mixer.music.play(start=new_pos)
                    self._start_time = time.perf_counter() - new_pos
                    LOGGER.info("Seeking to %.2fs", new_pos)
                
                elif event.key == pygame.K_RIGHT:  # Forward 5 seconds
                    current = self.playback_elapsed() or 0
                    new_pos = current + 5
                    self._current_pos = new_pos
                    pygame.mixer.music.rewind()
                    pygame.mixer.music.play(start=new_pos)
                    self._start_time = time.perf_counter() - new_pos
                    LOGGER.info("Seeking to %.2fs", new_pos)
                
                elif event.key == pygame.K_r:  # Restart
                    pygame.mixer.music.play()
                    self._start_time = time.perf_counter()
                    self._paused = False
                    LOGGER.info("Restarted playback")
                
                elif event.key == pygame.K_UP:  # Volume up
                    self._volume = min(1.0, self._volume + 0.1)
                    pygame.mixer.music.set_volume(self._volume)
                    LOGGER.info("Volume: %.1f", self._volume)
                
                elif event.key == pygame.K_DOWN:  # Volume down
                    self._volume = max(0.0, self._volume - 0.1)
                    pygame.mixer.music.set_volume(self._volume)
                    LOGGER.info("Volume: %.1f", self._volume)
                
                elif event.key == pygame.K_PAGEUP:  # Forward 30 seconds
                    current = self.playback_elapsed() or 0
                    new_pos = current + 30
                    self._current_pos = new_pos
                    pygame.mixer.music.rewind()
                    pygame.mixer.music.play(start=new_pos)
                    self._start_time = time.perf_counter() - new_pos
                    LOGGER.info("Seeking to %.2fs", new_pos)

                elif event.key == pygame.K_PAGEDOWN:  # Rewind 30 seconds
                    current = self.playback_elapsed() or 0
                    new_pos = max(0, current - 30)
                    self._current_pos = new_pos
                    pygame.mixer.music.rewind()
                    pygame.mixer.music.play(start=new_pos)
                    self._start_time = time.perf_counter() - new_pos
                    LOGGER.info("Seeking to %.2fs", new_pos)

                elif event.key == pygame.K_q:  # Quit
                    return False
            
            elif event.type == pygame.QUIT:
                return False

        # Update appropriate display
        if self._in_song_select:
            self._draw_song_select()
        else:
            self._draw_controls()
        return True

    def _draw_song_select(self):
        """Draw the song selection menu"""
        self._window.fill((0, 0, 0))  # Black background
        
        # Draw title
        title = self._title_font.render("Song Selection", True, (255, 255, 255))
        title_rect = title.get_rect(centerx=self._window.get_width() // 2, y=20)
        self._window.blit(title, title_rect)
        
        # Draw song buttons
        self._song_buttons = []  # Reset button list
        y = 100
        button_height = 50
        button_padding = 10
        
        for i, song in enumerate(self._available_songs):
            if y + button_height > self._window.get_height() - 60:  # Leave space for status
                break
                
            button_color = (60, 60, 60)
            if i == self._hover_index:
                button_color = (100, 100, 100)
                
            button_rect = pygame.Rect(40, y, self._window.get_width() - 80, button_height)
            pygame.draw.rect(self._window, button_color, button_rect, border_radius=5)
            
            song_text = self._font.render(song, True, (255, 255, 255))
            text_rect = song_text.get_rect(midleft=(50, y + button_height // 2))
            self._window.blit(song_text, text_rect)
            
            self._song_buttons.append((button_rect, song))
            y += button_height + button_padding
        
        # Draw instructions at bottom
        if self._song_finished:
            status = "Select a song to play"
        else:
            status = "Click a song or press Q to quit"
        status_surface = self._font.render(status, True, (200, 200, 200))
        status_rect = status_surface.get_rect(centerx=self._window.get_width() // 2, bottom=self._window.get_height() - 20)
        self._window.blit(status_surface, status_rect)
        
        pygame.display.flip()

    def set_available_songs(self, songs):
        """Set the list of available songs for the selection menu"""
        self._available_songs = list(songs)
        if self._in_song_select:
            self._draw_song_select()
