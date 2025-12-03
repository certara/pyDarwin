(function () {
  "use strict";

  // Minimal DOM-ready helper, similar to jQuery(fn).
  function onReady(fn) {
    if (document.readyState === "complete" || document.readyState === "interactive") {
      // Run soon but asynchronously, to match jQuery behavior.
      window.setTimeout(fn, 0);
    } else {
      document.addEventListener("DOMContentLoaded", fn);
    }
  }

  // Very small jQuery-compatible shim, just enough for jQuery(fn) used in the
  // Sphinx RTD HTML layout. It is NOT a full jQuery implementation.
  if (typeof window.jQuery === "undefined") {
    window.jQuery = function (arg) {
      if (typeof arg === "function") {
        onReady(arg);
        return;
      }
      // For our docs we only need jQuery(fn). Any selector usage can fall back
      // to a NodeList to avoid breaking if it is called.
      if (typeof arg === "string") {
        return document.querySelectorAll(arg);
      }
      return arg;
    };
  }

  // Provide a very small SphinxRtdTheme.Navigation shim so that
  // SphinxRtdTheme.Navigation.enable(true) does not fail. For now this is a
  // no-op; the default layout and search do not rely on the advanced
  // navigation features.
  if (!window.SphinxRtdTheme) {
    window.SphinxRtdTheme = {};
  }

  if (!window.SphinxRtdTheme.Navigation) {
    window.SphinxRtdTheme.Navigation = {
      enable: function () {
        // No-op shim. If desired, basic mobile nav behavior could be added here.
      },
    };
  }
})();


