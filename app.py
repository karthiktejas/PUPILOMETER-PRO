import cv2
import numpy as np
import time
import os
import sys
import traceback
import json
import csv
import io
import threading
import datetime
import math
from flask import Flask, Response, request, jsonify, redirect, render_template_string, url_for, send_file
from werkzeug.utils import secure_filename

# ==========================================
# 1. FRONTEND HTML (UNCHANGED VISUALS)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pupilometer // Pro</title>
    
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <style>
    .modal-dialog { margin: 0 !important; }
    .modal-dialog-scrollable { height: 100vh; }
    .modal-fullscreen .modal-content { width: 100vw; height: 100vh; border-radius: 0; }
    .modal-fullscreen .modal-body { overflow-y: auto; padding: 20px; }
    .modal { padding: 0 !important; }

        :root {
            --neon-cyan: #00f3ff;
            --neon-pink: #bc13fe;
            --neon-green: #0aff68;
            --neon-amber: #ffcc00;
            --bg-dark: #05050a;
            --glass-bg: rgba(20, 22, 30, 0.75);
            --glass-border: 1px solid rgba(255, 255, 255, 0.08);
            --text-main: #e0e0e0;
            --text-muted: #8a8a9b;
        }

        body {
            zoom: 100%; 
            background-color: var(--bg-dark);
            background-image: 
                radial-gradient(circle at 15% 15%, rgba(0, 243, 255, 0.08) 0%, transparent 30%),
                radial-gradient(circle at 85% 85%, rgba(188, 19, 254, 0.08) 0%, transparent 30%);
            background-attachment: fixed;
            color: var(--text-main);
            font-family: 'Rajdhani', sans-serif;
            overflow-x: hidden;
            min-height: 100vh;
        }

        h2, h4, h5 { font-weight: 700; letter-spacing: 1px; text-transform: uppercase; }
        .text-neon-cyan { color: var(--neon-cyan); text-shadow: 0 0 10px rgba(0, 243, 255, 0.4); }
        .text-neon-pink { color: var(--neon-pink); text-shadow: 0 0 10px rgba(188, 19, 254, 0.4); }
        .text-muted { color: var(--text-muted) !important; font-weight: 500; }

        .glass-panel {
            background: var(--glass-bg);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: var(--glass-border);
            border-radius: 16px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
            padding: 20px;
            margin-bottom: 20px;
            transition: transform 0.2s ease;
        }

        .video-wrapper {
            position: relative;
            padding: 2px;
            background: linear-gradient(45deg, var(--neon-cyan), transparent 40%, transparent 60%, var(--neon-pink));
            border-radius: 12px;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
        }
        .video-container {
            background: #000;
            border-radius: 10px;
            overflow: hidden;
            aspect-ratio: 4/3;
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .video-container img { width: 100%; height: 100%; object-fit: cover; display: block; }
        
        .upload-placeholder {
            color: var(--neon-green);
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: 4px;
            text-align: center;
            text-shadow: 0 0 15px rgba(10, 255, 104, 0.6);
        }

        .stat-box {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 15px;
            text-align: center;
        }
        .stat-label { font-size: 0.85rem; letter-spacing: 1px; color: var(--text-muted); text-transform: uppercase; margin-bottom: 5px; }
        .stat-value { font-size: 1.8rem; font-weight: 700; color: #fff; font-variant-numeric: tabular-nums; line-height: 1; }
        .stat-unit { font-size: 0.9rem; color: var(--text-muted); font-weight: 400; }

        .btn-cyber {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--neon-cyan);
            color: var(--neon-cyan);
            font-weight: 600;
            letter-spacing: 1px;
            text-transform: uppercase;
            border-radius: 6px;
            transition: all 0.3s ease;
            padding: 8px 16px;
        }
        .btn-cyber:hover {
            background: var(--neon-cyan);
            color: #000;
            box-shadow: 0 0 15px rgba(0, 243, 255, 0.5);
        }
        
        .btn-cyber-danger { border-color: #ff2a2a; color: #ff2a2a; }
        .btn-cyber-danger:hover { background: #ff2a2a; color: #fff; box-shadow: 0 0 15px rgba(255, 42, 42, 0.5); }

        .btn-cyber-warning {
            border: 1px solid var(--neon-amber); color: var(--neon-amber); background: rgba(255, 204, 0, 0.05);
            font-weight: 600; letter-spacing: 1px; text-transform: uppercase; border-radius: 6px; transition: all 0.3s ease;
        }
        .btn-cyber-warning:hover { background: var(--neon-amber); color: #000; box-shadow: 0 0 15px rgba(255, 204, 0, 0.5); }

        .btn-control-pad { width: 100%; height: 45px; font-size: 1.2rem; margin: 3px; }

        .btn-end-session {
            background: linear-gradient(90deg, #ff0055 0%, #ff007f 100%);
            border: none; color: white; font-weight: 600; padding: 5px 20px; height: 38px;
            display: flex; align-items: center; justify-content: center; border-radius: 30px;
            letter-spacing: 1px; text-transform: uppercase; box-shadow: 0 4px 15px rgba(255, 0, 85, 0.4); transition: 0.3s;
        }
        .btn-end-session:hover { transform: scale(1.05); box-shadow: 0 6px 20px rgba(255, 0, 85, 0.6); }

        .form-control, .form-select { background: rgba(0, 0, 0, 0.3); border: 1px solid #444; color: #fff; border-radius: 6px; }
        .form-control:focus, .form-select:focus { background: rgba(0, 0, 0, 0.5); border-color: var(--neon-cyan); color: #fff; box-shadow: 0 0 8px rgba(0, 243, 255, 0.3); }
        .form-check-input:checked { background-color: var(--neon-green); border-color: var(--neon-green); }
        input[type=range] {accent-color: var(--neon-cyan);}

        .modal-content { background: #0f0f15; border: 1px solid #333; color: #fff; }
        .modal-header, .modal-footer { border-color: #222; }
        .control-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; width: 160px; margin: 0 auto; }
    </style>
</head>
<body>

<div class="container-fluid px-4 py-4">
    <div class="row mb-4 align-items-center">
        <div class="col-12 text-center">
            <h2 class="m-0"><span class="text-neon-cyan">PUPIL</span>OMETER <span style="font-weight:300; opacity:0.5;">// PRO</span></h2>
        </div>
    </div>

    <div class="row g-4">
        <div class="col-lg-7">
            <div class="glass-panel p-3">
                <div class="video-wrapper mb-3">
                    <div class="video-container" id="videoContainer">
                        {% if has_video %}
                            <img id="videoStream" src="{{ url_for('video_feed') }}" onerror="reloadStream()" alt="Processing...">
                        {% else %}
                            <div class="upload-placeholder">UPLOAD VIDEO TO START</div>
                        {% endif %}
                    </div>
                </div>
                
                <div class="d-flex justify-content-between align-items-center px-2">
                    <div class="d-flex gap-2">
                        <button class="btn btn-cyber" onclick="videoControl('play')">▶ Play</button>
                        <button class="btn btn-cyber" onclick="videoControl('pause')" style="border-color: #ffcc00; color: #ffcc00;">❚❚ Pause</button>
                    </div>
                    
                    <div class="d-flex align-items-center">
                         <div class="form-check form-switch pt-1 me-5">
                            <input class="form-check-input" type="checkbox" id="filterToggle" checked onchange="toggleFilter(this.checked)">
                            <label class="form-check-label text-muted small" for="filterToggle">ANTI-BLINK</label>
                        </div>
                        
                        <div class="d-flex align-items-center gap-2">
                            <span class="text-muted small">SPEED</span>
                            <select class="form-select form-select-sm" style="width: 80px;" onchange="setSpeed(this.value)">
                                <option value="0.1">0.1x</option>
                                <option value="0.25">0.25x</option>
                                <option value="0.5">0.5x</option>
                                <option value="0.75">0.75x</option>
                                <option value="1.0" selected>1.0x</option>
                                <option value="2.0">2.0x</option>
                            </select>
                        </div>
                    </div>

                    <button class="btn-end-session" onclick="videoControl('end')">Stop & Analyze</button>
                </div>
            </div>

            <div class="glass-panel">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="m-0 text-neon-pink">Region of Interest</h5>
                    <div class="form-check form-switch">
                        <input class="form-check-input" type="checkbox" id="roiToggle" checked onchange="toggleROI(this.checked)">
                        <label class="form-check-label text-white fw-bold" for="roiToggle">Enable ROI Box</label>
                    </div>
                </div>
                
                <div class="row align-items-center">
                    <div class="col-md-6 text-center border-end border-secondary border-opacity-25">
                        <div class="mb-2 text-muted small">POSITION (Arrow Keys)</div>
                        <div class="control-grid">
                            <div></div>
                            <button class="btn btn-cyber btn-control-pad" onclick="move('up')">▲</button>
                            <div></div>
                            
                            <button class="btn btn-cyber btn-control-pad" onclick="move('left')">◀</button>
                            <button class="btn btn-cyber btn-control-pad btn-cyber-danger" onclick="move('reset')">⟲</button>
                            <button class="btn btn-cyber btn-control-pad" onclick="move('right')">▶</button>
                            
                            <div></div>
                            <button class="btn btn-cyber btn-control-pad" onclick="move('down')">▼</button>
                            <div></div>
                        </div>
                    </div>
                    <div class="col-md-6 px-4">
                        <div class="mb-2 text-muted small">DETECTION WINDOW SIZE</div>
                        <input type="range" class="form-range" min="100" max="500" step="10" id="sizeSlider" onchange="resize(this.value)" value="300">
                        <div class="d-flex justify-content-between text-muted small mt-1">
                            <span>Small</span>
                            <span>Large</span>
                        </div>
                        <div class="mt-3 text-muted small text-center">
                            <em>Auto-tracking active. Use arrows to override.</em>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="col-lg-5">
            <div class="glass-panel">
                <div class="row text-center">
                    <div class="col-lg-8 col-8 border-end border-secondary border-opacity-25">
                        <div class="text-muted small mb-1">VIDEO DURATION</div>
                        <div class="h3 mb-0 text-white" id="val_duration">--:--</div>
                    </div>
                    <div class="col-lg-4 col-4">
                        <div class="text-muted small mb-1">PROCESSING TIME</div>
                        <div class="h3 mb-0 text-neon-cyan" id="val_elapsed">00:00</div>
                    </div>
                </div>
            </div>

            <div class="glass-panel">
                <h5 class="mb-3 text-neon-pink">Live Telemetry</h5>
                <div class="row g-2 mb-4">
                    <div class="col-6">
                        <div class="stat-box">
                            <div class="stat-label">Diameter</div>
                            <div class="stat-value" style="color: var(--neon-green);"><span id="val_mm">0.00</span> <span class="stat-unit">mm</span></div>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="stat-box">
                            <div class="stat-label">Raw Width</div>
                            <div class="stat-value"><span id="val_px">0</span> <span class="stat-unit">px</span></div>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="stat-box">
                            <div class="stat-label">Blinks</div>
                            <div class="stat-value" style="color: var(--neon-pink);"><span id="val_blinks">0</span></div>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="stat-box">
                            <div class="stat-label">Framerate</div>
                            <div class="stat-value"><span id="val_fps">0</span> <span class="stat-unit">fps</span></div>
                        </div>
                    </div>
                </div>
                
                <div style="height: 200px; width: 100%;">
                    <canvas id="liveChart"></canvas>
                </div>
            </div>

            <div class="glass-panel">
                <h5 class="mb-3 text-neon-amber">System Calibration</h5>
                <p class="text-muted small" style="line-height: 1.2;">Use a reference object (e.g. coin) to set scale.</p>
                <div class="row g-2 align-items-end">
                    <div class="col-4">
                        <label class="small text-muted">Raw Pixels</label>
                        <input type="number" id="cal_px" class="form-control_sm" placeholder="px">
                    </div>
                    <div class="col-4">
                        <label class="small text-muted">Real MM</label>
                        <input type="number" id="cal_mm" class="form-control_sm" placeholder="mm">
                    </div>
                    <div class="col-4">
                        <button class="btn btn-cyber-warning w-100 btn-sm" onclick="calibrate()">Set Scale</button>
                    </div>
                </div>
                <div class="mt-2 text-center text-muted small">Current Scale: <span id="current_scale" class="text-white fw-bold">18.0</span> px/mm</div>
            </div>

            <div class="glass-panel">
                <h5 class="mb-3">Source Input</h5>
                <form action="/upload" method="post" enctype="multipart/form-data" class="d-flex gap-2">
                    <input type="file" name="file" class="form-control" accept="video/*" required>
                    <button type="submit" class="btn btn-cyber">LOAD</button>
                </form>
            </div>
        </div>
    </div>
</div>

<div class="modal fade" id="resultsModal" tabindex="-1" data-bs-backdrop="static">
    <div class="modal-dialog modal-fullscreen m-0 modal-dialog-scrollable">

        <div class="modal-content">
            <div class="modal-header">
                <h4 class="modal-title text-neon-cyan">SESSION ANALYSIS REPORT</h4>
                <div class="form-check form-switch ms-auto">
                    <input class="form-check-input" type="checkbox" id="showRawToggle" onchange="toggleView()">
                    <label class="form-check-label text-muted small" for="showRawToggle">SHOW NOISY DATA</label>
                </div>
                <button type="button" class="btn-close btn-close-white ms-3" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="row mb-4 g-3">
                    <div class="col-md-3">
                        <div class="stat-box border-secondary">
                            <div class="stat-label">Average Ø</div>
                            <div class="stat-value text-neon-cyan" id="res_avg">0.00</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-box border-secondary">
                            <div class="stat-label">Max Ø</div>
                            <div class="stat-value text-warning" id="res_max">0.00</div>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="stat-box border-secondary">
                            <div class="stat-label">Min Ø</div>
                            <div class="stat-value text-info" id="res_min">0.00</div>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="stat-box border-secondary">
                            <div class="stat-label">Blinks</div>
                            <div class="stat-value text-neon-pink" id="res_blinks">0</div>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="stat-box border-secondary">
                            <div class="stat-label">Frames</div>
                            <div class="stat-value text-white" id="res_frames">0</div>
                        </div>
                    </div>
                </div>

                <div class="row mb-4 g-3 justify-content-center">
                    <div class="col-md-3">
                        <div class="stat-box border-info border-opacity-50">
                            <div class="stat-label">Start Ø (mm)</div>
                            <div class="stat-value" id="res_start">0.00</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-box border-info border-opacity-50">
                            <div class="stat-label">End Ø (mm)</div>
                            <div class="stat-value" id="res_end">0.00</div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="stat-box border-neon-green border-opacity-50">
                            <div class="stat-label">Δ Change (mm)</div>
                            <div class="stat-value text-neon-green" id="res_delta">0.00</div>
                        </div>
                    </div>
                </div>

                <div class="row g-3">
                    <div class="col-md-6">
                        <div class="card bg-dark border-secondary p-3">
                            <h6 class="text-center text-muted mb-3">DIAMETER OVER TIME (MM)</h6>
                            <div style="height: 300px;"><canvas id="mmChart"></canvas></div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card bg-dark border-secondary p-3">
                            <h6 class="text-center text-muted mb-3">PIXEL WIDTH RAW</h6>
                            <div style="height: 300px;"><canvas id="pxChart"></canvas></div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="modal-footer justify-content-center gap-3">
                <a href="/download_csv" class="btn btn-success btn-lg px-4">📥 Download CSV (Full)</a>
                <a href="/repeat_session" class="btn btn-cyber-warning btn-lg px-4">↻ Repeat Session</a>
                <a href="/new_session" class="btn btn-outline-light btn-lg px-4">New Upload</a>
            </div>
        </div>
    </div>
</div>

<script>
    function reloadStream() {
        setTimeout(() => {
            const img = document.getElementById("videoStream");
            if(img) img.src = "{{ url_for('video_feed') }}?t=" + new Date().getTime();
        }, 1000);
    }

    document.addEventListener('keydown', function(event) {
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'SELECT') return;
        if(["ArrowUp","ArrowDown","ArrowLeft","ArrowRight"].includes(event.key)) {
            event.preventDefault();
            const isTurbo = event.shiftKey;
            const dir = event.key.replace('Arrow','').toLowerCase();
            move(dir, isTurbo);
        }
    });

    Chart.defaults.color = '#8a8a9b';
    Chart.defaults.scale.grid.color = 'rgba(255, 255, 255, 0.05)';
    Chart.defaults.font.family = "'Rajdhani', sans-serif";

    const ctx = document.getElementById('liveChart').getContext('2d');
    const liveChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array(50).fill(''),
            datasets: [{ 
                label: 'Dia (mm)', 
                data: Array(50).fill(0), 
                borderColor: '#0aff68', 
                backgroundColor: 'rgba(10, 255, 104, 0.1)', 
                borderWidth: 2, 
                tension: 0.2, 
                pointRadius: 0, 
                fill: true 
            }]
        },
        options: { 
            animation: false, responsive: true, maintainAspectRatio: false,
            scales: { y: { beginAtZero: true, grid: { display: true } }, x: { display: false } }, 
            plugins: { legend: { display: false } } 
        }
    });

    function move(direction, isTurbo=false) { 
        document.getElementById('roiToggle').checked = true;
        fetch(`/control/move/${direction}?turbo=${isTurbo}&t=${Date.now()}`); 
    }
    function resize(val) { 
        document.getElementById('roiToggle').checked = true;
        fetch('/control/resize/' + val + '?t=' + Date.now()); 
    }
    function videoControl(action) { fetch('/control/video/' + action + '?t=' + Date.now()); }
    function setSpeed(val) { fetch('/control/speed/' + val + '?t=' + Date.now()); }
    function toggleFilter(isActive) { fetch('/control/filter/' + (isActive ? 'on' : 'off')); }
    function toggleROI(isActive) { fetch('/control/roi_visibility/' + (isActive ? 'on' : 'off')); }

    function calibrate() {
        const px = document.getElementById('cal_px').value;
        const mm = document.getElementById('cal_mm').value;
        if(px && mm) {
            fetch(`/control/calibrate?px=${px}&mm=${mm}`)
                .then(res => res.json())
                .then(data => {
                    document.getElementById('current_scale').innerText = data.new_scale.toFixed(1);
                    alert("Calibration Updated!");
                });
        }
    }

    let sessionEnded = false;
    let finalData = null;
    let mainChart = null;
    let pxChart = null;
    const resultModal = new bootstrap.Modal(document.getElementById('resultsModal'));

    function formatTime(seconds) {
        if(isNaN(seconds)) return "00:00";
        const m = Math.floor(seconds / 60).toString().padStart(2,'0');
        const s = Math.floor(seconds % 60).toString().padStart(2,'0');
        return `${m}:${s}`;
    }

    setInterval(() => {
        if(sessionEnded) return;
        fetch('/data')
            .then(response => response.json())
            .then(data => {
                document.getElementById('val_mm').innerText = data.diameter_mm.toFixed(2);
                document.getElementById('val_px').innerText = data.diameter_px;
                document.getElementById('val_blinks').innerText = data.blinks;
                document.getElementById('val_fps').innerText = data.fps;
                document.getElementById('val_duration').innerText = data.total_duration;
                document.getElementById('val_elapsed').innerText = formatTime(data.elapsed_time);

                if (!data.paused && !data.ended) {
                    const chartData = liveChart.data.datasets[0].data;
                    chartData.push(data.diameter_mm);
                    chartData.shift();
                    liveChart.update();
                }

                if(data.ended) {
                    sessionEnded = true;
                    showResults();
                }
            });
    }, 100);

    function showResults() {
        fetch('/full_history')
            .then(response => response.json())
            .then(data => {
                finalData = data; 
                
                // Set the Stats
                document.getElementById('res_frames').innerText = data.stats.count;
                document.getElementById('res_blinks').innerText = data.stats.blinks;
                document.getElementById('res_avg').innerText = data.stats.avg.toFixed(2) + ' mm';
                document.getElementById('res_max').innerText = data.stats.max.toFixed(2) + ' mm';
                document.getElementById('res_min').innerText = data.stats.min.toFixed(2) + ' mm';
                
                // Set the Comparison Stats
                document.getElementById('res_start').innerText = data.comparison.start_mm.toFixed(2);
                document.getElementById('res_end').innerText = data.comparison.end_mm.toFixed(2);
                const delta = data.comparison.delta_mm;
                document.getElementById('res_delta').innerText = (delta >= 0 ? "+" : "") + delta.toFixed(2);
                
                resultModal.show();
                toggleView(); 
            });
    }

    function toggleView() {
        if(!finalData) return;
        const isRaw = document.getElementById('showRawToggle').checked;
        renderCharts(isRaw);
    }

    function renderCharts(isRaw) {
        const mmData = isRaw ? finalData.raw_mm : finalData.interp_mm;
        const mmLabel = isRaw ? 'Raw Dia (mm)' : 'Smooth Dia (mm)';
        const mmColor = isRaw ? '#ffcc00' : '#00f3ff';
        
        const mmCtx = document.getElementById('mmChart').getContext('2d');
        if(mainChart) mainChart.destroy();
        mainChart = new Chart(mmCtx, {
            type: 'line',
            data: { labels: finalData.indices, datasets: [{ label: mmLabel, data: mmData, borderColor: mmColor, borderWidth: 1.5, pointRadius: 0, tension: 0.1 }] },
            options: getChartOptions()
        });

        const pxCtx = document.getElementById('pxChart').getContext('2d');
        if(pxChart) pxChart.destroy();
        const pxData = isRaw ? finalData.px : finalData.interp_px;
        pxChart = new Chart(pxCtx, {
            type: 'line',
            data: { labels: finalData.indices, datasets: [{ label: isRaw ? 'Raw Dia (px)' : 'Smooth Dia (px)', data: pxData, borderColor: '#bc13fe', borderWidth: 1.5, pointRadius: 0, tension: 0.1 }] },
            options: getChartOptions()
        });
    }

    function getChartOptions() {
        return { animation: false, responsive: true, maintainAspectRatio: false, scales: { x: { display: true, grid: { color: '#333' } }, y: { grid: { color: '#333' } } }, plugins: { legend: { display: true } } };
    }
</script>
</body>
</html>
"""

# ==========================================
# 2. BACKEND LOGIC (IMPROVED ALGORITHMS)
# ==========================================
app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

APP_SETTINGS = {
    "pixels_per_mm": 18.0,
    "filter_on": True,
    "max_jump_mm": 2.0
}

roi_state = { "x": 170, "y": 90, "size": 300, "manual_override": True, "visible": True, "last_manual_time": 0 }
playback_state = { "paused": True, "ended": False, "speed": 1.0, "reset": False, "start_time": 0 }
current_data = { 
    "diameter_mm": 0, "diameter_px": 0, "fps": 0, "blinks": 0,
    "ended": False, "paused": True, "elapsed_time": 0, "total_duration": "--:--" 
}
full_history = { "mm": [], "raw_mm": [], "px": [], "indices": [] }
video_meta = {"duration_sec": 0, "duration_str": "--:--"}

# --- ADVANCED DETECTION FUNCTIONS (FROM STANDALONE SCRIPT) ---

def apply_binary_threshold(image, darkestPixelValue, addedThreshold):
    threshold = darkestPixelValue + addedThreshold
    _, thresholded_image = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY_INV)
    return thresholded_image

def get_darkest_area(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    box_size = 15
    avg_intensities = cv2.boxFilter(gray, -1, (box_size, box_size))
    ignoreBounds = 10
    mask = np.zeros_like(avg_intensities, dtype=np.uint8)
    mask[ignoreBounds:-ignoreBounds, ignoreBounds:-ignoreBounds] = 255
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(avg_intensities, mask=mask)
    return min_loc

def mask_outside_square(image, center, size):
    x, y = center
    half_size = size // 2
    mask = np.zeros_like(image)
    top_left_x = max(0, x - half_size)
    top_left_y = max(0, y - half_size)
    bottom_right_x = min(image.shape[1], x + half_size)
    bottom_right_y = min(image.shape[0], y + half_size)
    mask[top_left_y:bottom_right_y, top_left_x:bottom_right_x] = 255
    masked_image = cv2.bitwise_and(image, mask)
    return masked_image
    
def optimize_contours_by_angle(contours, image):
    if len(contours) < 1:
        return contours
    all_contours = np.concatenate(contours[0], axis=0)
    spacing = int(len(all_contours)/25) 
    if spacing < 1: spacing = 1 
    filtered_points = []
    centroid = np.mean(all_contours, axis=0)
    for i in range(0, len(all_contours), 1):
        current_point = all_contours[i]
        prev_point = all_contours[i - spacing] if i - spacing >= 0 else all_contours[-spacing]
        next_point = all_contours[i + spacing] if i + spacing < len(all_contours) else all_contours[spacing]
        vec1 = prev_point - current_point
        vec2 = next_point - current_point
        with np.errstate(invalid='ignore'):
            dot_prod = np.dot(vec1, vec2)
            norms = np.linalg.norm(vec1) * np.linalg.norm(vec2)
            if norms == 0: continue
            angle = np.arccos(dot_prod / norms)
        vec_to_centroid = centroid - current_point
        cos_threshold = np.cos(np.radians(60)) 
        if np.dot(vec_to_centroid, (vec1+vec2)/2) >= cos_threshold:
            filtered_points.append(current_point)
    return np.array(filtered_points, dtype=np.int32).reshape((-1, 1, 2))

def filter_contours_by_area_and_return_largest(contours, pixel_thresh, ratio_thresh):
    max_area = 0
    largest_contour = None
    for contour in contours:
        area = cv2.contourArea(contour)
        if area >= pixel_thresh:
            x, y, w, h = cv2.boundingRect(contour)
            if w == 0 or h == 0: continue
            length = max(w, h)
            width = min(w, h)
            if width == 0: continue
            length_to_width_ratio = length / width
            width_to_length_ratio = width / length
            current_ratio = max(length_to_width_ratio, width_to_length_ratio)
            if current_ratio <= ratio_thresh:
                if area > max_area:
                    max_area = area
                    largest_contour = contour
    if largest_contour is not None:
        return [largest_contour]
    else:
        return []

def check_contour_pixels(contour, image_shape):
    if len(contour) < 5:
        return [0, 0, 0] 
    contour_mask = np.zeros(image_shape, dtype=np.uint8)
    cv2.drawContours(contour_mask, [contour], -1, (255), 1)
    ellipse_mask_thick = np.zeros(image_shape, dtype=np.uint8)
    ellipse_mask_thin = np.zeros(image_shape, dtype=np.uint8)
    ellipse = cv2.fitEllipse(contour)
    cv2.ellipse(ellipse_mask_thick, ellipse, (255), 10) 
    cv2.ellipse(ellipse_mask_thin, ellipse, (255), 4) 
    overlap_thick = cv2.bitwise_and(contour_mask, ellipse_mask_thick)
    overlap_thin = cv2.bitwise_and(contour_mask, ellipse_mask_thin)
    absolute_pixel_total_thick = np.sum(overlap_thick > 0)
    # absolute_pixel_total_thin = np.sum(overlap_thin > 0)
    total_border_pixels = np.sum(contour_mask > 0)
    ratio_under_ellipse = absolute_pixel_total_thick / total_border_pixels if total_border_pixels > 0 else 0
    return [absolute_pixel_total_thick, ratio_under_ellipse]

def check_ellipse_goodness(binary_image, contour):
    ellipse_goodness = [0,0,0] 
    if len(contour) < 5:
        return 0 
    ellipse = cv2.fitEllipse(contour)
    mask = np.zeros_like(binary_image)
    cv2.ellipse(mask, ellipse, (255), -1)
    ellipse_area = np.sum(mask == 255)
    covered_pixels = np.sum((binary_image == 255) & (mask == 255))
    if ellipse_area == 0:
        return ellipse_goodness 
    ellipse_goodness[0] = covered_pixels / ellipse_area
    ellipse_goodness[2] = min(ellipse[1][1]/ellipse[1][0], ellipse[1][0]/ellipse[1][1])
    return ellipse_goodness

def detect_pupil_contour(thresholded_image_strict, thresholded_image_medium, thresholded_image_relaxed, roi_frame, gray_frame):
    final_rotated_rect = ((0,0),(0,0),0)
    image_array = [thresholded_image_relaxed, thresholded_image_medium, thresholded_image_strict] 
    final_contours = [] 
    goodness = 0 
    kernel = np.ones((5, 5), np.uint8)
    
    for i in range(1,4):
        dilated_image = cv2.dilate(image_array[i-1], kernel, iterations=2)
        contours, hierarchy = cv2.findContours(dilated_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        reduced_contours = filter_contours_by_area_and_return_largest(contours, 200, 3)

        if len(reduced_contours) > 0 and len(reduced_contours[0]) > 5:
            current_goodness = check_ellipse_goodness(dilated_image, reduced_contours[0])
            total_pixels = check_contour_pixels(reduced_contours[0], dilated_image.shape)
            
            # Simple weighting for scoring
            final_goodness = current_goodness[0] * total_pixels[0] * total_pixels[0] * total_pixels[1]

            if final_goodness > 0 and final_goodness > goodness: 
                goodness = final_goodness
                final_contours = reduced_contours
    
    # Refine result using angle optimization
    final_contours = [optimize_contours_by_angle(final_contours, gray_frame)]
    
    if final_contours and not isinstance(final_contours[0], list) and len(final_contours[0]) > 5:
        try:
            ellipse = cv2.fitEllipse(final_contours[0])
            final_rotated_rect = ellipse
        except:
            pass
            
    return final_rotated_rect

# --- END DETECTION FUNCTIONS ---

class SignalFilter:
    def __init__(self):
        self.last_valid_mm = 0.0
        self.last_valid_px = 0.0
        self.in_blink = False
    
    def process(self, raw_mm, raw_px):
        # Blink if eye closed OR pupil < 2 mm
        if raw_mm <= 0.1 or raw_mm < 1.0:
            if not self.in_blink:
                self.in_blink = True
                current_data['blinks'] += 1
            return self.last_valid_mm, self.last_valid_px
        
        self.in_blink = False
            
        if not APP_SETTINGS["filter_on"]:
            self.last_valid_mm = raw_mm
            self.last_valid_px = raw_px
            return raw_mm, raw_px

        if self.last_valid_mm > 0:
            diff = abs(raw_mm - self.last_valid_mm)
            if diff > APP_SETTINGS["max_jump_mm"]:
                return self.last_valid_mm, self.last_valid_px

        self.last_valid_mm = raw_mm
        self.last_valid_px = raw_px
        return raw_mm, raw_px

    def reset(self):
        self.last_valid_mm = 0.0
        self.last_valid_px = 0.0
        self.in_blink = False
        current_data['blinks'] = 0

signal_filter = SignalFilter()

class BackgroundProcessor:
    def __init__(self, source):
        self.source = source
        self.video = cv2.VideoCapture(self.source)
        self.lock = threading.Lock()
        self.jpeg = None
        self.stopped = False
        self.prev_frame_time = 0
        self.cached_frame = None 
        
        if self.video.isOpened():
            fps = self.video.get(cv2.CAP_PROP_FPS)
            frame_count = self.video.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = frame_count / fps if fps > 0 else 0
            m = int(duration // 60)
            s = int(duration % 60)
            video_meta["duration_sec"] = duration
            video_meta["duration_str"] = f"{m:02d}:{s:02d}"
            current_data["total_duration"] = video_meta["duration_str"]
            
            success, frame = self.video.read()
            if success:
                self.cached_frame = frame 
                self.process_frame(frame)
                self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)

        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()

    def update(self):
        while not self.stopped:
            if playback_state.get('reset', False):
                self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                playback_state.update({'reset': False, 'paused': True, 'ended': False, 'start_time': 0})
                current_data.update({'ended': False, 'elapsed_time': 0})
                signal_filter.reset()
                success, frame = self.video.read()
                if success: 
                    self.cached_frame = frame
                    self.process_frame(frame)
                    self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            if playback_state['paused']:
                if self.cached_frame is not None:
                    self.process_frame(self.cached_frame.copy(), is_paused=True)
                time.sleep(0.05)
                continue
            
            if playback_state['ended']:
                time.sleep(0.1)
                continue

            if playback_state['start_time'] == 0:
                playback_state['start_time'] = time.time()
            current_data['elapsed_time'] = time.time() - playback_state['start_time']

            speed = playback_state['speed']
            if speed < 1.0: time.sleep(0.03 * (1/speed))
            
            success, frame = self.video.read()
            if not success:
                playback_state['ended'] = True
                current_data['ended'] = True
                continue
            
            self.cached_frame = frame 
            self.process_frame(frame)

    def process_frame(self, frame, is_paused=False):
        frame_resized = crop_to_aspect_ratio(frame)
        if frame_resized is None: return

        if not is_paused:
            new_frame_time = time.time()
            time_diff = new_frame_time - self.prev_frame_time
            fps = 1 / time_diff if (self.prev_frame_time > 0 and time_diff > 0) else 0
            self.prev_frame_time = new_frame_time
        else:
            fps = 0
        
        h, w = frame_resized.shape[:2]
        roi_size = roi_state['size']
        
        # Clamp ROI to frame boundaries
        roi_state['x'] = max(0, min(roi_state['x'], w - roi_size))
        roi_state['y'] = max(0, min(roi_state['y'], h - roi_size))

        if roi_state['visible']:
            roi_x, roi_y, roi_w, roi_h = roi_state['x'], roi_state['y'], roi_size, roi_size
        else:
            roi_x, roi_y, roi_w, roi_h = 0, 0, w, h
        
        roi_frame = frame_resized[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
        
        final_mm = 0.0
        final_px = 0.0
        raw_mm = 0.0
        
        if roi_frame.size != 0:
            try:
                # --- NEW ROBUST DETECTION PIPELINE ---
                darkest_point = get_darkest_area(roi_frame)
                gray_frame = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
                darkest_pixel_value = gray_frame[darkest_point[1], darkest_point[0]]
                
                # Create 3 threshold variants
                t_strict = apply_binary_threshold(gray_frame, darkest_pixel_value, 5)
                t_strict = mask_outside_square(t_strict, darkest_point, 250)
                
                t_medium = apply_binary_threshold(gray_frame, darkest_pixel_value, 15)
                t_medium = mask_outside_square(t_medium, darkest_point, 250)
                
                t_relaxed = apply_binary_threshold(gray_frame, darkest_pixel_value, 25)
                t_relaxed = mask_outside_square(t_relaxed, darkest_point, 250)
                
                # Get optimized ellipse
                pupil_rect = detect_pupil_contour(t_strict, t_medium, t_relaxed, roi_frame, gray_frame)
                
                raw_px = 0.0
                if pupil_rect[1][0] > 0 and pupil_rect[1][1] > 0:
                    raw_px = (pupil_rect[1][0] + pupil_rect[1][1]) / 2
                    local_center = pupil_rect[0]
                    global_x = local_center[0] + roi_x
                    global_y = local_center[1] + roi_y
                    
                    # --- AUTO-TRACKING / ROI RECENTERING ---
                    # Check if manual override is active (2 second delay)
                    if time.time() - roi_state['last_manual_time'] > 2.0 and roi_state['visible']:
                        roi_center_x = roi_x + (roi_w // 2)
                        roi_center_y = roi_y + (roi_h // 2)
                        
                        diff_x = global_x - roi_center_x
                        diff_y = global_y - roi_center_y
                        
                        # Apply deadzone (15px) and smoothing factor (0.1)
                        if abs(diff_x) > 15 or abs(diff_y) > 15:
                            roi_state['x'] += int(diff_x * 0.1)
                            roi_state['y'] += int(diff_y * 0.1)
                            # Ensure we don't drift out of bounds
                            roi_state['x'] = max(0, min(roi_state['x'], w - roi_size))
                            roi_state['y'] = max(0, min(roi_state['y'], h - roi_size))
                    # ----------------------------------------
                    
                    global_rect = ((global_x, global_y), pupil_rect[1], pupil_rect[2])
                    cv2.ellipse(frame_resized, global_rect, (0, 255, 255), 2)
                    cv2.circle(frame_resized, (int(global_x), int(global_y)), 3, (0, 0, 255), -1)

                if roi_state['visible']:
                    cv2.rectangle(frame_resized, (roi_x, roi_y), (roi_x + roi_w, roi_y + roi_h), (0, 255, 0), 2)
                
                raw_mm = raw_px / APP_SETTINGS["pixels_per_mm"]
                final_mm, final_px = signal_filter.process(raw_mm, raw_px)
                
                text_str = f"{final_mm:.2f} mm"
                cv2.putText(frame_resized, text_str, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                current_data['diameter_mm'] = round(final_mm, 2)
                current_data['diameter_px'] = round(final_px, 1)
                current_data['fps'] = int(fps)
                current_data['paused'] = is_paused

                if not is_paused:
                    full_history['mm'].append(round(final_mm, 2))
                    full_history['raw_mm'].append(round(raw_mm, 2))
                    full_history['px'].append(round(final_px, 1))
                    full_history['indices'].append(len(full_history['indices']))
            except: 
                pass

        ret, encoded_img = cv2.imencode('.jpg', frame_resized)
        if ret:
            with self.lock: self.jpeg = encoded_img.tobytes()

    def get_jpeg(self):
        with self.lock: return self.jpeg

def crop_to_aspect_ratio(image, width=640, height=480):
    if image is None: return None
    h, w = image.shape[:2]
    r = width / height
    if w/h > r:
        nw = int(r * h)
        off = (w - nw) // 2
        cropped = image[:, off:off+nw]
    else:
        nh = int(w / r)
        off = (h - nh) // 2
        cropped = image[off:off+nh, :]
    return cv2.resize(cropped, (width, height))


@app.route('/')
def index(): 
    has_video = ('processor' in globals() and processor is not None)
    return render_template_string(HTML_TEMPLATE, has_video=has_video)

@app.route('/upload', methods=['POST'])
def upload_file():
    global processor
    file = request.files['file']
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
        file.save(filepath)
        playback_state['reset'] = True
        full_history.update({"mm":[], "raw_mm":[], "px":[], "indices":[]})
        if 'processor' in globals() and processor: processor.stopped = True
        processor = BackgroundProcessor(filepath)
    return redirect(url_for('index'))

@app.route('/video_feed')
def video_feed():
    def gen():
        while True:
            if 'processor' in globals() and processor:
                frame = processor.get_jpeg()
                if frame: yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
            time.sleep(0.05)
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/data')
def data(): return jsonify(current_data)

@app.route('/full_history')
def get_full_history(): 
    raw_mm = np.array(full_history['raw_mm'])
    indices = np.array(full_history['indices'])
    
    valid_mask = raw_mm > 0.1
    if not any(valid_mask):
        return jsonify({"indices": [], "stats": {"avg":0, "max":0, "min":0, "blinks": 0}})
        
    clean_indices = indices[valid_mask]
    clean_mm = raw_mm[valid_mask]
    interp_mm = np.interp(indices, clean_indices, clean_mm).tolist()
    
    start_val = np.mean(clean_mm[:10]) if len(clean_mm) > 0 else 0
    end_val = np.mean(clean_mm[-10:]) if len(clean_mm) > 0 else 0

    stats = {
        "avg": np.mean(interp_mm), 
        "max": np.max(interp_mm), 
        "min": np.min(clean_mm), 
        "count": len(interp_mm),
        "blinks": current_data['blinks']
    }
    
    comparison = {
        "start_mm": float(start_val),
        "end_mm": float(end_val),
        "delta_mm": float(end_val - start_val)
    }
    
    return jsonify({
        "indices": full_history['indices'], "px": full_history['px'],
        "interp_px": [round(x * APP_SETTINGS["pixels_per_mm"], 1) for x in interp_mm],
        "raw_mm": full_history['raw_mm'], "interp_mm": interp_mm,
        "stats": stats, 
        "comparison": comparison
    })

@app.route('/control/move/<direction>')
def move_roi(direction):
    step = 50 if request.args.get('turbo') == 'true' else 20
    if direction == 'up': roi_state['y'] -= step
    elif direction == 'down': roi_state['y'] += step
    elif direction == 'left': roi_state['x'] -= step
    elif direction == 'right': roi_state['x'] += step
    elif direction == 'reset': roi_state.update({'x': 170, 'y': 90})
    roi_state['last_manual_time'] = time.time()
    return "OK"

@app.route('/control/video/<action>')
def video_control(action):
    if action == 'play': playback_state['paused'] = False
    elif action == 'pause': playback_state['paused'] = True
    elif action == 'end': playback_state['ended'] = True; current_data['ended'] = True
    return "OK"

@app.route('/control/calibrate')
def calibrate_route():
    px = request.args.get('px', type=float)
    mm = request.args.get('mm', type=float)
    if px and mm: APP_SETTINGS["pixels_per_mm"] = px/mm
    return jsonify({"new_scale": APP_SETTINGS["pixels_per_mm"]})

@app.route('/control/resize/<size>')
def resize_roi(size): roi_state['size'] = int(size); roi_state['last_manual_time'] = time.time(); return "OK"

@app.route('/control/filter/<state>')
def toggle_filter(state): APP_SETTINGS["filter_on"] = (state == 'on'); return "OK"

@app.route('/control/roi_visibility/<state>')
def toggle_roi_v(state): roi_state['visible'] = (state == 'on'); return "OK"

@app.route('/control/speed/<float:val>')
def set_speed(val): playback_state['speed'] = val; return "OK"

@app.route('/download_csv')
def download_csv():
    raw_mm = np.array(full_history['raw_mm'])
    indices = np.array(full_history['indices'])
    valid_mask = raw_mm > 0.1
    if not any(valid_mask): return "No data", 400
    
    clean_mm = raw_mm[valid_mask]
    interp_mm = np.interp(indices, indices[valid_mask], clean_mm)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Frame Index', 'Raw (mm)', 'Smooth (mm)', 'Pixels'])
    for i in range(len(indices)):
        writer.writerow([indices[i], full_history['raw_mm'][i], round(interp_mm[i], 2), full_history['px'][i]])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='pupil_data.csv')

@app.route('/repeat_session')
def repeat_session():
    playback_state['reset'] = True
    return redirect('/')

@app.route('/new_session')
def new_session():
    global processor
    try:
        if 'processor' in globals() and processor:
            processor.stopped = True
    except:
        pass

    processor = None

    full_history.update({"mm": [], "raw_mm": [], "px": [], "indices": []})
    current_data.update({
        "diameter_mm": 0, "diameter_px": 0, "fps": 0, "blinks": 0,
        "ended": False, "paused": True, "elapsed_time": 0, "total_duration": "--:--"
    })
    playback_state.update({"paused": True, "ended": False, "reset": False, "start_time": 0})

    return redirect(url_for('index'))


if __name__ == '__main__':
    processor = None
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
