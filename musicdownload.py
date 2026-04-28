import os
import re
import time
import uuid
import shutil
import threading
import subprocess
import sys
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from contextlib import contextmanager
import contextlib
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, flash, jsonify, redirect, render_template_string, request, session, send_file, url_for
from datetime import datetime

try:
    from musicdl import musicdl
    from musicdl.modules.utils import SongInfo, AudioLinkTester
    from musicdl.modules.sources import base as musicdl_base_source
    MUSICDL_AVAILABLE = True
except ImportError:
    MUSICDL_AVAILABLE = False
    musicdl = None
    SongInfo = None
    AudioLinkTester = None
    musicdl_base_source = None


app = Flask(__name__)
app.secret_key = os.environ.get("MUSIC_WEB_SECRET", "musicdownload-web-secret")

STYLE_CSS = """:root {
  --bg: #f3f6fb;
  --card: #ffffff;
  --line: #dbe3ef;
  --text: #1f2937;
  --muted: #6b7280;
  --primary: #2563eb;
  --primary-hover: #1d4ed8;
  --success: #e8f7ec;
  --error: #fdecec;
  --warning: #fff6e5;
  --pending: #eef2ff;
  --progress-bg: #e5edf9;
  --progress-fill: linear-gradient(90deg, #2563eb, #06b6d4);
}

* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: var(--bg);
  color: var(--text);
}

.page {
  max-width: 1440px;
  margin: 0 auto;
  padding: 24px;
}

.hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.hero h1 {
  margin: 0 0 8px;
  font-size: 32px;
}

.hero p, .hero-meta {
  margin: 0;
  color: var(--muted);
}

.hero-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  flex-wrap: wrap;
}

.card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
}

.card h2 {
  margin-top: 0;
  margin-bottom: 16px;
}

.search-form,
.field-group,
.inline-grid,
.actions,
.table-actions {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.inline-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

label span {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
}

input[type="text"],
input[type="number"],
select {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 12px 14px;
  font-size: 15px;
  background: #fff;
}

input[type="text"]:focus,
input[type="number"]:focus,
select:focus {
  outline: 2px solid rgba(37, 99, 235, 0.15);
  border-color: var(--primary);
}

.source-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
}

.source-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fafcff;
}

.checkbox-line {
  display: flex;
  align-items: center;
  gap: 10px;
}

.checkbox-line span {
  margin: 0;
  font-weight: 500;
}

.checkbox-stack {
  display: flex;
  flex-direction: column;
}

.checkbox-boxed {
  min-height: 48px;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 11px 14px;
  background: #fafcff;
}

button {
  border: none;
  border-radius: 12px;
  padding: 11px 16px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
}

button.primary {
  background: var(--primary);
  color: #fff;
}
button.primary:hover { background: var(--primary-hover); }

button.secondary, button.mini {
  background: #eef2ff;
  color: #1e3a8a;
}
button.secondary:hover, button.mini:hover {
  background: #e0e7ff;
}

button.mini {
  padding: 8px 12px;
}

.alert {
  padding: 14px 16px;
  border-radius: 12px;
  margin-bottom: 12px;
  border: 1px solid transparent;
}
.alert-success {
  background: var(--success);
  border-color: #b7e4c7;
}
.alert-error {
  background: var(--error);
  border-color: #f5b7b1;
}
.alert-warning {
  background: var(--warning);
  border-color: #f7d794;
}

.progress-card {
  border-color: #cfe0ff;
  background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
}

.progress-head,
.results-head,
.song-progress-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.results-head p,
.progress-head p,
.song-progress-head span {
  margin: 6px 0 0;
  color: var(--muted);
}

.progress-overview {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.progress-meta-row,
.job-metrics,
.results-tools,
.table-actions,
.source-summary {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}

.progress-meta-row strong {
  font-size: 28px;
}

.progress-bar-shell,
.mini-progress-shell {
  width: 100%;
  background: var(--progress-bg);
  border-radius: 999px;
  overflow: hidden;
}

.progress-bar-shell {
  height: 16px;
}

.mini-progress-shell {
  height: 8px;
}

.progress-bar-fill,
.mini-progress-fill {
  height: 100%;
  width: 0;
  background: var(--progress-fill);
  border-radius: inherit;
  transition: width 0.35s ease;
}

.job-message,
.job-current {
  margin: 0;
  color: var(--muted);
}

.metric-pill,
.tag,
.status-badge,
.mini-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 999px;
  font-weight: 700;
}

.metric-pill {
  background: #eff6ff;
  color: #1d4ed8;
}

.tag {
  background: #eff6ff;
  color: #1d4ed8;
}

.tag-zero {
  background: #f8fafc;
  color: #64748b;
  border: 1px dashed #cbd5e1;
}

.status-badge {
  padding: 9px 14px;
}

.status-pending,
.status-queued {
  background: var(--pending);
  color: #4338ca;
}

.status-running,
.status-preparing,
.status-downloading,
.status-transcoding {
  background: #e0f2fe;
  color: #0369a1;
}

.status-warning {
  background: #fff7e6;
  color: #b45309;
}

.status-completed {
  background: #e8f7ec;
  color: #166534;
}

.status-failed,
.status-skipped {
  background: #fdecec;
  color: #b91c1c;
}

.song-progress-panel {
  margin-top: 18px;
  border-top: 1px solid #e7edf6;
  padding-top: 18px;
}

.song-progress-list {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 520px;
  overflow: auto;
  padding-right: 4px;
}

.song-progress-item {
  border: 1px solid #e5edf9;
  border-radius: 14px;
  padding: 12px 14px;
  background: #fbfdff;
}

.song-progress-title {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 10px;
}

.song-progress-title strong,
.song-progress-title span {
  display: block;
}

.song-progress-title span {
  margin-top: 4px;
  color: var(--muted);
  font-size: 13px;
}

.song-progress-desc {
  margin: 10px 0 0;
  color: var(--muted);
  font-size: 13px;
  word-break: break-word;
}

.song-progress-actions {
  margin-top: 10px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.mini-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 10px;
  background: #eef2ff;
  color: #1e3a8a;
  text-decoration: none;
  font-weight: 700;
}

.mini-link:hover {
  background: #e0e7ff;
}

.mini-button {
  border: none;
  border-radius: 10px;
  padding: 8px 12px;
  background: #f3f4f6;
  color: #374151;
  font-weight: 700;
  cursor: pointer;
}

.mini-button:hover {
  background: #e5e7eb;
}

.table-wrap {
  overflow: auto;
  margin-top: 16px;
}

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 1080px;
}

thead th {
  background: #f8fafc;
  font-size: 14px;
  text-align: left;
}

th, td {
  padding: 12px 10px;
  border-bottom: 1px solid #eef2f7;
  vertical-align: middle;
}

tr:hover td {
  background: #fafcff;
}

.center { text-align: center; }
.cover {
  width: 60px;
  height: 60px;
  object-fit: cover;
  border-radius: 12px;
  background: #eef2f7;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.cover-empty {
  font-size: 24px;
}

.action-cell {
  white-space: nowrap;
}

.summary-card code,
.hero code {
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 8px;
}

@media (max-width: 768px) {
  .page { padding: 16px; }
  .hero,
  .results-head,
  .progress-head,
  .song-progress-head,
  .song-progress-title {
    flex-direction: column;
    align-items: stretch;
  }

  .progress-meta-row strong {
    font-size: 22px;
  }
}

.browser-page {
  max-width: 1600px;
}

.browser-hero {
  margin-bottom: 16px;
}

.browser-card-head {
  margin-bottom: 16px;
}

.browser-meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.browser-path {
  margin: 8px 0 0;
  word-break: break-all;
}

.browser-breadcrumbs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-top: 8px;
}

.browser-breadcrumbs a {
  color: var(--primary);
  text-decoration: none;
  font-weight: 600;
}

.browser-breadcrumbs a:hover {
  text-decoration: underline;
}

.browser-table-wrap {
  margin-top: 10px;
}

.browser-name-cell {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  word-break: break-word;
}

.browser-name-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.browser-name-link {
  color: var(--text);
  text-decoration: none;
  font-size: 16px;
  font-weight: 700;
  line-height: 1.4;
  word-break: break-word;
}

.browser-name-link:hover {
  text-decoration: underline;
}

.browser-empty-action {
  color: var(--muted);
  font-size: 13px;
}

.browser-icon {
  font-size: 18px;
}

.browser-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.browser-actions-inline {
  margin-top: 0;
}

.browser-table tr.row-focus td {
  background: #eff6ff;
}
"""

INDEX_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>音乐下载器 · Web 版</title>
  <style>{{ style_css|safe }}</style>
