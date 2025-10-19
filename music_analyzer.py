#!/usr/bin/env python3
import os
import tkinter as tk
from tkinter import filedialog, ttk
import pygame
import librosa
import numpy as np
import json
import yaml
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import queue

class MusicAnalyzer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Music Analyzer")
        self.root.geometry("1200x800")
        
        # Initialize pygame mixer with better audio settings
        pygame.mixer.quit()  # Ensure clean state
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
        
        # Variables
        self.current_file = None
        self.playing = False
        self.current_position = 0
        self.marks = []
        self.waveform = None
        self.audio_features = None
        self.update_queue = queue.Queue()
        self.start_offset = 0  # Track the starting position for accurate seeking
        
        self._create_gui()
        self._setup_keyboard_shortcuts()
        
        # Ensure cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
    def _create_gui(self):
        # Top frame for file controls
        top_frame = ttk.Frame(self.root, padding="5")
        top_frame.pack(fill=tk.X)
        
        ttk.Button(top_frame, text="Open File", command=self.open_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Play/Pause (Space)", command=self.toggle_playback).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Mark Transition (M)", command=self.mark_transition).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Save Timings", command=self.save_timings).pack(side=tk.LEFT, padx=5)
        
        # Middle frame for waveform
        self.fig, self.ax = plt.subplots(figsize=(12, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Frame for markers list
        markers_frame = ttk.LabelFrame(self.root, text="Transition Markers", padding="5")
        markers_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview for markers
        columns = ("Time", "Description")
        self.markers_tree = ttk.Treeview(markers_frame, columns=columns, show="headings")
        
        # Define headings
        for col in columns:
            self.markers_tree.heading(col, text=col)
            self.markers_tree.column(col, width=100)
        
        self.markers_tree.pack(fill=tk.BOTH, expand=True)
        
        # Playback position slider
        self.position_slider = ttk.Scale(
            self.root,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            command=self.slider_changed
        )
        self.position_slider.pack(fill=tk.X, padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var)
        status_bar.pack(fill=tk.X, padx=5, pady=5)
        
    def _setup_keyboard_shortcuts(self):
        self.root.bind("<space>", lambda e: self.toggle_playback())
        self.root.bind("m", lambda e: self.mark_transition())
        self.root.bind("<Left>", lambda e: self.seek_relative(-5))
        self.root.bind("<Right>", lambda e: self.seek_relative(5))
        
    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3 *.wav")]
        )
        if file_path:
            self.current_file = file_path
            self.load_audio()
            
    def load_audio(self):
        if not self.current_file:
            return
            
        # Load audio file and compute waveform
        self.status_var.set("Loading audio file...")
        self.root.update()
        
        # Run audio analysis in a thread
        thread = threading.Thread(target=self._analyze_audio)
        thread.start()
        
    def _analyze_audio(self):
        try:
            # Load audio with librosa
            y, sr = librosa.load(self.current_file)
            
            # Compute waveform
            self.waveform = y
            self.sr = sr
            
            # Compute onset strength
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            self.audio_features = {
                'onset_env': onset_env,
                'times': librosa.times_like(onset_env, sr=sr)
            }
            
            # Update GUI in main thread
            self.update_queue.put(self._update_display)
            
        except Exception as e:
            self.status_var.set(f"Error loading audio: {str(e)}")
            
    def _update_display(self):
        if self.waveform is None:
            return
            
        # Clear previous plot
        self.ax.clear()
        
        # Plot waveform
        times = np.arange(len(self.waveform)) / self.sr
        self.ax.plot(times, self.waveform, color='blue', alpha=0.5)
        
        # Plot onset strength
        if self.audio_features is not None:
            onset_times = self.audio_features['times']
            onset_env = self.audio_features['onset_env']
            self.ax.plot(onset_times, onset_env / onset_env.max(), color='red', alpha=0.5)
        
        # Plot markers
        for mark in self.marks:
            self.ax.axvline(x=mark['time'], color='green', alpha=0.5)
        
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Amplitude')
        self.canvas.draw()
        
        # Update status
        self.status_var.set(f"Loaded: {os.path.basename(self.current_file)}")
        
        # Update slider
        self.position_slider.configure(to=len(self.waveform) / self.sr)
        
        # Load into pygame for playback
        pygame.mixer.music.load(self.current_file)
        
    def toggle_playback(self):
        if not self.current_file:
            return
            
        if self.playing:
            pygame.mixer.music.pause()
            self.playing = False
        else:
            try:
                if not pygame.mixer.music.get_busy():
                    pygame.mixer.music.load(self.current_file)
                    pygame.mixer.music.play(start=self.current_position)
                    self.start_offset = self.current_position
                else:
                    pygame.mixer.music.unpause()
                self.playing = True
                # Start update thread if playing
                threading.Thread(target=self._update_playback_position, daemon=True).start()
            except Exception as e:
                self.status_var.set(f"Playback error: {str(e)}")
                
    def _update_playback_position(self):
        import time
        while self.playing:
            if not pygame.mixer.music.get_busy():
                self.playing = False
                break
                
            try:
                pos = pygame.mixer.music.get_pos()
                if pos != -1:  # -1 indicates an error or song end
                    # Calculate actual position based on start offset
                    actual_pos = (pos / 1000.0) + self.start_offset
                    self.current_position = actual_pos
                    self.position_slider.set(actual_pos)
                    self.status_var.set(f"Time: {actual_pos:.2f}s")
                time.sleep(0.03)  # Smaller delay for more responsive updates
            except Exception as e:
                self.status_var.set(f"Playback error: {str(e)}")
                break
            
    def mark_transition(self):
        if not self.current_file:
            return
            
        # Get current position
        pos = self.current_position
        
        # Add marker
        self.marks.append({
            'time': pos,
            'description': f'Transition {len(self.marks) + 1}'
        })
        
        # Update markers display
        self.markers_tree.insert('', 'end', values=(f"{pos:.2f}", f"Transition {len(self.marks)}"))
        
        # Update plot
        self._update_display()
        
    def slider_changed(self, value):
        if not self.current_file:
            return
            
        try:
            # Update position
            new_pos = float(value)
            was_playing = self.playing
            
            # Stop any current playback
            if was_playing:
                self.playing = False
                pygame.mixer.music.stop()
            
            # Update position and reload
            self.current_position = new_pos
            self.start_offset = new_pos
            
            # Resume playback if needed
            if was_playing:
                pygame.mixer.music.load(self.current_file)
                pygame.mixer.music.play(start=new_pos)
                self.playing = True
                threading.Thread(target=self._update_playback_position, daemon=True).start()
        except Exception as e:
            self.status_var.set(f"Seek error: {str(e)}")
            
    def seek_relative(self, seconds):
        if not self.current_file:
            return
            
        try:
            new_pos = max(0, self.current_position + seconds)
            self.slider_changed(new_pos)  # Use existing slider logic for seeking
        except Exception as e:
            self.status_var.set(f"Seek error: {str(e)}")
            
    def _on_closing(self):
        """Clean up resources before closing"""
        self.playing = False
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        self.root.destroy()
            
    def save_timings(self):
        if not self.current_file or not self.marks:
            return
            
        # Sort marks by time
        sorted_marks = sorted(self.marks, key=lambda x: x['time'])
        
        # Create YAML structure
        song_name = os.path.basename(self.current_file)
        yaml_data = {
            'songs': {
                song_name: [
                    {
                        'time': mark['time'],
                        'controllers': {
                            'sword1': {
                                'preset': idx + 1  # Use sequential preset numbers
                            }
                        }
                    }
                    for idx, mark in enumerate(sorted_marks)
                ]
            }
        }
        
        # Save to file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".yml",
            filetypes=[("YAML files", "*.yml")],
            initialfile="timings.yml"
        )
        
        if file_path:
            with open(file_path, 'w') as f:
                yaml.dump(yaml_data, f, sort_keys=False)
            self.status_var.set(f"Saved timings to {os.path.basename(file_path)}")
            
    def run(self):
        # Start GUI update checker
        self._check_updates()
        self.root.mainloop()
        
    def _check_updates(self):
        try:
            while True:
                # Get all available updates
                update_func = self.update_queue.get_nowait()
                update_func()
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self._check_updates)

if __name__ == "__main__":
    analyzer = MusicAnalyzer()
    analyzer.run()
