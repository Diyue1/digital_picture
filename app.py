import sys
import os
import cv2
import numpy as np
import base64
import time
import datetime
import threading
import csv
import shutil
from collections import deque
from flask import Flask, render_template_string, jsonify, send_file, request
from flask_socketio import SocketIO, emit
import io

# =========================================================
# HTML 模板 (修复了 JS 初始化顺序和安全性)
# =========================================================
HTML_TEMPLATE = r'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="shortcut icon" href="data:;"> 
    <title>AETHER // 视觉追踪系统 v4.1 (Stable)</title>
    <script src="https://cdn.bootcdn.net/ajax/libs/socket.io/4.0.1/socket.io.min.js"></script>
    <script src="https://cdn.bootcdn.net/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.bootcdn.net/ajax/libs/Chart.js/3.7.0/chart.min.js"></script>
    <link href="https://cdn.bootcdn.net/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root { 
            --bg: #0a0a12; --panel: rgba(15, 20, 30, 0.95); --accent: #00f3ff; 
            --accent-dim: rgba(0, 243, 255, 0.3); --success: #00ff88;
            --warning: #ffaa00; --danger: #ff2255; --text: #e0f7ff; --text-dim: #667788;
        }
        * { box-sizing: border-box; }
        body { margin: 0; background: linear-gradient(135deg, #0a0a12 0%, #0d1520 100%);
            color: var(--text); font-family: 'Segoe UI', 'Microsoft YaHei', monospace; overflow: hidden; }
        .main-grid { display: grid; grid-template-columns: 220px 1fr 360px; 
            grid-template-rows: 1fr 180px; height: 100vh; gap: 6px; padding: 6px; }
        .panel { background: var(--panel); border: 1px solid var(--accent-dim); border-radius: 6px; 
            position: relative; overflow: hidden; backdrop-filter: blur(10px); }
        .panel-header { background: linear-gradient(90deg, rgba(0, 243, 255, 0.15), transparent);
            color: var(--accent); padding: 10px 12px; font-size: 11px; letter-spacing: 2px; 
            font-weight: bold; border-bottom: 1px solid var(--accent-dim); text-transform: uppercase;
            display: flex; align-items: center; gap: 8px; }
        .panel-content { padding: 10px; height: calc(100% - 38px); overflow-y: auto; }
        #control-panel { grid-column: 1; grid-row: 1 / span 2; }
        .control-section { margin-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 10px; }
        .control-section:last-child { border-bottom: none; }
        .control-section h4 { color: var(--text-dim); font-size: 10px; letter-spacing: 1px; 
            margin: 0 0 8px 0; text-transform: uppercase; }
        .btn { width: 100%; padding: 8px; margin-bottom: 6px; background: rgba(0, 243, 255, 0.08); 
            border: 1px solid var(--accent-dim); color: var(--accent); border-radius: 4px; 
            cursor: pointer; font-size: 11px; font-weight: bold; letter-spacing: 1px;
            transition: all 0.2s; display: flex; align-items: center; justify-content: center; gap: 6px; }
        .btn:hover { background: var(--accent); color: #000; }
        .btn-danger { border-color: var(--danger); color: var(--danger); background: rgba(255,34,85,0.08); }
        .btn-danger:hover { background: var(--danger); color: #fff; }
        .btn-success { border-color: var(--success); color: var(--success); background: rgba(0,255,136,0.08); }
        .btn-success:hover { background: var(--success); color: #000; }
        .btn-purple { border-color: #a855f7; color: #a855f7; background: rgba(168,85,247,0.08); }
        .btn-purple:hover { background: #a855f7; color: #fff; }
        .btn .key { font-size: 9px; opacity: 0.6; margin-left: auto; }
        .toggle-group { display: flex; flex-direction: column; gap: 6px; }
        .toggle-item { display: flex; align-items: center; justify-content: space-between;
            padding: 6px 8px; background: rgba(0,0,0,0.3); border-radius: 4px; font-size: 10px; }
        .toggle-switch { width: 32px; height: 16px; background: #333; border-radius: 8px;
            position: relative; cursor: pointer; transition: background 0.3s; }
        .toggle-switch.active { background: var(--accent); }
        .toggle-switch::after { content: ''; position: absolute; width: 12px; height: 12px;
            background: #fff; border-radius: 50%; top: 2px; left: 2px; transition: left 0.3s; }
        .toggle-switch.active::after { left: 18px; }
        .select-box { width: 100%; padding: 6px; background: rgba(0,0,0,0.4);
            border: 1px solid var(--accent-dim); color: var(--text); border-radius: 4px; font-size: 10px; margin-bottom: 5px;}
        .select-box option { background: #1a1a2e; }
        #video-panel { grid-column: 2; grid-row: 1; display: flex; flex-direction: column; }
        #video-container { flex: 1; display: flex; justify-content: center; align-items: center; 
            background: #000; position: relative; cursor: crosshair; overflow: hidden; user-select: none; }
        #video-img { width: 100%; height: 100%; object-fit: contain; pointer-events: none; -webkit-user-drag: none; }
        #selection-layer { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 5; }
        #particle-layer { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 4; }
        #select-hint { position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.8);
            padding: 8px 16px; border-radius: 4px; font-size: 11px; color: var(--accent); pointer-events: none; z-index: 15;
            border: 1px solid var(--accent-dim); opacity: 0.9; }
        #select-hint.hidden { display: none; }
        #hud-overlay { position: absolute; top: 8px; left: 8px; right: 8px; display: flex;
            justify-content: space-between; pointer-events: none; z-index: 10; }
        .hud-item { background: rgba(0,0,0,0.75); padding: 5px 10px; border: 1px solid var(--accent-dim);
            border-radius: 3px; font-size: 10px; font-family: 'Consolas', monospace; }
        .hud-rec { color: var(--danger); animation: blink 1s infinite; }
        @keyframes blink { 50% { opacity: 0.5; } }
        #telemetry-panel { grid-column: 3; grid-row: 1; }
        .metric-card { background: rgba(0,0,0,0.3); border-radius: 5px; padding: 10px;
            margin-bottom: 8px; border-left: 3px solid var(--accent); }
        .metric-label { font-size: 9px; color: var(--text-dim); letter-spacing: 1px; margin-bottom: 3px; }
        .metric-value { font-size: 20px; font-weight: bold; color: var(--accent); font-family: 'Consolas'; }
        .metric-unit { font-size: 10px; color: var(--text-dim); margin-left: 2px; }
        .metric-value.danger { color: var(--danger); }
        .gauge-container { display: flex; gap: 8px; margin-bottom: 10px; }
        .gauge { flex: 1; text-align: center; padding: 8px; background: rgba(0,0,0,0.3); border-radius: 5px; }
        .gauge canvas { width: 70px !important; height: 70px !important; }
        .gauge-label { font-size: 8px; color: var(--text-dim); margin-top: 4px; }
        .state-badge { display: inline-block; padding: 4px 10px; border-radius: 4px;
            font-size: 10px; font-weight: bold; letter-spacing: 1px; }
        .state-idle { background: rgba(100,100,100,0.3); color: #888; }
        .state-patrol { background: rgba(0,255,136,0.2); color: var(--success); }
        .state-alert { background: rgba(255,170,0,0.2); color: var(--warning); }
        .state-danger { background: rgba(255,34,85,0.2); color: var(--danger); }
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 8px; }
        .stat-item { background: rgba(0,0,0,0.25); padding: 8px; border-radius: 4px; text-align: center; }
        .stat-label { font-size: 8px; color: var(--text-dim); margin-bottom: 2px; }
        .stat-value { font-size: 14px; font-weight: bold; color: var(--text); font-family: 'Consolas'; }
        #data-panel { grid-column: 2 / span 2; grid-row: 2; display: flex; gap: 6px; }
        #chart-box { flex: 2; display: flex; flex-direction: column; }
        #chart-container { flex: 1; position: relative; }
        #three-panel { flex: 1; display: flex; flex-direction: column; max-width: 320px; }
        #three-container { flex: 1; min-height: 120px; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: rgba(0,0,0,0.3); }
        ::-webkit-scrollbar-thumb { background: var(--accent-dim); border-radius: 3px; }
        #toast { position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%) translateY(100px);
            background: var(--panel); border: 1px solid var(--accent); padding: 10px 20px;
            border-radius: 6px; font-size: 11px; z-index: 1001; transition: transform 0.3s ease; }
        #toast.show { transform: translateX(-50%) translateY(0); }
        .screenshot-flash { position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: #fff; opacity: 0; pointer-events: none; z-index: 9999; }
        .screenshot-flash.active { animation: flash 0.3s ease-out; }
        @keyframes flash { 0% { opacity: 0.8; } 100% { opacity: 0; } }
    </style>
</head>
<body>
{% raw %}
<div class="screenshot-flash" id="screenshot-flash"></div>
<div id="toast"></div>
<div class="main-grid">
    <div class="panel" id="control-panel">
        <div class="panel-header"><i class="fas fa-sliders-h"></i> 控制台</div>
        <div class="panel-content">
            <div class="control-section">
                <h4><i class="fas fa-file-video"></i> 视频输入源</h4>
                <input type="file" id="video-upload" accept="video/*" style="display:none">
                <button class="btn" onclick="document.getElementById('video-upload').click()">
                    <i class="fas fa-upload"></i> 选择视频文件 <span class="key">[U]</span>
                </button>
                <button class="btn btn-purple" id="btn-camera" style="margin-top:5px;">
                    <i class="fas fa-camera"></i> 切换至摄像头
                </button>
                <div id="upload-status" style="font-size:10px;color:var(--text-dim);margin-top:6px;text-align:center;">
                    当前: 默认源
                </div>
            </div>

            <div class="control-section">
                <h4>图像源与处理</h4>
                <select class="select-box" id="view-mode-select">
                    <option value="original">原始图像 (Original)</option>
                    <option value="preprocessed">预处理图像 (Preprocessed)</option>
                    <option value="mask">运动掩膜 (Binary Mask)</option>
                </select>
                <div class="toggle-item"><span>图像预处理</span><div class="toggle-switch active" id="toggle-preprocess"></div></div>
                <button class="btn btn-purple" id="btn-auto-detect" style="margin-top:5px;"><i class="fas fa-magic"></i> 智能自动检测 <span class="key">[A]</span></button>
            </div>

            <div class="control-section">
                <h4>追踪控制</h4>
                <button class="btn" id="btn-pause"><i class="fas fa-pause"></i> 暂停 <span class="key">[SPACE]</span></button>
                <button class="btn btn-danger" id="btn-reset"><i class="fas fa-redo"></i> 重置 <span class="key">[R]</span></button>
                <button class="btn btn-success" id="btn-export"><i class="fas fa-download"></i> 导出数据 <span class="key">[E]</span></button>
            </div>

            <div class="control-section">
                <h4>可视化与音效 (创新点)</h4>
                <div class="toggle-group">
                    <div class="toggle-item"><span>卡尔曼滤波 [K]</span><div class="toggle-switch active" id="toggle-kalman"></div></div>
                    <div class="toggle-item"><span>粒子特效 [P]</span><div class="toggle-switch active" id="toggle-particles"></div></div>
                    <div class="toggle-item"><span>信息叠加 [O]</span><div class="toggle-switch active" id="toggle-overlay"></div></div>
                    <div class="toggle-item"><span>热力图 [H]</span><div class="toggle-switch" id="toggle-heatmap"></div></div>
                    <div class="toggle-item"><span>🎵 空间音效 [M]</span><div class="toggle-switch" id="toggle-music"></div></div>
                </div>
            </div>

            <div class="control-section">
                <h4>时间轴与回放</h4>
                <div style="background:rgba(0,0,0,0.3);padding:8px;border-radius:4px;">
                    <div style="font-size:9px;color:var(--text-dim);margin-bottom:4px;">
                        <span id="frame-info">帧: 0 / 0</span>
                    </div>
                    <input type="range" id="timeline-slider" min="0" max="100" value="0" 
                        style="width:100%;height:4px;background:rgba(0,243,255,0.2);border-radius:2px;outline:none;cursor:pointer;">
                </div>
            </div>
        </div>
    </div>

    <div class="panel" id="video-panel">
        <div class="panel-header"><i class="fas fa-video"></i> 实时监控画面</div>
        <div id="video-container">
            <div id="hud-overlay">
                <div class="hud-item hud-rec"><i class="fas fa-circle"></i> REC <span id="hud-time">00:00:00</span></div>
                <div class="hud-item"><i class="fas fa-crosshairs"></i> <span id="hud-status">待命</span></div>
            </div>
            <img id="video-img" src="" alt="等待视频流..." draggable="false">
            <canvas id="selection-layer"></canvas>
            <canvas id="particle-layer"></canvas>
            <div id="select-hint">🎯 拖拽框选目标 或 点击"智能自动检测"</div>
        </div>
    </div>

    <div class="panel" id="telemetry-panel">
        <div class="panel-header"><i class="fas fa-tachometer-alt"></i> 状态遥测</div>
        <div class="panel-content">
            <div class="gauge-container">
                <div class="gauge"><canvas id="speed-gauge"></canvas><div class="gauge-label">速度</div></div>
                <div class="gauge"><canvas id="accel-gauge"></canvas><div class="gauge-label">加速度</div></div>
            </div>
            <div class="metric-card">
                <div class="metric-label">当前速度</div>
                <div class="metric-value" id="val-speed">0.0<span class="metric-unit">px/f</span></div>
            </div>
            <div class="metric-card" style="border-color: var(--success);">
                <div class="metric-label">目标坐标</div>
                <div class="metric-value" id="val-coord" style="font-size:16px; color: var(--success);">X:--- Y:---</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">运动状态</div>
                <div style="margin-top:4px;"><span class="state-badge state-idle" id="motion-state">IDLE</span></div>
            </div>
            <div class="metric-card" style="border-color: #a855f7;">
                <div class="metric-label">数据统计</div>
                <div class="stats-grid">
                    <div class="stat-item"><div class="stat-label">最大速度</div><div class="stat-value" id="stat-max-speed">0.0</div></div>
                    <div class="stat-item"><div class="stat-label">移动距离</div><div class="stat-value" id="stat-distance">0</div></div>
                </div>
            </div>
        </div>
    </div>

    <div class="panel" id="chart-box">
        <div class="panel-header"><i class="fas fa-chart-line"></i> 运动曲线分析</div>
        <div id="chart-container"><canvas id="velocityChart"></canvas></div>
    </div>

    <div class="panel" id="three-panel">
        <div class="panel-header"><i class="fas fa-cube"></i> 3D 轨迹重构</div>
        <div id="three-container"></div>
    </div>
</div>

<script>
    // ==========================================
    // 关键修正：全局变量前置声明 (Fix for ReferenceError)
    // ==========================================
    const socket = io();
    let isPaused = false, trackingStartTime = null;
    let particles = []; // 粒子系统
    let scene, camera, renderer, sphere, line, positions; // 3D变量
    let audioContext = null;
    let isDraggingTimeline = false;
    let isDragging = false, startX, startY;

    const config = { kalman: true, trail: true, overlay: true, heatmap: false, music: false, preprocess: true, particles: true };
    const stats = { maxSpeed: 0, totalDistance: 0, lastX: 0, lastY: 0 };

    // DOM 元素获取 (统一放在最前面)
    const imgEl = document.getElementById('video-img');
    const canvas = document.getElementById('selection-layer');
    const particleCanvas = document.getElementById('particle-layer');
    const ctx = canvas.getContext('2d');
    const pCtx = particleCanvas.getContext('2d');
    const speedEl = document.getElementById('val-speed');
    const coordEl = document.getElementById('val-coord');
    const stateEl = document.getElementById('motion-state');
    const hudStatus = document.getElementById('hud-status');
    const uploadStatus = document.getElementById('upload-status');
    const videoContainer = document.getElementById('video-container');

    // ==========================================
    // 核心函数定义
    // ==========================================
    function showToast(msg, duration=2000) {
        const toast = document.getElementById('toast');
        if(toast) {
            toast.innerText = msg; toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), duration);
        }
    }

    function reset3DTrail() { 
        if(positions) positions.fill(0); 
    }

    function resetStats() {
        stats.maxSpeed = 0; stats.totalDistance = 0; stats.lastX = 0; stats.lastY = 0;
        if(document.getElementById('stat-max-speed')) document.getElementById('stat-max-speed').innerText = '0.0';
        if(document.getElementById('stat-distance')) document.getElementById('stat-distance').innerText = '0';
        reset3DTrail();
        particles = [];
    }

    function updateStats(speed, x, y) {
        if(speed > stats.maxSpeed) stats.maxSpeed = speed;
        if(stats.lastX > 0) stats.totalDistance += Math.sqrt(Math.pow(x - stats.lastX, 2) + Math.pow(y - stats.lastY, 2));
        stats.lastX = x; stats.lastY = y;
        if(document.getElementById('stat-max-speed')) document.getElementById('stat-max-speed').innerText = stats.maxSpeed.toFixed(1);
        if(document.getElementById('stat-distance')) document.getElementById('stat-distance').innerText = Math.round(stats.totalDistance);
    }

    // ==========================================
    // 创新功能：粒子系统 (Particle System)
    // ==========================================
    function resizeCanvas() {
        if(!videoContainer) return;
        const rect = videoContainer.getBoundingClientRect();
        if(particleCanvas) { particleCanvas.width = rect.width; particleCanvas.height = rect.height; }
        if(canvas) { canvas.width = rect.width; canvas.height = rect.height; }
    }
    if(videoContainer) new ResizeObserver(resizeCanvas).observe(videoContainer);

    class Particle {
        constructor(x, y, speed) {
            this.x = x; this.y = y;
            this.vx = (Math.random() - 0.5) * 2;
            this.vy = (Math.random() - 0.5) * 2;
            this.life = 1.0;
            this.color = speed > 15 ? `255, 34, 85` : `0, 243, 255`; 
            this.size = Math.random() * 3 + 1;
        }
        update() {
            this.x += this.vx; this.y += this.vy;
            this.life -= 0.04;
        }
        draw(ctx) {
            ctx.fillStyle = `rgba(${this.color}, ${this.life})`;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    function animateParticles() {
        if(!pCtx) return;
        if(!config.particles) { pCtx.clearRect(0, 0, particleCanvas.width, particleCanvas.height); requestAnimationFrame(animateParticles); return; }
        pCtx.clearRect(0, 0, particleCanvas.width, particleCanvas.height);
        for(let i = particles.length - 1; i >= 0; i--) {
            particles[i].update();
            particles[i].draw(pCtx);
            if(particles[i].life <= 0) particles.splice(i, 1);
        }
        requestAnimationFrame(animateParticles);
    }
    animateParticles();

    // ==========================================
    // 创新功能：音乐化 + 空间音频
    // ==========================================
    const noteFrequencies = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25, 587.33, 659.25]; 

    function playSpatialNote(speed, x_pos, width) {
        if(!config.music) return;
        if(!audioContext) audioContext = new (window.AudioContext || window.webkitAudioContext)();

        const osc = audioContext.createOscillator();
        const gain = audioContext.createGain();
        const panner = audioContext.createStereoPanner(); 

        const index = Math.min(Math.floor(speed / 5), noteFrequencies.length - 1);
        osc.frequency.value = noteFrequencies[index];
        const panValue = Math.max(-1, Math.min(1, (x_pos / width - 0.5) * 2));
        panner.pan.value = panValue;
        gain.gain.value = Math.min(0.2, speed * 0.01);

        osc.connect(panner); panner.connect(gain); gain.connect(audioContext.destination);
        osc.start(); osc.stop(audioContext.currentTime + 0.15);
    }

    // ==========================================
    // 3D 场景初始化
    // ==========================================
    function init3D() {
        const c = document.getElementById('three-container');
        if(!c) return;
        scene = new THREE.Scene(); 
        camera = new THREE.PerspectiveCamera(60, c.clientWidth/c.clientHeight, 0.1, 100);
        renderer = new THREE.WebGLRenderer({alpha: true, antialias: true});
        renderer.setSize(c.clientWidth, c.clientHeight);
        renderer.setClearColor(0x000000, 0);
        c.appendChild(renderer.domElement);
        const grid = new THREE.GridHelper(20, 20, 0x00f3ff, 0x222222);
        grid.rotation.x = Math.PI/2; scene.add(grid);
        sphere = new THREE.Mesh(new THREE.SphereGeometry(0.5), new THREE.MeshBasicMaterial({color: 0xff2255}));
        scene.add(sphere);
        positions = new Float32Array(300);
        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        line = new THREE.Line(geo, new THREE.LineBasicMaterial({color: 0x00f3ff}));
        scene.add(line);
        camera.position.set(0, 0, 20);
        function animate() { requestAnimationFrame(animate); renderer.render(scene, camera); }
        animate();
    }

    function update3D(x, y, w, h) {
        if(!sphere || !positions) return;
        const nx = (x/w - 0.5) * 20, ny = -(y/h - 0.5) * 20; 
        sphere.position.set(nx, ny, 0);
        for(let i=299; i>=3; i--) positions[i] = positions[i-3];
        positions[0] = nx; positions[1] = ny; positions[2] = 0;
        line.geometry.attributes.position.needsUpdate = true;
    }

    init3D();

    // ==========================================
    // 事件监听 (安全绑定) (Fix for TypeError)
    // ==========================================
    const uploadBtn = document.getElementById('video-upload');
    if(uploadBtn) {
        uploadBtn.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            const formData = new FormData(); formData.append('video', file);
            if(uploadStatus) uploadStatus.innerText = '📤 正在上传...';
            showToast('📤 开始上传视频...');
            try {
                const response = await fetch('/upload_video', { method: 'POST', body: formData });
                const result = await response.json();
                if (result.success) {
                    if(uploadStatus) uploadStatus.innerText = '✅ ' + file.name;
                    showToast('✅ 视频加载成功');
                    resetStats(); 
                    if(document.getElementById('btn-reset')) document.getElementById('btn-reset').click();
                } else { showToast('❌ 上传失败: ' + result.error); }
            } catch (err) { showToast('❌ 上传出错'); }
        });
    }

    const cameraBtn = document.getElementById('btn-camera');
    if(cameraBtn) {
        cameraBtn.addEventListener('click', () => {
            socket.emit('switch_source', { type: 'camera' });
            if(uploadStatus) uploadStatus.innerText = '📷 摄像头模式'; 
            showToast('📷 已切换至摄像头'); resetStats();
        });
    }

    if(videoContainer) {
        videoContainer.addEventListener('mousedown', e => {
            if(isPaused) return;
            isDragging = true;
            const rect = videoContainer.getBoundingClientRect();
            startX = e.clientX - rect.left; startY = e.clientY - rect.top;
            if(document.getElementById('select-hint')) document.getElementById('select-hint').classList.add('hidden');
        });

        videoContainer.addEventListener('mousemove', e => {
            if(!isDragging) return;
            const rect = videoContainer.getBoundingClientRect();
            const curX = e.clientX - rect.left, curY = e.clientY - rect.top;
            const x = Math.min(startX, curX), y = Math.min(startY, curY);
            const w = Math.abs(curX - startX), h = Math.abs(curY - startY);
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.strokeStyle = '#00f3ff'; ctx.lineWidth = 2; ctx.strokeRect(x,y,w,h);
            ctx.fillStyle = 'rgba(0, 243, 255, 0.2)'; ctx.fillRect(x,y,w,h);
        });

        videoContainer.addEventListener('mouseup', e => {
            if(!isDragging) return;
            isDragging = false;
            const rect = videoContainer.getBoundingClientRect();
            const endX = e.clientX - rect.left, endY = e.clientY - rect.top;
            const w = Math.abs(endX - startX), h = Math.abs(endY - startY);
            if(w > 10 && h > 10) {
                const payload = { 
                    x: Math.min(startX, endX) / rect.width, y: Math.min(startY, endY) / rect.height,
                    w: w / rect.width, h: h / rect.height 
                };
                socket.emit('start_tracking', payload);
                trackingStartTime = Date.now(); resetStats();
                if(hudStatus) { hudStatus.innerText = '手动追踪'; hudStatus.style.color = '#00ff88'; }
                showToast('🎯 目标已锁定');
            }
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        });
    }

    // 绑定其他按钮
    const btnPause = document.getElementById('btn-pause');
    if(btnPause) btnPause.addEventListener('click', () => {
        isPaused = !isPaused; socket.emit('toggle_pause', { paused: isPaused });
        showToast(isPaused ? '⏸ 已暂停' : '▶ 继续');
    });

    const btnReset = document.getElementById('btn-reset');
    if(btnReset) btnReset.addEventListener('click', () => {
        socket.emit('reset_tracking'); resetStats();
        if(hudStatus) { hudStatus.innerText = '待命'; hudStatus.style.color = '#00f3ff'; }
        if(stateEl) { stateEl.className = 'state-badge state-idle'; stateEl.innerText = 'IDLE'; }
        showToast('🔄 已重置');
    });

    const btnExport = document.getElementById('btn-export');
    if(btnExport) btnExport.addEventListener('click', () => { window.location.href = '/export_data'; showToast('📥 正在下载数据...'); });

    const btnAutoDetect = document.getElementById('btn-auto-detect');
    if(btnAutoDetect) btnAutoDetect.addEventListener('click', () => {
        socket.emit('auto_detect'); 
        if(hudStatus) hudStatus.innerText = '智能检测中...';
        showToast('🔍 正在智能分析运动轨迹...');
    });

    const viewSelect = document.getElementById('view-mode-select');
    if(viewSelect) viewSelect.addEventListener('change', e => { socket.emit('set_view_mode', { mode: e.target.value }); });

    const trackerSelect = document.getElementById('tracker-select');
    if(trackerSelect) trackerSelect.addEventListener('change', e => { socket.emit('change_tracker', { tracker: e.target.value }); });

    const timeline = document.getElementById('timeline-slider');
    if(timeline) {
        timeline.addEventListener('input', (e) => { isDraggingTimeline = true; });
        timeline.addEventListener('change', (e) => {
            isDraggingTimeline = false; socket.emit('seek_frame', { frame: parseInt(e.target.value) });
        });
    }

    document.querySelectorAll('.toggle-switch').forEach(el => {
        el.addEventListener('click', () => {
            el.classList.toggle('active');
            const id = el.id.replace('toggle-', ''); config[id] = el.classList.contains('active');
            socket.emit('update_config', config);
        });
    });

    document.addEventListener('keydown', e => {
        if(e.target.tagName === 'INPUT') return;
        switch(e.key.toLowerCase()) {
            case ' ': e.preventDefault(); if(btnPause) btnPause.click(); break;
            case 'r': if(btnReset) btnReset.click(); break;
            case 'a': if(btnAutoDetect) btnAutoDetect.click(); break;
            case 'u': if(uploadBtn) uploadBtn.click(); break;
            case 'p': if(document.getElementById('toggle-particles')) document.getElementById('toggle-particles').click(); break;
            case 'm': if(document.getElementById('toggle-music')) document.getElementById('toggle-music').click(); break;
        }
    });

    // Chart init
    const ctxChart = document.getElementById('velocityChart');
    let chart;
    if(ctxChart) {
        chart = new Chart(ctxChart.getContext('2d'), {
            type: 'line',
            data: { labels: Array(50).fill(''),
                datasets: [{ label: '速度', data: Array(50).fill(0), borderColor: '#00f3ff', borderWidth: 2, tension: 0.4, pointRadius: 0 }]
            },
            options: { responsive: true, maintainAspectRatio: false, 
                plugins: { legend: { display: false } },
                scales: { x: { display: false }, y: { grid: { color: '#222' }, ticks: { color: '#00f3ff' } } }
            }
        });
    }

    function drawGauge(id, val, max, color) {
        const cvs = document.getElementById(id);
        if(!cvs) return;
        const c = cvs.getContext('2d');
        const cx = cvs.width/2, cy = cvs.height/2, r = cvs.width/2 - 5;
        c.clearRect(0,0,cvs.width,cvs.height);
        c.beginPath(); c.arc(cx,cy,r,0.75*Math.PI, 2.25*Math.PI);
        c.strokeStyle = '#333'; c.lineWidth = 5; c.stroke();
        c.beginPath(); c.arc(cx,cy,r,0.75*Math.PI, (0.75 + 1.5 * Math.min(val/max,1)) * Math.PI);
        c.strokeStyle = color; c.stroke();
        c.fillStyle=color; c.font='bold 12px Consolas'; c.textAlign='center';
        c.fillText(val.toFixed(1), cx, cy+5);
    }

    // Socket listeners
    socket.on('frame_update', msg => {
        if(imgEl) imgEl.src = "data:image/jpeg;base64," + msg.image;

        if(msg.total_frames > 0 && !isDraggingTimeline && timeline) {
            timeline.max = msg.total_frames; timeline.value = msg.frame_num;
            if(document.getElementById('frame-info')) document.getElementById('frame-info').innerText = `帧: ${msg.frame_num} / ${msg.total_frames}`;
        }

        if(msg.tracking) {
            const speed = msg.speed, accel = msg.accel;
            if(speedEl) speedEl.innerHTML = speed.toFixed(1) + '<span class="metric-unit">px/f</span>';
            if(coordEl) coordEl.innerText = `X:${msg.x} Y:${msg.y}`;

            let state = 'IDLE';
            if(speed < 1) state = 'STATIONARY';
            else if(speed < 15) state = 'PATROL';
            else state = 'HIGH SPEED';

            if(stateEl) {
                stateEl.innerText = state;
                stateEl.className = 'state-badge ' + (state==='HIGH SPEED'?'state-danger':(state==='PATROL'?'state-patrol':'state-idle'));
            }

            updateStats(speed, msg.x, msg.y);
            update3D(msg.x, msg.y, msg.w, msg.h);
            drawGauge('speed-gauge', speed, 50, '#00f3ff');
            drawGauge('accel-gauge', Math.abs(accel), 20, '#ff2255');

            if(chart) {
                chart.data.datasets[0].data.shift();
                chart.data.datasets[0].data.push(speed);
                chart.update('none');
            }

            if(config.particles && speed > 2) {
                const rect = videoContainer ? videoContainer.getBoundingClientRect() : {width: 640, height: 360};
                const pX = (msg.x / msg.w) * rect.width;
                const pY = (msg.y / msg.h) * rect.height;
                const count = Math.min(5, Math.floor(speed / 3));
                for(let k=0; k<count; k++) particles.push(new Particle(pX, pY, speed));
            }

            if(msg.frame_num % 5 === 0) playSpatialNote(speed, msg.x, msg.w);
        }
    });

    socket.on('auto_detect_success', () => {
        if(hudStatus) { hudStatus.innerText = '智能锁定'; hudStatus.style.color = '#ff00ff'; }
        showToast('🤖 目标锁定 (置信度100%)'); resetStats();
    });

    socket.on('auto_detect_fail', () => {
        if(hudStatus) { hudStatus.innerText = '分析中...'; hudStatus.style.color = 'orange'; }
        showToast('⚠ 环境复杂，正在筛选目标...');
    });

    setInterval(() => { 
        if(document.getElementById('hud-time')) document.getElementById('hud-time').innerText = new Date().toLocaleTimeString(); 
    }, 1000);

</script>
{% endraw %}
</body>
</html>
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['UPLOAD_FOLDER'] = 'uploads'
socketio = SocketIO(app, cors_allowed_origins="*")

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


class VideoProcessor:
    def __init__(self):
        self.trail_history = deque(maxlen=50)
        self.tracking_data = []
        self.video_path = None
        self.source_type = 'file'
        self.cap = None
        self.tracker = None
        self.tracking = False
        self.paused = False
        self.config = {'kalman': True, 'trail': True, 'overlay': True, 'preprocess': True, 'particles': True}
        self.view_mode = 'original'
        self.current_frame = None
        self.last_pos = None
        self.last_speed = 0
        self.tracker_type = 'CSRT'

        self.detect_counter = 0
        self.last_detected_rect = None

        self.kalman = cv2.KalmanFilter(4, 2)
        self.kalman.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
        self.kalman.transitionMatrix = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32)
        self.kalman.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03

        self.backSub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)

        default_video = 'supermario.mp4'
        if os.path.exists(default_video):
            self.load_video_source(default_video)
        else:
            self.load_camera_source()

    def load_video_source(self, path):
        if self.cap: self.cap.release()
        self.cap = cv2.VideoCapture(path)
        self.video_path = path
        self.source_type = 'file'
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.reset_state()
        print(f"[INFO] Loaded video: {path}")

    def load_camera_source(self):
        if self.cap: self.cap.release()
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.source_type = 'camera'
        self.total_frames = 0
        self.reset_state()
        print(f"[INFO] Loaded camera")

    def reset_state(self):
        self.tracking = False
        self.tracker = None
        self.paused = False
        self.trail_history.clear()
        self.tracking_data = []
        self.current_frame = None
        self.detect_counter = 0

    def reset_kalman(self):
        self.kalman.statePre = np.zeros((4, 1), np.float32)
        self.kalman.statePost = np.zeros((4, 1), np.float32)

    def init_tracker(self, frame, bbox):
        trackers = {
            'CSRT': cv2.TrackerCSRT_create,
            'KCF': cv2.TrackerKCF_create,
            'MIL': cv2.TrackerMIL_create,
            'MOSSE': cv2.legacy.TrackerMOSSE_create if hasattr(cv2.legacy,
                                                               'TrackerMOSSE_create') else cv2.TrackerCSRT_create
        }
        self.tracker = trackers.get(self.tracker_type, cv2.TrackerCSRT_create)()
        self.tracker.init(frame, bbox)
        self.tracking = True
        self.last_pos = None
        self.trail_history.clear()
        self.reset_kalman()
        print(f"Tracker initialized: {bbox}")

    def preprocess_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        equalized = cv2.equalizeHist(blurred)
        return equalized

    def auto_detect_target(self):
        if self.current_frame is None: return False

        mask = self.backSub.apply(self.current_frame)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        max_area = 0
        best_rect = None

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 500 < area < (self.current_frame.shape[0] * self.current_frame.shape[1] * 0.6):
                if area > max_area:
                    max_area = area
                    best_rect = cv2.boundingRect(cnt)

        if best_rect:
            if self.last_detected_rect:
                cx1, cy1 = best_rect[0], best_rect[1]
                cx2, cy2 = self.last_detected_rect[0], self.last_detected_rect[1]
                dist = np.sqrt((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2)
                if dist < 50:
                    self.detect_counter += 1
                else:
                    self.detect_counter = 0

            self.last_detected_rect = best_rect

            if self.detect_counter > 5:
                self.init_tracker(self.current_frame, best_rect)
                self.detect_counter = 0
                return True
        else:
            self.detect_counter = 0

        return False

    def process_frame(self):
        if self.cap is None or not self.cap.isOpened(): return None

        if self.paused and self.current_frame is not None:
            display_frame = self.current_frame.copy()
        else:
            ret, frame = self.cap.read()
            if not ret:
                if self.source_type == 'file':
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                return self.process_frame()
            self.current_frame = frame.copy()
            display_frame = frame

        preprocessed = self.preprocess_frame(self.current_frame)
        motion_mask = self.backSub.apply(self.current_frame)

        cx, cy, speed, accel = 0, 0, 0, 0

        if self.tracking:
            success, bbox = self.tracker.update(self.current_frame)
            if success:
                cx_raw = int(bbox[0] + bbox[2] / 2)
                cy_raw = int(bbox[1] + bbox[3] / 2)

                if self.config['kalman']:
                    mp = np.array([[np.float32(cx_raw)], [np.float32(cy_raw)]])
                    self.kalman.correct(mp)
                    pred = self.kalman.predict()
                    cx, cy = int(pred[0]), int(pred[1])
                else:
                    cx, cy = cx_raw, cy_raw

                if self.last_pos:
                    dist = np.sqrt((cx - self.last_pos[0]) ** 2 + (cy - self.last_pos[1]) ** 2)
                    speed = dist
                    accel = speed - self.last_speed

                self.last_pos = (cx, cy)
                self.last_speed = speed
                self.trail_history.append((cx, cy))

                self.tracking_data.append([
                    datetime.datetime.now().strftime("%H:%M:%S.%f"),
                    cx, cy, round(speed, 2), round(accel, 2)
                ])

                if self.config['overlay']:
                    p1 = (int(bbox[0]), int(bbox[1]))
                    p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                    cv2.rectangle(display_frame, p1, p2, (0, 243, 255), 2)
                    cv2.putText(display_frame, f"TARGET LOCKED", (p1[0], p1[1] - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 243, 255), 1)

                    if self.config['trail'] and len(self.trail_history) > 1:
                        pts = list(self.trail_history)
                        for i in range(1, len(pts)):
                            thickness = int(np.sqrt(i / len(pts)) * 3) + 1
                            cv2.line(display_frame, pts[i - 1], pts[i], (0, 255, 136), thickness)

        output_image = display_frame
        if self.view_mode == 'preprocessed':
            output_image = preprocessed
        elif self.view_mode == 'mask':
            output_image = motion_mask

        _, buffer = cv2.imencode('.jpg', output_image)
        b64_img = base64.b64encode(buffer).decode('utf-8')

        return {
            'image': b64_img,
            'tracking': self.tracking,
            'x': cx, 'y': cy, 'speed': speed, 'accel': accel,
            'w': self.current_frame.shape[1],
            'h': self.current_frame.shape[0],
            'frame_num': int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)),
            'total_frames': self.total_frames
        }

    def export_csv(self):
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(['Timestamp', 'X', 'Y', 'Speed', 'Accel'])
        cw.writerows(self.tracking_data)
        return si.getvalue()