</head>
<body>
  <div class="page">
    <header class="hero">
      <div>
        <h1>音乐下载器 · Web 版</h1>
      </div>
      <div class="hero-meta hero-actions">
        <span>当前地址：<code>{{ request.host_url.rstrip('/') }}</code></span>
        <button type="button" class="secondary" onclick="browseConfiguredSaveDir()">浏览下载目录</button>
      </div>
    </header>

    {% if not musicdl_available %}
      <div class="alert alert-error">
        <strong>musicdl 未安装：</strong> 请先执行 <code>pip install -r requirements.txt</code>
      </div>
    {% endif %}

    {% if not ffmpeg_available %}
      <div class="alert alert-warning">
        <strong>未检测到 ffmpeg：</strong> 当前环境无法把音频自动转成 MP3；如果选择“自动转 MP3”，会保留原始格式音频。
      </div>
    {% endif %}

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <section class="messages">
          {% for category, message in messages %}
            <div class="alert alert-{{ category }}">{{ message }}</div>
          {% endfor %}
        </section>
      {% endif %}
    {% endwith %}

    <section class="card">
      <h2>搜索设置</h2>
      <form method="post" class="search-form">
        <input type="hidden" name="action" value="search">

        <div class="field-group">
          <label>音乐来源</label>
          <div class="source-grid">
            {% for source in source_options %}
              <label class="source-item">
                <input type="checkbox" name="sources" value="{{ source.en }}"
                  {% if source.en in form.selected_sources %}checked{% endif %}>
                <span>{{ source.cn }}</span>
              </label>
            {% endfor %}
          </div>
        </div>

        <div class="inline-grid">
          <label>
            <span>搜索模式</span>
            <select name="search_mode">
              <option value="search_song" {% if form.search_mode == 'search_song' %}selected{% endif %}>搜索歌曲</option>
              <option value="parse_playlist" {% if form.search_mode == 'parse_playlist' %}selected{% endif %}>解析歌单链接</option>
            </select>
          </label>

          <label>
            <span>结果数量</span>
            <input type="number" name="limit" min="1" max="100" value="{{ form.limit }}">
          </label>
        </div>

        <label>
          <span>保存目录</span>
          <input type="text" name="save_dir" value="{{ form.save_dir }}" placeholder="输入服务端保存目录">
        </label>

        <div class="inline-grid">
          <label>
            <span>下载输出格式</span>
            <select name="output_format">
              <option value="mp3" {% if form.output_format == 'mp3' %}selected{% endif %}>自动转 MP3</option>
              <option value="original" {% if form.output_format == 'original' %}selected{% endif %}>保留原始格式</option>
            </select>
          </label>

          <label class="checkbox-stack">
            <span>转码细节</span>
            <span class="checkbox-line checkbox-boxed">
              <input type="checkbox" name="keep_original_audio" {% if form.keep_original_audio %}checked{% endif %}>
              <span>转 MP3 后保留原始音频</span>
            </span>
          </label>
        </div>

        <label>
          <span>关键词 / 歌单链接</span>
          <input type="text" name="keyword" value="{{ form.keyword }}" placeholder="输入歌曲名、歌手或歌单链接">
        </label>

        <label class="checkbox-line">
          <input type="checkbox" name="auto_download" {% if form.auto_download %}checked{% endif %}>
          <span>搜索完成后自动下载全部结果</span>
        </label>

        <div class="actions">
          <button type="submit" class="primary">开始搜索</button>
        </div>
      </form>
    </section>

    {% if active_download_job %}
      <section
        class="card progress-card"
        id="download-progress-card"
        data-job-id="{{ active_download_job.id }}"
        data-job-status="{{ active_download_job.status }}"
      >
        <div class="progress-head">
          <div>
            <h2>实时下载进度</h2>
            <p id="job-status-line">当前状态：<span id="job-status-text">{{ active_download_job.status_text }}</span></p>
          </div>
          <span class="status-badge status-{{ active_download_job.status }}" id="job-status-badge">{{ active_download_job.status_text }}</span>
        </div>

        <div class="progress-overview">
          <div class="progress-meta-row">
            <strong id="job-progress-percent">{{ '%.1f'|format(active_download_job.progress_percent or 0) }}%</strong>
            <span id="job-progress-count">已处理 {{ active_download_job.completed_songs }} / {{ active_download_job.total_songs }} 首</span>
          </div>
          <div class="progress-bar-shell">
            <div class="progress-bar-fill" id="job-progress-fill" style="width: {{ active_download_job.progress_percent or 0 }}%;"></div>
          </div>
          <p class="job-message" id="job-message">{{ active_download_job.message }}</p>
          <p class="job-current" id="job-current-song">
            {% if active_download_job.current_song %}
              当前歌曲：{{ active_download_job.current_song }}
            {% else %}
              当前歌曲：暂无
            {% endif %}
          </p>
          <div class="job-metrics">
            <span class="metric-pill">目标：<strong id="job-requested-count">{{ active_download_job.requested_count }}</strong></span>
            <span class="metric-pill">成功：<strong id="job-downloaded-count">{{ active_download_job.downloaded_count }}</strong></span>
            <span class="metric-pill">失败/跳过：<strong id="job-failed-count">{{ active_download_job.failed_count }}</strong></span>
          </div>
          <p class="job-current" id="job-output-format">输出格式：{{ active_download_job.output_format_requested_text }}{% if active_download_job.output_format_requested == 'mp3' and active_download_job.keep_original_audio %}（保留原始音频）{% endif %}</p>
          <div class="song-progress-actions">
            <button type="button" class="mini-button" id="job-open-dir-button" data-open-url="{{ active_download_job.open_dir_url }}" onclick="openDirectory(this.dataset.openUrl)">{{ active_download_job.open_dir_label or '浏览下载目录' }}</button>
          </div>
        </div>

        <div class="source-summary" id="job-source-summary">
          {% for source_name, count in active_download_job.per_source_requested.items() %}
            <span class="tag">{{ source_name }}：目标 {{ count }} 首</span>
          {% endfor %}
        </div>

        <div class="song-progress-panel">
          <div class="song-progress-head">
            <h3>歌曲进度</h3>
            <span>会自动刷新</span>
          </div>
          <div class="song-progress-list" id="job-song-list">
            {% for song in active_download_job.songs %}
              <div class="song-progress-item">
                <div class="song-progress-title">
                  <div>
                    <strong>{{ song.song_name }}</strong>
                    <span>{{ song.singers }} · {{ song.source }}</span>
                  </div>
                  <span class="mini-badge status-{{ song.status }}">{{ song.status_text }}</span>
                </div>
                <div class="mini-progress-shell">
                  <div class="mini-progress-fill" style="width: {{ song.percent or 0 }}%;"></div>
                </div>
                <p class="song-progress-desc">{{ song.description }}</p>
                {% if song.download_ready and song.download_url %}
                  <div class="song-progress-actions">
                    <a href="{{ song.download_url }}" class="mini-link" download>{{ song.download_label or '下载音频' }}</a>
                    {% if song.open_dir_url %}
                      <button type="button" class="mini-button" onclick="openDirectory('{{ song.open_dir_url }}')">{{ song.open_dir_label or '浏览目录' }}</button>
                    {% endif %}
                  </div>
                {% endif %}
              </div>
            {% endfor %}
          </div>
        </div>
      </section>
    {% endif %}

    {% if search_summary %}
      <section class="card summary-card">
        <h2>搜索来源统计</h2>
        <p><strong>搜索模式：</strong>{{ '搜索歌曲' if search_summary.search_mode == 'search_song' else '解析歌单链接' }}</p>
        <p><strong>关键词 / 输入：</strong><code>{{ search_summary.keyword }}</code></p>
        <p><strong>总结果数：</strong>{{ search_summary.total_results }}</p>
        <p><strong>当前输出策略：</strong>{{ output_format_text(form.output_format) }}{% if form.output_format == 'mp3' and not ffmpeg_available %}（当前环境未检测到 ffmpeg，实际会保留原始格式）{% endif %}</p>
        <div class="source-summary">
          {% for source_name, count in search_summary.per_source_counts.items() %}
            <span class="tag {% if count == 0 %}tag-zero{% endif %}">{{ source_name }}：{{ count }} 首</span>
          {% endfor %}
        </div>
      </section>
    {% endif %}

    {% if download_summary %}
      <section class="card summary-card">
        <h2>最近一次下载结果</h2>
        <p><strong>保存目录：</strong><code>{{ download_summary.save_dir }}</code></p>
        <p><strong>目标歌曲数：</strong>{{ download_summary.requested_count }}</p>
        <p><strong>成功下载数：</strong>{{ download_summary.downloaded_count }}</p>
        <p><strong>失败 / 跳过：</strong>{{ download_summary.failed_count }}</p>
        <p><strong>请求输出格式：</strong>{{ download_summary.output_format_requested_text }}</p>
        <p><strong>最终音频格式：</strong>{{ download_summary.final_audio_format_text }}</p>
        {% if download_summary.output_format_requested == 'mp3' %}
          <p><strong>需转码数量：</strong>{{ download_summary.transcode_required_count }}</p>
          <p><strong>转码成功：</strong>{{ download_summary.transcoded_count }}{% if download_summary.already_mp3_count %}，原本已是 MP3：{{ download_summary.already_mp3_count }}{% endif %}</p>
          <p><strong>转码失败：</strong>{{ download_summary.transcode_failed_count }}</p>
          <p><strong>保留原始音频：</strong>{{ '是' if download_summary.keep_original_audio else '否' }}</p>
        {% endif %}
        {% if download_summary.output_notice %}
          <p><strong>输出说明：</strong>{{ download_summary.output_notice }}</p>
        {% endif %}
        <div class="source-summary">
          {% for source_name, requested_count in download_summary.per_source_requested.items() %}
            <span class="tag">
              {{ source_name }}：成功 {{ download_summary.per_source_downloaded.get(source_name, 0) }} / 目标 {{ requested_count }}
            </span>
          {% endfor %}
        </div>
      </section>
    {% endif %}

    <section class="card">
      <div class="results-head">
        <div>
          <h2>搜索结果</h2>
          <p>
            {% if result_count %}
              当前共 {{ result_count }} 首
              {% if last_query %}，关键词：<code>{{ last_query }}</code>{% endif %}
            {% else %}
              暂无结果，请先搜索。
            {% endif %}
          </p>
        </div>
        {% if result_count %}
          <div class="results-tools">
            <button type="button" class="secondary" onclick="toggleRows(true)">全选</button>
            <button type="button" class="secondary" onclick="toggleRows(false)">取消全选</button>
          </div>
        {% endif %}
      </div>

      {% if result_count %}
        <form method="post">
          <div class="table-actions">
            <button type="submit" name="action" value="download_selected" class="primary">下载勾选项</button>
            <button type="submit" name="action" value="download_all" class="secondary">下载全部结果</button>
          </div>

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>选择</th>
                  <th>封面</th>
                  <th>歌曲名</th>
                  <th>歌手</th>
                  <th>专辑</th>
                  <th>原始 / 输出</th>
                  <th>大小</th>
                  <th>时长</th>
                  <th>来源</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {% for row in results %}
                  <tr>
                    <td class="center"><input type="checkbox" name="selected_rows" value="{{ row.row_id }}" class="row-check"></td>
                    <td class="center">
                      {% if row.cover_url %}
                        <img src="{{ row.cover_url }}" alt="cover" class="cover" loading="lazy">
                      {% else %}
                        <div class="cover cover-empty">🎵</div>
                      {% endif %}
                    </td>
                    <td>{{ row.song_name }}</td>
                    <td>{{ row.singers }}</td>
                    <td>{{ row.album }}</td>
                    <td class="center">{{ row.display_format }}</td>
                    <td class="center">{{ row.file_size }}</td>
                    <td class="center">{{ row.duration }}</td>
                    <td class="center">{{ row.source }}</td>
                    <td class="center action-cell">
                      <button type="submit" name="action" value="download_row:{{ row.row_id }}" class="mini">下载这首</button>
                    </td>
                  </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </form>
      {% endif %}
    </section>
  </div>

  <script>
    function toggleRows(checked) {
      document.querySelectorAll('.row-check').forEach((item) => {
        item.checked = checked;
      });
    }

    function escapeHtml(text) {
      return String(text ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
    }

    function renderSongList(songs) {
      const container = document.getElementById('job-song-list');
      if (!container) return;
      container.innerHTML = songs.map((song) => `
        <div class="song-progress-item">
          <div class="song-progress-title">
            <div>
              <strong>${escapeHtml(song.song_name)}</strong>
              <span>${escapeHtml(song.singers)} · ${escapeHtml(song.source)}</span>
            </div>
            <span class="mini-badge status-${escapeHtml(song.status)}">${escapeHtml(song.status_text)}</span>
          </div>
          <div class="mini-progress-shell">
            <div class="mini-progress-fill" style="width: ${Number(song.percent || 0).toFixed(1)}%;"></div>
          </div>
          <p class="song-progress-desc">${escapeHtml(song.description)}</p>
          ${song.download_ready && song.download_url ? `<div class="song-progress-actions"><a href="${escapeHtml(song.download_url)}" class="mini-link" download>${escapeHtml(song.download_label || '下载音频')}</a>${song.open_dir_url ? `<button type="button" class="mini-button" onclick="openDirectory('${escapeHtml(song.open_dir_url)}')">${escapeHtml(song.open_dir_label || '浏览目录')}</button>` : ''}</div>` : ''}
        </div>
      `).join('');
    }

    function renderSourceSummary(job) {
      const container = document.getElementById('job-source-summary');
      if (!container) return;
      const requested = job.per_source_requested || {};
      const downloaded = job.per_source_downloaded || {};
      const items = Object.keys(requested).map((sourceName) => {
        const requestedCount = requested[sourceName] || 0;
        const downloadedCount = downloaded[sourceName] || 0;
        return `<span class="tag">${escapeHtml(sourceName)}：成功 ${downloadedCount} / 目标 ${requestedCount}</span>`;
      });
      container.innerHTML = items.join('');
    }

    function browseConfiguredSaveDir() {
      const saveDirInput = document.querySelector('input[name="save_dir"]');
      const targetDir = saveDirInput ? saveDirInput.value.trim() : '';
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = '{{ url_for("browse_save_directory") }}';

      const appendField = (name, value) => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = name;
        input.value = value;
        form.appendChild(input);
      };

      appendField('normalize', '1');
      if (targetDir) {
        appendField('save_dir', targetDir);
      }

      document.body.appendChild(form);
      form.submit();
    }

    async function openDirectory(url) {
      if (!url) return;

      const openPopup = (targetUrl) => {
        const popup = window.open(targetUrl, '_blank', 'noopener,noreferrer,width=1080,height=760');
        if (!popup) {
          window.location.href = targetUrl;
        }
      };

      if (!url.startsWith('/api/')) {
        openPopup(url);
        return;
      }

      const popup = window.open('', '_blank', 'noopener,noreferrer,width=1080,height=760');
      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: { 'X-Requested-With': 'fetch' }
        });
        const data = await response.json();
        if (!response.ok || !data.ok || !data.browse_url) {
          if (popup) popup.close();
          window.alert(data.message || '打开目录失败');
          return;
        }
        if (popup) {
          popup.location = data.browse_url;
        } else {
          window.location.href = data.browse_url;
        }
        const message = document.getElementById('job-message');
        if (message && data.message) message.textContent = data.message;
      } catch (error) {
        if (popup) popup.close();
        window.alert('打开目录失败，请检查服务端日志');
      }
    }

    function updateJobUI(job) {
      const fill = document.getElementById('job-progress-fill');
      const percent = Number(job.progress_percent || 0);
      const statusText = document.getElementById('job-status-text');
      const badge = document.getElementById('job-status-badge');
      const count = document.getElementById('job-progress-count');
      const percentText = document.getElementById('job-progress-percent');
      const message = document.getElementById('job-message');
      const currentSong = document.getElementById('job-current-song');
      const requested = document.getElementById('job-requested-count');
      const downloaded = document.getElementById('job-downloaded-count');
      const failed = document.getElementById('job-failed-count');
      const outputFormat = document.getElementById('job-output-format');
      const openDirButton = document.getElementById('job-open-dir-button');
      const card = document.getElementById('download-progress-card');

      if (card) card.dataset.jobStatus = job.status;
      if (fill) fill.style.width = `${percent}%`;
      if (statusText) statusText.textContent = job.status_text || job.status;
      if (badge) {
        badge.className = `status-badge status-${job.status}`;
        badge.textContent = job.status_text || job.status;
      }
      if (count) count.textContent = `已处理 ${job.completed_songs} / ${job.total_songs} 首`;
      if (percentText) percentText.textContent = `${percent.toFixed(1)}%`;
      if (message) message.textContent = job.message || '';
      if (currentSong) currentSong.textContent = `当前歌曲：${job.current_song || '暂无'}`;
      if (requested) requested.textContent = job.requested_count ?? 0;
      if (downloaded) downloaded.textContent = job.downloaded_count ?? 0;
      if (failed) failed.textContent = job.failed_count ?? 0;
      if (outputFormat) {
        const keepRaw = job.output_format_requested === 'mp3' && job.keep_original_audio;
        outputFormat.textContent = `输出格式：${job.output_format_requested_text || job.output_format_requested || ''}${keepRaw ? '（保留原始音频）' : ''}`;
      }
      if (openDirButton && job.open_dir_url) {
        openDirButton.dataset.openUrl = job.open_dir_url;
      }

      renderSourceSummary(job);
      renderSongList(job.songs || []);
    }

    async function watchDownloadJob() {
      const card = document.getElementById('download-progress-card');
      if (!card) return;

      const jobId = card.dataset.jobId;
      if (!jobId) return;

      let timer = null;
      const stop = () => timer && clearTimeout(timer);

      const poll = async () => {
        try {
          const response = await fetch(`/api/download-jobs/${jobId}`, {
            headers: { 'X-Requested-With': 'fetch' }
          });
          if (!response.ok) {
            stop();
            return;
          }
          const job = await response.json();
          updateJobUI(job);
          if (job.status === 'running' || job.status === 'pending') {
            timer = setTimeout(poll, 1000);
          }
        } catch (error) {
          timer = setTimeout(poll, 2000);
        }
      };

      poll();
    }

    watchDownloadJob();
  </script>
