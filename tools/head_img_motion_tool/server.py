# -*- coding: utf-8 -*-
"""Local no-AI tool wrapper for the JD campaign head image Lottie pipeline."""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import math
import mimetypes
import os
import socket
import subprocess
import sys
import uuid
import webbrowser
from datetime import datetime
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs, unquote, urlparse
from urllib.request import urlretrieve


TOOL_DIR = Path(__file__).resolve().parent
SKILL_ROOT = TOOL_DIR.parents[1]
PIPELINE_SCRIPT = SKILL_ROOT / "scripts" / "generate_merged_lottie_pipeline.py"
RUNS_DIR = TOOL_DIR / "runs"
ANALYZE_DIR = TOOL_DIR / "analyze_cache"
VENDOR_DIR = TOOL_DIR / "vendor"
LOTTIE_PLAYER_URL = "https://cdn.jsdelivr.net/npm/lottie-web@5.12.2/build/player/lottie.min.js"
PIPELINE_MODULE = None


INDEX_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>会场头图 Lottie 工具</title>
  <style>
    :root {
      --bg: #101116;
      --panel: #181b22;
      --panel-2: #20242d;
      --line: #343b49;
      --text: #f2f4f8;
      --muted: #9ca7b6;
      --accent: #3fd39b;
      --accent-2: #e8c34a;
      --danger: #ff6b6b;
      --focus: #6ea8ff;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background:
        linear-gradient(120deg, rgba(63, 211, 155, .08), transparent 34%),
        linear-gradient(240deg, rgba(232, 195, 74, .08), transparent 38%),
        var(--bg);
      color: var(--text);
      font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif;
    }
    main {
      width: min(1180px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 24px 0 36px;
      display: grid;
      grid-template-columns: 360px 1fr;
      gap: 18px;
    }
    header {
      grid-column: 1 / -1;
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 16px;
      padding: 4px 0 8px;
    }
    h1 {
      margin: 0;
      font-size: 22px;
      line-height: 1.25;
      font-weight: 700;
      letter-spacing: 0;
    }
    .sub {
      margin-top: 6px;
      color: var(--muted);
      font-size: 13px;
    }
    .badge {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.04);
      color: var(--muted);
      padding: 7px 10px;
      border-radius: 6px;
      font-size: 12px;
      white-space: nowrap;
    }
    section {
      border: 1px solid var(--line);
      background: rgba(24, 27, 34, .94);
      border-radius: 8px;
      min-width: 0;
    }
    .form {
      padding: 16px;
      display: grid;
      gap: 14px;
      align-content: start;
    }
    label {
      display: block;
      margin-bottom: 7px;
      color: var(--muted);
      font-size: 12px;
    }
    input[type="text"], input[type="file"] {
      width: 100%;
      border: 1px solid var(--line);
      background: var(--panel-2);
      color: var(--text);
      border-radius: 6px;
      padding: 10px 11px;
      font-size: 13px;
    }
    input[type="file"] { color: var(--muted); }
    input:focus {
      outline: 2px solid rgba(110, 168, 255, .34);
      border-color: var(--focus);
    }
    .drop {
      border: 1px dashed #596273;
      border-radius: 8px;
      padding: 16px;
      background: rgba(255,255,255,.03);
    }
    .hint {
      margin-top: 7px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
    }
    .motion-help {
      border: 1px solid rgba(63, 211, 155, .28);
      background: rgba(63, 211, 155, .08);
      border-radius: 8px;
      padding: 12px;
      display: grid;
      gap: 8px;
      color: #d9f8eb;
      font-size: 12px;
      line-height: 1.5;
    }
    .motion-help strong { color: var(--text); }
    .selector {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.025);
      border-radius: 8px;
      padding: 12px;
      display: grid;
      gap: 10px;
    }
    .selector-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      color: var(--muted);
      font-size: 12px;
    }
    .selection-summary {
      border: 1px solid #2d3441;
      background: var(--panel-2);
      border-radius: 6px;
      padding: 9px 10px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }
    .selection-summary strong {
      color: var(--text);
      font-weight: 700;
    }
    .visual-picker {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255,255,255,.025);
      padding: 12px;
      display: grid;
      grid-template-rows: auto auto minmax(260px, 1fr);
      gap: 10px;
      min-height: 430px;
    }
    .visual-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
    }
    .visual-title {
      font-size: 13px;
      color: var(--text);
      font-weight: 700;
    }
    .visual-note {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
    }
    .scene-tabs {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }
    .scene-tab {
      min-height: 32px;
      padding: 6px 10px;
      border: 1px solid var(--line);
      background: var(--panel-2);
      color: var(--muted);
      border-radius: 6px;
      font-size: 12px;
      font-weight: 700;
    }
    .scene-tab.active {
      border-color: rgba(63, 211, 155, .72);
      background: rgba(63, 211, 155, .16);
      color: var(--text);
    }
    .static-stage {
      position: relative;
      width: 100%;
      align-self: start;
      border: 1px solid #2d3441;
      background: #202020;
      border-radius: 6px;
      overflow: hidden;
    }
    .static-render {
      position: absolute;
      inset: 0;
      z-index: 1;
    }
    .static-render svg,
    .static-render canvas {
      width: 100% !important;
      height: 100% !important;
      display: block;
    }
    .hotspot-layer {
      position: absolute;
      inset: 0;
      z-index: 2;
      pointer-events: none;
    }
    .hotspot {
      position: absolute;
      border: 2px solid rgba(110, 168, 255, .68);
      border-radius: 4px;
      background: rgba(110, 168, 255, .03);
      cursor: pointer;
      pointer-events: auto;
      transition: border-color .14s ease, background .14s ease, box-shadow .14s ease;
    }
    .hotspot:hover,
    .hotspot.hovered,
    .hotspot:focus-visible {
      border-color: rgba(110, 168, 255, 1);
      background: rgba(110, 168, 255, .10);
      box-shadow:
        0 0 0 1px rgba(255, 255, 255, .36) inset,
        0 0 0 2px rgba(110, 168, 255, .22);
      z-index: 8;
    }
    .hotspot.selected-deco {
      border-color: rgba(63, 211, 155, .86);
      background: rgba(63, 211, 155, .08);
      z-index: 5;
    }
    .hotspot.selected-highlight {
      border-color: rgba(232, 195, 74, .9);
      background: rgba(232, 195, 74, .09);
      z-index: 5;
    }
    .hotspot.selected-deco.selected-highlight {
      border-color: rgba(255, 255, 255, .70);
      background:
        linear-gradient(135deg, rgba(63, 211, 155, .10), rgba(232, 195, 74, .10));
    }
    .hotspot.selected-deco.hovered,
    .hotspot.selected-highlight.hovered,
    .hotspot.selected-deco.selected-highlight.hovered {
      border-color: rgba(110, 168, 255, .95);
      box-shadow: 0 0 0 1px rgba(110, 168, 255, .22) inset;
      z-index: 8;
    }
    .hotspot-edge {
      position: absolute;
      pointer-events: auto;
      background: transparent;
      cursor: pointer;
    }
    .hotspot-edge.top,
    .hotspot-edge.bottom {
      left: -5px;
      right: -5px;
      height: 10px;
    }
    .hotspot-edge.left,
    .hotspot-edge.right {
      top: -5px;
      bottom: -5px;
      width: 10px;
    }
    .hotspot-edge.top {
      top: -5px;
    }
    .hotspot-edge.right {
      right: -5px;
    }
    .hotspot-edge.bottom {
      bottom: -5px;
    }
    .hotspot-edge.left {
      left: -5px;
    }
    .marker-row {
      position: absolute;
      top: -1px;
      right: -1px;
      display: flex;
      gap: 3px;
      pointer-events: none;
    }
    .marker {
      display: none;
      min-width: 18px;
      height: 18px;
      padding: 0 5px;
      align-items: center;
      justify-content: center;
      border-radius: 4px;
      font-size: 11px;
      line-height: 18px;
      font-weight: 700;
      color: #07110d;
    }
    .marker.deco {
      background: rgba(63, 211, 155, .88);
    }
    .marker.highlight {
      background: rgba(232, 195, 74, .92);
      color: #181000;
    }
    .hotspot.selected-deco .marker.deco,
    .hotspot.selected-highlight .marker.highlight {
      display: inline-flex;
    }
    .layer-menu {
      position: fixed;
      z-index: 20;
      width: 168px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #161a22;
      box-shadow: 0 18px 45px rgba(0,0,0,.32);
      padding: 6px;
      display: grid;
      gap: 5px;
    }
    .layer-menu-title {
      padding: 5px 7px 6px;
      border-bottom: 1px solid #2d3441;
      color: var(--muted);
      font-size: 11px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .menu-choice {
      min-height: 30px;
      padding: 6px 8px;
      border: 1px solid transparent;
      background: transparent;
      color: var(--text);
      border-radius: 5px;
      font-size: 12px;
      font-weight: 600;
      justify-content: start;
    }
    .menu-choice:hover {
      border-color: rgba(255,255,255,.12);
      background: rgba(255,255,255,.06);
    }
    .menu-choice.active {
      color: #07110d;
      background: var(--accent);
    }
    .menu-choice.warn {
      color: var(--accent-2);
    }
    .actions {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }
    button, a.button {
      border: 1px solid transparent;
      border-radius: 6px;
      padding: 10px 14px;
      background: var(--accent);
      color: #06130f;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 38px;
    }
    button.secondary, a.secondary {
      background: var(--panel-2);
      color: var(--text);
      border-color: var(--line);
      font-weight: 600;
    }
    button:disabled {
      cursor: wait;
      opacity: .66;
    }
    .status {
      border-top: 1px solid var(--line);
      padding: 12px 16px;
      color: var(--muted);
      font-size: 12px;
      min-height: 44px;
      white-space: pre-wrap;
      line-height: 1.45;
    }
    .result {
      padding: 14px;
      display: grid;
      grid-template-rows: auto minmax(360px, 1fr);
      gap: 12px;
      min-height: 620px;
    }
    .result-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .result-title {
      color: var(--muted);
      font-size: 13px;
    }
    .result-path {
      color: var(--accent-2);
      font-size: 12px;
      word-break: break-all;
      margin-top: 5px;
    }
    iframe {
      width: 100%;
      height: 100%;
      min-height: 520px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #151515;
    }
    pre {
      margin: 0;
      max-height: 240px;
      overflow: auto;
      border: 1px solid var(--line);
      background: #0c0e13;
      padding: 10px;
      border-radius: 6px;
      color: #ced6e3;
      font-size: 12px;
      line-height: 1.45;
      white-space: pre-wrap;
    }
    .hidden { display: none; }
    .error { color: var(--danger); }
    @media (max-width: 900px) {
      main { grid-template-columns: 1fr; }
      header { align-items: start; flex-direction: column; }
      .result { min-height: 520px; }
      iframe { min-height: 420px; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>会场头图 Lottie 工具</h1>
        <div class="sub">本地处理 2-4 个静态 JSON，标记增强元素并生成循环 Lottie。</div>
      </div>
      <div class="badge">本地服务 · 不上传外网 · 不消耗 AI token</div>
    </header>

    <section>
      <form id="tool-form" class="form">
        <div class="drop">
          <label for="scenes">静态 JSON（按画面顺序选择 2-4 个）</label>
          <input id="scenes" name="scenes" type="file" accept=".json,application/json" multiple required>
          <div class="hint">按最终播放顺序选择静态 JSON，后续可在静态画面中标记需要增强的元素。</div>
        </div>
        <div class="motion-help">
          <div><strong>装饰元素</strong>：画面停留阶段循环轻微浮动，适合花、蝴蝶、星星、氛围装饰。</div>
          <div><strong>突出元素</strong>：画面停留阶段做缩放强调，适合商品、主利益点、需要被看见的视觉焦点。</div>
        </div>
        <div id="selector" class="selector hidden">
          <div class="selector-head">
            <span id="selector-title">元素动效增强标记</span>
            <button id="analyze" class="secondary" type="button">重新识别</button>
          </div>
          <div class="hint">这是非必选流程：不做标记也会生成基础切换动效；做了装饰或突出标记的元素，会在画面停留阶段增加对应增强动效。</div>
          <div id="selection-summary" class="selection-summary">未选择增强元素。</div>
        </div>
        <div class="actions">
          <button id="generate" type="submit">生成动效</button>
          <button class="secondary" type="reset">清空</button>
        </div>
      </form>
      <div id="status" class="status">等待选择文件。</div>
    </section>

    <section class="result">
      <div class="result-top">
        <div>
          <div class="result-title" id="result-title">还没有生成结果</div>
          <div class="result-path" id="result-path"></div>
        </div>
      </div>
      <div id="visual-picker" class="visual-picker hidden">
        <div class="visual-top">
          <div>
            <div class="visual-title">静态画面预览与元素动效增强标记</div>
            <div id="visual-note" class="visual-note">在静态画面中单击元素边界框，可以标记为装饰元素或突出元素。</div>
          </div>
          <div id="scene-tabs" class="scene-tabs"></div>
        </div>
        <div class="visual-note">装饰元素会在停留阶段循环浮动，突出元素会在停留阶段缩放强调；修改标记后可再次生成动效。</div>
        <div id="static-stage" class="static-stage"></div>
      </div>
      <div id="layer-menu" class="layer-menu hidden"></div>
      <iframe id="preview" class="hidden" title="Lottie preview"></iframe>
      <pre id="log" class="hidden"></pre>
    </section>
  </main>

  <script src="/vendor/lottie.min.js"></script>
  <script>
    const form = document.getElementById('tool-form');
    const statusEl = document.getElementById('status');
    const logEl = document.getElementById('log');
    const preview = document.getElementById('preview');
    const titleEl = document.getElementById('result-title');
    const pathEl = document.getElementById('result-path');
    const btn = document.getElementById('generate');
    const analyzeBtn = document.getElementById('analyze');
    const scenesInput = document.getElementById('scenes');
    const selector = document.getElementById('selector');
    const selectorTitle = document.getElementById('selector-title');
    const selectionSummary = document.getElementById('selection-summary');
    const visualPicker = document.getElementById('visual-picker');
    const sceneTabs = document.getElementById('scene-tabs');
    const staticStage = document.getElementById('static-stage');
    const layerMenu = document.getElementById('layer-menu');

    let analyzedScenes = [];
    let sourceSceneJsons = [];
    let activeSceneIndex = 0;
    let staticAnimation = null;
    const selectedTypes = new Map();

    function setStatus(text, isError=false) {
      statusEl.textContent = text;
      statusEl.classList.toggle('error', isError);
    }

    function filesAreValid() {
      const count = scenesInput.files.length;
      return count >= 2 && count <= 4;
    }

    function collectSelections() {
      const deco = new Set();
      const highlight = new Set();
      selectedTypes.forEach((state, code) => {
        const targetCode = state.targetCode || code;
        if (state.deco) deco.add(targetCode);
        if (state.highlight) highlight.add(targetCode + ':scale');
      });
      return { deco: Array.from(deco).join(','), highlight: Array.from(highlight).join(',') };
    }

    function selectionCounts() {
      let deco = 0;
      let highlight = 0;
      selectedTypes.forEach((state) => {
        if (state.deco) deco += 1;
        if (state.highlight) highlight += 1;
      });
      return { deco, highlight };
    }

    function targetSelectionState(targetCode) {
      const out = { deco: false, highlight: false, targetCode };
      selectedTypes.forEach((state, code) => {
        if ((state.targetCode || code) !== targetCode) return;
        if (state.deco) out.deco = true;
        if (state.highlight) out.highlight = true;
      });
      return out;
    }

    function clearSelectionTarget(targetCode) {
      Array.from(selectedTypes.entries()).forEach(([code, state]) => {
        if ((state.targetCode || code) === targetCode) selectedTypes.delete(code);
      });
    }

    function updateSelectionSummary() {
      const { deco, highlight } = selectionCounts();
      if (deco === 0 && highlight === 0) {
        selectionSummary.textContent = '未选择增强元素。直接生成时，只会输出基础切换动效。';
      } else {
        selectionSummary.innerHTML = `已选择 <strong>${deco}</strong> 个装饰元素，<strong>${highlight}</strong> 个突出元素。`;
      }
      document.querySelectorAll('.hotspot').forEach((hotspot) => {
        const targetCode = hotspot.dataset.targetCode || hotspot.dataset.code;
        const state = targetSelectionState(targetCode);
        hotspot.classList.toggle('selected-deco', !!state.deco);
        hotspot.classList.toggle('selected-highlight', !!state.highlight);
      });
    }

    async function readSourceSceneJsons() {
      const files = Array.from(scenesInput.files);
      return Promise.all(files.map(async (file) => ({
        name: file.name,
        data: JSON.parse(await file.text()),
      })));
    }

    function hideLayerMenu() {
      layerMenu.classList.add('hidden');
      layerMenu.innerHTML = '';
    }

    function clearStaticAnimation() {
      if (staticAnimation) {
        staticAnimation.destroy();
        staticAnimation = null;
      }
    }

    function clearVisualSelection() {
      clearStaticAnimation();
      analyzedScenes = [];
      sourceSceneJsons = [];
      activeSceneIndex = 0;
      selectedTypes.clear();
      sceneTabs.innerHTML = '';
      staticStage.innerHTML = '';
      visualPicker.classList.add('hidden');
      selector.classList.add('hidden');
      hideLayerMenu();
      updateSelectionSummary();
    }

    function layerDisplayName(layer) {
      return layer.name || `(未命名图层 ${layer.index || ''})`;
    }

    function renderCandidates(scenes, sourceJsons) {
      analyzedScenes = scenes || [];
      sourceSceneJsons = sourceJsons || [];
      activeSceneIndex = 0;
      selectedTypes.clear();
      hideLayerMenu();

      if (!scenes || scenes.length === 0) {
        selector.classList.add('hidden');
        visualPicker.classList.add('hidden');
        return;
      }

      selectorTitle.textContent = `已识别 ${scenes.reduce((sum, scene) => sum + scene.layers.length, 0)} 个可标记元素`;
      selector.classList.remove('hidden');
      visualPicker.classList.remove('hidden');
      renderSceneTabs();
      renderActiveScene();
      updateSelectionSummary();
    }

    function renderSceneTabs() {
      sceneTabs.innerHTML = '';
      analyzedScenes.forEach((scene, index) => {
        const tab = document.createElement('button');
        tab.type = 'button';
        tab.className = 'scene-tab' + (index === activeSceneIndex ? ' active' : '');
        tab.textContent = `画面 ${scene.label || String.fromCharCode(65 + index)}`;
        tab.addEventListener('click', () => {
          activeSceneIndex = index;
          hideLayerMenu();
          renderSceneTabs();
          renderActiveScene();
        });
        sceneTabs.appendChild(tab);
      });
    }

    function fallbackBounds(layer) {
      const width = Math.max(5, Math.min(18, 10000 / Math.max(1, layer.scene_w || 1125)));
      const height = Math.max(8, Math.min(24, 8000 / Math.max(1, layer.scene_h || 600)));
      return {
        left: Math.max(0, Math.min(100 - width, (layer.x || 0) / Math.max(1, layer.scene_w || 1125) * 100 - width / 2)),
        top: Math.max(0, Math.min(100 - height, (layer.y || 0) / Math.max(1, layer.scene_h || 600) * 100 - height / 2)),
        width,
        height,
      };
    }

    async function ensureLottieApi() {
      if (window.lottie || window.bodymovin) return window.lottie || window.bodymovin;
      if (window.__lottieApiPromise) return window.__lottieApiPromise;

      window.__lottieApiPromise = new Promise((resolve) => {
        const finish = () => resolve(window.lottie || window.bodymovin || null);
        const script = document.querySelector('script[src="/vendor/lottie.min.js"]');
        if (script) {
          script.addEventListener('load', finish, { once: true });
          script.addEventListener('error', finish, { once: true });
        }
        setTimeout(async () => {
          if (window.lottie || window.bodymovin) {
            finish();
            return;
          }
          try {
            const response = await fetch('/vendor/lottie.min.js');
            const code = await response.text();
            (0, eval)(code);
          } catch (error) {
            console.warn('Lottie player fallback failed', error);
          }
          finish();
        }, 300);
      });
      return window.__lottieApiPromise;
    }

    function renderActiveScene() {
      clearStaticAnimation();
      staticStage.innerHTML = '';
      const scene = analyzedScenes[activeSceneIndex];
      const source = sourceSceneJsons[activeSceneIndex]?.data;
      if (!scene || !source) return;

      const width = scene.w || source.w || 1125;
      const height = scene.h || source.h || 600;
      staticStage.style.aspectRatio = `${width} / ${height}`;

      const renderRoot = document.createElement('div');
      renderRoot.className = 'static-render';
      staticStage.appendChild(renderRoot);

      const hotspotLayer = document.createElement('div');
      hotspotLayer.className = 'hotspot-layer';
      staticStage.appendChild(hotspotLayer);

      ensureLottieApi().then((lottieApi) => {
        if (!renderRoot.isConnected) return;
        if (!lottieApi) {
          renderRoot.innerHTML = '<div class="visual-note" style="padding:16px">Lottie 播放器未加载，无法渲染静态画面。</div>';
          return;
        }
        staticAnimation = lottieApi.loadAnimation({
          container: renderRoot,
          renderer: 'svg',
          loop: false,
          autoplay: false,
          animationData: source,
        });
        staticAnimation.addEventListener('DOMLoaded', () => {
          staticAnimation.goToAndStop(0, true);
        });
      });

      const layersByHitPriority = [...scene.layers].sort((a, b) => {
        const boundsA = a.bounds || fallbackBounds(a);
        const boundsB = b.bounds || fallbackBounds(b);
        return (boundsB.width * boundsB.height) - (boundsA.width * boundsA.height);
      });

      layersByHitPriority.forEach((layer) => {
        const bounds = layer.bounds || fallbackBounds(layer);
        const hotspot = document.createElement('div');
        hotspot.className = 'hotspot';
        hotspot.dataset.code = layer.code;
        hotspot.dataset.targetCode = layer.target_code || layer.code;
        hotspot.title = `${layer.code} · ${layerDisplayName(layer)}`;
        hotspot.setAttribute('role', 'button');
        hotspot.setAttribute('tabindex', '0');
        hotspot.setAttribute('aria-label', hotspot.title);
        hotspot.style.left = bounds.left + '%';
        hotspot.style.top = bounds.top + '%';
        hotspot.style.width = bounds.width + '%';
        hotspot.style.height = bounds.height + '%';
        hotspot.innerHTML = [
          '<span class="hotspot-edge top"></span>',
          '<span class="hotspot-edge right"></span>',
          '<span class="hotspot-edge bottom"></span>',
          '<span class="hotspot-edge left"></span>',
          '<span class="marker-row"><span class="marker deco">装</span><span class="marker highlight">突</span></span>',
        ].join('');
        hotspot.querySelectorAll('.hotspot-edge').forEach((edge) => {
          edge.addEventListener('mouseenter', () => hotspot.classList.add('hovered'));
          edge.addEventListener('mouseleave', () => hotspot.classList.remove('hovered'));
        });
        hotspot.addEventListener('click', (event) => {
          event.stopPropagation();
          openLayerMenu(layer, event.clientX, event.clientY);
        });
        hotspot.addEventListener('keydown', (event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            const rect = hotspot.getBoundingClientRect();
            openLayerMenu(layer, rect.left + rect.width / 2, rect.top + rect.height / 2);
          }
        });
        hotspotLayer.appendChild(hotspot);
      });

      updateSelectionSummary();
    }

    function setLayerType(layer, type) {
      const code = layer.code;
      const targetCode = layer.target_code || code;
      const state = targetSelectionState(targetCode);
      state.targetCode = targetCode;
      if (type === 'deco') state.deco = !state.deco;
      if (type === 'highlight') state.highlight = !state.highlight;
      clearSelectionTarget(targetCode);
      if (state.deco || state.highlight) selectedTypes.set(code, state);
      updateSelectionSummary();
    }

    function clearLayerType(code, targetCode) {
      clearSelectionTarget(targetCode || code);
      updateSelectionSummary();
    }

    function openLayerMenu(layer, x, y) {
      const state = targetSelectionState(layer.target_code || layer.code);
      layerMenu.innerHTML = '';

      const title = document.createElement('div');
      title.className = 'layer-menu-title';
      title.textContent = `${layer.code} · ${layerDisplayName(layer)}`;
      layerMenu.appendChild(title);

      [
        ['deco', '装饰元素'],
        ['highlight', '突出元素'],
      ].forEach(([type, text]) => {
        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'menu-choice' + (state[type] ? ' active' : '');
        item.textContent = text;
        item.addEventListener('click', () => {
          setLayerType(layer, type);
          hideLayerMenu();
        });
        layerMenu.appendChild(item);
      });

      const clear = document.createElement('button');
      clear.type = 'button';
      clear.className = 'menu-choice warn';
      clear.textContent = '清除标记';
      clear.addEventListener('click', () => {
        clearLayerType(layer.code, layer.target_code || layer.code);
        hideLayerMenu();
      });
      layerMenu.appendChild(clear);

      layerMenu.classList.remove('hidden');
      const menuWidth = 168;
      const menuHeight = 150;
      layerMenu.style.left = Math.max(8, Math.min(window.innerWidth - menuWidth - 8, x + 8)) + 'px';
      layerMenu.style.top = Math.max(8, Math.min(window.innerHeight - menuHeight - 8, y + 8)) + 'px';
    }

    async function analyzeCandidates() {
      if (!filesAreValid()) {
        clearVisualSelection();
        setStatus('请选择 2-4 个 JSON 文件。', true);
        return;
      }

      analyzeBtn.disabled = true;
      setStatus('正在识别可选元素...');
      try {
        const sourceJsons = await readSourceSceneJsons();
        const formData = new FormData();
        Array.from(scenesInput.files).forEach((file) => formData.append('scenes', file));
        const response = await fetch('/analyze', { method: 'POST', body: formData });
        const data = await response.json();
        if (!response.ok || !data.ok) {
          throw new Error(data.error || '识别失败');
        }
        renderCandidates(data.scenes, sourceJsons);
        setStatus('识别完成。可在静态画面中标记增强元素，也可以直接生成基础切换动效。');
      } catch (error) {
        clearVisualSelection();
        setStatus(error.message, true);
      } finally {
        analyzeBtn.disabled = false;
      }
    }

    scenesInput.addEventListener('change', () => {
      if (filesAreValid()) analyzeCandidates();
      else clearVisualSelection();
    });

    analyzeBtn.addEventListener('click', analyzeCandidates);

    document.addEventListener('click', (event) => {
      if (!layerMenu.contains(event.target)) hideLayerMenu();
    });

    window.addEventListener('resize', hideLayerMenu);

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const files = document.getElementById('scenes').files;
      if (files.length < 2 || files.length > 4) {
        setStatus('请选择 2-4 个 JSON 文件。', true);
        return;
      }

      btn.disabled = true;
      logEl.classList.add('hidden');
      setStatus('生成中，正在生成动效预览...');

      try {
        const formData = new FormData(form);
        const selections = collectSelections();
        formData.set('deco', selections.deco);
        formData.set('highlight', selections.highlight);
        const response = await fetch('/generate', { method: 'POST', body: formData });
        const data = await response.json();
        if (!response.ok || !data.ok) {
          throw new Error(data.error || '生成失败');
        }
        const cacheBust = '?t=' + Date.now();
        preview.src = data.preview_url + cacheBust;
        preview.classList.remove('hidden');
        titleEl.textContent = '动效预览';
        pathEl.textContent = '可继续修改上方静态标记，然后再次生成。JSON 下载在预览面板内完成。';
        logEl.textContent = data.log || '';
        setStatus('生成完成。可在下方预览动效并下载 JSON；也可以继续调整静态标记后再次生成。');
      } catch (error) {
        preview.removeAttribute('src');
        preview.classList.add('hidden');
        titleEl.textContent = '生成失败';
        pathEl.textContent = '';
        setStatus(error.message, true);
      } finally {
        btn.disabled = false;
      }
    });

    form.addEventListener('reset', () => {
      setTimeout(() => {
        clearVisualSelection();
        preview.removeAttribute('src');
        preview.classList.add('hidden');
        logEl.classList.add('hidden');
        titleEl.textContent = '还没有生成结果';
        pathEl.textContent = '';
        setStatus('等待选择文件。');
      }, 0);
    });
  </script>
