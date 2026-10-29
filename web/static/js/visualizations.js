/**
 * OScope Vector Visualizations Engine — Modern Light Mode
 * Clean, high-precision SVG and DOM-based interactive visualizers for OS algorithms:
 * - CPU Gantt Chart
 * - Dynamic Memory Partition Map
 * - Virtual Memory Page Replacement Stepper
 * - MMU Logical-to-Physical Address Translation
 * - Disk Head Seek Trajectory Graph
 * - Storage Bitmap & Inode Tree
 */

const Viz = {
  // Refined accessible academic palette for process tokens
  PROCESS_COLORS: [
    "#2563eb", // P1: Royal Cobalt Blue
    "#7c3aed", // P2: Deep Iris Violet
    "#059669", // P3: Emerald Jade
    "#d97706", // P4: Amber Ochre
    "#e11d48", // P5: Crimson Rose
    "#0891b2", // P6: Cyan Slate
    "#c026d3", // P7: Fuchsia
    "#ea580c", // P8: Terracotta Orange
    "#4f46e5", // P9: Indigo
    "#0d9488", // P10: Teal
  ],

  getProcessColor(pid) {
    if (pid === null || pid === undefined) return "#64748b";
    const idx = Math.abs(pid - 1) % this.PROCESS_COLORS.length;
    return this.PROCESS_COLORS[idx];
  },

  // ==========================================
  // 1. CPU Scheduling Gantt Chart
  // ==========================================
  renderGanttChart(containerId, timeline) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = "";

    if (!timeline || timeline.length === 0) {
      container.innerHTML = `<div class="viz-placeholder">No execution timeline to display. Configure processes and click "Run Simulation".</div>`;
      return;
    }

    const firstStart = timeline[0].start_time;
    const finalEnd = timeline[timeline.length - 1].end_time;
    const span = Math.max(1, finalEnd - firstStart);

    const svgWidth = Math.max(container.clientWidth || 700, 600);
    const height = 120;
    const marginX = 36;
    const usableW = svgWidth - marginX * 2;
    const blockY = 20;
    const blockH = 46;
    const axisY = blockY + blockH + 6;

    let svgHtml = `
      <svg width="100%" height="${height}" viewBox="0 0 ${svgWidth} ${height}" xmlns="http://www.w3.org/2000/svg" style="display:block; overflow:visible;">
        <defs>
          <pattern id="idle-hatch-light" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
            <line x1="0" y1="0" x2="0" y2="8" stroke="#cbd5e1" stroke-width="1.8" />
          </pattern>
        </defs>
        <!-- Background frame -->
        <rect x="0" y="0" width="${svgWidth}" height="${height}" fill="#f8fafc" rx="4" />
    `;

    // Time points collection for grid ticks
    const timePoints = new Set([firstStart]);
    timeline.forEach((seg) => timePoints.add(seg.end_time));
    const sortedTimes = Array.from(timePoints).sort((a, b) => a - b);

    // Draw vertical guideline ticks
    sortedTimes.forEach((t) => {
      const tx = marginX + ((t - firstStart) / span) * usableW;
      svgHtml += `<line x1="${tx}" y1="${blockY - 4}" x2="${tx}" y2="${axisY + 4}" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="2 2" />`;
    });

    // Draw Segments
    timeline.forEach((seg) => {
      const x0 = marginX + ((seg.start_time - firstStart) / span) * usableW;
      const x1 = marginX + ((seg.end_time - firstStart) / span) * usableW;
      const segW = Math.max(3, x1 - x0);
      const isIdle = seg.is_idle || seg.pid === null;
      const fillColor = isIdle ? "url(#idle-hatch-light)" : this.getProcessColor(seg.pid);
      const strokeColor = isIdle ? "#cbd5e1" : "rgba(255,255,255,0.3)";
      const label = isIdle ? "IDLE" : `P${seg.pid}`;
      const duration = seg.end_time - seg.start_time;

      svgHtml += `
        <g class="gantt-segment" data-pid="${seg.pid}" data-start="${seg.start_time}" data-end="${seg.end_time}" data-dur="${duration}" style="cursor: pointer;">
          <rect x="${x0 + 0.5}" y="${blockY}" width="${Math.max(1, segW - 1)}" height="${blockH}" rx="3" fill="${fillColor}" stroke="${strokeColor}" stroke-width="1" />
      `;

      if (segW > 24) {
        svgHtml += `
          <text x="${x0 + segW / 2}" y="${blockY + (segW > 45 ? 20 : 28)}" fill="${isIdle ? '#64748b' : '#ffffff'}" font-size="${segW > 45 ? 12 : 10.5}" font-weight="700" text-anchor="middle" font-family="ui-monospace, monospace">${label}</text>
        `;
        if (segW > 45) {
          svgHtml += `
            <text x="${x0 + segW / 2}" y="${blockY + 36}" fill="${isIdle ? '#94a3b8' : 'rgba(255,255,255,0.85)'}" font-size="10" font-family="ui-monospace, monospace" text-anchor="middle">${duration}u</text>
          `;
        }
      }

      svgHtml += `</g>`;
    });

    // Draw Axis line
    svgHtml += `<line x1="${marginX}" y1="${axisY}" x2="${marginX + usableW}" y2="${axisY}" stroke="#cbd5e1" stroke-width="1.5" />`;

    // Draw Axis Ticks and Labels
    let lastDrawnX = -999;
    sortedTimes.forEach((t, i) => {
      const tx = marginX + ((t - firstStart) / span) * usableW;
      if (tx - lastDrawnX >= 22 || i === 0 || i === sortedTimes.length - 1) {
        svgHtml += `
          <line x1="${tx}" y1="${axisY}" x2="${tx}" y2="${axisY + 5}" stroke="#94a3b8" stroke-width="1" />
          <text x="${tx}" y="${axisY + 18}" fill="#475569" font-size="11" font-weight="600" text-anchor="middle" font-family="ui-monospace, monospace">${t}</text>
        `;
        lastDrawnX = tx;
      }
    });

    svgHtml += `</svg>`;
    container.innerHTML = svgHtml;
  },

  // ==========================================
  // 2. Dynamic Memory Partition Map
  // ==========================================
  renderMemoryMap(containerId, totalMemory, blocks) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = "";

    if (!blocks || blocks.length === 0) {
      container.innerHTML = `<div class="viz-placeholder">No memory partitions allocated. Run an allocation workload to visualize contiguous partitions.</div>`;
      return;
    }

    const svgWidth = Math.max(container.clientWidth || 700, 600);
    const height = 130;
    const marginX = 36;
    const usableW = svgWidth - marginX * 2;
    const barY = 22;
    const barH = 50;
    const axisY = barY + barH + 6;

    let svgHtml = `
      <svg width="100%" height="${height}" viewBox="0 0 ${svgWidth} ${height}" xmlns="http://www.w3.org/2000/svg" style="display:block; overflow:visible;">
        <rect x="0" y="0" width="${svgWidth}" height="${height}" fill="#f8fafc" rx="4" />
    `;

    const addressPoints = new Set([0, totalMemory]);

    blocks.forEach((blk) => {
      const x0 = marginX + (blk.start_address / totalMemory) * usableW;
      const bw = Math.max(2, (blk.size / totalMemory) * usableW);
      addressPoints.add(blk.start_address);
      addressPoints.add(blk.start_address + blk.size);

      const isAlloc = blk.is_allocated;
      const fillColor = isAlloc ? this.getProcessColor(blk.process_id) : "#f1f5f9";
      const strokeColor = isAlloc ? "rgba(255,255,255,0.4)" : "#cbd5e1";
      const label = isAlloc ? `P${blk.process_id}` : "FREE";

      svgHtml += `
        <g class="mem-block" data-start="${blk.start_address}" data-size="${blk.size}" style="cursor: pointer;">
          <rect x="${x0 + 0.5}" y="${barY}" width="${Math.max(1, bw - 1)}" height="${barH}" fill="${fillColor}" stroke="${strokeColor}" stroke-width="1" rx="2" />
      `;

      if (bw > 26) {
        svgHtml += `
          <text x="${x0 + bw / 2}" y="${barY + (bw > 50 ? 22 : 30)}" fill="${isAlloc ? '#ffffff' : '#64748b'}" font-size="${bw > 50 ? 12 : 10.5}" font-weight="700" text-anchor="middle" font-family="ui-monospace, monospace">${label}</text>
        `;
        if (bw > 50) {
          svgHtml += `
            <text x="${x0 + bw / 2}" y="${barY + 38}" fill="${isAlloc ? 'rgba(255,255,255,0.9)' : '#94a3b8'}" font-size="10" font-family="ui-monospace, monospace" text-anchor="middle">${blk.size} KB</text>
          `;
        }
      }

      svgHtml += `</g>`;
    });

    // Address Axis
    svgHtml += `<line x1="${marginX}" y1="${axisY}" x2="${marginX + usableW}" y2="${axisY}" stroke="#cbd5e1" stroke-width="1.5" />`;

    const sortedAddrs = Array.from(addressPoints).sort((a, b) => a - b);
    let lastX = -999;
    sortedAddrs.forEach((addr, i) => {
      const ax = marginX + (addr / totalMemory) * usableW;
      if (ax - lastX >= 30 || i === 0 || i === sortedAddrs.length - 1) {
        svgHtml += `
          <line x1="${ax}" y1="${axisY}" x2="${ax}" y2="${axisY + 5}" stroke="#94a3b8" stroke-width="1" />
          <text x="${ax}" y="${axisY + 18}" fill="#475569" font-size="11" font-weight="600" text-anchor="middle" font-family="ui-monospace, monospace">${addr}</text>
        `;
        lastX = ax;
      }
    });

    svgHtml += `</svg>`;
    container.innerHTML = svgHtml;
  },

  // ==========================================
  // 3. Virtual Memory Page Replacement Stepper
  // ==========================================
  setupPagingStepper(containerId, result) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = "";

    if (!result || !result.steps || result.steps.length === 0) {
      container.innerHTML = `<div class="viz-placeholder">Run a page replacement algorithm to view step-by-step frame contents.</div>`;
      return;
    }

    const { steps, frame_count, reference_string } = result;
    let currentStep = 0;

    container.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 16px;">
        <!-- Reference string sequence track -->
        <div>
          <div style="font-size: 11px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 6px; letter-spacing: 0.5px;">Reference String Progression:</div>
          <div id="ref-track" style="display: flex; gap: 6px; overflow-x: auto; padding: 4px 0;"></div>
        </div>

        <!-- Frame inspection state -->
        <div style="background-color: #ffffff; border: 1px solid var(--border); border-radius: 6px; box-shadow: var(--shadow-sm); padding: 18px;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px;">
            <div id="step-status-title" style="font-size: 13.5px; font-weight: 700; color: var(--text-main);">Step 1 of ${steps.length}</div>
            <div id="step-result-badge" style="padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; text-transform: uppercase;">FAULT</div>
          </div>

          <!-- Physical Frame Slots -->
          <div id="frame-slots" style="display: grid; grid-template-columns: repeat(${frame_count}, 1fr); gap: 12px;"></div>
        </div>

        <!-- Step Controls Bar -->
        <div class="stepper-bar">
          <div class="stepper-info" id="stepper-counter">Step 1 / ${steps.length}</div>
          <div class="stepper-buttons">
            <button class="btn btn-secondary btn-sm" id="btn-step-first" title="First step"><svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><polygon points="19 20 9 12 19 4 19 20"/><line x1="5" y1="19" x2="5" y2="5"/></svg>First</button>
            <button class="btn btn-secondary btn-sm" id="btn-step-prev" title="Previous step"><svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="15 18 9 12 15 6"/></svg>Prev</button>
            <button class="btn btn-primary btn-sm" id="btn-step-play" title="Auto-play simulation"><svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>Auto-Play</button>
            <button class="btn btn-secondary btn-sm" id="btn-step-next" title="Next step">Next<svg class="arrow-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="9 18 15 12 9 6"/></svg></button>
            <button class="btn btn-secondary btn-sm" id="btn-step-last" title="Last step">Last<svg class="arrow-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19"/></svg></button>
          </div>
        </div>
      </div>
    `;

    const refTrack = container.querySelector("#ref-track");
    const frameSlots = container.querySelector("#frame-slots");
    const statusTitle = container.querySelector("#step-status-title");
    const resultBadge = container.querySelector("#step-result-badge");
    const counter = container.querySelector("#stepper-counter");
    let playInterval = null;

    function renderStep(idx) {
      currentStep = idx;
      const step = steps[idx];

      // Update ref track
      refTrack.innerHTML = reference_string
        .map((p, i) => {
          const isCurrent = i === idx;
          const isPassed = i < idx;
          const bg = isCurrent ? "var(--primary)" : isPassed ? "#f1f5f9" : "#ffffff";
          const border = isCurrent ? "var(--primary)" : "#e2e8f0";
          const color = isCurrent ? "#ffffff" : isPassed ? "var(--text-main)" : "#94a3b8";
          return `<div style="min-width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; background-color: ${bg}; border: 1px solid ${border}; border-radius: 4px; color: ${color}; font-weight: 700; font-family: ui-monospace, monospace; font-size: 12px;">${p}</div>`;
        })
        .join("");

      // Update Frame Slots
      const frameContents = step.frames || [];
      frameSlots.innerHTML = "";
      for (let f = 0; f < frame_count; f++) {
        const pageVal = f < frameContents.length && frameContents[f] !== -1 && frameContents[f] !== undefined ? frameContents[f] : "EMPTY";
        const isLoadedNow = pageVal === step.page_number;

        const slotBg = pageVal === "EMPTY" ? "#f8fafc" : isLoadedNow ? "rgba(37, 99, 235, 0.08)" : "#ffffff";
        const slotBorder = isLoadedNow ? "var(--primary-accent)" : "var(--border)";
        const valColor = pageVal === "EMPTY" ? "#94a3b8" : "var(--text-main)";

        frameSlots.innerHTML += `
          <div style="background-color: ${slotBg}; border: 1px solid ${slotBorder}; border-radius: 6px; padding: 12px; text-align: center; box-shadow: var(--shadow-sm);">
            <div style="font-size: 10.5px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase;">Frame ${f}</div>
            <div style="font-size: 21px; font-weight: 700; color: ${valColor}; font-family: ui-monospace, monospace; margin-top: 4px;">${pageVal}</div>
          </div>
        `;
      }

      // Update Status and Badge
      statusTitle.innerHTML = `Step ${idx + 1}: Referencing Page <span style="font-family: ui-monospace, monospace; color: var(--primary-accent);">${step.page_number}</span>`;
      if (step.is_fault || step.page_fault) {
        resultBadge.innerText = "PAGE FAULT";
        resultBadge.style.backgroundColor = "var(--danger-bg)";
        resultBadge.style.color = "var(--danger-text)";
        resultBadge.style.border = "1px solid var(--danger-border)";
      } else {
        resultBadge.innerText = "PAGE HIT";
        resultBadge.style.backgroundColor = "var(--success-bg)";
        resultBadge.style.color = "var(--success-text)";
        resultBadge.style.border = "1px solid var(--success-border)";
      }

      counter.innerText = `Step ${idx + 1} of ${steps.length}`;
    }

    renderStep(0);

    // Event handlers
    container.querySelector("#btn-step-first").onclick = () => renderStep(0);
    container.querySelector("#btn-step-prev").onclick = () => renderStep(Math.max(0, currentStep - 1));
    container.querySelector("#btn-step-next").onclick = () => renderStep(Math.min(steps.length - 1, currentStep + 1));
    container.querySelector("#btn-step-last").onclick = () => renderStep(steps.length - 1);

    const btnPlay = container.querySelector("#btn-step-play");
    btnPlay.onclick = () => {
      if (playInterval) {
        clearInterval(playInterval);
        playInterval = null;
        btnPlay.innerHTML = '<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>Auto-Play';
      } else {
        btnPlay.innerHTML = '<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>Pause';
        playInterval = setInterval(() => {
          if (currentStep < steps.length - 1) {
            renderStep(currentStep + 1);
          } else {
            clearInterval(playInterval);
            playInterval = null;
            btnPlay.innerHTML = '<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>Auto-Play';
          }
        }, 700);
      }
    };
  },

  // ==========================================
  // 4. Disk Arm Head Seek Trajectory Graph
  // ==========================================
  renderDiskPlot(containerId, result) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = "";

    if (!result || !result.steps || result.steps.length === 0) {
      container.innerHTML = `<div class="viz-placeholder">Run a disk scheduling algorithm to visualize cylinder seek arm trajectory.</div>`;
      return;
    }

    const steps = result.steps;
    const totalCylinders = result.total_cylinders || 200;
    const svgWidth = Math.max(container.clientWidth || 700, 600);
    const height = Math.max(220, steps.length * 28 + 40);

    const marginX = 40;
    const marginY = 30;
    const usableW = svgWidth - marginX * 2;
    const usableH = height - marginY * 2;

    const points = [];
    steps.forEach((s, idx) => {
      const y = marginY + (idx / Math.max(1, steps.length - 1)) * usableH;
      const x = marginX + (s.to_cylinder / (totalCylinders - 1)) * usableW;
      points.push({ x, y, cyl: s.to_cylinder, step: s.step_number, movement: s.movement });
    });

    let svgHtml = `
      <svg width="100%" height="${height}" viewBox="0 0 ${svgWidth} ${height}" xmlns="http://www.w3.org/2000/svg" style="display:block;">
        <rect x="0" y="0" width="${svgWidth}" height="${height}" fill="#f8fafc" rx="4" />
    `;

    // Vertical cylinder track grid lines
    [0, 50, 100, 150, totalCylinders - 1].forEach((cyl) => {
      const cx = marginX + (cyl / (totalCylinders - 1)) * usableW;
      svgHtml += `
        <line x1="${cx}" y1="${marginY}" x2="${cx}" y2="${height - marginY}" stroke="#e2e8f0" stroke-width="1" />
        <text x="${cx}" y="${marginY - 10}" fill="#94a3b8" font-size="10.5" font-family="ui-monospace, monospace" text-anchor="middle">${cyl}</text>
      `;
    });

    // Connecting polyline
    const polyPoints = points.map((p) => `${p.x},${p.y}`).join(" ");
    svgHtml += `
      <polyline points="${polyPoints}" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
    `;

    // Node dots
    points.forEach((p, idx) => {
      const isStart = idx === 0;
      const dotColor = isStart ? "#059669" : "#2563eb";
      svgHtml += `
        <circle cx="${p.x}" cy="${p.y}" r="4.5" fill="${dotColor}" stroke="#ffffff" stroke-width="2" />
        <text x="${p.x + 8}" y="${p.y + 4}" fill="#0f172a" font-size="11" font-weight="700" font-family="ui-monospace, monospace">${p.cyl}</text>
      `;
    });

    svgHtml += `</svg>`;
    container.innerHTML = svgHtml;
  },

  // ==========================================
  // 5. MMU Logical-to-Physical Address Translation
  // ==========================================
  renderAddressTranslation(containerId, data) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = "";

    if (!data || !data.translations || data.translations.length === 0) {
      container.innerHTML = `<div class="viz-placeholder">Execute address translation to visualize MMU hardware translation flow.</div>`;
      return;
    }

    const t = data.translations[0];
    const pageSize = data.page_size || 4096;

    container.innerHTML = `
      <div style="background-color: #ffffff; border: 1px solid var(--border); border-radius: 6px; box-shadow: var(--shadow-sm); padding: 20px;">
        <div style="font-size: 13px; font-weight: 700; color: var(--text-main); margin-bottom: 16px;">
          Hardware Memory Management Unit (MMU) Architecture:
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 18px; align-items: center;">
          <!-- 1. Logical Address -->
          <div style="border: 1px solid var(--border); border-radius: 6px; padding: 14px; background-color: var(--bg-surface-alt);">
            <div style="font-size: 10.5px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase;">1. Virtual / Logical Address</div>
            <div style="font-size: 22px; font-weight: 700; color: var(--text-main); font-family: ui-monospace, monospace; margin: 6px 0;">0x${t.virtual_address.toString(16).toUpperCase()}</div>
            <div style="display: flex; gap: 8px; margin-top: 10px;">
              <div style="flex: 1; background-color: #ffffff; border: 1px solid var(--border); padding: 8px; border-radius: 4px; text-align: center;">
                <div style="font-size: 10px; color: var(--text-secondary);">Page Number (p)</div>
                <div style="font-size: 16px; font-weight: 700; color: var(--primary-accent); font-family: ui-monospace, monospace;">${t.page_number}</div>
              </div>
              <div style="flex: 1; background-color: #ffffff; border: 1px solid var(--border); padding: 8px; border-radius: 4px; text-align: center;">
                <div style="font-size: 10px; color: var(--text-secondary);">Offset (d)</div>
                <div style="font-size: 16px; font-weight: 700; color: #059669; font-family: ui-monospace, monospace;">0x${t.offset.toString(16).toUpperCase()}</div>
              </div>
            </div>
          </div>

          <!-- 2. Page Table Lookup -->
          <div style="border: 1px solid var(--border); border-radius: 6px; padding: 14px; background-color: var(--bg-surface-alt); text-align: center;">
            <div style="font-size: 10.5px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase;">2. Page Table Lookup</div>
            <div style="font-size: 13px; color: var(--text-secondary); margin: 8px 0; font-family: ui-monospace, monospace;">PT[ Page ${t.page_number} ]</div>
            <div style="display: inline-block; padding: 6px 14px; background-color: ${t.page_fault ? 'var(--danger-bg)' : 'var(--success-bg)'}; border: 1px solid ${t.page_fault ? 'var(--danger-border)' : 'var(--success-border)'}; border-radius: 4px; font-weight: 700; color: ${t.page_fault ? 'var(--danger-text)' : 'var(--success-text)'};">
              ${t.page_fault ? 'PAGE FAULT (Page Not Present)' : `Frame Number (f) = ${t.frame_number}`}
            </div>
          </div>

          <!-- 3. Physical Address -->
          <div style="border: 1px solid var(--border); border-radius: 6px; padding: 14px; background-color: var(--bg-surface-alt);">
            <div style="font-size: 10.5px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase;">3. Physical Address Generated</div>
            <div style="font-size: 22px; font-weight: 700; color: ${t.page_fault ? 'var(--danger-text)' : '#059669'}; font-family: ui-monospace, monospace; margin: 6px 0;">
              ${t.page_fault ? 'N/A (Trapped to OS)' : `0x${t.physical_address.toString(16).toUpperCase()}`}
            </div>
            <div style="font-size: 11px; color: var(--text-muted); font-family: ui-monospace, monospace; margin-top: 6px;">
              ${t.page_fault ? 'OS allocates frame via demand paging handler' : `Formula: (f × ${pageSize}) + d = ${t.physical_address}`}
            </div>
          </div>
        </div>
      </div>
    `;
  },

  // ==========================================
  // 6. Simulated File System Storage Bitmap
  // ==========================================
  renderFilesystemGrid(containerId, fsData) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = "";

    if (!fsData || !fsData.status || !fsData.status.block_bitmap) {
      container.innerHTML = `<div class="viz-placeholder">Run a file system simulation to visualize physical storage allocation blocks.</div>`;
      return;
    }

    const bitmap = fsData.status.block_bitmap;
    const inodes = fsData.inodes || [];

    let blocksHtml = bitmap
      .map((isUsed, bIdx) => {
        const bg = isUsed ? "var(--primary-accent)" : "#f1f5f9";
        const border = isUsed ? "var(--primary-accent)" : "#e2e8f0";
        return `
          <div title="Block ${bIdx}: ${isUsed ? 'Allocated' : 'Free'}" style="height: 32px; display: flex; align-items: center; justify-content: center; background-color: ${bg}; border: 1px solid ${border}; border-radius: 3px; font-family: ui-monospace, monospace; font-size: 11px; font-weight: 700; color: ${isUsed ? '#ffffff' : '#64748b'};">
            ${bIdx}
          </div>
        `;
      })
      .join("");

    container.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 16px;">
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="font-size: 11px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px;">Storage Allocation Block Bitmap (${bitmap.length} Blocks):</div>
            <div style="font-size: 12px; font-family: ui-monospace, monospace; color: var(--text-secondary);">
              Used: <span style="color: var(--primary-accent); font-weight: 700;">${fsData.status.used_blocks}</span> | Free: <span style="color: #059669; font-weight: 700;">${fsData.status.free_blocks}</span>
            </div>
          </div>
          <div style="display: grid; grid-template-columns: repeat(16, 1fr); gap: 6px;">
            ${blocksHtml}
          </div>
        </div>

        <!-- Inodes Table -->
        <div class="data-table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Inode ID</th>
                <th>Path</th>
                <th>Type</th>
                <th>Size (B)</th>
                <th>Strategy</th>
                <th>Blocks Allocated</th>
              </tr>
            </thead>
            <tbody>
              ${inodes
                .map(
                  (ino) => `
                <tr>
                  <td style="font-family: ui-monospace, monospace;">${ino.inode_id}</td>
                  <td style="font-family: ui-monospace, monospace; font-weight: 700; color: var(--text-main);">${ino.path}</td>
                  <td>${ino.is_directory ? '<span class="type-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z"/></svg>Directory</span>' : '<span class="type-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>File</span>'}</td>
                  <td style="font-family: ui-monospace, monospace;">${ino.size_bytes}</td>
                  <td><span class="module-tag">${ino.strategy}</span></td>
                  <td style="font-family: ui-monospace, monospace;">${ino.allocated_blocks && ino.allocated_blocks.length ? ino.allocated_blocks.join(', ') : 'None'}</td>
                </tr>
              `
                )
                .join("")}
            </tbody>
          </table>
        </div>
      </div>
    `;
  },
};

window.Viz = Viz;