</body>
</html>
"""

BROWSE_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ browser_title or '下载目录浏览器' }}</title>
  <style>{{ style_css|safe }}</style>
</head>
<body>
  <div class="page browser-page">
    <header class="hero browser-hero">
      <div>
        <h1>{{ browser_title or '下载目录浏览器' }}</h1>
        {% if browser_subtitle %}
          <p>{{ browser_subtitle }}</p>
        {% endif %}
      </div>
      <div class="hero-meta browser-actions">
        <a class="mini-link" href="{{ url_for('index') }}">返回主页面</a>
        {% if parent_url %}
          <a class="mini-link" href="{{ parent_url }}">返回上级目录</a>
        {% endif %}
      </div>
    </header>

    <section class="card browser-card">
      <div class="results-head browser-card-head">
        <div>
          <h2>{{ browser_info_title or '目录信息' }}</h2>
          {% if browser_info_items %}
            {% for item in browser_info_items %}
              <p>{{ item.label }}：<code>{{ item.value }}</code></p>
            {% endfor %}
          {% endif %}
        </div>
        <span class="status-badge {{ browser_badge_class or 'status-completed' }}">{{ browser_badge_text or '目录' }}</span>
      </div>

      <div class="browser-meta-grid">
        <div>
          <strong>当前目录</strong>
          <p class="browser-path"><code>{{ current_dir }}</code></p>
        </div>
        <div>
          <strong>面包屑</strong>
          <div class="browser-breadcrumbs">
            {% for crumb in breadcrumbs %}
              <a href="{{ crumb.url }}">{{ crumb.name }}</a>{% if not loop.last %}<span>/</span>{% endif %}
            {% endfor %}
          </div>
        </div>
      </div>

      {% if status_message %}
        <div class="alert alert-warning">{{ status_message }}</div>
      {% endif %}

      {% if entries %}
        <div class="table-wrap browser-table-wrap">
          <table class="browser-table">
            <thead>
              <tr>
                <th>名称</th>
                <th>类型</th>
                <th>大小</th>
                <th>修改时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {% for entry in entries %}
                <tr{% if entry.is_focus %} class="row-focus"{% endif %}>
                  <td>
                    <div class="browser-name-cell">
                      <span class="browser-icon">{{ '📁' if entry.is_dir else '🎵' if entry.name.lower().endswith(('.mp3', '.flac', '.wav', '.m4a', '.ogg', '.aac', '.opus', '.ape', '.alac', '.wma')) else '📄' }}</span>
                      <div class="browser-name-content">
                        {% if entry.name_download_url %}
                          <a class="browser-name-link" href="{{ entry.name_download_url }}" download>{{ entry.display_name or entry.name }}</a>
                        {% else %}
                          <strong>{{ entry.display_name or entry.name }}</strong>
                        {% endif %}
                      </div>
                    </div>
                  </td>
                  <td>{{ entry.type }}</td>
                  <td>{{ entry.size_text }}</td>
                  <td>{{ entry.modified_text }}</td>
                  <td>
                    <div class="song-progress-actions browser-actions-inline">
                      {% if entry.is_dir %}
                        <a class="mini-link" href="{{ entry.browse_url }}">进入目录</a>
                      {% elif show_file_action_download_link and entry.download_url %}
                        <a class="mini-link" href="{{ entry.download_url }}" download>下载文件</a>
                      {% else %}
                        <span class="browser-empty-action"></span>
                      {% endif %}
                    </div>
                  </td>
                </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      {% else %}
        <div class="alert alert-warning">当前目录没有可显示的文件。</div>
      {% endif %}
    </section>
  </div>
</body>
</html>
"""

SOURCE_MAP_CN_TO_EN: Dict[str, str] = {
    "苹果音乐": "AppleMusicClient",
    "Deezer": "DeezerMusicClient",
    "5sing": "FiveSingMusicClient",
    "Jamendo": "JamendoMusicClient",
    "Joox": "JooxMusicClient",
    "酷我音乐": "KuwoMusicClient",
    "酷狗音乐": "KugouMusicClient",
    "咪咕音乐": "MiguMusicClient",
    "网易云音乐": "NeteaseMusicClient",
    "QQ音乐": "QQMusicClient",
    "千千音乐": "QianqianMusicClient",
    "Qobuz": "QobuzMusicClient",
    "SoundCloud": "SoundCloudMusicClient",
    "StreetVoice": "StreetVoiceMusicClient",
    "汽水音乐": "SodaMusicClient",
    "Spotify": "SpotifyMusicClient",
    "TIDAL": "TIDALMusicClient",
}
SOURCE_MAP_EN_TO_CN: Dict[str, str] = {value: key for key, value in SOURCE_MAP_CN_TO_EN.items()}
HIDDEN_WEB_SOURCE_CODES = {"TIDALMusicClient"}
SOURCE_OPTIONS: List[Dict[str, str]] = [
    {"cn": cn_name, "en": en_name}
    for cn_name, en_name in SOURCE_MAP_CN_TO_EN.items()
    if en_name not in HIDDEN_WEB_SOURCE_CODES
]
DEFAULT_SELECTED_SOURCES = {
    "NeteaseMusicClient",
    "QQMusicClient",
    "KuwoMusicClient",
    "KugouMusicClient",
    "MiguMusicClient",
}
DEFAULT_SAVE_DIR = str((Path.cwd() / "已下载音乐").resolve())
APP_RUNTIME_DIR = (Path.cwd() / '.musicdownload_runtime').resolve()
SEARCH_WORKSPACE_ROOT = APP_RUNTIME_DIR / 'search'
FALLBACK_AUDIO_EXTENSIONS = {'.mp3', '.flac', '.wav', '.m4a', '.aac', '.ogg', '.opus', '.wma', '.ape', '.alac', '.aiff', '.aif', '.wv', '.tta', '.dsf', '.dff', '.amr', '.ac3', '.mka', '.mp2', '.m4b', '.oga', '.weba'}
AUDIO_FILE_EXTENSIONS = {f".{str(ext).lower().lstrip('.')}" for ext in getattr(AudioLinkTester, 'VALID_AUDIO_EXTS', [])} or FALLBACK_AUDIO_EXTENSIONS
FFMPEG_PATH = shutil.which("ffmpeg")
SEARCH_CACHE: Dict[str, Dict[str, Any]] = {}
DOWNLOAD_JOBS: Dict[str, Dict[str, Any]] = {}
APP_STATE_LOCK = threading.RLock()
_PROGRESS_PATCH_LOCK = threading.Lock()
_PROGRESS_PATCH_DEPTH = 0
_ORIGINAL_BASE_PROGRESS = None
_PROGRESS_REPORTER_LOCAL = threading.local()
_UNSET = object()


@dataclass
class LightweightTask:
    description: str
    total: Optional[float] = None
    completed: float = 0
    fields: Dict[str, Any] = field(default_factory=dict)


class WebDownloadProgress:
    def __init__(self, *args: Any, reporter: Optional["DownloadProgressReporter"] = None, **kwargs: Any):
        self.reporter = reporter
        self.tasks: List[LightweightTask] = []
        self.instance_key = uuid.uuid4().hex

    def __enter__(self) -> "WebDownloadProgress":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def add_task(self, description: str, total: Optional[float] = None, **fields: Any) -> int:
        task = LightweightTask(description=description, total=total, completed=0, fields=dict(fields))
        task_id = len(self.tasks)
        self.tasks.append(task)
        if self.reporter:
            self.reporter.on_add_task(self, task_id, task)
        return task_id

    def update(self, task_id: int, description: Any = _UNSET, total: Any = _UNSET, completed: Any = _UNSET, **fields: Any) -> None:
        task = self.tasks[task_id]
        if description is not _UNSET:
            task.description = description
        if total is not _UNSET:
            task.total = total
        if completed is not _UNSET:
            task.completed = completed
        if fields:
            task.fields.update(fields)
        if self.reporter:
            self.reporter.on_task_changed(self, task_id, task)

    def advance(self, task_id: int, advance: float = 1) -> None:
        task = self.tasks[task_id]
        task.completed += advance
        if self.reporter:
            self.reporter.on_task_changed(self, task_id, task)


def _progress_factory(*args: Any, **kwargs: Any) -> WebDownloadProgress:
    reporter = getattr(_PROGRESS_REPORTER_LOCAL, "reporter", None)
    return WebDownloadProgress(*args, reporter=reporter, **kwargs)


@contextmanager
def patched_musicdl_progress(reporter: Optional["DownloadProgressReporter"]):
    global _PROGRESS_PATCH_DEPTH, _ORIGINAL_BASE_PROGRESS
    if not MUSICDL_AVAILABLE or musicdl_base_source is None:
        yield
        return

    with _PROGRESS_PATCH_LOCK:
        if _PROGRESS_PATCH_DEPTH == 0:
            _ORIGINAL_BASE_PROGRESS = musicdl_base_source.Progress
            musicdl_base_source.Progress = _progress_factory
        _PROGRESS_PATCH_DEPTH += 1

    previous_reporter = getattr(_PROGRESS_REPORTER_LOCAL, "reporter", None)
    _PROGRESS_REPORTER_LOCAL.reporter = reporter
    try:
        yield
    finally:
        _PROGRESS_REPORTER_LOCAL.reporter = previous_reporter
        with _PROGRESS_PATCH_LOCK:
            _PROGRESS_PATCH_DEPTH -= 1
            if _PROGRESS_PATCH_DEPTH == 0 and _ORIGINAL_BASE_PROGRESS is not None:
                musicdl_base_source.Progress = _ORIGINAL_BASE_PROGRESS
                _ORIGINAL_BASE_PROGRESS = None


