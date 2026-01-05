/**
 * FaceMortgage Embeddable Widget
 *
 * Usage:
 * <script src="https://facemortgage.com/widget/fm-widget.js"></script>
 * <script>
 *   new FMWidget({
 *     partnerToken: 'your-partner-token',
 *     loanOfficerId: 'loan-officer-uuid',
 *     buttonText: 'Get Pre-Approved',
 *     theme: 'blue', // 'blue', 'green', 'purple', 'dark'
 *     position: 'bottom-right', // 'bottom-right', 'bottom-left', 'top-right', 'top-left'
 *   }).init();
 * </script>
 */
(function() {
  'use strict';

  // Configuration
  var WIDGET_BASE_URL = 'https://facemortgage.com';

  // Detect if we're in development
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    WIDGET_BASE_URL = 'http://localhost:3000';
  }

  // Theme colors
  var THEMES = {
    blue: {
      primary: '#2563eb',
      hover: '#1d4ed8',
      shadow: 'rgba(37, 99, 235, 0.4)',
    },
    green: {
      primary: '#16a34a',
      hover: '#15803d',
      shadow: 'rgba(22, 163, 74, 0.4)',
    },
    purple: {
      primary: '#9333ea',
      hover: '#7e22ce',
      shadow: 'rgba(147, 51, 234, 0.4)',
    },
    dark: {
      primary: '#1f2937',
      hover: '#111827',
      shadow: 'rgba(31, 41, 55, 0.4)',
    },
  };

  /**
   * FMWidget Constructor
   * @param {Object} config - Widget configuration
   */
  function FMWidget(config) {
    this.partnerToken = config.partnerToken || '';
    this.loanOfficerId = config.loanOfficerId || '';
    this.buttonText = config.buttonText || 'Get Pre-Approved';
    this.theme = THEMES[config.theme] || THEMES.blue;
    this.themeName = config.theme || 'blue';
    this.position = config.position || 'bottom-right';
    this.showOnLoad = config.showOnLoad !== false;
    this.onSuccess = config.onSuccess || function() {};
    this.onClose = config.onClose || function() {};

    this._button = null;
    this._modal = null;
    this._initialized = false;
  }

  /**
   * Initialize the widget
   */
  FMWidget.prototype.init = function() {
    if (this._initialized) {
      console.warn('FMWidget: Already initialized');
      return this;
    }

    this._injectStyles();
    this._createButton();
    this._setupMessageListener();
    this._initialized = true;

    return this;
  };

  /**
   * Inject CSS styles
   */
  FMWidget.prototype._injectStyles = function() {
    var styleId = 'fm-widget-styles';
    if (document.getElementById(styleId)) {
      return;
    }

    var style = document.createElement('style');
    style.id = styleId;
    style.textContent = '\n' +
      '.fm-widget-btn {\n' +
      '  position: fixed;\n' +
      '  padding: 14px 28px;\n' +
      '  color: white;\n' +
      '  border: none;\n' +
      '  border-radius: 50px;\n' +
      '  font-size: 16px;\n' +
      '  font-weight: 600;\n' +
      '  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;\n' +
      '  cursor: pointer;\n' +
      '  z-index: 9998;\n' +
      '  transition: transform 0.2s ease, box-shadow 0.2s ease;\n' +
      '  display: flex;\n' +
      '  align-items: center;\n' +
      '  gap: 8px;\n' +
      '}\n' +
      '.fm-widget-btn:hover {\n' +
      '  transform: translateY(-2px);\n' +
      '}\n' +
      '.fm-widget-btn:active {\n' +
      '  transform: translateY(0);\n' +
      '}\n' +
      '.fm-widget-btn svg {\n' +
      '  width: 20px;\n' +
      '  height: 20px;\n' +
      '}\n' +
      '.fm-widget-modal {\n' +
      '  position: fixed;\n' +
      '  inset: 0;\n' +
      '  background: rgba(0, 0, 0, 0.5);\n' +
      '  display: flex;\n' +
      '  align-items: center;\n' +
      '  justify-content: center;\n' +
      '  z-index: 9999;\n' +
      '  opacity: 0;\n' +
      '  visibility: hidden;\n' +
      '  transition: opacity 0.3s ease, visibility 0.3s ease;\n' +
      '  padding: 20px;\n' +
      '}\n' +
      '.fm-widget-modal.fm-visible {\n' +
      '  opacity: 1;\n' +
      '  visibility: visible;\n' +
      '}\n' +
      '.fm-widget-container {\n' +
      '  width: 100%;\n' +
      '  max-width: 480px;\n' +
      '  height: 90vh;\n' +
      '  max-height: 700px;\n' +
      '  background: white;\n' +
      '  border-radius: 16px;\n' +
      '  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);\n' +
      '  overflow: hidden;\n' +
      '  transform: scale(0.95) translateY(20px);\n' +
      '  transition: transform 0.3s ease;\n' +
      '  position: relative;\n' +
      '}\n' +
      '.fm-widget-modal.fm-visible .fm-widget-container {\n' +
      '  transform: scale(1) translateY(0);\n' +
      '}\n' +
      '.fm-widget-close {\n' +
      '  position: absolute;\n' +
      '  top: 12px;\n' +
      '  right: 12px;\n' +
      '  width: 32px;\n' +
      '  height: 32px;\n' +
      '  border-radius: 50%;\n' +
      '  background: rgba(0, 0, 0, 0.1);\n' +
      '  border: none;\n' +
      '  cursor: pointer;\n' +
      '  display: flex;\n' +
      '  align-items: center;\n' +
      '  justify-content: center;\n' +
      '  z-index: 10;\n' +
      '  transition: background 0.2s ease;\n' +
      '}\n' +
      '.fm-widget-close:hover {\n' +
      '  background: rgba(0, 0, 0, 0.2);\n' +
      '}\n' +
      '.fm-widget-close svg {\n' +
      '  width: 18px;\n' +
      '  height: 18px;\n' +
      '  color: #374151;\n' +
      '}\n' +
      '.fm-widget-iframe {\n' +
      '  width: 100%;\n' +
      '  height: 100%;\n' +
      '  border: none;\n' +
      '}\n' +
      '@media (max-width: 640px) {\n' +
      '  .fm-widget-container {\n' +
      '    max-width: 100%;\n' +
      '    height: 100vh;\n' +
      '    max-height: 100vh;\n' +
      '    border-radius: 0;\n' +
      '  }\n' +
      '  .fm-widget-modal {\n' +
      '    padding: 0;\n' +
      '  }\n' +
      '}\n';

    document.head.appendChild(style);
  };

  /**
   * Create the floating button
   */
  FMWidget.prototype._createButton = function() {
    var self = this;
    var btn = document.createElement('button');
    btn.className = 'fm-widget-btn';
    btn.setAttribute('aria-label', this.buttonText);

    // Position
    var posStyles = {
      'bottom-right': 'bottom: 24px; right: 24px;',
      'bottom-left': 'bottom: 24px; left: 24px;',
      'top-right': 'top: 24px; right: 24px;',
      'top-left': 'top: 24px; left: 24px;',
    };
    btn.style.cssText = posStyles[this.position] || posStyles['bottom-right'];
    btn.style.backgroundColor = this.theme.primary;
    btn.style.boxShadow = '0 4px 14px ' + this.theme.shadow;

    // Hover effect
    btn.onmouseenter = function() {
      btn.style.backgroundColor = self.theme.hover;
      btn.style.boxShadow = '0 6px 20px ' + self.theme.shadow;
    };
    btn.onmouseleave = function() {
      btn.style.backgroundColor = self.theme.primary;
      btn.style.boxShadow = '0 4px 14px ' + self.theme.shadow;
    };

    // Icon
    btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>' +
      '<span>' + this.buttonText + '</span>';

    btn.onclick = function() {
      self.open();
    };

    document.body.appendChild(btn);
    this._button = btn;
  };

  /**
   * Open the modal
   */
  FMWidget.prototype.open = function() {
    if (this._modal) {
      this._modal.classList.add('fm-visible');
      return;
    }

    var self = this;

    // Create modal
    var modal = document.createElement('div');
    modal.className = 'fm-widget-modal';
    modal.onclick = function(e) {
      if (e.target === modal) {
        self.close();
      }
    };

    // Container
    var container = document.createElement('div');
    container.className = 'fm-widget-container';

    // Close button
    var closeBtn = document.createElement('button');
    closeBtn.className = 'fm-widget-close';
    closeBtn.setAttribute('aria-label', 'Close');
    closeBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';
    closeBtn.onclick = function() {
      self.close();
    };

    // Iframe
    var iframe = document.createElement('iframe');
    iframe.className = 'fm-widget-iframe';
    iframe.src = WIDGET_BASE_URL + '/embed/get-matched?partner=' + encodeURIComponent(this.partnerToken) + '&lo=' + encodeURIComponent(this.loanOfficerId);
    iframe.setAttribute('title', 'Get Pre-Approved');
    iframe.setAttribute('allow', 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture');

    container.appendChild(closeBtn);
    container.appendChild(iframe);
    modal.appendChild(container);
    document.body.appendChild(modal);

    this._modal = modal;

    // Animate in
    requestAnimationFrame(function() {
      modal.classList.add('fm-visible');
    });

    // Handle escape key
    this._escHandler = function(e) {
      if (e.key === 'Escape') {
        self.close();
      }
    };
    document.addEventListener('keydown', this._escHandler);
  };

  /**
   * Close the modal
   */
  FMWidget.prototype.close = function() {
    if (!this._modal) return;

    var self = this;
    this._modal.classList.remove('fm-visible');

    // Remove escape handler
    if (this._escHandler) {
      document.removeEventListener('keydown', this._escHandler);
    }

    // Trigger callback
    this.onClose();
  };

  /**
   * Setup message listener for iframe communication
   */
  FMWidget.prototype._setupMessageListener = function() {
    var self = this;

    window.addEventListener('message', function(event) {
      // Verify origin
      if (event.origin !== WIDGET_BASE_URL) return;

      if (event.data && event.data.type === 'fm-widget-success') {
        self.onSuccess();
        // Auto-close after success
        setTimeout(function() {
          self.close();
        }, 3000);
      }
    });
  };

  /**
   * Destroy the widget
   */
  FMWidget.prototype.destroy = function() {
    if (this._button) {
      this._button.remove();
      this._button = null;
    }
    if (this._modal) {
      this._modal.remove();
      this._modal = null;
    }
    if (this._escHandler) {
      document.removeEventListener('keydown', this._escHandler);
    }
    this._initialized = false;
  };

  /**
   * Show the button
   */
  FMWidget.prototype.show = function() {
    if (this._button) {
      this._button.style.display = 'flex';
    }
  };

  /**
   * Hide the button
   */
  FMWidget.prototype.hide = function() {
    if (this._button) {
      this._button.style.display = 'none';
    }
  };

  // Export to window
  window.FMWidget = FMWidget;

})();
