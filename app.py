import sys
import os
import cv2
import numpy as np
import base64
import time
import datetime
import threading
import csv
from collections import deque
from flask import Flask, render_template_string, jsonify, send_file
from flask_socketio import SocketIO, emit
import io

# =========================================================
# 修复版 HTML 模板
# =========================================================
HTML_TEMPLATE = r'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="shortcut icon" href="data:;"> 
    <title>AETHER // 视觉追踪系统 v2.1 (Debug Fix)</title>
    <script src="https://cdn.bootcdn.net/ajax/libs/socket.io/4.0.1/socket.io.min.js"></script>
    <script src="https://cdn.bootcdn.net/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.bootcdn.net/ajax/libs/Chart.js/3.7.0/chart.min.js"></script>
    <link href="https://cdn.bootcdn.net/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root { 
            --bg: #0a0a12; --panel: rgba(15, 20, 30, 0.9); --accent: #00f3ff; 
            --accent-dim: rgba(0, 243, 255, 0.3); --success: #00ff88;
            --warning: #ffaa00; --danger: #ff2255; --text: #e0f7ff; --text-dim: #667788;
        }
        * { box-sizing: border-box; }
        body { margin: 0; background: linear-gradient(135deg, #0a0a12 0%, #0d1520 100%);
            color: var(--text); font-family: 'Segoe UI', 'Microsoft YaHei', monospace; overflow: hidden; }
        .main-grid { display: grid; grid-template-columns: 200px 1fr 360px; 
            grid-template-rows: 1fr 180px; height: 100vh; gap: 6px; padding: 6px; }
        .panel { background: var(--panel); border: 1px solid var(--accent-dim); border-radius: 6px; 
            position: relative; overflow: hidden; backdrop-filter: blur(10px); }
        .panel-header { background: linear-gradient(90deg, rgba(0, 243, 255, 0.15), transparent);
            color: var(--accent); padding: 10px 12px; font-size: 10px; letter-spacing: 2px; 
            font-weight: bold; border-bottom: 1px solid var(--accent-dim); text-transform: uppercase;
            display: flex; align-items: center; gap: 8px; }
        .panel-header i { font-size: 12px; }
        .panel-content { padding: 10px; height: calc(100% - 38px); overflow-y: auto; }
        #control-panel { grid-column: 1; grid-row: 1 / span 2; }
        .control-section { margin-bottom: 15px; }
        .control-section h4 { color: var(--text-dim); font-size: 9px; letter-spacing: 1px; 
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
        .btn .key { font-size: 9px; opacity: 0.6; }
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
            border: 1px solid var(--accent-dim); color: var(--text); border-radius: 4px; font-size: 10px; }
        .select-box option { background: #1a1a2e; }
        #video-panel { grid-column: 2; grid-row: 1; display: flex; flex-direction: column; }
        #video-container { flex: 1; display: flex; justify-content: center; align-items: center; 
            background: #000; position: relative; cursor: crosshair; overflow: hidden; user-select: none; }
        #video-img { width: 100%; height: 100%; object-fit: contain; pointer-events: none; -webkit-user-drag: none; }
        #selection-layer { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 5; }
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
                <h4>追踪控制</h4>
                <button class="btn" id="btn-pause"><i class="fas fa-pause"></i> 暂停 <span class="key">[空格]</span></button>
                <button class="btn btn-danger" id="btn-reset"><i class="fas fa-redo"></i> 重置 <span class="key">[R]</span></button>
                <button class="btn btn-purple" id="btn-screenshot"><i class="fas fa-camera"></i> 截图 <span class="key">[S]</span></button>
                <button class="btn btn-success" id="btn-export"><i class="fas fa-download"></i> 导出 <span class="key">[E]</span></button>
            </div>
            <div class="control-section">
                <h4>追踪算法</h4>
                <select class="select-box" id="tracker-select">
                    <option value="CSRT">CSRT (精确)</option>
                    <option value="KCF">KCF (快速)</option>
                    <option value="MIL">MIL (稳定)</option>
                    <option value="MOSSE">MOSSE (极速)</option>
                </select>
            </div>
            <div class="control-section">
                <h4>功能开关</h4>
                <div class="toggle-group">
                    <div class="toggle-item"><span>卡尔曼滤波 [K]</span><div class="toggle-switch active" id="toggle-kalman"></div></div>
                    <div class="toggle-item"><span>轨迹显示 [T]</span><div class="toggle-switch active" id="toggle-trail"></div></div>
                    <div class="toggle-item"><span>战术叠加</span><div class="toggle-switch active" id="toggle-overlay"></div></div>
                    <div class="toggle-item"><span>热力图 [H]</span><div class="toggle-switch" id="toggle-heatmap"></div></div>
                    <div class="toggle-item"><span>🎵 音乐化 [M]</span><div class="toggle-switch" id="toggle-music"></div></div>
                </div>
            </div>
            <div class="control-section">
                <h4>⏰ 时间旅行</h4>
                <div style="background:rgba(0,0,0,0.3);padding:8px;border-radius:4px;">
                    <div style="font-size:9px;color:var(--text-dim);margin-bottom:4px;">
                        <span id="frame-info">帧: 0 / 0</span>
                    </div>
                    <input type="range" id="timeline-slider" min="0" max="100" value="0" 
                        style="width:100%;height:4px;background:rgba(0,243,255,0.2);border-radius:2px;outline:none;cursor:pointer;">
                    <div style="margin-top:8px;">
                        <button class="btn" style="font-size:9px;padding:4px 8px;" id="btn-keyframes">
                            <i class="fas fa-star"></i> 关键帧 (<span id="keyframe-count">0</span>)
                        </button>
                    </div>
                </div>
            </div>
            <div class="control-section">
                <h4>报警设置</h4>
                <div class="toggle-item"><span>速度阈值</span>
                    <input type="number" value="25" min="5" max="100" style="width:50px;padding:3px;background:#222;border:1px solid #444;color:#fff;border-radius:3px;font-size:10px;" id="alert-threshold">
                </div>
            </div>
        </div>
    </div>
    <div class="panel" id="video-panel">
        <div class="panel-header"><i class="fas fa-video"></i> 光学传感器 // 实时画面</div>
        <div id="video-container">
            <div id="hud-overlay">
                <div class="hud-item hud-rec"><i class="fas fa-circle"></i> REC <span id="hud-time">00:00:00</span></div>
                <div class="hud-item"><i class="fas fa-crosshairs"></i> <span id="hud-status">待命</span></div>
            </div>
            <img id="video-img" src="" alt="等待视频流..." draggable="false">
            <canvas id="selection-layer"></canvas>
            <div id="select-hint">🎯 在画面上拖拽框选目标开始追踪</div>
        </div>
    </div>
    <div class="panel" id="telemetry-panel">
        <div class="panel-header"><i class="fas fa-tachometer-alt"></i> 遥测数据</div>
        <div class="panel-content">
            <div class="gauge-container">
                <div class="gauge"><canvas id="speed-gauge"></canvas><div class="gauge-label">速度</div></div>
                <div class="gauge"><canvas id="accel-gauge"></canvas><div class="gauge-label">加速度</div></div>
            </div>
            <div class="metric-card">
                <div class="metric-label">当前速度</div>
                <div class="metric-value" id="val-speed">0.0<span class="metric-unit">px/f</span></div>
            </div>
            <div class="metric-card" style="border-color: var(--danger);">
                <div class="metric-label">加速度</div>
                <div class="metric-value" id="val-accel" style="color: var(--danger);">0.0<span class="metric-unit">px/f²</span></div>
            </div>
            <div class="metric-card" style="border-color: var(--success);">
                <div class="metric-label">目标坐标</div>
                <div class="metric-value" id="val-coord" style="font-size:16px; color: var(--success);">X:--- Y:---</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">运动状态</div>
                <div style="margin-top:4px;"><span class="state-badge state-idle" id="motion-state">IDLE</span></div>
            </div>
            <div class="metric-card" style="border-color: #ff6b9d;">
                <div class="metric-label">🎵 当前音符</div>
                <div class="metric-value" id="val-music-note" style="font-size:16px; color: #ff6b9d;">---</div>
                <div style="font-size:8px;color:var(--text-dim);margin-top:4px;" id="music-instrument">等待追踪...</div>
            </div>
            <div class="metric-card" style="border-color: #a855f7;">
                <div class="metric-label">追踪统计</div>
                <div class="stats-grid">
                    <div class="stat-item"><div class="stat-label">最大速度</div><div class="stat-value" id="stat-max-speed">0.0</div></div>
                    <div class="stat-item"><div class="stat-label">平均速度</div><div class="stat-value" id="stat-avg-speed">0.0</div></div>
                    <div class="stat-item"><div class="stat-label">移动距离</div><div class="stat-value" id="stat-distance">0</div></div>
                    <div class="stat-item"><div class="stat-label">追踪时长</div><div class="stat-value" id="val-duration">00:00</div></div>
                </div>
            </div>
        </div>
    </div>
    <div class="panel" id="chart-box">
        <div class="panel-header"><i class="fas fa-chart-line"></i> 速度/加速度 时间线</div>
        <div id="chart-container"><canvas id="velocityChart"></canvas></div>
    </div>
    <div class="panel" id="three-panel">
        <div class="panel-header"><i class="fas fa-cube"></i> 3D 空间轨迹</div>
        <div id="three-container"></div>
    </div>
</div>
<script>
    const socket = io();
    let isPaused = false, trackingStartTime = null, lastSpeed = 0, alertThreshold = 25;
    const config = { kalman: true, trail: true, overlay: true, heatmap: false, tracker: 'CSRT', music: false };
    const stats = { maxSpeed: 0, totalSpeed: 0, speedCount: 0, totalDistance: 0, lastX: 0, lastY: 0 };
    let keyframes = [];
    let audioContext = null;
    let isDraggingTimeline = false;
    const imgEl = document.getElementById('video-img');
    const canvas = document.getElementById('selection-layer');
    const ctx = canvas.getContext('2d');
    const speedEl = document.getElementById('val-speed');
    const accelEl = document.getElementById('val-accel');
    const coordEl = document.getElementById('val-coord');
    const stateEl = document.getElementById('motion-state');
    const durationEl = document.getElementById('val-duration');
    const hudStatus = document.getElementById('hud-status');
    const hudTime = document.getElementById('hud-time');

    function addLog(msg, type = 'info') {
        console.log('[' + type.toUpperCase() + '] ' + msg);
    }

    function showToast(msg, duration = 2000) {
        const toast = document.getElementById('toast');
        toast.innerText = msg;
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), duration);
    }

    function resetStats() {
        stats.maxSpeed = 0; stats.totalSpeed = 0; stats.speedCount = 0;
        stats.totalDistance = 0; stats.lastX = 0; stats.lastY = 0;
        document.getElementById('stat-max-speed').innerText = '0.0';
        document.getElementById('stat-avg-speed').innerText = '0.0';
        document.getElementById('stat-distance').innerText = '0';
        reset3DTrail();
    }

    function updateStats(speed, x, y) {
        if(speed > stats.maxSpeed) stats.maxSpeed = speed;
        stats.totalSpeed += speed;
        stats.speedCount++;
        if(stats.lastX > 0) stats.totalDistance += Math.sqrt(Math.pow(x - stats.lastX, 2) + Math.pow(y - stats.lastY, 2));
        stats.lastX = x; stats.lastY = y;
        document.getElementById('stat-max-speed').innerText = stats.maxSpeed.toFixed(1);
        document.getElementById('stat-avg-speed').innerText = (stats.totalSpeed / stats.speedCount).toFixed(1);
        document.getElementById('stat-distance').innerText = Math.round(stats.totalDistance);
    }

    let isDragging = false, startX, startY;
    const selectHint = document.getElementById('select-hint');

    function resizeOverlay() {
        const container = document.getElementById('video-container');
        canvas.width = container.clientWidth;
        canvas.height = container.clientHeight;
        canvas.style.top = "0px";
        canvas.style.left = "0px";
    }
    imgEl.onload = resizeOverlay;
    window.onresize = resizeOverlay;
    setTimeout(resizeOverlay, 100);

    const videoContainer = document.getElementById('video-container');

    function getMousePos(e) {
        const rect = videoContainer.getBoundingClientRect();
        return { x: e.clientX - rect.left, y: e.clientY - rect.top };
    }

    videoContainer.addEventListener('mousedown', e => {
        e.preventDefault();
        if(isPaused) { showToast('⚠ 请先继续播放'); return; }
        isDragging = true;
        const pos = getMousePos(e);
        startX = pos.x; startY = pos.y;
        if(selectHint) selectHint.classList.add('hidden');
    });

    videoContainer.addEventListener('mousemove', e => {
        e.preventDefault();
        if(!isDragging) return;
        const pos = getMousePos(e);
        const curX = pos.x, curY = pos.y;
        const x = Math.min(startX, curX), y = Math.min(startY, curY);
        const w = Math.abs(curX - startX), h = Math.abs(curY - startY);

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        // 半透明填充
        ctx.fillStyle = 'rgba(0, 243, 255, 0.2)';
        ctx.fillRect(x, y, w, h);
        // 虚线边框
        ctx.strokeStyle = '#00f3ff'; ctx.lineWidth = 2; ctx.setLineDash([6, 4]);
        ctx.strokeRect(x, y, w, h);
        ctx.setLineDash([]);
        // 四角标记
        const cornerLen = Math.min(15, w/3, h/3);
        ctx.strokeStyle = '#00ff88'; ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(x, y + cornerLen); ctx.lineTo(x, y); ctx.lineTo(x + cornerLen, y);
        ctx.moveTo(x + w - cornerLen, y); ctx.lineTo(x + w, y); ctx.lineTo(x + w, y + cornerLen);
        ctx.moveTo(x + w, y + h - cornerLen); ctx.lineTo(x + w, y + h); ctx.lineTo(x + w - cornerLen, y + h);
        ctx.moveTo(x + cornerLen, y + h); ctx.lineTo(x, y + h); ctx.lineTo(x, y + h - cornerLen);
        ctx.stroke();
        // 中心十字
        const cx = x + w/2, cy = y + h/2;
        ctx.strokeStyle = '#ff2255'; ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(cx - 10, cy); ctx.lineTo(cx + 10, cy);
        ctx.moveTo(cx, cy - 10); ctx.lineTo(cx, cy + 10);
        ctx.stroke();
        // 尺寸显示
        ctx.fillStyle = '#00f3ff'; ctx.font = '11px Consolas';
        ctx.fillText(Math.round(w) + ' x ' + Math.round(h), x + 4, y - 6);
    });

    videoContainer.addEventListener('mouseup', e => {
        if(!isDragging) return;
        isDragging = false;
        const pos = getMousePos(e);
        const endX = pos.x, endY = pos.y;
        const containerW = videoContainer.clientWidth, containerH = videoContainer.clientHeight;

        const selW = Math.abs(endX - startX), selH = Math.abs(endY - startY);
        if(selW > 20 && selH > 20) {
            const payload = { 
                x: Math.min(startX, endX) / containerW, 
                y: Math.min(startY, endY) / containerH,
                w: selW / containerW, 
                h: selH / containerH 
            };
            socket.emit('start_tracking', payload);
            trackingStartTime = Date.now(); resetStats();
            addLog('目标锁定 [' + Math.round(selW) + 'x' + Math.round(selH) + ']', 'info');
            hudStatus.innerText = '追踪中'; hudStatus.style.color = '#00ff88';
            showToast('🎯 目标已锁定');
        } else if(selW > 5 || selH > 5) {
            showToast('⚠ 选框太小，请框选更大区域');
        }
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    });

    videoContainer.addEventListener('mouseleave', () => {
        if(isDragging) { isDragging = false; ctx.clearRect(0, 0, canvas.width, canvas.height); }
    });

    function togglePause() {
        isPaused = !isPaused;
        const btn = document.getElementById('btn-pause');
        btn.innerHTML = isPaused ? '<i class="fas fa-play"></i> 继续 <span class="key">[空格]</span>' : '<i class="fas fa-pause"></i> 暂停 <span class="key">[空格]</span>';
        socket.emit('toggle_pause', { paused: isPaused });
        addLog(isPaused ? '系统已暂停' : '系统继续运行', 'warn');
        showToast(isPaused ? '⏸ 已暂停' : '▶ 继续');
    }
    function resetTracking() {
        socket.emit('reset_tracking'); trackingStartTime = null; resetStats();
        addLog('追踪已重置', 'warn'); hudStatus.innerText = '待命'; hudStatus.style.color = '#00f3ff';
        stateEl.className = 'state-badge state-idle'; stateEl.innerText = 'IDLE';
        showToast('🔄 已重置');
    }
    function takeScreenshot() {
        document.getElementById('screenshot-flash').classList.add('active');
        setTimeout(() => document.getElementById('screenshot-flash').classList.remove('active'), 300);
        const link = document.createElement('a'); link.href = imgEl.src;
        link.download = 'screenshot_' + new Date().toISOString().slice(0,19).replace(/:/g,'-') + '.jpg';
        link.click(); addLog('截图已保存', 'info'); showToast('📷 截图已保存');
    }
    function exportData() { addLog('导出数据...', 'info'); window.location.href = '/export_data'; showToast('📥 导出中...'); }

    // 音乐化追踪：播放音符
    function playMusicNote(note, velocity, instrument) {
        if(!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }

        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        // MIDI音符转频率
        const frequency = 440 * Math.pow(2, (note - 69) / 12);
        oscillator.frequency.value = frequency;

        // 根据乐器选择波形
        if(instrument === 'piano') oscillator.type = 'sine';
        else if(instrument === 'violin') oscillator.type = 'triangle';
        else if(instrument === 'drums') oscillator.type = 'square';
        else oscillator.type = 'sine';

        // 音量
        gainNode.gain.value = velocity / 127 * 0.3;

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.15);
    }

    // 时间旅行：跳转到指定帧
    function seekToFrame(frameNum) {
        socket.emit('seek_to_frame', { frame_num: frameNum });
        showToast('⏰ 时间旅行到帧 ' + frameNum);
    }

    // 显示关键帧列表
    function showKeyframes() {
        if(keyframes.length === 0) {
            showToast('⚠ 暂无关键帧');
            return;
        }

        let msg = '🌟 关键帧列表:\n';
        keyframes.slice(-5).forEach((kf, idx) => {
            msg += `\n${kf.event} - 帧${kf.frame_num} (速度:${kf.speed.toFixed(1)})`;
        });
        addLog(msg, 'info');
        showToast(`📍 共${keyframes.length}个关键帧`);
    }

    document.getElementById('btn-pause').addEventListener('click', togglePause);
    document.getElementById('btn-reset').addEventListener('click', resetTracking);
    document.getElementById('btn-screenshot').addEventListener('click', takeScreenshot);
    document.getElementById('btn-export').addEventListener('click', exportData);
    document.getElementById('btn-keyframes').addEventListener('click', showKeyframes);

    // 时间线滑块控制
    const timelineSlider = document.getElementById('timeline-slider');
    timelineSlider.addEventListener('mousedown', () => { isDraggingTimeline = true; });
    timelineSlider.addEventListener('mouseup', e => {
        isDraggingTimeline = false;
        const frameNum = parseInt(e.target.value);
        seekToFrame(frameNum);
    });
    document.getElementById('tracker-select').addEventListener('change', e => {
        config.tracker = e.target.value;
        socket.emit('change_tracker', { tracker: config.tracker });
        addLog('切换算法: ' + config.tracker, 'info');
    });
    document.getElementById('alert-threshold').addEventListener('change', e => {
        alertThreshold = parseInt(e.target.value);
        socket.emit('set_threshold', { threshold: alertThreshold });
        addLog('报警阈值: ' + alertThreshold, 'info');
    });
    document.querySelectorAll('.toggle-switch').forEach(el => {
        el.addEventListener('click', () => {
            el.classList.toggle('active');
            const id = el.id.replace('toggle-', '');
            config[id] = el.classList.contains('active');
            socket.emit('update_config', config);
            addLog(id + ' ' + (config[id] ? '启用' : '禁用'));
        });
    });

    document.addEventListener('keydown', e => {
        if(e.target.tagName === 'INPUT') return;
        switch(e.key.toLowerCase()) {
            case ' ': e.preventDefault(); togglePause(); break;
            case 'r': resetTracking(); break;
            case 's': takeScreenshot(); break;
            case 'e': exportData(); break;
            case 'k': document.getElementById('toggle-kalman').click(); break;
            case 't': document.getElementById('toggle-trail').click(); break;
            case 'h': document.getElementById('toggle-heatmap').click(); break;
            case 'm': document.getElementById('toggle-music').click(); break;
        }
    });

    const ctxChart = document.getElementById('velocityChart').getContext('2d');
    const chart = new Chart(ctxChart, {
        type: 'line',
        data: { labels: Array(60).fill(''),
            datasets: [{ label: '速度', data: Array(60).fill(0), borderColor: '#00f3ff',
                backgroundColor: 'rgba(0, 243, 255, 0.1)', borderWidth: 2, fill: true, tension: 0.4, pointRadius: 0, yAxisID: 'y' },
            { label: '加速度', data: Array(60).fill(0), borderColor: '#ff2255', borderWidth: 1, fill: false, tension: 0.4, pointRadius: 0, yAxisID: 'y1' }]
        },
        options: { responsive: true, maintainAspectRatio: false, animation: false,
            plugins: { legend: { display: true, position: 'top', labels: { color: '#888', font: { size: 9 } } } },
            scales: { x: { display: false },
                y: { type: 'linear', position: 'left', grid: { color: '#222' }, ticks: { color: '#00f3ff', font: { size: 9 } } },
                y1: { type: 'linear', position: 'right', grid: { drawOnChartArea: false }, ticks: { color: '#ff2255', font: { size: 9 } } }
            }
        }
    });

    function drawGauge(canvasId, value, maxVal, color) {
        const cvs = document.getElementById(canvasId);
        const c = cvs.getContext('2d');
        const w = cvs.width, h = cvs.height, cx = w/2, cy = h/2, r = Math.min(w,h)/2 - 6;
        c.clearRect(0, 0, w, h);
        c.beginPath(); c.arc(cx, cy, r, 0.75 * Math.PI, 2.25 * Math.PI);
        c.strokeStyle = '#333'; c.lineWidth = 5; c.stroke();
        const ratio = Math.min(value / maxVal, 1);
        c.beginPath(); c.arc(cx, cy, r, 0.75 * Math.PI, (0.75 + 1.5 * ratio) * Math.PI);
        c.strokeStyle = color; c.lineWidth = 5; c.lineCap = 'round'; c.stroke();
        c.fillStyle = color; c.font = 'bold 12px Consolas'; c.textAlign = 'center';
        c.fillText(value.toFixed(1), cx, cy + 4);
    }

    setInterval(() => {
        hudTime.innerText = new Date().toLocaleTimeString('zh-CN');
        if(trackingStartTime) {
            const elapsed = Math.floor((Date.now() - trackingStartTime) / 1000);
            durationEl.innerText = Math.floor(elapsed/60).toString().padStart(2,'0') + ':' + (elapsed%60).toString().padStart(2,'0');
        }
    }, 1000);

    let scene, camera, renderer, sphere, line, positions;
    const MAX_POINTS = 120;
    function init3D() {
        const container = document.getElementById('three-container');
        if(!container) return;
        scene = new THREE.Scene(); scene.background = new THREE.Color(0x0a0a12);
        camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 1000);
        renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        container.appendChild(renderer.domElement);
        scene.add(new THREE.GridHelper(20, 20, 0x00f3ff, 0x1a1a2e));
        camera.position.set(0, 12, 18); camera.lookAt(0, 0, 0);
        sphere = new THREE.Mesh(new THREE.SphereGeometry(0.4, 32, 32), new THREE.MeshBasicMaterial({ color: 0xff2255 }));
        scene.add(sphere);
        const geometry = new THREE.BufferGeometry();
        positions = new Float32Array(MAX_POINTS * 3);
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        line = new THREE.Line(geometry, new THREE.LineBasicMaterial({ color: 0x00f3ff }));
        scene.add(line);
        animate3D();
    }
    function animate3D() {
        requestAnimationFrame(animate3D);
        if(scene) scene.rotation.y += 0.002;
        if(renderer && scene && camera) renderer.render(scene, camera);
    }
    function update3D(x, y, frameW, frameH) {
        if(!sphere || !positions) return;
        const x3d = (x / frameW - 0.5) * 20, z3d = (y / frameH - 0.5) * 20;
        sphere.position.set(x3d, 0.5, z3d);
        for(let i = (MAX_POINTS-1) * 3; i >= 3; i -= 3) {
            positions[i] = positions[i - 3]; positions[i + 1] = positions[i - 2]; positions[i + 2] = positions[i - 1];
        }
        positions[0] = x3d; positions[1] = 0.5; positions[2] = z3d;
        line.geometry.attributes.position.needsUpdate = true;
    }
    function reset3DTrail() {
        if(positions) { for(let i = 0; i < positions.length; i++) positions[i] = 0; if(line) line.geometry.attributes.position.needsUpdate = true; }
    }
    init3D();

    socket.on('connect', () => addLog('WebSocket 连接成功', 'info'));
    socket.on('frame_update', msg => {
        imgEl.src = "data:image/jpeg;base64," + msg.image;

        // 更新时间线和帧数
        if(msg.frame_num !== undefined && msg.total_frames !== undefined) {
            document.getElementById('frame-info').innerText = '帧: ' + msg.frame_num + ' / ' + msg.total_frames;
            if(!isDraggingTimeline) {
                timelineSlider.max = msg.total_frames;
                timelineSlider.value = msg.frame_num;
            }
        }

        if(msg.tracking) {
            const speed = msg.speed, accel = msg.accel || 0;
            speedEl.innerHTML = speed.toFixed(1) + '<span class="metric-unit">px/f</span>';
            accelEl.innerHTML = accel.toFixed(1) + '<span class="metric-unit">px/f²</span>';
            coordEl.innerText = 'X:' + msg.x + ' Y:' + msg.y;

            // 音乐化追踪：播放音符
            if(msg.music_note && config.music) {
                const note = msg.music_note;
                playMusicNote(note.note, note.velocity, note.instrument);

                // 显示音符信息
                const noteNames = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
                const octave = Math.floor((note.note - 12) / 12);
                const noteName = noteNames[(note.note - 12) % 12] + octave;
                document.getElementById('val-music-note').innerText = noteName;

                const instrumentEmoji = {
                    'piano': '🎹 钢琴',
                    'violin': '🎻 小提琴',
                    'drums': '🥁 鼓点',
                    'rest': '🎵 休止'
                };
                document.getElementById('music-instrument').innerText = instrumentEmoji[note.instrument] || '🎵';
            }

            // 时间旅行：检测关键帧
            if(msg.keyframe) {
                keyframes.push(msg.keyframe);
                document.getElementById('keyframe-count').innerText = keyframes.length;
                addLog('🌟 关键帧: ' + msg.keyframe.event, 'info');
                showToast('⭐ ' + msg.keyframe.event);
            }

            updateStats(speed, msg.x, msg.y);
            update3D(msg.x, msg.y, msg.w, msg.h);
            if(speed > alertThreshold) { speedEl.classList.add('danger'); if(speed > lastSpeed + 5) addLog('⚠ 高速警报: ' + speed.toFixed(1), 'error'); }
            else { speedEl.classList.remove('danger'); }
            lastSpeed = speed;
            const state = msg.state || 'IDLE';
            stateEl.innerText = state; stateEl.className = 'state-badge';
            if(state === 'STATIONARY') stateEl.classList.add('state-idle');
            else if(state === 'PATROL') stateEl.classList.add('state-patrol');
            else if(state === 'ALERT') stateEl.classList.add('state-alert');
            else if(state === 'HIGH SPEED') stateEl.classList.add('state-danger');
            chart.data.datasets[0].data.shift(); chart.data.datasets[0].data.push(speed);
            chart.data.datasets[1].data.shift(); chart.data.datasets[1].data.push(Math.abs(accel));
            chart.update();
            drawGauge('speed-gauge', speed, 50, '#00f3ff');
            drawGauge('accel-gauge', Math.abs(accel), 20, '#ff2255');
        }
    });
    socket.on('log_message', msg => addLog(msg.text, msg.type || 'info'));
    drawGauge('speed-gauge', 0, 50, '#00f3ff');
    drawGauge('accel-gauge', 0, 20, '#ff2255');