class DownloadProgressReporter:
    def __init__(self, job_id: str, song_infos: List[Any]):
        self.job_id = job_id
        self.lock = threading.RLock()
        self.song_entries_by_key: Dict[str, Dict[str, Any]] = {}
        self.song_signatures_by_key: Dict[str, str] = {}
        self.song_key_by_signature: Dict[str, str] = {}
        self.source_song_queues: Dict[str, List[str]] = {}
        self.overall_task_sources: Dict[Tuple[str, int], str] = {}
        self.song_task_keys: Dict[Tuple[str, int], str] = {}
        self.actual_totals_by_source: Dict[str, int] = {}
        self.completed_by_source: Dict[str, int] = {}

        for index, song_info in enumerate(song_infos):
            song_key = str(index)
            source_code = get_song_value(song_info, "source") or "未知来源"
            source_name = SOURCE_MAP_EN_TO_CN.get(str(source_code), str(source_code))
            entry = {
                "song_key": song_key,
                "song_name": str(get_song_value(song_info, "song_name") or "未知歌曲"),
                "singers": format_artists(get_song_value(song_info, "singers")),
                "source": source_name,
                "source_code": str(source_code),
                "status": "queued",
                "status_text": "等待下载",
                "description": "等待下载",
                "completed": 0,
                "total": None,
                "percent": 0.0,
                "download_ready": False,
                "download_url": "",
                "download_label": "",
                "download_path": "",
                "download_filename": "",
                "open_dir_url": "",
                "open_dir_label": "浏览目录",
            }
            self.song_entries_by_key[song_key] = entry
            self.song_signatures_by_key[song_key] = song_signature(song_info)
            self.song_key_by_signature[self.song_signatures_by_key[song_key]] = song_key
            self.source_song_queues.setdefault(str(source_code), []).append(song_key)

    def on_add_task(self, progress: WebDownloadProgress, task_id: int, task: LightweightTask) -> None:
        task_key = (progress.instance_key, task_id)
        source_code = extract_source_code(task.description) or getattr(progress, "source_code", "")
        if source_code:
            progress.source_code = source_code

        if task.fields.get("kind") == "overall":
            self.overall_task_sources[task_key] = progress.source_code or source_code
            self._update_overall(progress.source_code or source_code, task)
            return

        song_queue = self.source_song_queues.get(progress.source_code or source_code, [])
        song_key = song_queue.pop(0) if song_queue else None
        if song_key is not None:
            self.song_task_keys[task_key] = song_key
            self._update_song(song_key, task)

    def on_task_changed(self, progress: WebDownloadProgress, task_id: int, task: LightweightTask) -> None:
        task_key = (progress.instance_key, task_id)
        if task_key in self.overall_task_sources:
            self._update_overall(self.overall_task_sources[task_key], task)
        elif task_key in self.song_task_keys:
            self._update_song(self.song_task_keys[task_key], task)

    def _set_song_download_info(self, song_key: str, file_path: str, label: Optional[str] = None) -> None:
        entry = self.song_entries_by_key.get(song_key)
        if not entry:
            return
        resolved_path = str(Path(file_path).resolve()) if file_path else ""
        file_name = Path(resolved_path).name if resolved_path else ""
        suffix = Path(resolved_path).suffix.lower() if resolved_path else ""
        default_label = '下载 MP3' if suffix == '.mp3' else ('下载音频' if resolved_path else '')
        entry.update({
            'download_ready': bool(resolved_path),
            'download_url': f'/downloads/{self.job_id}/{song_key}' if resolved_path else '',
            'download_label': label or default_label,
            'download_path': resolved_path,
            'download_filename': file_name,
            'open_dir_url': f'/browse-song/{self.job_id}/{song_key}' if resolved_path else '',
            'open_dir_label': '浏览目录',
        })

    def _set_song_download_info_by_signature(self, signature: str, file_path: str, label: Optional[str] = None) -> None:
        song_key = self.song_key_by_signature.get(signature)
        if song_key is not None:
            self._set_song_download_info(song_key, file_path, label)

    def finish(self, downloaded_song_infos: List[Any], summary: Dict[str, Any]) -> None:
        downloaded_signatures = {song_signature(song_info) for song_info in downloaded_song_infos}
        with self.lock:
            for song_key, entry in self.song_entries_by_key.items():
                if entry["status"] in {"completed", "warning", "failed"}:
                    entry["percent"] = 100.0
                    continue
                if self.song_signatures_by_key[song_key] in downloaded_signatures:
                    entry.update({
                        "status": "completed",
                        "status_text": "已完成",
                        "description": "下载完成",
                        "percent": 100.0,
                    })
                    matched_song = next((item for item in downloaded_song_infos if song_signature(item) == self.song_signatures_by_key[song_key]), None)
                    if matched_song is not None:
                        download_path = locate_downloaded_audio_path(matched_song)
                        self._set_song_download_info(song_key, download_path)
                    continue
                if entry["status"] not in {"failed", "completed", "warning"}:
                    entry.update({
                        "status": "skipped",
                        "status_text": "未完成",
                        "description": "未获得有效下载结果或已被跳过",
                        "percent": 100.0,
                    })

            message = f"下载完成：成功 {summary.get('downloaded_count', 0)} 首，失败/跳过 {summary.get('failed_count', 0)} 首"
            if summary.get('output_notice'):
                message = f"{message}；{summary.get('output_notice')}"

            set_download_job_fields(
                self.job_id,
                status="completed",
                status_text="已完成",
                progress_percent=100.0,
                completed_songs=summary.get("requested_count", 0),
                downloaded_count=summary.get("downloaded_count", 0),
                failed_count=summary.get("failed_count", 0),
                message=message,
                current_song="",
                summary=summary,
                per_source_downloaded=summary.get("per_source_downloaded", {}),
                output_format_requested=summary.get('output_format_requested', 'mp3'),
                output_format_requested_text=summary.get('output_format_requested_text', '自动转 MP3'),
                keep_original_audio=summary.get('keep_original_audio', False),
                ffmpeg_available=summary.get('ffmpeg_available', ffmpeg_available()),
                transcode_required_count=summary.get('transcode_required_count', 0),
                already_mp3_count=summary.get('already_mp3_count', 0),
                transcoded_count=summary.get('transcoded_count', 0),
                transcode_failed_count=summary.get('transcode_failed_count', 0),
                finished_at=time.time(),
            )

    def fail(self, error_message: str) -> None:
        with self.lock:
            active_song = next(
                (song for song in self.song_entries_by_key.values() if song["status"] in {"preparing", "downloading", "transcoding"}),
                None,
            )
            if active_song is not None:
                active_song.update({
                    "status": "failed",
                    "status_text": "失败",
                    "description": error_message,
                })
            set_download_job_fields(
                self.job_id,
                status="failed",
                status_text="失败",
                error=error_message,
                message=f"下载失败：{error_message}",
                finished_at=time.time(),
            )

    def mark_transcoding(self, song_info: Any, index: int, total: int) -> None:
        with self.lock:
            song_key = self.song_key_by_signature.get(song_signature(song_info))
            if song_key and song_key in self.song_entries_by_key:
                entry = self.song_entries_by_key[song_key]
                entry.update({
                    'status': 'transcoding',
                    'status_text': '转码中',
                    'description': f'正在转码为 MP3（{index}/{total}）',
                    'percent': 100.0,
                })
                set_download_job_fields(
                    self.job_id,
                    message=f'正在转码为 MP3（{index}/{total}）',
                    current_song=f"{entry['song_name']} - {entry['singers']}",
                )

    def mark_transcoded(self, song_info: Any, index: int, total: int, output_path: str) -> None:
        with self.lock:
            song_key = self.song_key_by_signature.get(song_signature(song_info))
            if song_key and song_key in self.song_entries_by_key:
                entry = self.song_entries_by_key[song_key]
                entry.update({
                    'status': 'completed',
                    'status_text': '已完成',
                    'description': f'已转为 MP3：{Path(output_path).name}',
                    'percent': 100.0,
                })
                self._set_song_download_info(song_key, output_path, '下载 MP3')
            set_download_job_fields(
                self.job_id,
                message=f'正在整理 MP3 输出（{index}/{total}）',
                transcoded_count=index,
            )

    def mark_transcode_failed(self, song_info: Any, index: int, total: int, error_message: str) -> None:
        with self.lock:
            song_key = self.song_key_by_signature.get(song_signature(song_info))
            if song_key and song_key in self.song_entries_by_key:
                entry = self.song_entries_by_key[song_key]
                entry.update({
                    'status': 'warning',
                    'status_text': '转码失败',
                    'description': f'转码失败，已保留原始音频：{error_message}',
                    'percent': 100.0,
                })
            set_download_job_fields(
                self.job_id,
                message=f'部分歌曲转 MP3 失败（{index}/{total}）',
                transcode_failed_count=(get_download_job(self.job_id).get('transcode_failed_count', 0) + 1),
            )

    def _update_overall(self, source_code: str, task: LightweightTask) -> None:
        source_code = source_code or "未知来源"
        with self.lock:
            if task.total is not None:
                self.actual_totals_by_source[source_code] = int(task.total)
            self.completed_by_source[source_code] = int(task.completed)
            actual_total = sum(self.actual_totals_by_source.values())
            if actual_total <= 0:
                actual_total = get_download_job(self.job_id).get("requested_count", 0)
            completed_total = min(sum(self.completed_by_source.values()), actual_total)
            progress_percent = (completed_total / actual_total * 100.0) if actual_total else 0.0
            set_download_job_fields(
                self.job_id,
                total_songs=actual_total,
                completed_songs=completed_total,
                progress_percent=progress_percent,
                current_source=SOURCE_MAP_EN_TO_CN.get(source_code, source_code),
                message=task.description,
            )

    def _update_song(self, song_key: str, task: LightweightTask) -> None:
        with self.lock:
            entry = self.song_entries_by_key.get(song_key)
            if not entry:
                return
            entry["description"] = task.description
            entry["completed"] = int(task.completed or 0)
            entry["total"] = int(task.total) if task.total not in (None, 0) else None
            entry["status"], entry["status_text"] = derive_song_status(task.description, entry["status"])
            if entry["status"] == "completed":
                entry["percent"] = 100.0
            elif entry["status"] == "failed":
                entry["percent"] = 100.0
            elif entry["total"]:
                entry["percent"] = max(0.0, min(100.0, entry["completed"] / entry["total"] * 100.0))
            elif entry["status"] in {"preparing", "downloading"}:
                entry["percent"] = max(entry.get("percent", 0.0), 1.0)

            if entry["status"] in {"preparing", "downloading"}:
                set_download_job_fields(
                    self.job_id,
                    current_song=f"{entry['song_name']} - {entry['singers']}",
                    message=task.description,
                )


def ensure_session_id() -> str:
    sid = session.get("sid")
    if not sid:
        sid = uuid.uuid4().hex
        session["sid"] = sid
    return sid


def default_form_state() -> Dict[str, Any]:
    return {
        "selected_sources": sorted(DEFAULT_SELECTED_SOURCES),
        "limit": 10,
        "save_dir": DEFAULT_SAVE_DIR,
        "auto_download": False,
        "search_mode": "search_song",
        "keyword": "",
        "output_format": "mp3",
        "keep_original_audio": False,
        "active_download_job_id": None,
    }


def get_state_for_sid(sid: str) -> Dict[str, Any]:
    with APP_STATE_LOCK:
        if sid not in SEARCH_CACHE:
            SEARCH_CACHE[sid] = {
                "form": default_form_state(),
                "results": [],
                "row_map": {},
                "last_query": "",
                "download_summary": None,
                "search_summary": None,
                "active_download_job_id": None,
            }
        return SEARCH_CACHE[sid]


def get_state() -> Dict[str, Any]:
    return get_state_for_sid(ensure_session_id())


def update_state_for_sid(sid: str, **kwargs: Any) -> Dict[str, Any]:
    state = get_state_for_sid(sid)
    with APP_STATE_LOCK:
        state.update(kwargs)
    return state


def get_song_value(song_info: Any, key: str, default: Any = None) -> Any:
    if song_info is None:
        return default
    if hasattr(song_info, "get"):
        try:
            value = song_info.get(key, default)
            return default if value is None else value
        except Exception:
            pass
    if isinstance(song_info, dict):
        value = song_info.get(key, default)
        return default if value is None else value
    return getattr(song_info, key, default)


def song_signature(song_info: Any) -> str:
    parts = [
        str(get_song_value(song_info, "source", "")),
        str(get_song_value(song_info, "identifier", "")),
        str(get_song_value(song_info, "song_name", "")),
        str(get_song_value(song_info, "download_url", "")),
    ]
    return "||".join(parts)


def extract_source_code(description: str) -> str:
    for marker in (".download", "._download"):
        if marker in description:
            return description.split(marker, 1)[0].strip()
    return ""


def derive_song_status(description: str, previous_status: str) -> Tuple[str, str]:
    if "(Success)" in description:
        return "completed", "已完成"
    if "(Error:" in description:
        return "failed", "失败"
    if "Preparing" in description:
        return "preparing", "准备中"
    if "Downloading:" in description or "Segments" in description:
        return "downloading", "下载中"
    if previous_status == "queued":
        return "preparing", "准备中"
    return previous_status, status_text_for_song(previous_status)


def status_text_for_song(status: str) -> str:
    mapping = {
        "queued": "等待下载",
        "preparing": "准备中",
        "downloading": "下载中",
        "transcoding": "转码中",
        "completed": "已完成",
        "failed": "失败",
        "warning": "转码失败",
        "skipped": "未完成",
    }
    return mapping.get(status, status or "未知")


def status_text_for_job(status: str) -> str:
    mapping = {
        "pending": "等待启动",
        "running": "处理中",
        "completed": "已完成",
        "failed": "失败",
    }
    return mapping.get(status, status or "未知")


def normalize_save_dir(save_dir: str) -> str:
    raw_path = (save_dir or DEFAULT_SAVE_DIR).strip()
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def parse_limit(raw_limit: str) -> int:
    try:
        value = int(raw_limit)
    except (TypeError, ValueError):
        value = 10
    return max(1, min(100, value))


def ffmpeg_available() -> bool:
    return bool(FFMPEG_PATH)


def output_format_text(output_format: str) -> str:
    return "自动转 MP3" if output_format == "mp3" else "保留原始格式"


def build_mp3_output_path(input_path: str) -> str:
    return str(Path(input_path).with_suffix('.mp3'))


def safe_remove_file(file_path: str) -> None:
    with contextlib.suppress(FileNotFoundError, PermissionError, OSError):
        Path(file_path).unlink()


def get_session_search_workspace(sid: str) -> str:
    workspace = (SEARCH_WORKSPACE_ROOT / sid).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    return str(workspace)