processor = VideoProcessor()


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})
    file = request.files['video']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})

    if file:
        filename = "upload_" + str(int(time.time())) + ".mp4"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        processor.load_video_source(filepath)
        return jsonify({'success': True, 'filename': filename})


@app.route('/export_data')
def export_data():
    data = processor.export_csv()
    mem = io.BytesIO()
    mem.write(data.encode('utf-8'))
    mem.seek(0)
    return send_file(mem, as_attachment=True, download_name='tracking_data.csv', mimetype='text/csv')


@socketio.on('connect')
def handle_connect():
    socketio.start_background_task(video_stream_task)


@socketio.on('start_tracking')
def handle_start(data):
    if processor.current_frame is not None:
        h, w = processor.current_frame.shape[:2]
        x = int(data['x'] * w)
        y = int(data['y'] * h)
        bw = int(data['w'] * w)
        bh = int(data['h'] * h)
        processor.init_tracker(processor.current_frame, (x, y, bw, bh))


@socketio.on('auto_detect')
def handle_auto_detect():
    success = processor.auto_detect_target()
    if success:
        emit('auto_detect_success')
    else:
        emit('auto_detect_fail')


@socketio.on('reset_tracking')
def handle_reset():
    processor.tracking = False
    processor.tracker = None
    processor.trail_history.clear()


@socketio.on('toggle_pause')
def handle_pause(data):
    processor.paused = data['paused']


@socketio.on('switch_source')
def handle_switch_source(data):
    if data['type'] == 'camera':
        processor.load_camera_source()


@socketio.on('update_config')
def handle_config(data):
    processor.config.update(data)


@socketio.on('set_view_mode')
def handle_view_mode(data):
    processor.view_mode = data['mode']


@socketio.on('change_tracker')
def handle_tracker_change(data):
    processor.tracker_type = data['tracker']


@socketio.on('seek_frame')
def handle_seek(data):
    if processor.cap.isOpened() and processor.source_type == 'file':
        processor.cap.set(cv2.CAP_PROP_POS_FRAMES, data['frame'])


def video_stream_task():
    while True:
        data = processor.process_frame()
        if data:
            socketio.emit('frame_update', data)
        socketio.sleep(0.03)


if __name__ == '__main__':
    print("Starting AETHER Tracking System v4.1 Stable...")
    socketio.run(app, debug=False, port=5000, allow_unsafe_werkzeug=True)