</script>
{% endraw %}
</body>
</html>
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aether_secret'
socketio = SocketIO(app, cors_allowed_origins="*")


class VideoProcessor:
    def __init__(self):
        # 优化：尝试打开视频文件，如果失败则打开摄像头（索引0）
        self.video_path = 'supermario.mp4'
        self.cap = None

        if os.path.exists(self.video_path):
            self.cap = cv2.VideoCapture(self.video_path)
            print(f"[INFO] 成功加载视频文件: {self.video_path}")

        # 如果文件加载失败，尝试打开摄像头 (Index 0)
        # 添加 cv2.CAP_DSHOW 增加 Windows 兼容性
        if self.cap is None or not self.cap.isOpened():
            print(f"[WARN] 视频文件无效，尝试打开摄像头 (Index 0)...")
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        if not self.cap.isOpened():
            print(f"[ERROR] 严重错误：无法打开任何视频源！")

        self.tracker = None
        self.tracking = False
        self.paused = False
        self.current_frame = None
        self.tracker_type = 'CSRT'
        self.config = {'kalman': True, 'trail': True, 'overlay': True, 'heatmap': False, 'music': False}
        self.alert_threshold = 25
        self.kalman = cv2.KalmanFilter(4, 2)
        self.kalman.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
        self.kalman.transitionMatrix = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32)
        self.kalman.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03
        self.last_pos = None
        self.last_speed = 0
        self.trail_history = deque(maxlen=100)
        self.heatmap = None
        self.tracking_data = []
        self.keyframes = []

        if self.cap and self.cap.isOpened():
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        else:
            self.total_frames = 0
            self.fps = 30

        self.current_frame_num = 0
        self.music_notes = deque(maxlen=50)
        self.last_note_time = 0

    def create_tracker(self):
        trackers = {
            'CSRT': cv2.TrackerCSRT_create,
            'KCF': cv2.TrackerKCF_create,
            'MIL': cv2.TrackerMIL_create,
            'MOSSE': cv2.legacy.TrackerMOSSE_create if hasattr(cv2, 'legacy') else cv2.TrackerCSRT_create
        }
        return trackers.get(self.tracker_type, cv2.TrackerCSRT_create)()

    def reset_kalman(self):
        self.kalman = cv2.KalmanFilter(4, 2)
        self.kalman.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
        self.kalman.transitionMatrix = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32)
        self.kalman.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03

    def init_tracker(self, norm_rect, frame_w, frame_h):
        x = int(norm_rect['x'] * frame_w)
        y = int(norm_rect['y'] * frame_h)
        w = int(norm_rect['w'] * frame_w)
        h = int(norm_rect['h'] * frame_h)
        self.tracker = self.create_tracker()
        self.init_bbox = (x, y, w, h)
        self.tracking = False
        self.last_pos = None
        self.last_speed = 0
        self.trail_history.clear()
        self.tracking_data = []
        self.reset_kalman()
        if self.current_frame is not None:
            self.heatmap = np.zeros((self.current_frame.shape[0], self.current_frame.shape[1]), dtype=np.float32)

    def reset_tracking(self):
        self.tracking = False
        self.tracker = None
        self.last_pos = None
        self.last_speed = 0
        self.trail_history.clear()
        if hasattr(self, 'init_bbox'):
            del self.init_bbox

    def get_motion_state(self, speed):
        if speed < 1.0:
            return 'STATIONARY'
        elif speed < 10.0:
            return 'PATROL'
        elif speed < self.alert_threshold:
            return 'ALERT'
        else:
            return 'HIGH SPEED'

    def speed_to_music_note(self, speed, accel):
        note = int(48 + min(speed, 50) * 0.72)
        velocity = int(64 + min(abs(accel), 20) * 3)
        if speed < 1.0:
            instrument = 'rest'
        elif speed < 10.0:
            instrument = 'piano'
        elif speed < 25.0:
            instrument = 'violin'
        else:
            instrument = 'drums'
        return {'note': note, 'velocity': velocity, 'instrument': instrument, 'speed': speed}

    def detect_keyframe(self, speed, accel, state):
        current_time = time.time()
        is_keyframe = False
        event_type = None

        if abs(accel) > 15:
            is_keyframe = True
            event_type = '急加速' if accel > 0 else '急减速'
        elif speed > self.alert_threshold * 1.5:
            is_keyframe = True
            event_type = '极速运动'
        elif state == 'STATIONARY' and self.last_speed > 10:
            is_keyframe = True
            event_type = '突然停止'
        elif len(self.keyframes) == 0 and self.tracking:
            is_keyframe = True
            event_type = '追踪开始'

        if is_keyframe and (len(self.keyframes) == 0 or current_time - self.keyframes[-1]['time'] > 2):
            keyframe = {
                'frame_num': self.current_frame_num,
                'time': current_time,
                'speed': speed,
                'accel': accel,
                'event': event_type,
                'timestamp': datetime.datetime.now().isoformat()
            }
            self.keyframes.append(keyframe)
            return keyframe
        return None

    def seek_to_frame(self, frame_num):
        if 0 <= frame_num < self.total_frames:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            self.current_frame_num = frame_num
            return True
        return False

    def get_keyframes_list(self):
        return self.keyframes

    def get_frame_data(self):
        if self.cap is None or not self.cap.isOpened():
            return None

        if self.paused and self.current_frame is not None:
            _, buffer = cv2.imencode('.jpg', self.current_frame)
            img_str = base64.b64encode(buffer).decode('utf-8')
            return {'image': img_str, 'tracking': self.tracking,
                    'x': self.last_pos[0] if self.last_pos else 0,
                    'y': self.last_pos[1] if self.last_pos else 0,
                    'w': self.current_frame.shape[1], 'h': self.current_frame.shape[0],
                    'speed': self.last_speed, 'accel': 0, 'state': self.get_motion_state(self.last_speed)}

        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            if not ret or frame is None:
                return None
        self.current_frame = frame.copy()
        speed, accel, cx, cy, state = 0, 0, 0, 0, 'IDLE'

        keyframe = None
        music_note = None

        if hasattr(self, 'init_bbox'):
            if frame is not None and frame.size > 0 and self.tracker is not None:
                try:
                    x, y, w, h = self.init_bbox
                    if w > 0 and h > 0 and x >= 0 and y >= 0:
                        self.tracker.init(frame, self.init_bbox)
                        self.tracking = True
                        self.heatmap = np.zeros((frame.shape[0], frame.shape[1]), dtype=np.float32)
                        print(f"[INFO] 追踪器初始化成功: bbox={self.init_bbox}")
                    else:
                        print(f"[WARN] 无效的边界框: {self.init_bbox}")
                except Exception as e:
                    print(f"[ERROR] 追踪器初始化失败: {e}")
                    self.tracking = False
            del self.init_bbox

        if self.config['overlay']:
            h, w = frame.shape[:2]
            cv2.line(frame, (w // 2 - 30, h // 2), (w // 2 + 30, h // 2), (80, 80, 80), 1)
            cv2.line(frame, (w // 2, h // 2 - 30), (w // 2, h // 2 + 30), (80, 80, 80), 1)
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, f"REC {ts}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.rectangle(frame, (5, 5), (w - 5, h - 5), (40, 40, 40), 1)

        if self.tracking:
            success, bbox = self.tracker.update(frame)
            if success:
                cx = int(bbox[0] + bbox[2] / 2)
                cy = int(bbox[1] + bbox[3] / 2)
                if self.config['kalman']:
                    self.kalman.correct(np.array([[np.float32(cx)], [np.float32(cy)]]))
                    pred = self.kalman.predict()
                    px, py = int(pred[0]), int(pred[1])
                else:
                    px, py = cx, cy
                if self.last_pos:
                    speed = np.sqrt((px - self.last_pos[0]) ** 2 + (py - self.last_pos[1]) ** 2)
                    accel = speed - self.last_speed
                self.last_pos = (px, py)
                self.last_speed = speed
                state = self.get_motion_state(speed)
                self.trail_history.append((px, py))

                self.current_frame_num = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))

                if self.config.get('music', False):
                    current_time = time.time()
                    if current_time - self.last_note_time > 0.1:
                        music_note = self.speed_to_music_note(speed, accel)
                        self.music_notes.append(music_note)
                        self.last_note_time = current_time

                keyframe = self.detect_keyframe(speed, accel, state)

                if self.config['heatmap'] and self.heatmap is not None:
                    cv2.circle(self.heatmap, (px, py), 20, 1, -1)
                self.tracking_data.append({
                    'timestamp': datetime.datetime.now().isoformat(),
                    'x': px, 'y': py, 'speed': speed, 'accel': accel, 'state': state
                })
                p1 = (int(bbox[0]), int(bbox[1]))
                p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                color = (0, 0, 255) if speed > self.alert_threshold else (0, 165, 255) if speed > 10 else (255, 255, 0)
                cv2.rectangle(frame, p1, p2, color, 1)
                l = 15
                cv2.line(frame, p1, (p1[0] + l, p1[1]), color, 2)
                cv2.line(frame, p1, (p1[0], p1[1] + l), color, 2)
                cv2.line(frame, (p2[0], p1[1]), (p2[0] - l, p1[1]), color, 2)
                cv2.line(frame, (p2[0], p1[1]), (p2[0], p1[1] + l), color, 2)
                cv2.line(frame, (p1[0], p2[1]), (p1[0] + l, p2[1]), color, 2)
                cv2.line(frame, (p1[0], p2[1]), (p1[0], p2[1] - l), color, 2)
                cv2.line(frame, p2, (p2[0] - l, p2[1]), color, 2)
                cv2.line(frame, p2, (p2[0], p2[1] - l), color, 2)
                if self.config['trail'] and len(self.trail_history) > 1:
                    points = list(self.trail_history)
                    for i in range(1, len(points)):
                        alpha = i / len(points)
                        thickness = max(1, int(alpha * 3))
                        pt_color = (int(255 * alpha), int(255 * (1 - alpha)), 255)
                        cv2.line(frame, points[i - 1], points[i], pt_color, thickness)
                if self.config['kalman']:
                    cv2.line(frame, (cx, cy), (px, py), (0, 255, 0), 1)
                    cv2.circle(frame, (px, py), 4, (0, 255, 0), -1)
                cv2.putText(frame, f"{state} | V:{speed:.1f}", (p1[0], p1[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            color, 1)
                cx, cy = px, py
        if self.config['heatmap'] and self.heatmap is not None and self.tracking:
            heatmap_normalized = cv2.normalize(self.heatmap, None, 0, 255, cv2.NORM_MINMAX)
            heatmap_colored = cv2.applyColorMap(heatmap_normalized.astype(np.uint8), cv2.COLORMAP_JET)
            frame = cv2.addWeighted(frame, 0.7, heatmap_colored, 0.3, 0)
        self.current_frame = frame
        _, buffer = cv2.imencode('.jpg', frame)
        img_str = base64.b64encode(buffer).decode('utf-8')

        result = {
            'image': img_str, 'tracking': self.tracking, 'x': cx, 'y': cy,
            'w': frame.shape[1], 'h': frame.shape[0], 'speed': speed, 'accel': accel, 'state': state,
            'frame_num': self.current_frame_num, 'total_frames': self.total_frames
        }

        if self.tracking and music_note:
            result['music_note'] = music_note

        if keyframe:
            result['keyframe'] = keyframe

        return result

    def export_data(self):
        if not self.tracking_data: return None
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['timestamp', 'x', 'y', 'speed', 'accel', 'state'])
        writer.writeheader()
        writer.writerows(self.tracking_data)
        return output.getvalue()


processor = VideoProcessor()


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/export_data')
def export_data():
    csv_data = processor.export_data()
    if csv_data:
        output = io.BytesIO()
        output.write(csv_data.encode('utf-8'))
        output.seek(0)
        return send_file(output, mimetype='text/csv', as_attachment=True,
                         download_name=f'tracking_data_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
    return jsonify({'error': 'No data available'}), 404


@socketio.on('connect')
def handle_connect():
    print(f"[WS] 客户端连接: {threading.current_thread().name}")
    emit('log_message', {'text': '服务端连接成功', 'type': 'info'})
    socketio.start_background_task(stream_video)


@socketio.on('disconnect')
def handle_disconnect():
    print(f"[WS] 客户端断开")


@socketio.on('start_tracking')
def handle_track(data):
    if processor.current_frame is not None:
        h, w = processor.current_frame.shape[:2]
        processor.init_tracker(data, w, h)
        emit('log_message', {'text': f'追踪初始化: {processor.tracker_type}', 'type': 'info'})


@socketio.on('reset_tracking')
def handle_reset():
    processor.reset_tracking()
    emit('log_message', {'text': '追踪已重置', 'type': 'warn'})


@socketio.on('toggle_pause')
def handle_pause(data):
    processor.paused = data.get('paused', False)


@socketio.on('change_tracker')
def handle_change_tracker(data):
    processor.tracker_type = data.get('tracker', 'CSRT')
    emit('log_message', {'text': f'算法切换: {processor.tracker_type}', 'type': 'info'})


@socketio.on('update_config')
def handle_config(data):
    processor.config.update(data)


@socketio.on('set_threshold')
def handle_threshold(data):
    processor.alert_threshold = data.get('threshold', 25)


@socketio.on('seek_to_frame')
def handle_seek_frame(data):
    frame_num = data.get('frame_num', 0)
    if processor.seek_to_frame(frame_num):
        emit('log_message', {'text': f'⏰ 时间旅行到帧: {frame_num}', 'type': 'info'})
    else:
        emit('log_message', {'text': '跳转失败', 'type': 'error'})


@socketio.on('get_keyframes')
def handle_get_keyframes():
    keyframes = processor.get_keyframes_list()
    emit('keyframes_list', {'keyframes': keyframes})


def stream_video():
    while True:
        data = processor.get_frame_data()
        if data:
            socketio.emit('frame_update', data)
        socketio.sleep(0.033)


def find_free_port(start=5000, end=5100):
    import socket
    for port in range(start, end):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return start


if __name__ == '__main__':
    port = find_free_port()
    print("=" * 50)
    print("  AETHER // 智能视觉追踪系统 v2.0")
    print("=" * 50)
    print("  启动中...")
    print(f"  请在浏览器打开: http://127.0.0.1:{port}")
    print("=" * 50)
    socketio.run(app, debug=False, port=port, allow_unsafe_werkzeug=True)