def is_audio_file_path(path: Path) -> bool:
    return path.suffix.lower() in AUDIO_FILE_EXTENSIONS


def set_song_audio_output_path(song_info: Any, new_audio_path: str) -> None:
    resolved_path = str(Path(new_audio_path).resolve())
    parent_dir = str(Path(resolved_path).parent)
    if isinstance(song_info, dict):
        song_info['_save_path'] = resolved_path
        song_info['save_path'] = resolved_path
        song_info['work_dir'] = parent_dir
        return
    with contextlib.suppress(Exception):
        setattr(song_info, '_save_path', resolved_path)
    with contextlib.suppress(Exception):
        setattr(song_info, 'work_dir', parent_dir)


def prepare_song_info_for_flat_download(song_info: Any, save_dir: str) -> None:
    target_dir = str(Path(save_dir).resolve())
    if isinstance(song_info, dict):
        song_info['work_dir'] = target_dir
        song_info['_save_path'] = None
        song_info.pop('save_path', None)
    else:
        with contextlib.suppress(Exception):
            setattr(song_info, 'work_dir', target_dir)
        with contextlib.suppress(Exception):
            setattr(song_info, '_save_path', None)
    for episode in get_song_value(song_info, 'episodes', []) or []:
        prepare_song_info_for_flat_download(episode, target_dir)


def prepare_song_infos_for_flat_download(song_infos: List[Any], save_dir: str) -> None:
    for song_info in song_infos:
        prepare_song_info_for_flat_download(song_info, save_dir)


def build_unique_audio_output_path(base_dir: Path, desired_name: str, source_path: Optional[Path] = None) -> Path:
    candidate = (base_dir / desired_name).resolve()
    source_resolved = source_path.resolve() if source_path is not None else None
    if source_resolved is not None and candidate == source_resolved:
        return candidate
    stem, suffix = Path(desired_name).stem, Path(desired_name).suffix
    counter = 1
    while candidate.exists():
        if source_resolved is not None:
            with contextlib.suppress(OSError):
                if candidate.samefile(source_resolved):
                    return candidate
        candidate = (base_dir / f"{stem} ({counter}){suffix}").resolve()
        counter += 1
    return candidate


def flatten_and_clean_output_directory(downloaded_song_infos: List[Any], save_dir: str, reporter: Optional["DownloadProgressReporter"] = None) -> Dict[str, int]:
    base_dir = Path(save_dir).resolve()
    base_dir.mkdir(parents=True, exist_ok=True)
    moved_paths: Dict[Path, Path] = {}
    moved_audio_count = 0
    removed_non_audio_count = 0
    removed_empty_dirs = 0

    all_files = sorted([path for path in base_dir.rglob('*') if path.is_file()], key=lambda item: (len(item.parts), item.name.lower()))
    for file_path in all_files:
        resolved_file = file_path.resolve()
        if is_audio_file_path(resolved_file):
            target_path = build_unique_audio_output_path(base_dir, resolved_file.name, source_path=resolved_file)
            if resolved_file.parent != base_dir or target_path != resolved_file:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(resolved_file), str(target_path))
                moved_paths[resolved_file] = target_path.resolve()
                moved_audio_count += 1
        else:
            safe_remove_file(str(resolved_file))
            removed_non_audio_count += 1

    for directory in sorted([path for path in base_dir.rglob('*') if path.is_dir()], key=lambda item: len(item.parts), reverse=True):
        if directory == base_dir:
            continue
        with contextlib.suppress(OSError):
            directory.rmdir()
            removed_empty_dirs += 1

    for song_info in downloaded_song_infos:
        current_path = locate_downloaded_audio_path(song_info)
        if not current_path:
            continue
        resolved_current = Path(current_path).resolve()
        final_path = moved_paths.get(resolved_current, resolved_current)
        if final_path.exists() and final_path.is_file():
            set_song_audio_output_path(song_info, str(final_path))
            if reporter is not None:
                reporter._set_song_download_info_by_signature(song_signature(song_info), str(final_path))

    return {
        'moved_audio_count': moved_audio_count,
        'removed_non_audio_count': removed_non_audio_count,
        'removed_empty_dirs': removed_empty_dirs,
    }


def open_directory_in_system(path: str) -> Tuple[bool, str]:
    directory = Path(path).resolve()
    if not directory.exists() or not directory.is_dir():
        return False, f"目录不存在：{directory}"

    try:
        if sys.platform.startswith('win'):
            os.startfile(str(directory))
            return True, f"已打开目录：{directory}"
        if sys.platform == 'darwin':
            subprocess.Popen(['open', str(directory)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            return True, f"已打开目录：{directory}"

        for command in (['xdg-open', str(directory)], ['gio', 'open', str(directory)]):
            executable = shutil.which(command[0])
            if not executable:
                continue
            try:
                proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=8)
                if proc.returncode == 0:
                    return True, f"已打开目录：{directory}"
                last_error = summarize_subprocess_error(proc.stderr, proc.stdout)
            except subprocess.TimeoutExpired:
                return True, f"已尝试打开目录：{directory}"
        return False, last_error if 'last_error' in locals() else '未找到可用的系统文件管理器命令'
    except Exception as exc:
        return False, str(exc)


def summarize_subprocess_error(stderr_text: str, stdout_text: str = "") -> str:
    for candidate in reversed((stderr_text or "").splitlines() + (stdout_text or "").splitlines()):
        candidate = candidate.strip()
        if candidate:
            return candidate[:200]
    return "ffmpeg 执行失败"


def transcode_audio_file_to_mp3(input_path: str, output_path: str) -> Tuple[bool, str]:
    if not ffmpeg_available():
        return False, "未检测到 ffmpeg，无法自动转 MP3"
    input_file = Path(input_path)
    if not input_file.exists():
        return False, f"源文件不存在：{input_path}"
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    safe_remove_file(str(output_file))
    command = [FFMPEG_PATH, '-y', '-i', str(input_file), '-vn', '-codec:a', 'libmp3lame', '-b:a', '320k', str(output_file)]
    proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0 or not output_file.exists():
        safe_remove_file(str(output_file))
        return False, summarize_subprocess_error(proc.stderr, proc.stdout)
    return True, str(output_file)


def locate_downloaded_audio_path(song_info: Any) -> str:
    if isinstance(song_info, dict):
        return str(song_info.get('_save_path') or song_info.get('save_path') or '')
    for attr_name in ('_save_path', 'save_path'):
        with contextlib.suppress(Exception):
            attr_value = getattr(song_info, attr_name, None)
            if attr_value:
                return str(attr_value)
    save_path = get_song_value(song_info, 'save_path', '')
    return str(save_path or '')


def update_song_file_metadata(song_info: Any, new_audio_path: str) -> None:
    audio_path = Path(new_audio_path)
    if not audio_path.exists():
        return
    file_size_bytes = audio_path.stat().st_size
    if hasattr(song_info, 'update'):
        try:
            song_info.update(ext='mp3', file_size='%.2f MB' % (file_size_bytes / 1024 / 1024), file_size_bytes=file_size_bytes)
        except TypeError:
            song_info.update({'ext': 'mp3', 'file_size': '%.2f MB' % (file_size_bytes / 1024 / 1024), 'file_size_bytes': file_size_bytes})
    elif isinstance(song_info, dict):
        song_info['ext'] = 'mp3'
        song_info['file_size'] = '%.2f MB' % (file_size_bytes / 1024 / 1024)
        song_info['file_size_bytes'] = file_size_bytes
    set_song_audio_output_path(song_info, str(audio_path))


def build_output_postprocess_summary(downloaded_song_infos: List[Any], form_state: Dict[str, Any], reporter: Optional["DownloadProgressReporter"] = None) -> Dict[str, Any]:
    requested_output = form_state.get('output_format', 'mp3')
    keep_original_audio = bool(form_state.get('keep_original_audio', False))
    result = {
        'output_format_requested': requested_output,
        'output_format_requested_text': output_format_text(requested_output),
        'keep_original_audio': keep_original_audio,
        'ffmpeg_available': ffmpeg_available(),
        'transcode_required_count': 0,
        'already_mp3_count': 0,
        'transcoded_count': 0,
        'transcode_failed_count': 0,
        'final_audio_format': 'original',
        'final_audio_format_text': '原始格式',
        'notice': '',
    }

    if requested_output != 'mp3':
        result['notice'] = '已按原始格式保留下载结果'
    elif not result['ffmpeg_available']:
        result['notice'] = '未检测到 ffmpeg，已保留原始格式音频，未执行 MP3 转码'
    else:
        items_to_transcode: List[Tuple[Any, str, str]] = []
        for song_info in downloaded_song_infos:
            input_path = locate_downloaded_audio_path(song_info)
            if not input_path:
                continue
            input_suffix = Path(input_path).suffix.lower()
            if input_suffix == '.mp3':
                result['already_mp3_count'] += 1
                continue
            items_to_transcode.append((song_info, input_path, build_mp3_output_path(input_path)))

        result['transcode_required_count'] = len(items_to_transcode)
        if not items_to_transcode and result['already_mp3_count'] > 0:
            result['final_audio_format'] = 'mp3'
            result['final_audio_format_text'] = 'MP3'
            result['notice'] = '下载结果本身已经是 MP3'
        else:
            total = len(items_to_transcode)
            for index, (song_info, input_path, output_path) in enumerate(items_to_transcode, start=1):
                if reporter:
                    reporter.mark_transcoding(song_info, index, total)
                success, detail = transcode_audio_file_to_mp3(input_path, output_path)
                if success:
                    result['transcoded_count'] += 1
                    update_song_file_metadata(song_info, detail)
                    if not keep_original_audio:
                        safe_remove_file(input_path)
                    if reporter:
                        reporter.mark_transcoded(song_info, index, total, detail)
                else:
                    result['transcode_failed_count'] += 1
                    if reporter:
                        reporter.mark_transcode_failed(song_info, index, total, detail)

            if result['transcode_failed_count'] == 0 and (result['transcoded_count'] > 0 or result['already_mp3_count'] > 0):
                result['final_audio_format'] = 'mp3'
                result['final_audio_format_text'] = 'MP3'
                if result['transcoded_count'] > 0:
                    result['notice'] = '已自动转为 MP3' + ('，并保留原始音频' if keep_original_audio else '，原始音频已删除')
                else:
                    result['notice'] = '下载结果本身已经是 MP3'
            elif result['transcoded_count'] > 0:
                result['final_audio_format'] = 'mixed'
                result['final_audio_format_text'] = '混合格式'
                result['notice'] = '部分歌曲已转为 MP3，部分转码失败，失败项保留原始音频'
            else:
                result['final_audio_format'] = 'original'
                result['final_audio_format_text'] = '原始格式'
                result['notice'] = 'MP3 转码未成功，已保留原始音频'

    cleanup_summary = flatten_and_clean_output_directory(downloaded_song_infos, form_state['save_dir'], reporter=reporter)
    if cleanup_summary['moved_audio_count'] > 0 or cleanup_summary['removed_non_audio_count'] > 0 or cleanup_summary['removed_empty_dirs'] > 0:
        cleanup_notice = '已整理为扁平目录，仅保留音频文件'
        result['notice'] = f"{result['notice']}；{cleanup_notice}" if result['notice'] else cleanup_notice

    return result


def extract_form_state() -> Dict[str, Any]:
    selected_sources = [
        source for source in request.form.getlist("sources") if source in SOURCE_MAP_EN_TO_CN
    ]
    output_format = request.form.get("output_format", "mp3")
    if output_format not in {"original", "mp3"}:
        output_format = "mp3"
    return {
        "selected_sources": selected_sources,
        "limit": parse_limit(request.form.get("limit", "10")),
        "save_dir": normalize_save_dir(request.form.get("save_dir", DEFAULT_SAVE_DIR)),
        "auto_download": request.form.get("auto_download") == "on",
        "search_mode": request.form.get("search_mode", "search_song"),
        "keyword": request.form.get("keyword", "").strip(),
        "output_format": output_format,
        "keep_original_audio": request.form.get("keep_original_audio") == "on",
    }


def init_music_client(selected_sources: List[str], limit: int, work_dir: str):
    if not MUSICDL_AVAILABLE:
        raise RuntimeError("musicdl 库未安装，请先执行 pip install -r requirements.txt")
    if not selected_sources:
        raise ValueError("请至少选择一个音乐来源")

    init_cfg = {
        source: {"search_size_per_source": limit, "work_dir": work_dir}
        for source in selected_sources
    }
    return musicdl.MusicClient(
        music_sources=selected_sources,
        init_music_clients_cfg=init_cfg,
    )


def get_file_format(song_info: Any) -> str:
    for field in ["format", "ext", "file_format", "type"]:
        value = get_song_value(song_info, field)
        if value:
            return str(value).upper()
    download_url = str(get_song_value(song_info, "download_url", "")).lower()
    for ext in ["mp3", "flac", "wav", "m4a", "aac"]:
        if f".{ext}" in download_url:
            return ext.upper()
    return "未知"


def get_album_image_url(song_info: Any) -> str:
    image_fields = [
        "cover", "album_cover", "pic", "picture", "img", "image",
        "album_img", "album_pic", "cover_url", "pic_url",
    ]
    for field in image_fields:
        value = get_song_value(song_info, field)
        if value:
            url = str(value)
            if url.startswith("http"):
                return url
    return ""


def build_display_format(original_format: str, output_format: str, with_ffmpeg: bool) -> str:
    normalized_original = (original_format or "未知").upper()
    if output_format != 'mp3':
        return normalized_original
    if normalized_original == 'MP3':
        return 'MP3'
    if not with_ffmpeg:
        return f'{normalized_original}（未转 MP3）'
    return f'{normalized_original} → MP3'


def format_artists(value: Any) -> str:
    if not value:
        return "未知歌手"
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple, set)):
        names: List[str] = []
        for item in value:
            if isinstance(item, dict):
                name = item.get("name") or item.get("artist") or item.get("singer")
                if name:
                    names.append(str(name))
            elif item:
                names.append(str(item))
        return ", ".join(names) if names else "未知歌手"
    if isinstance(value, dict):
        name = value.get("name") or value.get("artist") or value.get("singer")
        return str(name) if name else "未知歌手"
    return str(value)


