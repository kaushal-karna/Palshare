(function () {
  "use strict";

  var STORAGE_KEY = "palshare-theme";
  var VALID_MODES = ["system", "light", "dark"];

  function getStoredMode() {
    try {
      var stored = window.localStorage.getItem(STORAGE_KEY);

      if (VALID_MODES.indexOf(stored) !== -1) {
        return stored;
      }
    } catch (error) {
      // localStorage can be unavailable in restricted browser contexts.
    }

    return "system";
  }

  function applyMode(mode, persist) {
    if (VALID_MODES.indexOf(mode) === -1) {
      mode = "system";
    }

    var root = document.documentElement;

    if (mode === "system") {
      root.removeAttribute("data-theme");
    } else {
      root.setAttribute("data-theme", mode);
    }

    if (persist) {
      try {
        window.localStorage.setItem(STORAGE_KEY, mode);
      } catch (error) {
        // Theme still applies for the current page.
      }
    }

    document.querySelectorAll("[data-theme-option]").forEach(function (button) {
      var active = button.dataset.themeOption === mode;
      button.setAttribute("aria-checked", active ? "true" : "false");
    });

    var label = document.querySelector("[data-theme-current-label]");

    if (label) {
      var labels = {
        system: "🖥️ Default",
        light: "☀️ Light",
        dark: "🌙 Dark"
      };

      label.textContent = labels[mode];
    }
  }

  function setupThemeControls() {
    applyMode(getStoredMode(), false);

    document.querySelectorAll("[data-theme-option]").forEach(function (button) {
      button.addEventListener("click", function () {
        applyMode(button.dataset.themeOption, true);

        var menu = button.closest("details");

        if (menu) {
          menu.removeAttribute("open");
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", setupThemeControls);
})();
