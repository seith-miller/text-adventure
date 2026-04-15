/**
 * MIR'S END — Save/Load Manager
 * Handles game state persistence via browser localStorage.
 * Supports multiple save slots, auto-save, and manual save/restore.
 */

(function () {
  "use strict";

  var STORAGE_PREFIX = "mirsend_";
  var SLOT_COUNT = 3;
  var AUTO_SAVE_KEY = STORAGE_PREFIX + "autosave";

  /**
   * Build the localStorage key for a numbered slot.
   * @param {number} slotNum - 1-based slot number
   * @returns {string}
   */
  function slotKey(slotNum) {
    return STORAGE_PREFIX + "slot_" + slotNum;
  }

  /**
   * Check if localStorage is available.
   * @returns {boolean}
   */
  function storageAvailable() {
    try {
      var test = "__storage_test__";
      localStorage.setItem(test, test);
      localStorage.removeItem(test);
      return true;
    } catch (e) {
      return false;
    }
  }

  /**
   * Capture the current game state snapshot.
   * @returns {object} serializable state object
   */
  function captureState() {
    var uiState = window.MirsEnd ? window.MirsEnd.getState() : {};
    return {
      version: 1,
      timestamp: new Date().toISOString(),
      currentRoom: uiState.currentRoom || null,
      o2: uiState.o2 !== undefined ? uiState.o2 : 100,
      morale: uiState.morale !== undefined ? uiState.morale : 70,
      inventory: uiState.inventory ? uiState.inventory.slice() : [],
      commandHistory: uiState.commandHistory ? uiState.commandHistory.slice() : [],
    };
  }

  /**
   * Save game state to a specific storage key.
   * @param {string} key - localStorage key
   * @returns {{success: boolean, message: string}}
   */
  function saveToKey(key) {
    if (!storageAvailable()) {
      return { success: false, message: "localStorage is not available." };
    }
    try {
      var snapshot = captureState();
      localStorage.setItem(key, JSON.stringify(snapshot));
      return { success: true, message: "Game saved successfully." };
    } catch (e) {
      return { success: false, message: "Save failed: " + e.message };
    }
  }

  /**
   * Load game state from a specific storage key.
   * @param {string} key - localStorage key
   * @returns {{success: boolean, message: string, data: object|null}}
   */
  function loadFromKey(key) {
    if (!storageAvailable()) {
      return { success: false, message: "localStorage is not available.", data: null };
    }
    try {
      var raw = localStorage.getItem(key);
      if (!raw) {
        return { success: false, message: "No save data found.", data: null };
      }
      var data = JSON.parse(raw);
      return { success: true, message: "Game loaded successfully.", data: data };
    } catch (e) {
      return { success: false, message: "Load failed: " + e.message, data: null };
    }
  }

  /**
   * Apply loaded state to the game.
   * @param {object} data - saved state object
   */
  function applyState(data) {
    if (!window.MirsEnd || !data) return;
    window.MirsEnd.setState({
      o2: data.o2,
      morale: data.morale,
      inventory: data.inventory || [],
      currentRoom: data.currentRoom,
    });
  }

  /**
   * Format a save slot summary for display.
   * @param {string} key - localStorage key
   * @returns {string} human-readable summary
   */
  function slotSummary(key) {
    if (!storageAvailable()) return "[ unavailable ]";
    var raw = localStorage.getItem(key);
    if (!raw) return "[ empty ]";
    try {
      var data = JSON.parse(raw);
      var room = data.currentRoom || "Unknown";
      var date = new Date(data.timestamp);
      var dateStr = date.toLocaleDateString() + " " + date.toLocaleTimeString();
      return room + " — O2: " + data.o2 + "%, Morale: " + data.morale + "% — " + dateStr;
    } catch (e) {
      return "[ corrupted ]";
    }
  }

  /**
   * Delete a save from a specific key.
   * @param {string} key - localStorage key
   * @returns {{success: boolean, message: string}}
   */
  function deleteFromKey(key) {
    if (!storageAvailable()) {
      return { success: false, message: "localStorage is not available." };
    }
    try {
      localStorage.removeItem(key);
      return { success: true, message: "Save deleted." };
    } catch (e) {
      return { success: false, message: "Delete failed: " + e.message };
    }
  }

  /**
   * Get info about all save slots.
   * @returns {Array<{slot: number|string, key: string, summary: string, hasData: boolean}>}
   */
  function listSlots() {
    var slots = [];
    // Auto-save slot
    slots.push({
      slot: "auto",
      key: AUTO_SAVE_KEY,
      summary: slotSummary(AUTO_SAVE_KEY),
      hasData: storageAvailable() && localStorage.getItem(AUTO_SAVE_KEY) !== null,
    });
    // Numbered slots
    for (var i = 1; i <= SLOT_COUNT; i++) {
      var key = slotKey(i);
      slots.push({
        slot: i,
        key: key,
        summary: slotSummary(key),
        hasData: storageAvailable() && localStorage.getItem(key) !== null,
      });
    }
    return slots;
  }

  /**
   * Get the most recent save across all slots.
   * @returns {{key: string, data: object}|null}
   */
  function getMostRecentSave() {
    if (!storageAvailable()) return null;
    var newest = null;
    var newestTime = 0;
    var allKeys = [AUTO_SAVE_KEY];
    for (var i = 1; i <= SLOT_COUNT; i++) {
      allKeys.push(slotKey(i));
    }
    for (var k = 0; k < allKeys.length; k++) {
      var raw = localStorage.getItem(allKeys[k]);
      if (raw) {
        try {
          var data = JSON.parse(raw);
          var t = new Date(data.timestamp).getTime();
          if (t > newestTime) {
            newestTime = t;
            newest = { key: allKeys[k], data: data };
          }
        } catch (e) {
          // skip corrupted
        }
      }
    }
    return newest;
  }

  /* ── Public API ── */
  window.SaveManager = {
    SLOT_COUNT: SLOT_COUNT,
    storageAvailable: storageAvailable,
    slotKey: slotKey,
    AUTO_SAVE_KEY: AUTO_SAVE_KEY,

    saveToSlot: function (slotNum) {
      return saveToKey(slotKey(slotNum));
    },
    loadFromSlot: function (slotNum) {
      return loadFromKey(slotKey(slotNum));
    },
    deleteSlot: function (slotNum) {
      return deleteFromKey(slotKey(slotNum));
    },

    autoSave: function () {
      return saveToKey(AUTO_SAVE_KEY);
    },
    loadAutoSave: function () {
      return loadFromKey(AUTO_SAVE_KEY);
    },

    applyState: applyState,
    captureState: captureState,
    listSlots: listSlots,
    getMostRecentSave: getMostRecentSave,
    slotSummary: slotSummary,
  };
})();