def format_duration(value: Any) -> str:
    if value in (None, ""):
        return "未知"
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped.isdigit():
            return stripped
        value = int(stripped)
    if isinstance(value, (int, float)):
        seconds = int(value)
        if seconds > 100000:
            seconds //= 1000
        if seconds >= 0:
            return f"{seconds // 60:02d}:{seconds % 60:02d}"
    return str(value)


def format_file_size(value: Any) -> str:
    if value in (None, ""):
        return "未知"
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped.isdigit():
            return stripped
        value = int(stripped)
    if isinstance(value, (int, float)):
        size = float(value)
        units = ["B", "KB", "MB", "GB", "TB"]
        for unit in units:
            if size < 1024 or unit == units[-1]:
                return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
            size /= 1024
    return str(value)


def coerce_song_info(raw_song_info: Any) -> Any:
    if SongInfo is None:
        return raw_song_info
    if isinstance(raw_song_info, SongInfo):
        return raw_song_info
    if isinstance(raw_song_info, dict):
        return SongInfo.fromdict(raw_song_info)
    if hasattr(raw_song_info, "todict"):
        try:
            return SongInfo.fromdict(raw_song_info.todict())
        except Exception:
            return raw_song_info
    return raw_song_info


def normalize_results(search_results: Any, form_state: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if not isinstance(search_results, dict):
        search_results = {"歌单": search_results or []}

    normalized_rows: List[Dict[str, Any]] = []
    row_map: Dict[str, Any] = {}
    row_index = 0

    for fallback_source, per_source_results in search_results.items():
        if per_source_results is None:
            continue
        if isinstance(per_source_results, dict):
            iterable_results = [per_source_results]
        elif isinstance(per_source_results, (list, tuple)):
            iterable_results = list(per_source_results)
        else:
            iterable_results = [per_source_results]

        for raw_song_info in iterable_results:
            song_info = coerce_song_info(raw_song_info)
            if song_info is None:
                continue
            source = get_song_value(song_info, "source") or fallback_source
            if hasattr(song_info, "update"):
                try:
                    song_info.update(source=source)
                except TypeError:
                    song_info.update({"source": source})
            elif isinstance(song_info, dict):
                song_info["source"] = source

            row_id = str(row_index)
            row_map[row_id] = song_info
            original_format = get_file_format(song_info)
            requested_output = (form_state or {}).get('output_format', 'mp3')
            display_format = build_display_format(original_format, requested_output, ffmpeg_available())
            normalized_rows.append(
                {
                    "row_id": row_id,
                    "song_name": str(get_song_value(song_info, "song_name") or "未知歌曲"),
                    "singers": format_artists(get_song_value(song_info, "singers")),
                    "album": str(get_song_value(song_info, "album") or "未知专辑"),
                    "file_format": original_format,
                    "display_format": display_format,
                    "output_format": 'MP3' if requested_output == 'mp3' and ffmpeg_available() else ('MP3（未启用）' if requested_output == 'mp3' else '原始'),
                    "file_size": format_file_size(get_song_value(song_info, "file_size")),
                    "duration": format_duration(get_song_value(song_info, "duration")),
                    "source": SOURCE_MAP_EN_TO_CN.get(str(source), str(source) or "未知来源"),
                    "cover_url": get_album_image_url(song_info),
                }
            )
            row_index += 1

    return normalized_rows, row_map


def build_search_summary(raw_results: Any, normalized_rows: List[Dict[str, Any]], form_state: Dict[str, Any]) -> Dict[str, Any]:
    per_source_counts: Dict[str, int] = {
        SOURCE_MAP_EN_TO_CN.get(source_code, source_code): 0
        for source_code in form_state.get("selected_sources", [])
    }

    if isinstance(raw_results, dict):
        for source_code, items in raw_results.items():
            source_name = SOURCE_MAP_EN_TO_CN.get(str(source_code), str(source_code) or "未知来源")
            if isinstance(items, dict):
                count = 1
            elif isinstance(items, (list, tuple)):
                count = len(items)
            elif items:
                count = 1
            else:
                count = 0
            per_source_counts[source_name] = count
    else:
        fallback_counts: Dict[str, int] = {}
        for row in normalized_rows:
            source_name = row.get("source", "未知来源")
            fallback_counts[source_name] = fallback_counts.get(source_name, 0) + 1
        if fallback_counts:
            per_source_counts.update(fallback_counts)

    nonzero_counts = {k: v for k, v in per_source_counts.items() if v > 0}
    zero_counts = {k: v for k, v in per_source_counts.items() if v == 0}
    ordered_counts = {**dict(sorted(nonzero_counts.items(), key=lambda item: (-item[1], item[0]))), **dict(sorted(zero_counts.items(), key=lambda item: item[0]))}

    return {
        "search_mode": form_state.get("search_mode", "search_song"),
        "keyword": form_state.get("keyword", ""),
        "selected_source_count": len(form_state.get("selected_sources", [])),
        "total_results": len(normalized_rows),
        "per_source_counts": ordered_counts,
        "has_any_result": len(normalized_rows) > 0,
    }


def search_music(form_state: Dict[str, Any], sid: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any], Dict[str, Any]]:
    client = init_music_client(
        selected_sources=form_state["selected_sources"],
        limit=form_state["limit"],
        work_dir=get_session_search_workspace(sid),
    )
    if form_state["search_mode"] == "parse_playlist":
        raw_results = client.parseplaylist(form_state["keyword"])
    else:
        raw_results = client.search(keyword=form_state["keyword"])
    normalized_rows, row_map = normalize_results(raw_results, form_state=form_state)
    search_summary = build_search_summary(raw_results, normalized_rows, form_state)
    return normalized_rows, row_map, search_summary


