/**
 * OScope Main Web Application Controller
 * Manages experiment routing, interactive form inputs, preset loaders,
 * simulation execution pipelines, and result presentation.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Navigation Routing
  const navItems = document.querySelectorAll(".nav-item");
  const views = document.querySelectorAll(".experiment-view");
  const pageTitle = document.getElementById("page-title");
  const pageSubtitle = document.getElementById("page-subtitle");

  const routeMetadata = {
    overview: {
      title: "Laboratory Overview",
      subtitle: "Discover, configure, and launch Operating Systems experimentation modules.",
    },
    scheduling: {
      title: "CPU Scheduling",
      subtitle: "Preemptive and non-preemptive CPU dispatching algorithms, Gantt execution charts, and metrics.",
    },
    memory: {
      title: "Dynamic Memory Allocation",
      subtitle: "Contiguous partitioning strategies, variable-size allocation, coalescing, and external fragmentation.",
    },
    paging: {
      title: "Page Replacement",
      subtitle: "Virtual memory page replacement algorithms, reference strings, page hit/fault rates, and Belady's anomaly.",
    },
    deadlock: {
      title: "Deadlock Avoidance & Detection",
      subtitle: "Dijkstra's Banker's Algorithm, safe execution sequence analysis, and resource-allocation matrices.",
    },
    disk: {
      title: "Secondary Storage & Disk Scheduling",
      subtitle: "Rotational disk arm head movement optimization, cylinder seek trajectories, and boundary semantics.",
    },
    "address-translation": {
      title: "Virtual Memory & MMU Paging",
      subtitle: "Logical-to-physical address translation, offset preservation, page table lookups, and demand paging.",
    },
    filesystem: {
      title: "Simulated File System",
      subtitle: "Directory hierarchy, file inodes, contiguous vs indexed allocation, and physical block allocation bitmaps.",
    },
    "process-lifecycle": {
      title: "Process Lifecycle Explorer",
      subtitle: "Process state machine transitions (New, Ready, Running, Waiting, Terminated) and POSIX process management.",
    },
    "linux-experiments": {
      title: "POSIX & Linux Concurrency Sandbox",
      subtitle: "Real OS kernel primitives: pipes, shared memory, POSIX semaphores, Peterson's algorithm, and producer-consumer.",
    },
    "host-monitor": {
      title: "Host System Diagnostics",
      subtitle: "Real-time Linux host kernel metrics parsed directly from /proc/stat, /proc/meminfo, and sysfs.",
    },
  };

  function navigateTo(route) {
    const targetRoute = routeMetadata[route] ? route : "overview";

    navItems.forEach((item) => {
      if (item.getAttribute("data-route") === targetRoute) {
        item.classList.add("active");
      } else {
        item.classList.remove("active");
      }
    });

    views.forEach((view) => {
      if (view.id === `view-${targetRoute}`) {
        view.classList.add("active");
      } else {
        view.classList.remove("active");
      }
    });

    if (pageTitle && pageSubtitle) {
      pageTitle.innerText = routeMetadata[targetRoute].title;
      pageSubtitle.innerText = routeMetadata[targetRoute].subtitle;
    }

    window.location.hash = targetRoute;
  }

  navItems.forEach((item) => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const route = item.getAttribute("data-route");
      navigateTo(route);
    });
  });

  // Overview quick-launch cards
  document.querySelectorAll(".module-card").forEach((card) => {
    card.addEventListener("click", () => {
      const target = card.getAttribute("data-target");
      if (target) navigateTo(target);
    });
  });

  // Hash-based deep link on page load
  const initialHash = window.location.hash.replace("#", "") || "overview";
  navigateTo(initialHash);

  window.addEventListener("hashchange", () => {
    const hash = window.location.hash.replace("#", "") || "overview";
    navigateTo(hash);
  });

  // Check system backend readiness
  const statusIndicator = document.getElementById("status-indicator");
  const statusText = document.getElementById("status-text");

  async function checkBackendStatus() {
    try {
      const status = await Api.getStatus();
      if (status.is_available) {
        statusIndicator.className = "status-indicator ready";
        statusText.innerText = `Backend Active (${status.runner_type.toUpperCase()})`;
      } else {
        statusIndicator.className = "status-indicator error";
        statusText.innerText = "Backend Offline";
      }
    } catch (e) {
      statusIndicator.className = "status-indicator error";
      statusText.innerText = "Connection Failed";
    }
  }
  checkBackendStatus();

  // ==========================================
  // MODULE 1: CPU Scheduling Controller
  // ==========================================
  const schedAlgo = document.getElementById("sched-algo");
  const schedQuantumGroup = document.getElementById("sched-quantum-group");
  const schedMlfqGroup = document.getElementById("sched-mlfq-group");
  const schedProcTable = document.getElementById("sched-proc-tbody");
  const btnSchedAdd = document.getElementById("btn-sched-add");
  const btnSchedRun = document.getElementById("btn-sched-run");
  const schedPreset = document.getElementById("sched-preset");
  const schedAlert = document.getElementById("sched-alert");

  function updateSchedFields() {
    const val = schedAlgo.value;
    if (val === "Round Robin") {
      schedQuantumGroup.style.display = "block";
      schedMlfqGroup.style.display = "none";
    } else if (val === "MLFQ") {
      schedQuantumGroup.style.display = "none";
      schedMlfqGroup.style.display = "block";
    } else if (val === "Compare All") {
      schedQuantumGroup.style.display = "block";
      schedMlfqGroup.style.display = "block";
    } else {
      schedQuantumGroup.style.display = "none";
      schedMlfqGroup.style.display = "none";
    }
  }
  schedAlgo.addEventListener("change", updateSchedFields);
  updateSchedFields();

  function addSchedRow(pid, arrival = 0, burst = 5, priority = 0) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="font-family: ui-monospace, monospace; font-weight: 700; color: var(--primary);">P${pid}</td>
      <td><input type="number" class="proc-arrival" value="${arrival}" min="0" /></td>
      <td><input type="number" class="proc-burst" value="${burst}" min="1" /></td>
      <td><input type="number" class="proc-priority" value="${priority}" min="0" /></td>
      <td><button class="btn btn-outline btn-sm btn-del-row" style="color: var(--danger-text); padding: 3px 6px;" title="Remove process"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button></td>
    `;
    tr.querySelector(".btn-del-row").onclick = () => tr.remove();
    schedProcTable.appendChild(tr);
  }

  btnSchedAdd.onclick = () => {
    const nextPid = schedProcTable.querySelectorAll("tr").length + 1;
    addSchedRow(nextPid, 0, 4, 1);
  };

  const schedPresets = {
    standard: [
      { pid: 1, arrival: 0, burst: 6, priority: 2 },
      { pid: 2, arrival: 1, burst: 4, priority: 1 },
      { pid: 3, arrival: 2, burst: 8, priority: 3 },
      { pid: 4, arrival: 3, burst: 3, priority: 2 },
    ],
    convoy: [
      { pid: 1, arrival: 0, burst: 24, priority: 1 },
      { pid: 2, arrival: 1, burst: 3, priority: 1 },
      { pid: 3, arrival: 2, burst: 3, priority: 1 },
    ],
    priority_demo: [
      { pid: 1, arrival: 0, burst: 10, priority: 3 },
      { pid: 2, arrival: 0, burst: 1, priority: 1 },
      { pid: 3, arrival: 0, burst: 2, priority: 4 },
      { pid: 4, arrival: 0, burst: 1, priority: 5 },
      { pid: 5, arrival: 0, burst: 5, priority: 2 },
    ],
  };

  function loadSchedPreset(key) {
    schedProcTable.innerHTML = "";
    const list = schedPresets[key] || schedPresets.standard;
    list.forEach((p) => addSchedRow(p.pid, p.arrival, p.burst, p.priority));
  }
  loadSchedPreset("standard");

  schedPreset.addEventListener("change", (e) => loadSchedPreset(e.target.value));

  btnSchedRun.onclick = async () => {
    schedAlert.className = "alert-banner";
    schedAlert.style.display = "none";
    btnSchedRun.disabled = true;
    btnSchedRun.innerText = "Simulating...";

    try {
      const rows = schedProcTable.querySelectorAll("tr");
      const processes = [];
      rows.forEach((tr, idx) => {
        processes.push({
          pid: idx + 1,
          arrival_time: parseInt(tr.querySelector(".proc-arrival").value, 10),
          burst_time: parseInt(tr.querySelector(".proc-burst").value, 10),
          priority: parseInt(tr.querySelector(".proc-priority").value, 10),
        });
      });

      const payload = {
        algorithm: schedAlgo.value,
        processes: processes,
        rr_quantum: parseInt(document.getElementById("sched-rr-quantum").value, 10),
        mlfq_q0: parseInt(document.getElementById("sched-mlfq-q0").value, 10),
        mlfq_q1: parseInt(document.getElementById("sched-mlfq-q1").value, 10),
        mlfq_q2: parseInt(document.getElementById("sched-mlfq-q2").value, 10),
      };

      const result = await Api.runScheduling(payload);

      schedAlert.innerText = `Simulation finished successfully for ${result.algorithm_name || schedAlgo.value}.`;
      schedAlert.className = "alert-banner success active";
      schedAlert.style.display = "block";

      if (result.timeline) {
        Viz.renderGanttChart("sched-gantt-container", result.timeline);
      }

      if (result.averages) {
        document.getElementById("sched-val-wait").innerText = result.averages.average_waiting_time.toFixed(2);
        document.getElementById("sched-val-tat").innerText = result.averages.average_turnaround_time.toFixed(2);
        document.getElementById("sched-val-resp").innerText = result.averages.average_response_time.toFixed(2);
      }

      // Comparison table if Compare All
      const compContainer = document.getElementById("sched-comparison-container");
      if (result.comparisons && result.comparisons.length > 0) {
        compContainer.style.display = "block";
        const tbody = document.getElementById("sched-comparison-tbody");
        tbody.innerHTML = result.comparisons
          .map(
            (c, i) => `
          <tr>
            <td style="font-weight: 700;">#${i + 1} ${c.algorithm_name}</td>
            <td style="font-family: ui-monospace, monospace; font-weight: 700; color: #34d399;">${c.average_waiting_time.toFixed(2)}</td>
            <td style="font-family: ui-monospace, monospace;">${c.average_turnaround_time.toFixed(2)}</td>
            <td style="font-family: ui-monospace, monospace;">${c.average_response_time.toFixed(2)}</td>
          </tr>
        `
          )
          .join("");
      } else {
        compContainer.style.display = "none";
      }

      if (result.raw_output) {
        document.getElementById("sched-raw-output").innerText = result.raw_output;
      }
    } catch (err) {
      schedAlert.innerText = err.message || "Simulation error occurred.";
      schedAlert.className = "alert-banner danger active";
      schedAlert.style.display = "block";
    } finally {
      btnSchedRun.disabled = false;
      btnSchedRun.innerText = "▶ Run Simulation";
    }
  };

  // ==========================================
  // MODULE 2: Dynamic Memory Allocation Controller
  // ==========================================
  const memStrategy = document.getElementById("mem-strategy");
  const memTotalInput = document.getElementById("mem-total");
  const memOpsTbody = document.getElementById("mem-ops-tbody");
  const btnMemAddOp = document.getElementById("btn-mem-add-op");
  const btnMemRun = document.getElementById("btn-mem-run");
  const memPreset = document.getElementById("mem-preset");
  const memAlert = document.getElementById("mem-alert");

  function addMemRow(opType = "alloc", pid = 1, size = 150) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>
        <select class="mem-op-type form-select" style="padding: 2px 6px; font-size: 11px;">
          <option value="alloc" ${opType === "alloc" ? "selected" : ""}>Allocate</option>
          <option value="free" ${opType === "free" ? "selected" : ""}>Deallocate</option>
        </select>
      </td>
      <td><input type="number" class="mem-op-pid" value="${pid}" min="1" /></td>
      <td><input type="number" class="mem-op-size" value="${size}" min="0" /></td>
      <td><button class="btn btn-outline btn-sm btn-del-row" style="color: var(--danger-text); padding: 3px 6px;" title="Remove operation"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button></td>
    `;
    tr.querySelector(".btn-del-row").onclick = () => tr.remove();
    memOpsTbody.appendChild(tr);
  }

  btnMemAddOp.onclick = () => addMemRow("alloc", 1, 100);

  const memPresets = {
    standard: [
      { op: "alloc", pid: 1, size: 200 },
      { op: "alloc", pid: 2, size: 300 },
      { op: "alloc", pid: 3, size: 150 },
      { op: "free", pid: 2, size: 0 },
      { op: "alloc", pid: 4, size: 120 },
    ],
    fragmentation: [
      { op: "alloc", pid: 1, size: 150 },
      { op: "alloc", pid: 2, size: 100 },
      { op: "alloc", pid: 3, size: 200 },
      { op: "alloc", pid: 4, size: 100 },
      { op: "free", pid: 2, size: 0 },
      { op: "free", pid: 4, size: 0 },
      { op: "alloc", pid: 5, size: 180 },
    ],
  };

  function loadMemPreset(key) {
    memOpsTbody.innerHTML = "";
    const list = memPresets[key] || memPresets.standard;
    list.forEach((m) => addMemRow(m.op, m.pid, m.size));
  }
  loadMemPreset("standard");

  memPreset.addEventListener("change", (e) => loadMemPreset(e.target.value));

  btnMemRun.onclick = async () => {
    memAlert.style.display = "none";
    btnMemRun.disabled = true;
    btnMemRun.innerText = "Simulating...";

    try {
      const rows = memOpsTbody.querySelectorAll("tr");
      const operations = [];
      rows.forEach((tr, idx) => {
        operations.push({
          request_id: idx + 1,
          operation_type: tr.querySelector(".mem-op-type").value,
          pid: parseInt(tr.querySelector(".mem-op-pid").value, 10),
          size: parseInt(tr.querySelector(".mem-op-size").value, 10),
        });
      });

      const totalMem = parseInt(memTotalInput.value, 10);
      const payload = {
        strategy: memStrategy.value,
        total_memory: totalMem,
        operations: operations,
      };

      const result = await Api.runMemory(payload);

      memAlert.innerText = `Memory allocation simulation completed successfully for ${result.strategy_name || memStrategy.value}.`;
      memAlert.className = "alert-banner success active";
      memAlert.style.display = "block";

      if (result.final_blocks) {
        Viz.renderMemoryMap("mem-map-container", totalMem, result.final_blocks);
      }

      if (result.metrics) {
        document.getElementById("mem-val-ext-frag").innerText = `${result.metrics.external_fragmentation_percent.toFixed(1)}%`;
        document.getElementById("mem-val-util").innerText = `${result.metrics.allocation_success_rate.toFixed(1)}%`;
        document.getElementById("mem-val-holes").innerText = result.metrics.free_blocks_count;
      }

      // Comparison table if Compare All
      const compContainer = document.getElementById("mem-comparison-container");
      if (result.entries && result.entries.length > 0) {
        compContainer.style.display = "block";
        const tbody = document.getElementById("mem-comparison-tbody");
        tbody.innerHTML = result.entries
          .map(
            (e) => `
          <tr>
            <td style="font-weight: 700;">${e.strategy_name}</td>
            <td style="font-family: ui-monospace, monospace; color: #34d399;">${e.allocation_success_rate.toFixed(1)}%</td>
            <td style="font-family: ui-monospace, monospace; color: var(--warning-text);">${e.external_fragmentation_percent.toFixed(1)}%</td>
            <td style="font-family: ui-monospace, monospace;">${e.free_blocks_count}</td>
          </tr>
        `
          )
          .join("");
      } else {
        compContainer.style.display = "none";
      }

      if (result.raw_output) {
        document.getElementById("mem-raw-output").innerText = result.raw_output;
      }
    } catch (err) {
      memAlert.innerText = err.message || "Memory simulation error.";
      memAlert.className = "alert-banner danger active";
      memAlert.style.display = "block";
    } finally {
      btnMemRun.disabled = false;
      btnMemRun.innerText = "▶ Run Simulation";
    }
  };

  // ==========================================
  // MODULE 3: Page Replacement Controller
  // ==========================================
  const pagingAlgo = document.getElementById("paging-algo");
  const pagingFrames = document.getElementById("paging-frames");
  const pagingRefString = document.getElementById("paging-ref-string");
  const btnPagingRun = document.getElementById("btn-paging-run");
  const pagingPreset = document.getElementById("paging-preset");
  const pagingAlert = document.getElementById("paging-alert");

  const pagingPresets = {
    standard: {
      frames: 3,
      ref: "7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1",
    },
    belady: {
      frames: 3,
      ref: "1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5",
    },
    looping: {
      frames: 4,
      ref: "1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 5",
    },
  };

  function loadPagingPreset(key) {
    const p = pagingPresets[key] || pagingPresets.standard;
    pagingFrames.value = p.frames;
    pagingRefString.value = p.ref;
  }
  loadPagingPreset("standard");
  pagingPreset.addEventListener("change", (e) => loadPagingPreset(e.target.value));

  btnPagingRun.onclick = async () => {
    pagingAlert.style.display = "none";
    btnPagingRun.disabled = true;
    btnPagingRun.innerText = "Simulating...";

    try {
      const refArr = pagingRefString.value
        .split(/[\s,]+/)
        .map((x) => x.trim())
        .filter((x) => x.length > 0)
        .map((x) => parseInt(x, 10));

      const payload = {
        algorithm: pagingAlgo.value,
        num_frames: parseInt(pagingFrames.value, 10),
        reference_string: refArr,
      };

      const result = await Api.runPaging(payload);

      pagingAlert.innerText = `Paging simulation completed for ${result.algorithm_name || pagingAlgo.value}.`;
      pagingAlert.className = "alert-banner success active";
      pagingAlert.style.display = "block";

      if (result.metrics) {
        document.getElementById("paging-val-faults").innerText = result.metrics.page_faults;
        document.getElementById("paging-val-hits").innerText = result.metrics.page_hits;
        document.getElementById("paging-val-rate").innerText = `${(result.metrics.fault_rate * 100).toFixed(1)}%`;
      }

      if (result.steps) {
        Viz.setupPagingStepper("paging-stepper-container", result);
      }

      // Comparison table if Compare All
      const compContainer = document.getElementById("paging-comparison-container");
      if (result.entries && result.entries.length > 0) {
        compContainer.style.display = "block";
        const tbody = document.getElementById("paging-comparison-tbody");
        tbody.innerHTML = result.entries
          .map(
            (e) => `
          <tr>
            <td style="font-weight: 700;">${e.algorithm_name}</td>
            <td style="font-family: ui-monospace, monospace; color: var(--danger-text); font-weight: 700;">${e.page_faults}</td>
            <td style="font-family: ui-monospace, monospace; color: #34d399;">${e.page_hits}</td>
            <td style="font-family: ui-monospace, monospace;">${(e.fault_rate * 100).toFixed(1)}%</td>
          </tr>
        `
          )
          .join("");
      } else {
        compContainer.style.display = "none";
      }

      if (result.raw_output) {
        document.getElementById("paging-raw-output").innerText = result.raw_output;
      }
    } catch (err) {
      pagingAlert.innerText = err.message || "Paging simulation error.";
      pagingAlert.className = "alert-banner danger active";
      pagingAlert.style.display = "block";
    } finally {
      btnPagingRun.disabled = false;
      btnPagingRun.innerText = "▶ Run Simulation";
    }
  };

  // ==========================================
  // MODULE 4: Deadlock Management Controller
  // ==========================================
  const dlMode = document.getElementById("dl-mode");
  const dlAvailInput = document.getElementById("dl-available");
  const dlAllocInput = document.getElementById("dl-allocation");
  const dlMaxInput = document.getElementById("dl-max");
  const dlReqPid = document.getElementById("dl-req-pid");
  const dlReqVec = document.getElementById("dl-req-vec");
  const dlReqGroup = document.getElementById("dl-request-group");
  const btnDlRun = document.getElementById("btn-dl-run");
  const dlPreset = document.getElementById("dl-preset");
  const dlAlert = document.getElementById("dl-alert");

  function updateDlFields() {
    dlReqGroup.style.display = dlMode.value === "request" ? "block" : "none";
  }
  dlMode.addEventListener("change", updateDlFields);
  updateDlFields();

  const dlPresets = {
    safe: {
      avail: "3, 3, 2",
      alloc: "0, 1, 0\n2, 0, 0\n3, 0, 2\n2, 1, 1\n0, 0, 2",
      max: "7, 5, 3\n3, 2, 2\n9, 0, 2\n2, 2, 2\n4, 3, 3",
    },
    deadlock: {
      avail: "0, 0, 0",
      alloc: "0, 1, 0\n2, 0, 0\n3, 0, 3",
      max: "0, 0, 0\n2, 0, 2\n0, 0, 0",
    },
  };

  function loadDlPreset(key) {
    const p = dlPresets[key] || dlPresets.safe;
    dlAvailInput.value = p.avail;
    dlAllocInput.value = p.alloc;
    dlMaxInput.value = p.max;
  }
  loadDlPreset("safe");
  dlPreset.addEventListener("change", (e) => loadDlPreset(e.target.value));

  btnDlRun.onclick = async () => {
    dlAlert.style.display = "none";
    btnDlRun.disabled = true;
    btnDlRun.innerText = "Evaluating...";

    try {
      const parseVec = (str) =>
        str
          .split(/[\s,]+/)
          .map((x) => x.trim())
          .filter(Boolean)
          .map((x) => parseInt(x, 10));
      const parseMat = (str) =>
        str
          .trim()
          .split("\n")
          .map((line) => parseVec(line))
          .filter((row) => row.length > 0);

      const available = parseVec(dlAvailInput.value);
      const allocation = parseMat(dlAllocInput.value);
      const maxClaim = parseMat(dlMaxInput.value);

      const payload = {
        mode: dlMode.value,
        num_processes: allocation.length,
        num_resources: available.length,
        available: available,
        allocation: allocation,
        max_claim: maxClaim,
        requesting_process_id: parseInt(dlReqPid.value || 0, 10),
        request_vector: parseVec(dlReqVec.value || "0, 0, 0"),
      };

      const result = await Api.runDeadlock(payload);

      const badge = document.getElementById("dl-safe-badge");
      const seqDisplay = document.getElementById("dl-safe-seq");

      if (result.is_safe || result.granted) {
        dlAlert.innerText = result.message || "State is completely SAFE. No deadlock risk.";
        dlAlert.className = "alert-banner success active";
        dlAlert.style.display = "block";

        badge.innerText = "SAFE STATE";
        badge.style.backgroundColor = "var(--success-bg)";
        badge.style.color = "var(--success-text)";
        badge.style.border = "1px solid var(--success)";

        if (result.safe_sequence && result.safe_sequence.length) {
          seqDisplay.innerText = result.safe_sequence.map((p) => `P${p}`).join(" → ");
        } else {
          seqDisplay.innerText = "All processes completed safely.";
        }
      } else {
        dlAlert.innerText = result.message || "DEADLOCK RISK: System cannot guarantee safe completion.";
        dlAlert.className = "alert-banner danger active";
        dlAlert.style.display = "block";

        badge.innerText = "UNSAFE / DEADLOCK";
        badge.style.backgroundColor = "var(--danger-bg)";
        badge.style.color = "var(--danger-text)";
        badge.style.border = "1px solid var(--danger)";

        seqDisplay.innerText = result.deadlocked_processes && result.deadlocked_processes.length
          ? `Deadlocked: ${result.deadlocked_processes.map((p) => `P${p}`).join(", ")}`
          : "No safe execution sequence exists.";
      }

      // Display Need Matrix
      if (result.need) {
        const needTbody = document.getElementById("dl-need-tbody");
        needTbody.innerHTML = result.need
          .map(
            (row, p) => `
          <tr>
            <td style="font-weight: 700; color: var(--primary);">P${p}</td>
            <td style="font-family: ui-monospace, monospace;">${row.join(", ")}</td>
          </tr>
        `
          )
          .join("");
      }

      if (result.raw_output) {
        document.getElementById("dl-raw-output").innerText = result.raw_output;
      }
    } catch (err) {
      dlAlert.innerText = err.message || "Deadlock evaluation error.";
      dlAlert.className = "alert-banner danger active";
      dlAlert.style.display = "block";
    } finally {
      btnDlRun.disabled = false;
      btnDlRun.innerText = "▶ Evaluate State";
    }
  };

  // ==========================================
  // MODULE 5: Disk Scheduling Controller
  // ==========================================
  const diskAlgo = document.getElementById("disk-algo");
  const diskHead = document.getElementById("disk-head");
  const diskTotal = document.getElementById("disk-total");
  const diskDirection = document.getElementById("disk-direction");
  const diskRequests = document.getElementById("disk-requests");
  const btnDiskRun = document.getElementById("btn-disk-run");
  const diskPreset = document.getElementById("disk-preset");
  const diskAlert = document.getElementById("disk-alert");

  const diskPresets = {
    standard: "98, 183, 37, 122, 14, 124, 65, 67",
    clustered: "50, 52, 55, 180, 182, 185, 20, 22",
  };

  function loadDiskPreset(key) {
    diskRequests.value = diskPresets[key] || diskPresets.standard;
  }
  loadDiskPreset("standard");
  diskPreset.addEventListener("change", (e) => loadDiskPreset(e.target.value));

  btnDiskRun.onclick = async () => {
    diskAlert.style.display = "none";
    btnDiskRun.disabled = true;
    btnDiskRun.innerText = "Simulating...";

    try {
      const reqArr = diskRequests.value
        .split(/[\s,]+/)
        .map((x) => x.trim())
        .filter(Boolean)
        .map((x) => parseInt(x, 10));

      const payload = {
        algorithm: diskAlgo.value,
        initial_head: parseInt(diskHead.value, 10),
        total_cylinders: parseInt(diskTotal.value, 10),
        direction: diskDirection.value,
        requests: reqArr,
      };

      const result = await Api.runDisk(payload);

      diskAlert.innerText = `Disk scheduling completed for ${result.algorithm_name || diskAlgo.value}.`;
      diskAlert.className = "alert-banner success active";
      diskAlert.style.display = "block";

      if (result.total_head_movement !== undefined) {
        document.getElementById("disk-val-movement").innerText = `${result.total_head_movement} cyl`;
      }
      if (result.average_seek_distance !== undefined) {
        document.getElementById("disk-val-seek").innerText = result.average_seek_distance.toFixed(2);
      }

      Viz.renderDiskPlot("disk-plot-container", result);

      // Comparison table if Compare All
      const compContainer = document.getElementById("disk-comparison-container");
      if (result.comparisons && result.comparisons.length > 0) {
        compContainer.style.display = "block";
        const tbody = document.getElementById("disk-comparison-tbody");
        tbody.innerHTML = result.comparisons
          .map(
            (c, i) => `
          <tr>
            <td style="font-weight: 700;">#${i + 1} ${c.algorithm_name}</td>
            <td style="font-family: ui-monospace, monospace; color: #34d399; font-weight: 700;">${c.total_head_movement} cyl</td>
            <td style="font-family: ui-monospace, monospace;">${c.average_seek_distance.toFixed(2)}</td>
          </tr>
        `
          )
          .join("");
      } else {
        compContainer.style.display = "none";
      }

      if (result.raw_output) {
        document.getElementById("disk-raw-output").innerText = result.raw_output;
      }
    } catch (err) {
      diskAlert.innerText = err.message || "Disk simulation error.";
      diskAlert.className = "alert-banner danger active";
      diskAlert.style.display = "block";
    } finally {
      btnDiskRun.disabled = false;
      btnDiskRun.innerText = "▶ Run Simulation";
    }
  };

  // ==========================================
  // MODULE 6: Address Translation & MMU
  // ==========================================
  const atPageSize = document.getElementById("at-page-size");
  const atAddrsInput = document.getElementById("at-addresses");
  const btnAtRun = document.getElementById("btn-at-run");
  const atAlert = document.getElementById("at-alert");

  btnAtRun.onclick = async () => {
    atAlert.style.display = "none";
    btnAtRun.disabled = true;
    btnAtRun.innerText = "Translating...";

    try {
      const addrs = atAddrsInput.value
        .split(/[\s,]+/)
        .map((x) => x.trim())
        .filter(Boolean)
        .map((x) => parseInt(x, 10));

      const payload = {
        mode: "custom",
        page_size: parseInt(atPageSize.value, 10),
        num_frames: 4,
        logical_addresses: addrs,
      };

      const result = await Api.runAddressTranslation(payload);

      atAlert.innerText = "Virtual address translation completed successfully.";
      atAlert.className = "alert-banner success active";
      atAlert.style.display = "block";

      Viz.renderAddressTranslation("at-mmu-container", result);

      if (result.translations) {
        const tbody = document.getElementById("at-results-tbody");
        tbody.innerHTML = result.translations
          .map(
            (t) => `
          <tr>
            <td style="font-family: ui-monospace, monospace; font-weight: 700;">0x${t.virtual_address.toString(16).toUpperCase()} (${t.virtual_address})</td>
            <td style="font-family: ui-monospace, monospace; color: var(--primary);">${t.page_number}</td>
            <td style="font-family: ui-monospace, monospace;">0x${t.offset.toString(16).toUpperCase()}</td>
            <td>
              <span class="module-tag" style="background-color: ${t.page_fault ? 'var(--danger-bg)' : 'var(--success-bg)'}; color: ${t.page_fault ? 'var(--danger-text)' : 'var(--success-text)'};">
                ${t.page_fault ? 'PAGE FAULT' : 'VALID'}
              </span>
            </td>
            <td style="font-family: ui-monospace, monospace;">${t.page_fault ? 'N/A' : t.frame_number}</td>
            <td style="font-family: ui-monospace, monospace; font-weight: 700; color: #34d399;">${t.page_fault ? 'N/A' : '0x' + t.physical_address.toString(16).toUpperCase()}</td>
          </tr>
        `
          )
          .join("");
      }

      if (result.logs) {
        document.getElementById("at-raw-output").innerText = result.logs.join("\n");
      }
    } catch (err) {
      atAlert.innerText = err.message || "Address translation error.";
      atAlert.className = "alert-banner danger active";
      atAlert.style.display = "block";
    } finally {
      btnAtRun.disabled = false;
      btnAtRun.innerText = "▶ Translate Addresses";
    }
  };

  // ==========================================
  // MODULE 7: Simulated File System
  // ==========================================
  const fsPreset = document.getElementById("fs-preset");
  const fsStrategy = document.getElementById("fs-strategy");
  const btnFsRun = document.getElementById("btn-fs-run");
  const fsAlert = document.getElementById("fs-alert");

  btnFsRun.onclick = async () => {
    fsAlert.style.display = "none";
    btnFsRun.disabled = true;
    btnFsRun.innerText = "Simulating...";

    try {
      const payload = {
        preset: fsPreset.value,
        allocation_strategy: fsStrategy.value,
        total_blocks: 32,
        block_size: 512,
      };

      const result = await Api.runFilesystem(payload);

      fsAlert.innerText = `Simulated file system execution completed for ${fsPreset.options[fsPreset.selectedIndex].text}.`;
      fsAlert.className = "alert-banner success active";
      fsAlert.style.display = "block";

      Viz.renderFilesystemGrid("fs-grid-container", result);

      if (result.status) {
        document.getElementById("fs-val-used").innerText = result.status.used_blocks;
        document.getElementById("fs-val-free").innerText = result.status.free_blocks;
        document.getElementById("fs-val-files").innerText = result.status.file_count;
      }

      if (result.operation_logs) {
        document.getElementById("fs-raw-output").innerText = result.operation_logs.join("\n");
      }
    } catch (err) {
      fsAlert.innerText = err.message || "File system simulation error.";
      fsAlert.className = "alert-banner danger active";
      fsAlert.style.display = "block";
    } finally {
      btnFsRun.disabled = false;
      btnFsRun.innerText = "▶ Run File System Workload";
    }
  };

  // ==========================================
  // MODULE 8: Process Lifecycle Explorer
  // ==========================================
  const btnPlRun = document.getElementById("btn-pl-run");
  const plAlert = document.getElementById("pl-alert");

  btnPlRun.onclick = async () => {
    plAlert.style.display = "none";
    btnPlRun.disabled = true;
    btnPlRun.innerText = "Simulating...";

    try {
      const payload = { mode: "demo" };
      const result = await Api.runProcessLifecycle(payload);

      plAlert.innerText = "Process lifecycle state machine simulation completed.";
      plAlert.className = "alert-banner success active";
      plAlert.style.display = "block";

      if (result.transitions) {
        document.getElementById("pl-val-transitions").innerText = result.transitions.length;
        const tbody = document.getElementById("pl-history-tbody");
        tbody.innerHTML = result.transitions
          .map(
            (tr) => `
          <tr>
            <td style="font-family: ui-monospace, monospace; font-weight: 700; color: var(--primary);">P${tr.process_id}</td>
            <td style="font-family: ui-monospace, monospace;">${tr.action}</td>
            <td><span class="module-tag">${tr.from_state}</span></td>
            <td style="color: var(--text-muted); font-size: 14px;">→</td>
            <td><span class="module-tag" style="color: var(--success); font-weight: 700;">${tr.to_state}</span></td>
            <td style="color: var(--text-secondary);">${tr.details || tr.message || 'State Transition'}</td>
          </tr>
        `
          )
          .join("");
      }

      if (result.logs) {
        document.getElementById("pl-raw-output").innerText = result.logs.join("\n");
      }
    } catch (err) {
      plAlert.innerText = err.message || "Process lifecycle error.";
      plAlert.className = "alert-banner danger active";
      plAlert.style.display = "block";
    } finally {
      btnPlRun.disabled = false;
      btnPlRun.innerText = "▶ Run Lifecycle Simulation";
    }
  };

  // ==========================================
  // MODULE 9: POSIX & Linux Concurrency Sandbox
  // ==========================================
  const lxCategory = document.getElementById("lx-category");
  const btnLxRun = document.getElementById("btn-lx-run");
  const lxAlert = document.getElementById("lx-alert");

  btnLxRun.onclick = async () => {
    lxAlert.style.display = "none";
    btnLxRun.disabled = true;
    btnLxRun.innerText = "Executing Linux Kernel Experiments...";

    try {
      const payload = { category: lxCategory.value };
      const result = await Api.runLinux(payload);

      lxAlert.innerText = `Kernel experiments finished successfully for category: ${lxCategory.options[lxCategory.selectedIndex].text}.`;
      lxAlert.className = "alert-banner success active";
      lxAlert.style.display = "block";

      if (result.raw_output) {
        document.getElementById("lx-raw-output").innerText = result.raw_output;
      }
    } catch (err) {
      lxAlert.innerText = err.message || "Linux experiment error.";
      lxAlert.className = "alert-banner danger active";
      lxAlert.style.display = "block";
    } finally {
      btnLxRun.disabled = false;
      btnLxRun.innerText = "▶ Execute Concurrency Experiment";
    }
  };

  // ==========================================
  // MODULE 10: Host System Diagnostics
  // ==========================================
  const btnHmRefresh = document.getElementById("btn-hm-refresh");
  const hmAlert = document.getElementById("hm-alert");

  async function pollHostMonitor() {
    btnHmRefresh.disabled = true;
    btnHmRefresh.innerText = "Reading Host...";

    try {
      const result = await Api.runHostMonitor();

      if (result.cpu) {
        document.getElementById("hm-val-cpu").innerText = `${result.cpu.total_usage_percent.toFixed(1)}%`;
        document.getElementById("hm-val-user").innerText = `${result.cpu.user_percent.toFixed(1)}%`;
        document.getElementById("hm-val-sys").innerText = `${result.cpu.system_percent.toFixed(1)}%`;
      }

      if (result.memory) {
        document.getElementById("hm-val-ram").innerText = `${(result.memory.used_kb / 1024).toFixed(0)} MB`;
        document.getElementById("hm-val-free").innerText = `${(result.memory.free_kb / 1024).toFixed(0)} MB`;
      }

      if (result.processes && result.processes.length > 0) {
        const tbody = document.getElementById("hm-proc-tbody");
        tbody.innerHTML = result.processes
          .slice(0, 15)
          .map(
            (p) => `
          <tr>
            <td style="font-family: ui-monospace, monospace; font-weight: 700; color: var(--primary);">${p.pid}</td>
            <td style="font-family: ui-monospace, monospace; font-weight: 600; color: #ffffff;">${p.name}</td>
            <td><span class="module-tag">${p.state}</span></td>
            <td style="font-family: ui-monospace, monospace;">${p.cpu_percent ? p.cpu_percent.toFixed(1) + '%' : '0.0%'}</td>
            <td style="font-family: ui-monospace, monospace;">${(p.memory_rss_kb / 1024).toFixed(1)} MB</td>
          </tr>
        `
          )
          .join("");
      }

      if (result.raw_output) {
        document.getElementById("hm-raw-output").innerText = result.raw_output;
      }
    } catch (err) {
      hmAlert.innerText = err.message || "Failed to poll host kernel metrics.";
      hmAlert.className = "alert-banner danger active";
      hmAlert.style.display = "block";
    } finally {
      btnHmRefresh.disabled = false;
      btnHmRefresh.innerHTML = '<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16"/></svg>Refresh Host Metrics';
    }
  }

  btnHmRefresh.onclick = pollHostMonitor;
});
