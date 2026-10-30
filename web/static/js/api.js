/**
 * OScope Web Client API
 * Lightweight asynchronous client connecting the web UI to the simulation REST API.
 */

const Api = {
  async _request(endpoint, options = {}) {
    const config = {
      headers: { "Content-Type": "application/json" },
      ...options,
    };
    try {
      const response = await fetch(endpoint, config);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || `HTTP ${response.status}: Simulation error`);
      }
      return data;
    } catch (err) {
      console.error(`API Error on [${endpoint}]:`, err);
      throw err;
    }
  },

  getStatus() {
    return this._request("/api/status");
  },

  runScheduling(payload) {
    return this._request("/api/scheduling/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  runMemory(payload) {
    return this._request("/api/memory/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  runPaging(payload) {
    return this._request("/api/paging/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  runDeadlock(payload) {
    return this._request("/api/deadlock/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  runDisk(payload) {
    return this._request("/api/disk/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  runLinux(payload) {
    return this._request("/api/linux/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  runHostMonitor() {
    return this._request("/api/host-monitor/run");
  },

  runFilesystem(payload) {
    return this._request("/api/filesystem/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  runAddressTranslation(payload) {
    return this._request("/api/address-translation/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  runProcessLifecycle(payload) {
    return this._request("/api/process-lifecycle/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};

window.Api = Api;