def build_download_summary(downloaded_song_infos: List[Any], requested_song_infos: List[Any], form_state: Dict[str, Any], output_summary: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    per_source_requested: Dict[str, int] = {}
    per_source_downloaded: Dict[str, int] = {}

    for song_info in requested_song_infos:
        source_code = str(get_song_value(song_info, "source") or "未知来源")
        source_name = SOURCE_MAP_EN_TO_CN.get(source_code, source_code)
        per_source_requested[source_name] = per_source_requested.get(source_name, 0) + 1

    for song_info in downloaded_song_infos:
        source_code = str(get_song_value(song_info, "source") or "未知来源")
        source_name = SOURCE_MAP_EN_TO_CN.get(source_code, source_code)
        per_source_downloaded[source_name] = per_source_downloaded.get(source_name, 0) + 1

    downloaded_count = len(downloaded_song_infos)
    requested_count = len(requested_song_infos)
    output_summary = dict(output_summary or {})
    return {
        "requested_count": requested_count,
        "downloaded_count": downloaded_count,
        "failed_count": max(requested_count - downloaded_count, 0),
        "save_dir": form_state["save_dir"],
        "per_source_requested": per_source_requested,
        "per_source_downloaded": per_source_downloaded,
        "output_format_requested": output_summary.get('output_format_requested', form_state.get('output_format', 'mp3')),
        "output_format_requested_text": output_summary.get('output_format_requested_text', output_format_text(form_state.get('output_format', 'mp3'))),
        "final_audio_format": output_summary.get('final_audio_format', 'original'),
        "final_audio_format_text": output_summary.get('final_audio_format_text', '原始格式'),
        "keep_original_audio": output_summary.get('keep_original_audio', bool(form_state.get('keep_original_audio', False))),
        "ffmpeg_available": output_summary.get('ffmpeg_available', ffmpeg_available()),
        "transcode_required_count": output_summary.get('transcode_required_count', 0),
        "already_mp3_count": output_summary.get('already_mp3_count', 0),
        "transcoded_count": output_summary.get('transcoded_count', 0),
        "transcode_failed_count": output_summary.get('transcode_failed_count', 0),
        "output_notice": output_summary.get('notice', ''),
    }


def create_download_job_payload(job_id: str, sid: str, song_infos: List[Any], form_state: Dict[str, Any], reporter: Optional[DownloadProgressReporter] = None) -> Dict[str, Any]:
    per_source_requested: Dict[str, int] = {}
    songs: List[Dict[str, Any]] = []
    if reporter is not None:
        songs = [reporter.song_entries_by_key[key] for key in sorted(reporter.song_entries_by_key.keys(), key=int)]
        for entry in songs:
            per_source_requested[entry['source']] = per_source_requested.get(entry['source'], 0) + 1
    else:
        for index, song_info in enumerate(song_infos):
            source_code = str(get_song_value(song_info, "source") or "未知来源")
            source_name = SOURCE_MAP_EN_TO_CN.get(source_code, source_code)
            per_source_requested[source_name] = per_source_requested.get(source_name, 0) + 1
            songs.append(
                {
                    "song_key": str(index),
                    "song_name": str(get_song_value(song_info, "song_name") or "未知歌曲"),
                    "singers": format_artists(get_song_value(song_info, "singers")),
                    "source": source_name,
                    "source_code": source_code,
                    "status": "queued",
                    "status_text": "等待下载",
                    "description": "等待下载",
                    "completed": 0,
                    "total": None,
                    "percent": 0.0,
                    "download_ready": False,
                    "download_url": "",
                    "download_label": "",
                    "download_path": "",
                    "download_filename": "",
                    "open_dir_url": "",
                    "open_dir_label": "浏览目录",
                }
            )

    return {
        "id": job_id,
        "sid": sid,
        "status": "pending",
        "status_text": "等待启动",
        "message": "任务已创建，等待开始下载",
        "error": "",
        "save_dir": form_state["save_dir"],
        "open_dir_url": f'/browse/{job_id}',
        "open_dir_label": '浏览下载目录',
        "output_format_requested": form_state.get("output_format", "mp3"),
        "output_format_requested_text": output_format_text(form_state.get("output_format", "mp3")),
        "keep_original_audio": bool(form_state.get("keep_original_audio", False)),
        "ffmpeg_available": ffmpeg_available(),
        "transcode_required_count": 0,
        "already_mp3_count": 0,
        "transcoded_count": 0,
        "transcode_failed_count": 0,
        "requested_count": len(song_infos),
        "total_songs": len(song_infos),
        "completed_songs": 0,
        "downloaded_count": 0,
        "failed_count": 0,
        "progress_percent": 0.0,
        "current_song": "",
        "current_source": "",
        "per_source_requested": per_source_requested,
        "per_source_downloaded": {},
        "summary": None,
        "songs": songs,
        "created_at": time.time(),
        "updated_at": time.time(),
        "started_at": None,
        "finished_at": None,
    }


def get_download_job(job_id: Optional[str]) -> Dict[str, Any]:
    if not job_id:
        return {}
    with APP_STATE_LOCK:
        return DOWNLOAD_JOBS.get(job_id, {})


def set_download_job_fields(job_id: str, **kwargs: Any) -> None:
    with APP_STATE_LOCK:
        job = DOWNLOAD_JOBS.get(job_id)
        if not job:
            return
        job.update(kwargs)
        job["updated_at"] = time.time()


def serialize_download_job(job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not job:
        return None
    with APP_STATE_LOCK:
        snapshot = deepcopy(job)
    snapshot.pop("sid", None)
    snapshot.pop("browser_targets", None)
    snapshot.pop("browser_target_lookup", None)
    snapshot["status_text"] = status_text_for_job(snapshot.get("status", "pending"))
    for song in snapshot.get("songs", []):
        song["status_text"] = status_text_for_song(song.get("status", "queued"))
    return snapshot


def prune_finished_jobs() -> None:
    now = time.time()
    with APP_STATE_LOCK:
        stale_job_ids = [
            job_id for job_id, job in DOWNLOAD_JOBS.items()
            if job.get("status") in {"completed", "failed"} and now - float(job.get("finished_at") or now) > 3600
        ]
        for job_id in stale_job_ids:
            DOWNLOAD_JOBS.pop(job_id, None)


def run_download_job(job_id: str, sid: str, song_infos: List[Any], form_state: Dict[str, Any], reporter: DownloadProgressReporter) -> None:
    set_download_job_fields(
        job_id,
        status="running",
        status_text="下载中",
        message="正在初始化下载客户端",
        started_at=time.time(),
    )
    try:
        client = init_music_client(
            selected_sources=form_state["selected_sources"],
            limit=form_state["limit"],
            work_dir=form_state["save_dir"],
        )
        with patched_musicdl_progress(reporter):
            downloaded_song_infos = client.download(song_infos=song_infos)
        set_download_job_fields(
            job_id,
            message=("音频下载完成，正在转码为 MP3" if form_state.get("output_format", "mp3") == "mp3" else "音频下载完成，正在整理结果"),
            current_song="",
        )
        output_summary = build_output_postprocess_summary(downloaded_song_infos, form_state, reporter)
        summary = build_download_summary(downloaded_song_infos, song_infos, form_state, output_summary)
        reporter.finish(downloaded_song_infos, summary)
        update_state_for_sid(sid, download_summary=summary)
    except Exception as exc:
        reporter.fail(str(exc))
        update_state_for_sid(sid, download_summary=None)


def start_download_job(song_infos: List[Any], form_state: Dict[str, Any], sid: str) -> str:
    if not song_infos:
        raise ValueError("没有可下载的歌曲")

    prepare_song_infos_for_flat_download(song_infos, form_state["save_dir"])
    prune_finished_jobs()
    job_id = uuid.uuid4().hex
    reporter = DownloadProgressReporter(job_id=job_id, song_infos=song_infos)
    job_payload = create_download_job_payload(job_id, sid, song_infos, form_state, reporter=reporter)

    with APP_STATE_LOCK:
        DOWNLOAD_JOBS[job_id] = job_payload
    update_state_for_sid(sid, active_download_job_id=job_id, download_summary=None)

    thread = threading.Thread(
        target=run_download_job,
        args=(job_id, sid, list(song_infos), dict(form_state), reporter),
        daemon=True,
        name=f"musicdownload-job-{job_id[:8]}",
    )
    thread.start()
    return job_id


def resolve_job_and_validate_owner(job_id: str, sid: str) -> Tuple[Optional[Dict[str, Any]], Optional[Path]]:
    job = get_download_job(job_id)
    if not job or job.get('sid') != sid:
        return None, None
    save_dir = Path(str(job.get('save_dir') or '.')).resolve()
    return job, save_dir


def ensure_path_within(base_dir: Path, target_path: Path) -> bool:
    try:
        target_path.resolve().relative_to(base_dir.resolve())
        return True
    except Exception:
        return False


def find_job_song_entry(job: Dict[str, Any], song_key: str) -> Optional[Dict[str, Any]]:
    return next((item for item in job.get("songs", []) if str(item.get("song_key")) == str(song_key)), None)


def resolve_song_file_for_job(job: Dict[str, Any], save_dir: Path, song_key: str) -> Tuple[Optional[Dict[str, Any]], Optional[Path], Optional[str]]:
    song = find_job_song_entry(job, song_key)
    if not song or not song.get("download_ready"):
        return None, None, "文件尚未准备好"
    file_path = str(song.get("download_path") or "")
    if not file_path:
        return song, None, "文件不存在"
    resolved_file = Path(file_path).resolve()
    if not resolved_file.exists() or not resolved_file.is_file():
        return song, None, "文件不存在"
    if not ensure_path_within(save_dir, resolved_file):
        return song, None, "文件路径非法"
    return song, resolved_file, None


def normalize_browser_relative_path(raw_path: str) -> str:
    cleaned = str(raw_path or "").replace("\\", "/").strip()
    if not cleaned or cleaned == ".":
        return ""
    cleaned = cleaned.lstrip("/")
    parts = [part for part in Path(cleaned).parts if part not in {"", "."}]
    return Path(*parts).as_posix() if parts else ""


def relative_posix_path(base_dir: Path, target_path: Path) -> str:
    try:
        relative = target_path.resolve().relative_to(base_dir.resolve())
    except Exception:
        return ""
    return "" if str(relative) == "." else relative.as_posix()


def build_job_browser_default_relative_path(job: Dict[str, Any], save_dir: Path) -> str:
    candidate_dirs: List[Path] = []
    for song in job.get("songs", []):
        file_path = str(song.get("download_path") or "")
        if not file_path:
            continue
        resolved_file = Path(file_path).resolve()
        if not resolved_file.exists() or not resolved_file.is_file():
            continue
        if not ensure_path_within(save_dir, resolved_file):
            continue
        candidate_dirs.append(resolved_file.parent)

    if not candidate_dirs:
        return ""

    try:
        common_dir = Path(os.path.commonpath([str(item) for item in candidate_dirs])).resolve()
    except Exception:
        common_dir = candidate_dirs[0]

    if not ensure_path_within(save_dir, common_dir):
        common_dir = save_dir.resolve()

    if common_dir == save_dir.resolve() and len(candidate_dirs) == 1:
        common_dir = candidate_dirs[0]

    return relative_posix_path(save_dir, common_dir)


def register_job_browser_target(job_id: str, kind: str, relative_path: str) -> str:
    normalized_path = normalize_browser_relative_path(relative_path)
    registry_key = f"{kind}:{normalized_path}"
    with APP_STATE_LOCK:
        job = DOWNLOAD_JOBS.get(job_id)
        if not job:
            return ""
        lookup = job.setdefault("browser_target_lookup", {})
        targets = job.setdefault("browser_targets", {})
        token = str(lookup.get(registry_key) or "")
        if not token:
            token = uuid.uuid4().hex
            lookup[registry_key] = token
        targets[token] = {"kind": kind, "path": normalized_path}
        return token


def resolve_job_browser_target(job_id: str, sid: str, token: str, expected_kind: str) -> Tuple[Optional[Dict[str, Any]], Optional[Path], Optional[str], Optional[str]]:
    job, save_dir = resolve_job_and_validate_owner(job_id, sid)
    if not job or save_dir is None:
        return None, None, None, "任务不存在"
    token = str(token or "").strip()
    if not token:
        return job, save_dir, "", None
    with APP_STATE_LOCK:
        target_entry = dict((job.get("browser_targets") or {}).get(token) or {})
    if not target_entry:
        return job, save_dir, None, "浏览目标不存在"
    if target_entry.get("kind") != expected_kind:
        return job, save_dir, None, "浏览目标类型不匹配"
    return job, save_dir, normalize_browser_relative_path(str(target_entry.get("path") or "")), None


def build_browser_breadcrumbs(current_relative_path: str, browse_url_builder, root_label: str = "下载根目录") -> List[Dict[str, str]]:
    breadcrumbs = [{"name": root_label, "url": browse_url_builder("")}]
    current_parts: List[str] = []
    for part in Path(current_relative_path).parts:
        current_parts.append(part)
        breadcrumbs.append({
            "name": part,
            "url": browse_url_builder(Path(*current_parts).as_posix()),
        })
    return breadcrumbs


def format_browser_file_size(size_bytes: int) -> str:
    size = float(size_bytes or 0)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.2f} {unit}"
        size /= 1024
    return "0 B"


def format_browser_mtime(timestamp_value: float) -> str:
    try:
        return datetime.fromtimestamp(timestamp_value).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "-"


def derive_browser_song_title(file_name: str) -> str:
    stem = Path(file_name).stem
    cleaned_stem = re.sub(r" \(\d+\)$", "", stem).strip()
    left, sep, right = cleaned_stem.rpartition(" - ")
    if sep and left.strip() and re.fullmatch(r"[A-Za-z0-9_-]+", right.strip()):
        return left.strip()
    return cleaned_stem or stem or file_name


def list_browser_entries(base_dir: Path, target_dir: Path, browse_url_builder, download_url_builder, focus_name: str = "", *, prefer_song_title: bool = False, show_name_download_link: bool = False) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for child in sorted(target_dir.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
        with contextlib.suppress(OSError):
            stat_result = child.stat()
            relative_path = relative_posix_path(base_dir, child)
            if child.is_dir():
                entries.append({
                    "name": child.name,
                    "display_name": child.name,
                    "name_download_url": "",
                    "name_download_label": "",
                    "type": "目录",
                    "size_text": "-",
                    "modified_text": format_browser_mtime(stat_result.st_mtime),
                    "browse_url": browse_url_builder(relative_path),
                    "download_url": "",
                    "is_dir": True,
                    "is_focus": child.name == focus_name,
                })
            elif child.is_file():
                download_url = download_url_builder(relative_path)
                entries.append({
                    "name": child.name,
                    "display_name": derive_browser_song_title(child.name) if prefer_song_title else child.name,
                    "name_download_url": download_url if show_name_download_link else "",
                    "name_download_label": child.name if show_name_download_link else "",
                    "type": child.suffix.lower().lstrip(".").upper() or "文件",
                    "size_text": format_browser_file_size(stat_result.st_size),
                    "modified_text": format_browser_mtime(stat_result.st_mtime),
                    "browse_url": "",
                    "download_url": download_url,
                    "is_dir": False,
                    "is_focus": child.name == focus_name,
                })
    return entries


def render_directory_browser(*, base_dir: Path, requested_path: str, focus_name: str, browse_url_builder, download_url_builder, browser_title: str, browser_subtitle: str, browser_info_title: str, browser_info_items: List[Dict[str, str]], browser_badge_text: str, browser_badge_class: str, root_label: str = "下载根目录", prefer_song_title: bool = False, show_name_download_link: bool = False, show_file_action_download_link: bool = True):
    current_relative_path = normalize_browser_relative_path(requested_path)
    target_dir = (base_dir / current_relative_path).resolve() if current_relative_path else base_dir.resolve()
    if not ensure_path_within(base_dir, target_dir):
        return "目录路径非法", 403

    entries: List[Dict[str, Any]] = []
    status_message = ""
    if target_dir.exists() and target_dir.is_dir():
        entries = list_browser_entries(base_dir, target_dir, browse_url_builder, download_url_builder, focus_name=focus_name, prefer_song_title=prefer_song_title, show_name_download_link=show_name_download_link)
    elif target_dir.exists() and not target_dir.is_dir():
        return "目标不是目录", 404
    else:
        status_message = "当前目录还不存在，可能下载尚未开始或文件还未写入，稍后刷新即可。"

    parent_url = None
    if current_relative_path:
        parent_relative = Path(current_relative_path).parent.as_posix()
        if parent_relative == ".":
            parent_relative = ""
        parent_url = browse_url_builder(parent_relative)

    return render_template_string(
        BROWSE_TEMPLATE,
        style_css=STYLE_CSS,
        browser_title=browser_title,
        browser_subtitle=browser_subtitle,
        browser_info_title=browser_info_title,
        browser_info_items=browser_info_items,
        browser_badge_text=browser_badge_text,
        browser_badge_class=browser_badge_class,
        current_dir=str(target_dir),
        current_relative_path=current_relative_path,
        breadcrumbs=build_browser_breadcrumbs(current_relative_path, browse_url_builder, root_label=root_label),
        parent_url=parent_url,
        entries=entries,
        status_message=status_message,
        focus_name=focus_name,
        show_file_action_download_link=show_file_action_download_link,
    )


def resolve_configured_save_dir(sid: str) -> Path:
    state = get_state_for_sid(sid)
    raw_target = str(state.get("form", {}).get("save_dir") or DEFAULT_SAVE_DIR).strip()
    return Path(normalize_save_dir(raw_target)).resolve()


def update_save_dir_in_state(sid: str, raw_save_dir: str) -> str:
    state = get_state_for_sid(sid)
    form_state = dict(state.get("form") or default_form_state())
    normalized_save_dir = normalize_save_dir(raw_save_dir or form_state.get("save_dir") or DEFAULT_SAVE_DIR)
    form_state["save_dir"] = normalized_save_dir
    update_state_for_sid(sid, form=form_state)
    with APP_STATE_LOCK:
        state["save_browser_targets"] = {}
        state["save_browser_target_lookup"] = {}
    return normalized_save_dir


def register_save_browser_target(sid: str, kind: str, relative_path: str) -> str:
    normalized_path = normalize_browser_relative_path(relative_path)
    registry_key = f"{kind}:{normalized_path}"
    state = get_state_for_sid(sid)
    with APP_STATE_LOCK:
        lookup = state.setdefault("save_browser_target_lookup", {})
        targets = state.setdefault("save_browser_targets", {})
        token = str(lookup.get(registry_key) or "")
        if not token:
            token = uuid.uuid4().hex
            lookup[registry_key] = token
        targets[token] = {"kind": kind, "path": normalized_path}
        return token


def resolve_save_browser_target(sid: str, token: str, expected_kind: str) -> Tuple[Optional[str], Optional[str]]:
    token = str(token or "").strip()
    if not token:
        return "", None
    state = get_state_for_sid(sid)
    with APP_STATE_LOCK:
        target_entry = dict((state.get("save_browser_targets") or {}).get(token) or {})
    if not target_entry:
        return None, "浏览目标不存在"
    if target_entry.get("kind") != expected_kind:
        return None, "浏览目标类型不匹配"
    return normalize_browser_relative_path(str(target_entry.get("path") or "")), None


@app.route("/api/open-job-dir/<job_id>", methods=["POST"])
def open_job_directory(job_id: str):
    sid = ensure_session_id()
    job, _ = resolve_job_and_validate_owner(job_id, sid)
    if not job:
        return jsonify({'ok': False, 'message': '任务不存在'}), 404
    return jsonify({
        'ok': True,
        'message': '已打开网页文件浏览器',
        'browse_url': url_for('browse_job_directory', job_id=job_id),
    })


@app.route("/api/open-song-dir/<job_id>/<song_key>", methods=["POST"])
def open_song_directory(job_id: str, song_key: str):
    sid = ensure_session_id()
    job, save_dir = resolve_job_and_validate_owner(job_id, sid)
    if not job or save_dir is None:
        return jsonify({'ok': False, 'message': '任务不存在'}), 404
    _, resolved_file, error_message = resolve_song_file_for_job(job, save_dir, song_key)
    if error_message or resolved_file is None:
        return jsonify({'ok': False, 'message': error_message or '文件不存在'}), 404
    return jsonify({
        'ok': True,
        'message': '已打开网页文件浏览器',
        'browse_url': url_for('browse_song_directory', job_id=job_id, song_key=song_key),
    })


@app.route("/browse-save-dir", methods=["GET", "POST"])
def browse_save_directory():
    sid = ensure_session_id()
    if request.method == "POST":
        update_save_dir_in_state(sid, request.form.get("save_dir", ""))
        normalize_flag = "1" if request.form.get("normalize") == "1" else "0"
        return redirect(url_for('browse_save_directory', normalize=normalize_flag if normalize_flag == "1" else None))

    base_dir = resolve_configured_save_dir(sid)
    requested_token = str(request.args.get("target", "") or "").strip()
    if requested_token:
        requested_path, error_message = resolve_save_browser_target(sid, requested_token, "dir")
        if error_message or requested_path is None:
            return error_message or "浏览目标不存在", 404
    else:
        requested_path = ""
    focus_name = (request.args.get("focus") or "").strip()
    if request.args.get("normalize") == "1":
        state = get_state_for_sid(sid)
        active_job = get_download_job(state.get("active_download_job_id"))
        if not active_job or active_job.get("status") not in {"pending", "running"}:
            flatten_and_clean_output_directory([], str(base_dir), reporter=None)

    def browse_url_builder(relative_path: str) -> str:
        if not relative_path:
            return url_for('browse_save_directory')
        token = register_save_browser_target(sid, 'dir', relative_path)
        return url_for('browse_save_directory', target=token)

    def download_url_builder(relative_path: str) -> str:
        token = register_save_browser_target(sid, 'file', relative_path)
        return url_for('browse_save_download_file', target=token)

    return render_directory_browser(
        base_dir=base_dir,
        requested_path=requested_path,
        focus_name=focus_name,
        browse_url_builder=browse_url_builder,
        download_url_builder=download_url_builder,
        browser_title="下载目录浏览器",
        browser_subtitle="浏览当前配置的下载目录，点击歌曲名即可下载。",
        browser_info_title="下载目录",
        browser_info_items=[{"label": "根目录", "value": str(base_dir)}],
        browser_badge_text="本地目录",
        browser_badge_class="status-completed",
        root_label="下载目录",
        prefer_song_title=True,
        show_name_download_link=True,
        show_file_action_download_link=True,
    )


@app.route("/browse-save-download", methods=["GET"])
def browse_save_download_file():
    sid = ensure_session_id()
    base_dir = resolve_configured_save_dir(sid)
    relative_path, error_message = resolve_save_browser_target(sid, request.args.get("target", ""), "file")
    if error_message or relative_path is None:
        return error_message or "文件不存在", 404
    if not relative_path:
        return "文件不存在", 404
    resolved_file = (base_dir / relative_path).resolve()
    if not ensure_path_within(base_dir, resolved_file):
        return "文件路径非法", 403
    if not resolved_file.exists() or not resolved_file.is_file():
        return "文件不存在", 404
    return send_file(str(resolved_file), as_attachment=True, download_name=resolved_file.name)


@app.route("/browse/<job_id>", methods=["GET"])
def browse_job_directory(job_id: str):
    sid = ensure_session_id()
    requested_token = str(request.args.get("target", "") or "").strip()
    if requested_token:
        job, save_dir, requested_path, error_message = resolve_job_browser_target(job_id, sid, requested_token, "dir")
        if error_message or not job or save_dir is None or requested_path is None:
            return error_message or "任务不存在", 404
    else:
        job, save_dir = resolve_job_and_validate_owner(job_id, sid)
        if not job or save_dir is None:
            return "任务不存在", 404
        requested_path = build_job_browser_default_relative_path(job, save_dir)
    focus_name = (request.args.get("focus") or "").strip()

    def browse_url_builder(relative_path: str) -> str:
        if not relative_path:
            return url_for('browse_job_directory', job_id=job_id)
        token = register_job_browser_target(job_id, 'dir', relative_path)
        return url_for('browse_job_directory', job_id=job_id, target=token)

    def download_url_builder(relative_path: str) -> str:
        token = register_job_browser_target(job_id, 'file', relative_path)
        return url_for('browse_download_file', job_id=job_id, target=token)

    return render_directory_browser(
        base_dir=save_dir,
        requested_path=requested_path,
        focus_name=focus_name,
        browse_url_builder=browse_url_builder,
        download_url_builder=download_url_builder,
        browser_title="下载目录浏览器",
        browser_subtitle="在浏览器里查看当前任务输出文件，点击即可下载。",
        browser_info_title="任务信息",
        browser_info_items=[{"label": "任务 ID", "value": str(job.get('id') or '')}],
        browser_badge_text=str(job.get('status_text') or job.get('status') or '任务'),
        browser_badge_class=f"status-{job.get('status', 'completed')}",
        root_label="下载根目录",
    )


@app.route("/browse-song/<job_id>/<song_key>", methods=["GET"])
def browse_song_directory(job_id: str, song_key: str):
    sid = ensure_session_id()
    job, save_dir = resolve_job_and_validate_owner(job_id, sid)
    if not job or save_dir is None:
        return "任务不存在", 404
    song, resolved_file, error_message = resolve_song_file_for_job(job, save_dir, song_key)
    if error_message or resolved_file is None or song is None:
        return error_message or "文件不存在", 404
    directory_token = register_job_browser_target(job_id, 'dir', relative_posix_path(save_dir, resolved_file.parent))
    return redirect(url_for(
        "browse_job_directory",
        job_id=job_id,
        target=directory_token,
        focus=resolved_file.name,
    ))


@app.route("/browse-download/<job_id>", methods=["GET"])
def browse_download_file(job_id: str):
    sid = ensure_session_id()
    requested_token = str(request.args.get("target", "") or "").strip()
    if requested_token:
        job, save_dir, relative_path, error_message = resolve_job_browser_target(job_id, sid, requested_token, "file")
        if error_message or not job or save_dir is None or relative_path is None:
            return error_message or "任务不存在", 404
    else:
        job, save_dir = resolve_job_and_validate_owner(job_id, sid)
        if not job or save_dir is None:
            return "任务不存在", 404
        relative_path = normalize_browser_relative_path(request.args.get("path", ""))
    if not relative_path:
        return "文件不存在", 404
    resolved_file = (save_dir / relative_path).resolve()
    if not ensure_path_within(save_dir, resolved_file):
        return "文件路径非法", 403
    if not resolved_file.exists() or not resolved_file.is_file():
        return "文件不存在", 404
    return send_file(str(resolved_file), as_attachment=True, download_name=resolved_file.name)


@app.route("/downloads/<job_id>/<song_key>", methods=["GET"])
def download_song_file(job_id: str, song_key: str):
    sid = ensure_session_id()
    job, save_dir = resolve_job_and_validate_owner(job_id, sid)
    if not job or save_dir is None:
        return "任务不存在", 404
    song, resolved_file, error_message = resolve_song_file_for_job(job, save_dir, song_key)
    if error_message or resolved_file is None or song is None:
        if error_message == "文件路径非法":
            return error_message, 403
        return error_message or "文件不存在", 404
    return send_file(str(resolved_file), as_attachment=True, download_name=song.get("download_filename") or resolved_file.name)


@app.route("/api/download-jobs/<job_id>", methods=["GET"])
def download_job_status(job_id: str):
    sid = ensure_session_id()
    job = get_download_job(job_id)
    if not job or job.get("sid") != sid:
        return jsonify({"error": "任务不存在"}), 404
    return jsonify(serialize_download_job(job))


@app.route("/", methods=["GET", "POST"])
def index():
    sid = ensure_session_id()
    state = get_state_for_sid(sid)

    if request.method == "POST":
        action = request.form.get("action", "")

        if action == "search":
            form_state = extract_form_state()
            update_state_for_sid(sid, form=form_state, download_summary=None, search_summary=None)

            if not form_state["keyword"]:
                flash("请输入搜索关键词或歌单链接", "error")
                return redirect(url_for("index"))
            if not form_state["selected_sources"]:
                flash("请至少选择一个音乐来源", "error")
                return redirect(url_for("index"))

            try:
                results, row_map, search_summary = search_music(form_state, sid)
                update_state_for_sid(
                    sid,
                    form=form_state,
                    results=results,
                    row_map=row_map,
                    last_query=form_state["keyword"],
                    download_summary=None,
                    search_summary=search_summary,
                )
                flash(f"搜索完成，共找到 {len(results)} 首歌曲", "success")
                if form_state["auto_download"] and results:
                    job_id = start_download_job(list(row_map.values()), form_state, sid)
                    flash(f"已启动后台下载任务：{job_id[:8]}，页面会实时显示进度", "success")
            except Exception as exc:
                flash(f"搜索失败：{exc}", "error")
            return redirect(url_for("index"))

        if action in {"download_selected", "download_all"} or action.startswith("download_row:"):
            form_state = state.get("form", default_form_state())
            row_map = state.get("row_map", {})
            selected_song_infos: List[Any] = []

            if not row_map:
                flash("当前没有搜索结果，请先执行搜索", "error")
                return redirect(url_for("index"))

            if action == "download_selected":
                selected_row_ids = request.form.getlist("selected_rows")
                selected_song_infos = [row_map[row_id] for row_id in selected_row_ids if row_id in row_map]
                if not selected_song_infos:
                    flash("请先勾选要下载的歌曲", "error")
                    return redirect(url_for("index"))
            elif action == "download_all":
                selected_song_infos = list(row_map.values())
            elif action.startswith("download_row:"):
                row_id = action.split(":", 1)[1]
                if row_id not in row_map:
                    flash("未找到要下载的歌曲，请重新搜索后再试", "error")
                    return redirect(url_for("index"))
                selected_song_infos = [row_map[row_id]]

            try:
                job_id = start_download_job(selected_song_infos, form_state, sid)
                flash(f"已启动后台下载任务：{job_id[:8]}，页面会实时显示进度", "success")
            except Exception as exc:
                flash(f"下载启动失败：{exc}", "error")
            return redirect(url_for("index"))

        flash("未知操作", "error")
        return redirect(url_for("index"))

    form_state = state.get("form", default_form_state())
    active_job = serialize_download_job(get_download_job(state.get("active_download_job_id")))
    return render_template_string(
        INDEX_TEMPLATE,
        style_css=STYLE_CSS,
        musicdl_available=MUSICDL_AVAILABLE,
        source_options=SOURCE_OPTIONS,
        form=form_state,
        results=state.get("results", []),
        result_count=len(state.get("results", [])),
        last_query=state.get("last_query", ""),
        download_summary=state.get("download_summary"),
        search_summary=state.get("search_summary"),
        active_download_job=active_job,
        ffmpeg_available=ffmpeg_available(),
        output_format_text=output_format_text,
    )


if __name__ == "__main__":
    host = os.environ.get("MUSIC_WEB_HOST", "0.0.0.0")
    port = int(os.environ.get("MUSIC_WEB_PORT", "8005"))
    debug = os.environ.get("MUSIC_WEB_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug, threaded=True)