</body>
</html>
"""


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class MotionToolHandler(BaseHTTPRequestHandler):
    server_version = "HeadImgMotionTool/1.0"

    def log_message(self, fmt: str, *args) -> None:
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(INDEX_HTML)
            return
        if parsed.path == "/vendor/lottie.min.js":
            self._serve_static_file(get_lottie_player_path(), "application/javascript")
            return
        if parsed.path.startswith("/runs/"):
            self._serve_run_file(parsed.path, parsed.query)
            return
        self.send_error(404, "Not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path not in ("/generate", "/analyze"):
            self.send_error(404, "Not found")
            return
        try:
            if parsed.path == "/analyze":
                result = self._handle_analyze()
            else:
                result = self._handle_generate()
            self._send_json(result)
        except Exception as exc:  # noqa: BLE001 - user-facing local tool
            self._send_json({"ok": False, "error": str(exc)}, status=500)

    def _handle_analyze(self) -> dict:
        if not PIPELINE_SCRIPT.exists():
            raise RuntimeError(f"找不到流水线脚本: {PIPELINE_SCRIPT}")

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)
        _, files = parse_multipart(self.headers.get("Content-Type", ""), body)
        scene_files = [item for item in files if item["name"] == "scenes" and item["data"]]
        if not (2 <= len(scene_files) <= 4):
            raise ValueError("需要上传 2-4 个静态 JSON 文件。")

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        analyze_dir = ANALYZE_DIR / f"{stamp}-{uuid.uuid4().hex[:6]}"
        input_dir = analyze_dir / "inputs"
        stage_dir = analyze_dir / "stage"
        input_dir.mkdir(parents=True, exist_ok=True)
        stage_dir.mkdir(parents=True, exist_ok=True)

        input_paths = save_uploaded_scenes(scene_files, input_dir)
        pipeline = load_pipeline_module()

        capture = io.StringIO()
        with contextlib.redirect_stdout(capture):
            parse_out = pipeline.stage_parse([str(p) for p in input_paths])
            classify_out = pipeline.stage_classify(parse_out, str(stage_dir))

        return {
            "ok": True,
            "scenes": build_candidate_payload(classify_out),
            "log": capture.getvalue().strip(),
        }

    def _handle_generate(self) -> dict:
        if not PIPELINE_SCRIPT.exists():
            raise RuntimeError(f"找不到流水线脚本: {PIPELINE_SCRIPT}")

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)
        fields, files = parse_multipart(self.headers.get("Content-Type", ""), body)

        scene_files = [item for item in files if item["name"] == "scenes" and item["data"]]
        if not (2 <= len(scene_files) <= 4):
            raise ValueError("需要上传 2-4 个静态 JSON 文件。")

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_id = f"{stamp}-motion-{uuid.uuid4().hex[:6]}"
        run_dir = RUNS_DIR / run_id
        input_dir = run_dir / "inputs"
        output_dir = run_dir / "output"
        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        input_paths = save_uploaded_scenes(scene_files, input_dir)

        cmd = [sys.executable, str(PIPELINE_SCRIPT), *[str(p) for p in input_paths], str(output_dir)]
        deco = (fields.get("deco") or "").strip()
        highlight = (fields.get("highlight") or "").strip()
        if deco:
            cmd.extend(["--deco", deco])
        if highlight:
            cmd.extend(["--highlight", highlight])

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run(
            cmd,
            cwd=str(SKILL_ROOT),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )

        log = "\n".join(part for part in [proc.stdout.strip(), proc.stderr.strip()] if part)
        if proc.returncode != 0:
            raise RuntimeError(log or f"流水线退出码: {proc.returncode}")

        merged = output_dir / "merged_output.json"
        preview = output_dir / "preview_embedded.html"
        if not merged.exists() or not preview.exists():
            raise RuntimeError("流水线完成但缺少 merged_output.json 或 preview_embedded.html。")

        return {
            "ok": True,
            "run_id": run_id,
            "output_dir": str(output_dir),
            "json_url": f"/runs/{run_id}/output/merged_output.json",
            "preview_url": f"/runs/{run_id}/output/preview_embedded.html",
            "log": log,
        }

    def _serve_run_file(self, path: str, query: str) -> None:
        rel = unquote(path[len("/runs/") :])
        target = (RUNS_DIR / rel).resolve()
        runs_root = RUNS_DIR.resolve()
        if target != runs_root and runs_root not in target.parents:
            self.send_error(403, "Forbidden")
            return
        if not target.is_file():
            self.send_error(404, "Not found")
            return

        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        payload = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        if parse_qs(query).get("download") == ["1"] or target.name == "merged_output.json":
            self.send_header("Content-Disposition", f'attachment; filename="{target.name}"')
        self.end_headers()
        self.wfile.write(payload)

    def _serve_static_file(self, target: Path, content_type: str | None = None) -> None:
        if not target.is_file():
            self.send_error(404, "Not found")
            return

        payload = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type or mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_html(self, html: str) -> None:
        payload = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, data: dict, status: int = 200) -> None:
        payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def get_lottie_player_path() -> Path:
    target = VENDOR_DIR / "lottie.min.js"
    if target.exists() and target.stat().st_size > 100_000:
        return target

    VENDOR_DIR.mkdir(parents=True, exist_ok=True)
    search_roots = [RUNS_DIR, SKILL_ROOT]
    for root in search_roots:
        if not root.exists():
            continue
        for candidate in root.rglob("lottie.min.js"):
            if candidate.resolve() == target.resolve():
                continue
            if candidate.is_file() and candidate.stat().st_size > 100_000:
                target.write_bytes(candidate.read_bytes())
                return target

    urlretrieve(LOTTIE_PLAYER_URL, target)
    return target


def parse_multipart(content_type: str, body: bytes) -> tuple[dict[str, str], list[dict]]:
    if "multipart/form-data" not in content_type:
        raise ValueError("请求格式不是 multipart/form-data。")
    raw = (
        f"Content-Type: {content_type}\r\n"
        "MIME-Version: 1.0\r\n\r\n"
    ).encode("utf-8") + body
    message = BytesParser(policy=policy.default).parsebytes(raw)
    fields: dict[str, str] = {}
    files: list[dict] = []

    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if not name:
            continue
        filename = part.get_filename()
        data = part.get_payload(decode=True) or b""
        if filename:
            files.append({"name": name, "filename": filename, "data": data})
        else:
            charset = part.get_content_charset() or "utf-8"
            fields[name] = data.decode(charset, errors="replace")
    return fields, files


def save_uploaded_scenes(scene_files: list[dict], input_dir: Path) -> list[Path]:
    input_paths = []
    for index, file_item in enumerate(scene_files, start=1):
        filename = Path(file_item["filename"] or f"scene-{index}.json").name
        if not filename.lower().endswith(".json"):
            filename = f"scene-{index}.json"
        target = input_dir / f"{index:02d}-{filename}"
        target.write_bytes(file_item["data"])
        input_paths.append(target)
    return input_paths


def load_pipeline_module():
    global PIPELINE_MODULE
    if PIPELINE_MODULE is not None:
        return PIPELINE_MODULE
    spec = importlib.util.spec_from_file_location("head_img_motion_pipeline", PIPELINE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载流水线脚本: {PIPELINE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    PIPELINE_MODULE = module
    return module


def build_candidate_payload(classify_out: dict) -> list[dict]:
    scenes = []
    meta = classify_out.get("meta", {})
    canvas_w = float(meta.get("w") or 1125)
    canvas_h = float(meta.get("h") or 600)
    assets_map = {asset.get("id"): asset for asset in classify_out.get("assets", []) if asset.get("id")}
    for scene in classify_out.get("scenes", []):
        layers = []
        for layer in scene.get("fg", []):
            tag = scene.get("tag", "")
            ind = layer.get("ind")
            if not tag or ind is None:
                continue
            code = f"{tag.upper()}_{ind}"
            root_candidate = build_layer_candidate(
                layer, tag, canvas_w, canvas_h, assets_map,
                code=code, target_code=code,
            )
            nested_candidates = build_nested_layer_candidates(
                layer, tag, canvas_w, canvas_h, assets_map,
                parent_code=code, target_code=code,
            )
            if should_use_nested_candidates(root_candidate["bounds"], nested_candidates):
                layers.extend(nested_candidates)
            else:
                layers.append(root_candidate)
        scenes.append({
            "tag": scene.get("tag", ""),
            "label": scene.get("label", scene.get("tag", "")).upper(),
            "w": round(canvas_w, 2),
            "h": round(canvas_h, 2),
            "layers": layers,
        })
    return scenes


def build_layer_candidate(
    layer: dict,
    tag: str,
    canvas_w: float,
    canvas_h: float,
    assets_map: dict,
    code: str,
    target_code: str,
    parent_code: str | None = None,
    nested: bool = False,
) -> dict:
    pos = layer.get("pos") or [0, 0]
    anc = layer.get("anc") or [0, 0]
    scl = layer.get("scl") or [100, 100, 100]
    asset_w, asset_h = layer_dimensions(layer, assets_map)
    ind = layer.get("ind")
    name = layer.get("nm") or f"layer_{ind}"
    if nested and parent_code:
        name = f"{name}（{parent_code} 内）"
    return {
        "code": code,
        "target_code": target_code,
        "parent_code": parent_code or "",
        "name": name,
        "index": ind,
        "type": layer.get("ty", 2),
        "nested": nested,
        "group": layer.get("group_id", ""),
        "dir": layer.get("dir", ""),
        "x": round(float(pos[0]), 1) if len(pos) > 0 else 0,
        "y": round(float(pos[1]), 1) if len(pos) > 1 else 0,
        "anchor": [round(float(anc[0]), 2), round(float(anc[1]), 2)],
        "scale": [round(float(scl[0]), 2), round(float(scl[1]), 2)],
        "asset_w": round(float(asset_w), 2),
        "asset_h": round(float(asset_h), 2),
        "scene_w": round(canvas_w, 2),
        "scene_h": round(canvas_h, 2),
        "bounds": build_layer_bounds(layer, canvas_w, canvas_h, assets_map),
    }


def layer_dimensions(layer: dict, assets_map: dict | None = None) -> tuple[float, float]:
    assets_map = assets_map or {}
    ty = layer.get("ty", 2)
    ref_id = layer.get("refId", "")
    asset = assets_map.get(ref_id, {})

    if ty == 0:
        width = layer.get("w") or asset.get("w") or layer.get("aw") or 100
        height = layer.get("h") or asset.get("h") or layer.get("ah") or 100
    elif ty == 2:
        width = layer.get("aw") or asset.get("w") or layer.get("w") or 100
        height = layer.get("ah") or asset.get("h") or layer.get("h") or 100
    elif ty == 4:
        shape_bounds = shape_local_bounds(layer.get("shapes"))
        if shape_bounds:
            width = shape_bounds[2] - shape_bounds[0]
            height = shape_bounds[3] - shape_bounds[1]
        else:
            width = layer.get("w") or layer.get("aw") or asset.get("w") or 100
            height = layer.get("h") or layer.get("ah") or asset.get("h") or 100
    else:
        width = layer.get("w") or layer.get("aw") or asset.get("w") or 100
        height = layer.get("h") or layer.get("ah") or asset.get("h") or 100

    return max(1.0, float(width)), max(1.0, float(height))


def should_use_nested_candidates(parent_bounds: dict, nested_candidates: list[dict]) -> bool:
    if not nested_candidates:
        return False
    width = float(parent_bounds.get("width") or 0)
    height = float(parent_bounds.get("height") or 0)
    area = width * height
    return width >= 55.0 or height >= 55.0 or area >= 2200.0


def build_nested_layer_candidates(
    layer: dict,
    tag: str,
    canvas_w: float,
    canvas_h: float,
    assets_map: dict,
    parent_code: str,
    target_code: str,
) -> list[dict]:
    if layer.get("ty") != 0:
        return []
    asset = assets_map.get(layer.get("refId"), {})
    children = asset.get("layers") or []
    if not children:
        return []

    parent_matrix = layer_transform_matrix(layer)
    candidates: list[dict] = []
    for index, child in enumerate(children):
        candidates.extend(build_raw_visual_candidates(
            child, tag, canvas_w, canvas_h, assets_map,
            parent_matrix=parent_matrix,
            prefix=parent_code,
            target_code=target_code,
            parent_code=parent_code,
            fallback_index=index,
            depth=0,
        ))
    return candidates


def build_raw_visual_candidates(
    raw_layer: dict,
    tag: str,
    canvas_w: float,
    canvas_h: float,
    assets_map: dict,
    parent_matrix: tuple[float, float, float, float, float, float],
    prefix: str,
    target_code: str,
    parent_code: str,
    fallback_index: int,
    depth: int,
) -> list[dict]:
    if not is_raw_layer_visible(raw_layer):
        return []

    local_bounds = raw_layer_local_bounds(raw_layer, assets_map)
    if not local_bounds:
        return []

    ind = raw_layer.get("ind", fallback_index)
    code = f"{prefix}.{ind}"
    matrix = matrix_multiply(parent_matrix, raw_layer_transform_matrix(raw_layer))
    pixel_bounds = transform_bounds_with_matrix(local_bounds, matrix)
    percent_bounds = pixel_bounds_to_percent(pixel_bounds, canvas_w, canvas_h)
    if not percent_bounds:
        return []

    if raw_layer.get("ty") == 0 and depth < 3 and is_large_percent_bounds(percent_bounds):
        nested_asset = assets_map.get(raw_layer.get("refId"), {})
        nested_children = nested_asset.get("layers") or []
        nested_candidates: list[dict] = []
        for child_index, child in enumerate(nested_children):
            nested_candidates.extend(build_raw_visual_candidates(
                child, tag, canvas_w, canvas_h, assets_map,
                parent_matrix=matrix,
                prefix=code,
                target_code=target_code,
                parent_code=parent_code,
                fallback_index=child_index,
                depth=depth + 1,
            ))
        if nested_candidates:
            return nested_candidates

    name = raw_layer.get("nm") or f"layer_{ind}"
    center_x = (percent_bounds["left"] + percent_bounds["width"] / 2.0) / 100.0 * canvas_w
    center_y = (percent_bounds["top"] + percent_bounds["height"] / 2.0) / 100.0 * canvas_h
    asset_w = max(1.0, local_bounds[2] - local_bounds[0])
    asset_h = max(1.0, local_bounds[3] - local_bounds[1])
    return [{
        "code": code,
        "target_code": target_code,
        "parent_code": parent_code,
        "name": name,
        "index": ind,
        "type": raw_layer.get("ty", 2),
        "nested": True,
        "group": "",
        "dir": "",
        "x": round(center_x, 1),
        "y": round(center_y, 1),
        "anchor": [0, 0],
        "scale": [100, 100],
        "asset_w": round(float(asset_w), 2),
        "asset_h": round(float(asset_h), 2),
        "scene_w": round(canvas_w, 2),
        "scene_h": round(canvas_h, 2),
        "bounds": percent_bounds,
    }]


def is_large_percent_bounds(bounds: dict) -> bool:
    width = float(bounds.get("width") or 0)
    height = float(bounds.get("height") or 0)
    return width >= 55.0 or height >= 55.0 or width * height >= 2200.0


def raw_layer_local_bounds(raw_layer: dict, assets_map: dict) -> tuple[float, float, float, float] | None:
    ty = raw_layer.get("ty", 2)
    if ty == 4:
        return shape_local_bounds(raw_layer.get("shapes"))
    width, height = raw_layer_dimensions(raw_layer, assets_map)
    return 0.0, 0.0, width, height


def raw_layer_dimensions(raw_layer: dict, assets_map: dict) -> tuple[float, float]:
    asset = assets_map.get(raw_layer.get("refId"), {})
    width = raw_layer.get("w") or raw_layer.get("aw") or asset.get("w") or 100
    height = raw_layer.get("h") or raw_layer.get("ah") or asset.get("h") or 100
    return max(1.0, float(width)), max(1.0, float(height))


def is_raw_layer_visible(raw_layer: dict) -> bool:
    if raw_layer.get("hd"):
        return False
    opacity = read_scalar((raw_layer.get("ks") or {}).get("o"), 100)
    return opacity > 1


def layer_transform_matrix(layer: dict) -> tuple[float, float, float, float, float, float]:
    pos = layer.get("pos") or [0, 0, 0]
    anc = layer.get("anc") or [0, 0, 0]
    scl = layer.get("scl") or [100, 100, 100]
    rot = layer.get("rot", layer.get("r", 0))
    return transform_matrix(pos, anc, scl, rot)


def raw_layer_transform_matrix(raw_layer: dict) -> tuple[float, float, float, float, float, float]:
    ks = raw_layer.get("ks") or {}
    pos = read_vector(ks.get("p"), [0, 0, 0])
    anc = read_vector(ks.get("a"), [0, 0, 0])
    scl = read_vector(ks.get("s"), [100, 100, 100])
    rot = read_scalar(ks.get("r"), 0)
    return transform_matrix(pos, anc, scl, rot)


def transform_matrix(pos, anc, scl, rot) -> tuple[float, float, float, float, float, float]:
    px = float(pos[0]) if len(pos) > 0 else 0.0
    py = float(pos[1]) if len(pos) > 1 else 0.0
    ax = float(anc[0]) if len(anc) > 0 else 0.0
    ay = float(anc[1]) if len(anc) > 1 else 0.0
    sx = float(scl[0]) / 100.0 if len(scl) > 0 else 1.0
    sy = float(scl[1]) / 100.0 if len(scl) > 1 else 1.0
    angle = math.radians(float(rot or 0))
    cos_r = math.cos(angle)
    sin_r = math.sin(angle)
    a = cos_r * sx
    b = sin_r * sx
    c = -sin_r * sy
    d = cos_r * sy
    e = px - ax * a - ay * c
    f = py - ax * b - ay * d
    return a, b, c, d, e, f


def matrix_multiply(
    left: tuple[float, float, float, float, float, float],
    right: tuple[float, float, float, float, float, float],
) -> tuple[float, float, float, float, float, float]:
    a1, b1, c1, d1, e1, f1 = left
    a2, b2, c2, d2, e2, f2 = right
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1,
    )


def transform_bounds_with_matrix(
    bounds: tuple[float, float, float, float],
    matrix: tuple[float, float, float, float, float, float],
) -> tuple[float, float, float, float]:
    a, b, c, d, e, f = matrix
    x1, y1, x2, y2 = bounds
    points = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    xs = [a * x + c * y + e for x, y in points]
    ys = [b * x + d * y + f for x, y in points]
    return min(xs), min(ys), max(xs), max(ys)


def pixel_bounds_to_percent(
    bounds: tuple[float, float, float, float],
    canvas_w: float,
    canvas_h: float,
) -> dict | None:
    left, top, right, bottom = bounds
    visible_left = max(0.0, min(canvas_w, left))
    visible_top = max(0.0, min(canvas_h, top))
    visible_right = max(0.0, min(canvas_w, right))
    visible_bottom = max(0.0, min(canvas_h, bottom))
    if visible_right - visible_left < 2 or visible_bottom - visible_top < 2:
        return None
    return {
        "left": round(visible_left / canvas_w * 100.0, 3),
        "top": round(visible_top / canvas_h * 100.0, 3),
        "width": round(max(0.5, (visible_right - visible_left) / canvas_w * 100.0), 3),
        "height": round(max(0.5, (visible_bottom - visible_top) / canvas_h * 100.0), 3),
    }


def build_layer_bounds(layer: dict, canvas_w: float, canvas_h: float, assets_map: dict | None = None) -> dict:
    pos = layer.get("pos") or [0, 0]
    anc = layer.get("anc") or [0, 0]
    scl = layer.get("scl") or [100, 100, 100]
    asset_w, asset_h = layer_dimensions(layer, assets_map)
    shape_bounds = shape_local_bounds(layer.get("shapes")) if layer.get("ty") == 4 else None
    local_left = shape_bounds[0] if shape_bounds else 0.0
    local_top = shape_bounds[1] if shape_bounds else 0.0
    x = float(pos[0]) if len(pos) > 0 else 0.0
    y = float(pos[1]) if len(pos) > 1 else 0.0
    ax = float(anc[0]) if len(anc) > 0 else asset_w / 2
    ay = float(anc[1]) if len(anc) > 1 else asset_h / 2
    sx = abs(float(scl[0]) / 100.0) if len(scl) > 0 else 1.0
    sy = abs(float(scl[1]) / 100.0) if len(scl) > 1 else 1.0

    width = max(1.0, asset_w * sx)
    height = max(1.0, asset_h * sy)
    left = x + local_left * sx - ax * sx
    top = y + local_top * sy - ay * sy
    right = left + width
    bottom = top + height

    visible_left = max(0.0, min(canvas_w, left))
    visible_top = max(0.0, min(canvas_h, top))
    visible_right = max(0.0, min(canvas_w, right))
    visible_bottom = max(0.0, min(canvas_h, bottom))

    if visible_right - visible_left < 2 or visible_bottom - visible_top < 2:
        min_w = min(canvas_w, max(24.0, canvas_w * 0.04))
        min_h = min(canvas_h, max(24.0, canvas_h * 0.10))
        visible_left = max(0.0, min(canvas_w - min_w, x - min_w / 2))
        visible_top = max(0.0, min(canvas_h - min_h, y - min_h / 2))
        visible_right = visible_left + min_w
        visible_bottom = visible_top + min_h

    return {
        "left": round(visible_left / canvas_w * 100.0, 3),
        "top": round(visible_top / canvas_h * 100.0, 3),
        "width": round(max(0.5, (visible_right - visible_left) / canvas_w * 100.0), 3),
        "height": round(max(0.5, (visible_bottom - visible_top) / canvas_h * 100.0), 3),
    }


def read_vector(prop, default: list[float]) -> list[float]:
    value = read_raw_value(prop, default)
    if isinstance(value, (int, float)):
        value = [value]
    if not isinstance(value, list):
        value = default
    out = list(value[:3])
    while len(out) < 3:
        out.append(default[len(out)] if len(default) > len(out) else 0)
    return out


def read_scalar(prop, default: float) -> float:
    value = read_raw_value(prop, default)
    if isinstance(value, list):
        value = value[0] if value else default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def read_raw_value(prop, default):
    if isinstance(prop, dict):
        value = prop.get("k", default)
    else:
        value = prop if prop is not None else default
    if isinstance(value, list) and value and isinstance(value[0], dict):
        first = value[0]
        value = first.get("s", first.get("e", default))
    return value


def shape_local_bounds(shapes) -> tuple[float, float, float, float] | None:
    def path_bounds(path_data) -> tuple[float, float, float, float] | None:
        if not isinstance(path_data, dict):
            return None
        xs: list[float] = []
        ys: list[float] = []
        for point in path_data.get("v", []) or []:
            if isinstance(point, list) and len(point) >= 2:
                xs.append(float(point[0]))
                ys.append(float(point[1]))
        if not xs or not ys:
            return None
        return min(xs), min(ys), max(xs), max(ys)

    def merge_bounds(items: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float] | None:
        valid = [item for item in items if item]
        if not valid:
            return None
        return (
            min(item[0] for item in valid),
            min(item[1] for item in valid),
            max(item[2] for item in valid),
            max(item[3] for item in valid),
        )

    def apply_transform(
        bounds: tuple[float, float, float, float] | None,
        transform: dict | None,
    ) -> tuple[float, float, float, float] | None:
        if not bounds or not transform:
            return bounds

        import math

        pos = read_vector(transform.get("p"), [0, 0, 0])
        anc = read_vector(transform.get("a"), [0, 0, 0])
        scl = read_vector(transform.get("s"), [100, 100, 100])
        rot = read_scalar(transform.get("r"), 0)
        sx = float(scl[0]) / 100.0
        sy = float(scl[1]) / 100.0
        rad = math.radians(rot)
        cos_r = math.cos(rad)
        sin_r = math.sin(rad)

        x1, y1, x2, y2 = bounds
        points = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
        out_x: list[float] = []
        out_y: list[float] = []
        for px, py in points:
            tx = (px - float(anc[0])) * sx
            ty = (py - float(anc[1])) * sy
            out_x.append(tx * cos_r - ty * sin_r + float(pos[0]))
            out_y.append(tx * sin_r + ty * cos_r + float(pos[1]))
        return min(out_x), min(out_y), max(out_x), max(out_y)

    def item_bounds(item: dict) -> tuple[float, float, float, float] | None:
        item_type = item.get("ty")
        if item_type == "sh":
            key_data = (item.get("ks") or {}).get("k")
            if isinstance(key_data, dict):
                return path_bounds(key_data)
            if isinstance(key_data, list):
                bounds_list = []
                for keyframe in key_data:
                    if not isinstance(keyframe, dict):
                        continue
                    for key in ("s", "e"):
                        value = keyframe.get(key)
                        if isinstance(value, list) and value and isinstance(value[0], dict):
                            bound = path_bounds(value[0])
                            if bound:
                                bounds_list.append(bound)
                return merge_bounds(bounds_list)
        if item_type == "gr":
            return group_bounds(item.get("it"))
        return None

    def group_bounds(items) -> tuple[float, float, float, float] | None:
        bounds_list = []
        transform = None
        for item in items or []:
            if not isinstance(item, dict):
                continue
            if item.get("ty") == "tr":
                transform = item
            else:
                bound = item_bounds(item)
                if bound:
                    bounds_list.append(bound)
        return apply_transform(merge_bounds(bounds_list), transform)

    return group_bounds(shapes)


def sanitize_slug(value: str) -> str:
    value = value.strip().replace("\\", "-").replace("/", "-")
    allowed = []
    for char in value:
        if char.isascii() and (char.isalnum() or char in ("-", "_")):
            allowed.append(char)
        elif char.isspace():
            allowed.append("-")
    slug = "".join(allowed).strip("-_")
    return slug[:48] or "run"


def find_available_port(host: str, start_port: int) -> int:
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex((host, port)) != 0:
                return port
    raise RuntimeError("没有找到可用端口。")


def main() -> None:
    parser = argparse.ArgumentParser(description="会场头图 Lottie 本地工具")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    port = find_available_port(args.host, args.port)
    server = ThreadingHTTPServer((args.host, port), MotionToolHandler)
    url = f"http://{args.host}:{port}/"
    print(f"会场头图 Lottie 工具已启动: {url}")
    print("按 Ctrl+C 停止。")
    if not args.no_open:
        webbrowser.open(url)
    server.serve_forever()


if __name__ == "__main__":
    main()
