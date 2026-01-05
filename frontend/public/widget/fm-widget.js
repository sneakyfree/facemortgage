/**
 * FaceMortgage Embeddable Widget v2.0
 *
 * A standalone JavaScript widget that displays mortgage professionals
 * and allows borrowers to initiate video calls directly from partner websites.
 *
 * Usage (Data Attributes - Simple):
 * <div id="fm-widget" data-partner-id="partner123" data-theme="light" data-max-professionals="6"></div>
 * <script src="https://facemortgage.com/widget/fm-widget.js" async></script>
 *
 * Usage (JavaScript API - Advanced):
 * <script src="https://facemortgage.com/widget/fm-widget.js"></script>
 * <script>
 *   FMWidget.init({
 *     containerId: 'fm-widget',
 *     partnerId: 'partner123',
 *     theme: 'light',
 *     maxProfessionals: 6,
 *     onProfessionalClick: (professional) => console.log('Clicked:', professional),
 *     onCallInitiated: (professional) => console.log('Call started:', professional),
 *   });
 * </script>
 *
 * Configuration Options:
 * - partnerId: Partner ID for tracking (required)
 * - theme: 'light' | 'dark' (default: 'light')
 * - maxProfessionals: Number of professionals to show (default: 6, max: 12)
 * - showFilters: Show filter controls (default: false)
 * - language: Filter by language code
 * - specialty: Filter by specialty
 * - state: Filter by state code
 * - userType: Filter by user type (loan_officer, realtor, etc.)
 * - primaryColor: Custom primary color (hex)
 * - compactMode: Use compact card layout (default: false)
 */
(function(window, document) {
  'use strict';

  // ==================== Configuration ====================

  var VERSION = '2.0.0';
  var WIDGET_NAME = 'FMWidget';

  // Detect environment
  var WIDGET_BASE_URL = 'https://facemortgage.com';
  var API_BASE_URL = 'https://api.facemortgage.com';

  if (typeof window !== 'undefined') {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      WIDGET_BASE_URL = 'http://localhost:3000';
      API_BASE_URL = 'http://localhost:8000';
    }
    // Allow override via global config
    if (window.FM_WIDGET_CONFIG) {
      if (window.FM_WIDGET_CONFIG.baseUrl) WIDGET_BASE_URL = window.FM_WIDGET_CONFIG.baseUrl;
      if (window.FM_WIDGET_CONFIG.apiUrl) API_BASE_URL = window.FM_WIDGET_CONFIG.apiUrl;
    }
  }

  // Theme configurations
  var THEMES = {
    light: {
      background: '#ffffff',
      cardBg: '#ffffff',
      cardBorder: '#e5e7eb',
      text: '#111827',
      textSecondary: '#6b7280',
      primary: '#2563eb',
      primaryHover: '#1d4ed8',
      available: '#16a34a',
      busy: '#f59e0b',
      offline: '#9ca3af',
      shadow: 'rgba(0, 0, 0, 0.1)',
    },
    dark: {
      background: '#1f2937',
      cardBg: '#374151',
      cardBorder: '#4b5563',
      text: '#f9fafb',
      textSecondary: '#9ca3af',
      primary: '#3b82f6',
      primaryHover: '#2563eb',
      available: '#22c55e',
      busy: '#fbbf24',
      offline: '#6b7280',
      shadow: 'rgba(0, 0, 0, 0.3)',
    },
  };

  // ==================== Utility Functions ====================

  function generateId() {
    return 'fm-' + Math.random().toString(36).substr(2, 9);
  }

  function createElement(tag, attrs, children) {
    var el = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function(key) {
        if (key === 'style' && typeof attrs[key] === 'object') {
          Object.assign(el.style, attrs[key]);
        } else if (key === 'className') {
          el.className = attrs[key];
        } else if (key.startsWith('on') && typeof attrs[key] === 'function') {
          el.addEventListener(key.substring(2).toLowerCase(), attrs[key]);
        } else {
          el.setAttribute(key, attrs[key]);
        }
      });
    }
    if (children) {
      if (typeof children === 'string') {
        el.textContent = children;
      } else if (Array.isArray(children)) {
        children.forEach(function(child) {
          if (child) el.appendChild(child);
        });
      } else {
        el.appendChild(children);
      }
    }
    return el;
  }

  function debounce(func, wait) {
    var timeout;
    return function() {
      var context = this;
      var args = arguments;
      clearTimeout(timeout);
      timeout = setTimeout(function() {
        func.apply(context, args);
      }, wait);
    };
  }

  // ==================== Widget Class ====================

  function Widget(options) {
    this.options = Object.assign({
      containerId: 'fm-widget',
      partnerId: '',
      theme: 'light',
      maxProfessionals: 6,
      showFilters: false,
      language: null,
      specialty: null,
      state: null,
      userType: null,
      primaryColor: null,
      compactMode: false,
      onProfessionalClick: null,
      onCallInitiated: null,
      onError: null,
    }, options);

    this.id = generateId();
    this.container = null;
    this.shadowRoot = null;
    this.professionals = [];
    this.loading = true;
    this.error = null;
    this.theme = THEMES[this.options.theme] || THEMES.light;

    // Apply custom primary color if provided
    if (this.options.primaryColor) {
      this.theme.primary = this.options.primaryColor;
      this.theme.primaryHover = this.options.primaryColor;
    }

    this._init();
  }

  Widget.prototype._init = function() {
    var container = document.getElementById(this.options.containerId);
    if (!container) {
      console.error('[FMWidget] Container element not found:', this.options.containerId);
      return;
    }

    this.container = container;

    // Create shadow DOM for style isolation
    if (container.attachShadow) {
      this.shadowRoot = container.attachShadow({ mode: 'open' });
    } else {
      // Fallback for older browsers
      this.shadowRoot = container;
    }

    this._injectStyles();
    this._render();
    this._fetchProfessionals();
    this._setupMessageListener();
  };

  Widget.prototype._injectStyles = function() {
    var theme = this.theme;
    var styles = document.createElement('style');
    styles.textContent = '\n' +
      '*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }\n' +
      '\n' +
      '.fm-widget-container {\n' +
      '  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;\n' +
      '  background: ' + theme.background + ';\n' +
      '  border-radius: 12px;\n' +
      '  padding: 16px;\n' +
      '  min-height: 200px;\n' +
      '}\n' +
      '\n' +
      '.fm-widget-header {\n' +
      '  display: flex;\n' +
      '  align-items: center;\n' +
      '  justify-content: space-between;\n' +
      '  margin-bottom: 16px;\n' +
      '  padding-bottom: 12px;\n' +
      '  border-bottom: 1px solid ' + theme.cardBorder + ';\n' +
      '}\n' +
      '\n' +
      '.fm-widget-title {\n' +
      '  font-size: 18px;\n' +
      '  font-weight: 600;\n' +
      '  color: ' + theme.text + ';\n' +
      '}\n' +
      '\n' +
      '.fm-widget-subtitle {\n' +
      '  font-size: 13px;\n' +
      '  color: ' + theme.textSecondary + ';\n' +
      '}\n' +
      '\n' +
      '.fm-widget-powered {\n' +
      '  font-size: 11px;\n' +
      '  color: ' + theme.textSecondary + ';\n' +
      '}\n' +
      '\n' +
      '.fm-widget-powered a {\n' +
      '  color: ' + theme.primary + ';\n' +
      '  text-decoration: none;\n' +
      '}\n' +
      '\n' +
      '.fm-widget-powered a:hover {\n' +
      '  text-decoration: underline;\n' +
      '}\n' +
      '\n' +
      '.fm-widget-grid {\n' +
      '  display: grid;\n' +
      '  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));\n' +
      '  gap: 12px;\n' +
      '}\n' +
      '\n' +
      '.fm-widget-grid.compact {\n' +
      '  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));\n' +
      '  gap: 8px;\n' +
      '}\n' +
      '\n' +
      '.fm-prof-card {\n' +
      '  background: ' + theme.cardBg + ';\n' +
      '  border: 1px solid ' + theme.cardBorder + ';\n' +
      '  border-radius: 10px;\n' +
      '  padding: 14px;\n' +
      '  text-align: center;\n' +
      '  cursor: pointer;\n' +
      '  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;\n' +
      '}\n' +
      '\n' +
      '.fm-prof-card:hover {\n' +
      '  transform: translateY(-2px);\n' +
      '  box-shadow: 0 8px 20px ' + theme.shadow + ';\n' +
      '  border-color: ' + theme.primary + ';\n' +
      '}\n' +
      '\n' +
      '.fm-prof-card.compact {\n' +
      '  padding: 10px;\n' +
      '}\n' +
      '\n' +
      '.fm-prof-avatar-wrap {\n' +
      '  position: relative;\n' +
      '  width: 64px;\n' +
      '  height: 64px;\n' +
      '  margin: 0 auto 10px;\n' +
      '}\n' +
      '\n' +
      '.fm-prof-avatar-wrap.compact {\n' +
      '  width: 48px;\n' +
      '  height: 48px;\n' +
      '  margin-bottom: 8px;\n' +
      '}\n' +
      '\n' +
      '.fm-prof-avatar {\n' +
      '  width: 100%;\n' +
      '  height: 100%;\n' +
      '  border-radius: 50%;\n' +
      '  object-fit: cover;\n' +
      '  background: ' + theme.cardBorder + ';\n' +
      '}\n' +
      '\n' +
      '.fm-prof-avatar-placeholder {\n' +
      '  width: 100%;\n' +
      '  height: 100%;\n' +
      '  border-radius: 50%;\n' +
      '  background: linear-gradient(135deg, ' + theme.primary + ' 0%, ' + theme.primaryHover + ' 100%);\n' +
      '  display: flex;\n' +
      '  align-items: center;\n' +
      '  justify-content: center;\n' +
      '  color: white;\n' +
      '  font-weight: 600;\n' +
      '  font-size: 20px;\n' +
      '}\n' +
      '\n' +
      '.fm-prof-avatar-placeholder.compact {\n' +
      '  font-size: 16px;\n' +
      '}\n' +
      '\n' +
      '.fm-prof-status {\n' +
      '  position: absolute;\n' +
      '  bottom: 2px;\n' +
      '  right: 2px;\n' +
      '  width: 14px;\n' +
      '  height: 14px;\n' +
      '  border-radius: 50%;\n' +
      '  border: 2px solid ' + theme.cardBg + ';\n' +
      '}\n' +
      '\n' +
      '.fm-prof-status.available { background: ' + theme.available + '; }\n' +
      '.fm-prof-status.busy { background: ' + theme.busy + '; }\n' +
      '.fm-prof-status.offline { background: ' + theme.offline + '; }\n' +
      '\n' +
      '.fm-prof-name {\n' +
      '  font-size: 14px;\n' +
      '  font-weight: 600;\n' +
      '  color: ' + theme.text + ';\n' +
      '  margin-bottom: 2px;\n' +
      '  white-space: nowrap;\n' +
      '  overflow: hidden;\n' +
      '  text-overflow: ellipsis;\n' +
      '}\n' +
      '\n' +
      '.fm-prof-name.compact {\n' +
      '  font-size: 13px;\n' +
      '}\n' +
      '\n' +
      '.fm-prof-title {\n' +
      '  font-size: 12px;\n' +
      '  color: ' + theme.textSecondary + ';\n' +
      '  margin-bottom: 6px;\n' +
      '  white-space: nowrap;\n' +
      '  overflow: hidden;\n' +
      '  text-overflow: ellipsis;\n' +
      '}\n' +
      '\n' +
      '.fm-prof-rating {\n' +
      '  display: flex;\n' +
      '  align-items: center;\n' +
      '  justify-content: center;\n' +
      '  gap: 4px;\n' +
      '  font-size: 12px;\n' +
      '  color: ' + theme.textSecondary + ';\n' +
      '  margin-bottom: 10px;\n' +
      '}\n' +
      '\n' +
      '.fm-prof-rating.compact {\n' +
      '  margin-bottom: 8px;\n' +
      '}\n' +
      '\n' +
      '.fm-prof-rating svg {\n' +
      '  width: 14px;\n' +
      '  height: 14px;\n' +
      '  fill: #fbbf24;\n' +
      '}\n' +
      '\n' +
      '.fm-prof-call-btn {\n' +
      '  width: 100%;\n' +
      '  padding: 8px 12px;\n' +
      '  background: ' + theme.primary + ';\n' +
      '  color: white;\n' +
      '  border: none;\n' +
      '  border-radius: 6px;\n' +
      '  font-size: 13px;\n' +
      '  font-weight: 500;\n' +
      '  cursor: pointer;\n' +
      '  transition: background 0.2s ease;\n' +
      '  display: flex;\n' +
      '  align-items: center;\n' +
      '  justify-content: center;\n' +
      '  gap: 6px;\n' +
      '}\n' +
      '\n' +
      '.fm-prof-call-btn:hover {\n' +
      '  background: ' + theme.primaryHover + ';\n' +
      '}\n' +
      '\n' +
      '.fm-prof-call-btn:disabled {\n' +
      '  background: ' + theme.offline + ';\n' +
      '  cursor: not-allowed;\n' +
      '}\n' +
      '\n' +
      '.fm-prof-call-btn.compact {\n' +
      '  padding: 6px 10px;\n' +
      '  font-size: 12px;\n' +
      '}\n' +
      '\n' +
      '.fm-prof-call-btn svg {\n' +
      '  width: 14px;\n' +
      '  height: 14px;\n' +
      '}\n' +
      '\n' +
      '.fm-widget-loading {\n' +
      '  display: flex;\n' +
      '  flex-direction: column;\n' +
      '  align-items: center;\n' +
      '  justify-content: center;\n' +
      '  padding: 40px;\n' +
      '  color: ' + theme.textSecondary + ';\n' +
      '}\n' +
      '\n' +
      '.fm-widget-spinner {\n' +
      '  width: 32px;\n' +
      '  height: 32px;\n' +
      '  border: 3px solid ' + theme.cardBorder + ';\n' +
      '  border-top-color: ' + theme.primary + ';\n' +
      '  border-radius: 50%;\n' +
      '  animation: fm-spin 0.8s linear infinite;\n' +
      '  margin-bottom: 12px;\n' +
      '}\n' +
      '\n' +
      '@keyframes fm-spin {\n' +
      '  to { transform: rotate(360deg); }\n' +
      '}\n' +
      '\n' +
      '.fm-widget-error {\n' +
      '  display: flex;\n' +
      '  flex-direction: column;\n' +
      '  align-items: center;\n' +
      '  justify-content: center;\n' +
      '  padding: 40px;\n' +
      '  color: ' + theme.textSecondary + ';\n' +
      '  text-align: center;\n' +
      '}\n' +
      '\n' +
      '.fm-widget-error-icon {\n' +
      '  width: 48px;\n' +
      '  height: 48px;\n' +
      '  color: #ef4444;\n' +
      '  margin-bottom: 12px;\n' +
      '}\n' +
      '\n' +
      '.fm-widget-error-btn {\n' +
      '  margin-top: 12px;\n' +
      '  padding: 8px 16px;\n' +
      '  background: ' + theme.primary + ';\n' +
      '  color: white;\n' +
      '  border: none;\n' +
      '  border-radius: 6px;\n' +
      '  font-size: 13px;\n' +
      '  cursor: pointer;\n' +
      '}\n' +
      '\n' +
      '.fm-widget-empty {\n' +
      '  display: flex;\n' +
      '  flex-direction: column;\n' +
      '  align-items: center;\n' +
      '  justify-content: center;\n' +
      '  padding: 40px;\n' +
      '  color: ' + theme.textSecondary + ';\n' +
      '  text-align: center;\n' +
      '}\n' +
      '\n' +
      '.fm-widget-empty-icon {\n' +
      '  width: 48px;\n' +
      '  height: 48px;\n' +
      '  margin-bottom: 12px;\n' +
      '  color: ' + theme.textSecondary + ';\n' +
      '}\n' +
      '\n' +
      '.fm-widget-filters {\n' +
      '  display: flex;\n' +
      '  flex-wrap: wrap;\n' +
      '  gap: 8px;\n' +
      '  margin-bottom: 16px;\n' +
      '}\n' +
      '\n' +
      '.fm-widget-filter {\n' +
      '  padding: 6px 12px;\n' +
      '  background: ' + theme.cardBg + ';\n' +
      '  border: 1px solid ' + theme.cardBorder + ';\n' +
      '  border-radius: 20px;\n' +
      '  font-size: 12px;\n' +
      '  color: ' + theme.text + ';\n' +
      '  cursor: pointer;\n' +
      '  transition: all 0.2s ease;\n' +
      '}\n' +
      '\n' +
      '.fm-widget-filter:hover,\n' +
      '.fm-widget-filter.active {\n' +
      '  background: ' + theme.primary + ';\n' +
      '  border-color: ' + theme.primary + ';\n' +
      '  color: white;\n' +
      '}\n' +
      '\n' +
      '.fm-widget-modal-overlay {\n' +
      '  position: fixed;\n' +
      '  inset: 0;\n' +
      '  background: rgba(0, 0, 0, 0.6);\n' +
      '  display: flex;\n' +
      '  align-items: center;\n' +
      '  justify-content: center;\n' +
      '  z-index: 999999;\n' +
      '  padding: 16px;\n' +
      '  opacity: 0;\n' +
      '  visibility: hidden;\n' +
      '  transition: opacity 0.3s ease, visibility 0.3s ease;\n' +
      '}\n' +
      '\n' +
      '.fm-widget-modal-overlay.visible {\n' +
      '  opacity: 1;\n' +
      '  visibility: visible;\n' +
      '}\n' +
      '\n' +
      '.fm-widget-modal {\n' +
      '  width: 100%;\n' +
      '  max-width: 420px;\n' +
      '  max-height: 90vh;\n' +
      '  background: ' + theme.cardBg + ';\n' +
      '  border-radius: 16px;\n' +
      '  overflow: hidden;\n' +
      '  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);\n' +
      '  transform: scale(0.95) translateY(20px);\n' +
      '  transition: transform 0.3s ease;\n' +
      '}\n' +
      '\n' +
      '.fm-widget-modal-overlay.visible .fm-widget-modal {\n' +
      '  transform: scale(1) translateY(0);\n' +
      '}\n' +
      '\n' +
      '.fm-widget-modal-header {\n' +
      '  display: flex;\n' +
      '  align-items: center;\n' +
      '  justify-content: space-between;\n' +
      '  padding: 16px;\n' +
      '  border-bottom: 1px solid ' + theme.cardBorder + ';\n' +
      '}\n' +
      '\n' +
      '.fm-widget-modal-title {\n' +
      '  font-size: 16px;\n' +
      '  font-weight: 600;\n' +
      '  color: ' + theme.text + ';\n' +
      '}\n' +
      '\n' +
      '.fm-widget-modal-close {\n' +
      '  width: 32px;\n' +
      '  height: 32px;\n' +
      '  border: none;\n' +
      '  background: transparent;\n' +
      '  cursor: pointer;\n' +
      '  border-radius: 50%;\n' +
      '  display: flex;\n' +
      '  align-items: center;\n' +
      '  justify-content: center;\n' +
      '  color: ' + theme.textSecondary + ';\n' +
      '  transition: background 0.2s ease;\n' +
      '}\n' +
      '\n' +
      '.fm-widget-modal-close:hover {\n' +
      '  background: ' + theme.cardBorder + ';\n' +
      '}\n' +
      '\n' +
      '.fm-widget-modal-body {\n' +
      '  padding: 0;\n' +
      '}\n' +
      '\n' +
      '.fm-widget-modal-iframe {\n' +
      '  width: 100%;\n' +
      '  height: 600px;\n' +
      '  border: none;\n' +
      '}\n' +
      '\n' +
      '@media (max-width: 480px) {\n' +
      '  .fm-widget-modal {\n' +
      '    max-width: 100%;\n' +
      '    max-height: 100vh;\n' +
      '    border-radius: 0;\n' +
      '  }\n' +
      '  .fm-widget-modal-iframe {\n' +
      '    height: calc(100vh - 60px);\n' +
      '  }\n' +
      '}\n';

    this.shadowRoot.appendChild(styles);
  };

  Widget.prototype._render = function() {
    var self = this;
    var theme = this.theme;

    // Clear previous content
    var existingContainer = this.shadowRoot.querySelector('.fm-widget-container');
    if (existingContainer) {
      existingContainer.remove();
    }

    var container = createElement('div', { className: 'fm-widget-container' });

    // Header
    var header = createElement('div', { className: 'fm-widget-header' }, [
      createElement('div', {}, [
        createElement('div', { className: 'fm-widget-title' }, 'Mortgage Professionals'),
        createElement('div', { className: 'fm-widget-subtitle' }, 'Connect via live video'),
      ]),
      createElement('div', { className: 'fm-widget-powered' }, [
        document.createTextNode('Powered by '),
        createElement('a', { href: WIDGET_BASE_URL, target: '_blank', rel: 'noopener noreferrer' }, 'FaceMortgage'),
      ]),
    ]);
    container.appendChild(header);

    // Content
    if (this.loading) {
      container.appendChild(this._renderLoading());
    } else if (this.error) {
      container.appendChild(this._renderError());
    } else if (this.professionals.length === 0) {
      container.appendChild(this._renderEmpty());
    } else {
      container.appendChild(this._renderGrid());
    }

    this.shadowRoot.appendChild(container);
  };

  Widget.prototype._renderLoading = function() {
    return createElement('div', { className: 'fm-widget-loading' }, [
      createElement('div', { className: 'fm-widget-spinner' }),
      createElement('div', {}, 'Loading professionals...'),
    ]);
  };

  Widget.prototype._renderError = function() {
    var self = this;
    return createElement('div', { className: 'fm-widget-error' }, [
      createElement('div', {
        className: 'fm-widget-error-icon',
        innerHTML: '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>',
      }),
      createElement('div', {}, this.error || 'Unable to load professionals'),
      createElement('button', {
        className: 'fm-widget-error-btn',
        onClick: function() { self._fetchProfessionals(); },
      }, 'Try Again'),
    ]);
  };

  Widget.prototype._renderEmpty = function() {
    return createElement('div', { className: 'fm-widget-empty' }, [
      createElement('div', {
        className: 'fm-widget-empty-icon',
        innerHTML: '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>',
      }),
      createElement('div', {}, 'No professionals available'),
      createElement('div', { style: { fontSize: '13px', marginTop: '4px' } }, 'Check back soon'),
    ]);
  };

  Widget.prototype._renderGrid = function() {
    var self = this;
    var compact = this.options.compactMode;
    var gridClass = 'fm-widget-grid' + (compact ? ' compact' : '');
    var grid = createElement('div', { className: gridClass });

    this.professionals.forEach(function(prof) {
      grid.appendChild(self._renderProfessionalCard(prof));
    });

    return grid;
  };

  Widget.prototype._renderProfessionalCard = function(prof) {
    var self = this;
    var compact = this.options.compactMode;
    var isAvailable = prof.status === 'online_available';
    var statusClass = isAvailable ? 'available' : (prof.status === 'online_busy' || prof.status === 'in_call' ? 'busy' : 'offline');

    var cardClass = 'fm-prof-card' + (compact ? ' compact' : '');
    var card = createElement('div', {
      className: cardClass,
      onClick: function() {
        if (self.options.onProfessionalClick) {
          self.options.onProfessionalClick(prof);
        }
      },
    });

    // Avatar
    var avatarWrapClass = 'fm-prof-avatar-wrap' + (compact ? ' compact' : '');
    var avatarWrap = createElement('div', { className: avatarWrapClass });

    if (prof.avatar_url) {
      var avatar = createElement('img', {
        className: 'fm-prof-avatar',
        src: prof.avatar_url,
        alt: prof.first_name + ' ' + prof.last_name,
      });
      avatar.onerror = function() {
        this.style.display = 'none';
        var placeholder = this.nextSibling;
        if (placeholder) placeholder.style.display = 'flex';
      };
      avatarWrap.appendChild(avatar);
    }

    var placeholderClass = 'fm-prof-avatar-placeholder' + (compact ? ' compact' : '');
    var placeholder = createElement('div', {
      className: placeholderClass,
      style: { display: prof.avatar_url ? 'none' : 'flex' },
    }, (prof.first_name.charAt(0) + prof.last_name.charAt(0)).toUpperCase());
    avatarWrap.appendChild(placeholder);

    // Status indicator
    avatarWrap.appendChild(createElement('div', { className: 'fm-prof-status ' + statusClass }));
    card.appendChild(avatarWrap);

    // Name
    card.appendChild(createElement('div', {
      className: 'fm-prof-name' + (compact ? ' compact' : ''),
    }, prof.first_name + ' ' + prof.last_name));

    // Title
    var title = prof.job_title || this._formatUserType(prof.user_type);
    card.appendChild(createElement('div', { className: 'fm-prof-title' }, title));

    // Rating
    if (prof.avg_rating > 0) {
      var ratingClass = 'fm-prof-rating' + (compact ? ' compact' : '');
      card.appendChild(createElement('div', { className: ratingClass }, [
        createElement('span', {
          innerHTML: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>',
        }),
        document.createTextNode(prof.avg_rating.toFixed(1)),
        createElement('span', { style: { color: this.theme.textSecondary } }, ' (' + prof.total_reviews + ')'),
      ]));
    }

    // Call button
    var btnClass = 'fm-prof-call-btn' + (compact ? ' compact' : '');
    var callBtn = createElement('button', {
      className: btnClass,
      disabled: !isAvailable,
      onClick: function(e) {
        e.stopPropagation();
        if (isAvailable) {
          self._initiateCall(prof);
        }
      },
    }, [
      createElement('span', {
        innerHTML: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>',
      }),
      document.createTextNode(isAvailable ? 'Video Call' : 'Unavailable'),
    ]);
    card.appendChild(callBtn);

    return card;
  };

  Widget.prototype._formatUserType = function(userType) {
    var types = {
      loan_officer: 'Loan Officer',
      realtor: 'Realtor',
      title_rep: 'Title Representative',
      attorney: 'Attorney',
    };
    return types[userType] || userType;
  };

  Widget.prototype._fetchProfessionals = function() {
    var self = this;
    this.loading = true;
    this.error = null;
    this._render();

    var params = new URLSearchParams();
    params.append('limit', Math.min(this.options.maxProfessionals, 12).toString());
    params.append('only_available', 'false');

    if (this.options.language) params.append('language', this.options.language);
    if (this.options.specialty) params.append('specialty', this.options.specialty);
    if (this.options.state) params.append('state', this.options.state);
    if (this.options.userType) params.append('user_type', this.options.userType);

    var url = API_BASE_URL + '/api/v1/professionals?' + params.toString();

    fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-Partner-ID': this.options.partnerId,
      },
    })
      .then(function(response) {
        if (!response.ok) {
          throw new Error('Failed to fetch professionals');
        }
        return response.json();
      })
      .then(function(data) {
        self.professionals = data.professionals || [];
        self.loading = false;
        self._render();

        // Track impressions
        self._trackImpressions();
      })
      .catch(function(err) {
        console.error('[FMWidget] Error fetching professionals:', err);
        self.loading = false;
        self.error = err.message || 'Unable to load professionals';
        self._render();

        if (self.options.onError) {
          self.options.onError(err);
        }
      });
  };

  Widget.prototype._trackImpressions = function() {
    if (this.professionals.length === 0) return;

    var impressions = this.professionals.map(function(prof, index) {
      return {
        professional_id: prof.id,
        position: index + 1,
      };
    });

    var url = API_BASE_URL + '/api/v1/grid/track-impressions';

    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Partner-ID': this.options.partnerId,
      },
      body: JSON.stringify({
        impressions: impressions,
        session_id: this.id,
      }),
    }).catch(function(err) {
      console.warn('[FMWidget] Failed to track impressions:', err);
    });
  };

  Widget.prototype._initiateCall = function(prof) {
    var self = this;

    // Track click
    this._trackClick(prof, 'call_initiated');

    if (this.options.onCallInitiated) {
      this.options.onCallInitiated(prof);
    }

    // Open call modal
    this._openCallModal(prof);
  };

  Widget.prototype._trackClick = function(prof, clickType) {
    var position = this.professionals.findIndex(function(p) { return p.id === prof.id; }) + 1;

    var url = API_BASE_URL + '/api/v1/grid/track-click';

    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Partner-ID': this.options.partnerId,
      },
      body: JSON.stringify({
        professional_id: prof.id,
        click_type: clickType,
        grid_position: position,
        session_id: this.id,
        filter_context: {
          partner_id: this.options.partnerId,
          widget_version: VERSION,
        },
      }),
    }).catch(function(err) {
      console.warn('[FMWidget] Failed to track click:', err);
    });
  };

  Widget.prototype._openCallModal = function(prof) {
    var self = this;

    // Create overlay
    var overlay = createElement('div', { className: 'fm-widget-modal-overlay' });

    var modal = createElement('div', { className: 'fm-widget-modal' });

    // Header
    var header = createElement('div', { className: 'fm-widget-modal-header' }, [
      createElement('div', { className: 'fm-widget-modal-title' }, 'Call ' + prof.first_name + ' ' + prof.last_name),
      createElement('button', {
        className: 'fm-widget-modal-close',
        'aria-label': 'Close',
        onClick: function() { self._closeCallModal(overlay); },
        innerHTML: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>',
      }),
    ]);
    modal.appendChild(header);

    // Body with iframe
    var body = createElement('div', { className: 'fm-widget-modal-body' });
    var iframeSrc = WIDGET_BASE_URL + '/embed/widget?professional_id=' + encodeURIComponent(prof.id) +
      '&partner_id=' + encodeURIComponent(this.options.partnerId) +
      '&theme=' + encodeURIComponent(this.options.theme);

    var iframe = createElement('iframe', {
      className: 'fm-widget-modal-iframe',
      src: iframeSrc,
      allow: 'camera; microphone; autoplay; fullscreen',
      title: 'Video Call',
    });
    body.appendChild(iframe);
    modal.appendChild(body);

    overlay.appendChild(modal);

    // Close on overlay click
    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) {
        self._closeCallModal(overlay);
      }
    });

    // Close on escape key
    var escHandler = function(e) {
      if (e.key === 'Escape') {
        self._closeCallModal(overlay);
        document.removeEventListener('keydown', escHandler);
      }
    };
    document.addEventListener('keydown', escHandler);
    overlay._escHandler = escHandler;

    // Append to shadow root or document body
    if (this.shadowRoot.host) {
      document.body.appendChild(overlay);
    } else {
      this.shadowRoot.appendChild(overlay);
    }

    // Animate in
    requestAnimationFrame(function() {
      overlay.classList.add('visible');
    });
  };

  Widget.prototype._closeCallModal = function(overlay) {
    if (overlay._escHandler) {
      document.removeEventListener('keydown', overlay._escHandler);
    }

    overlay.classList.remove('visible');
    setTimeout(function() {
      overlay.remove();
    }, 300);
  };

  Widget.prototype._setupMessageListener = function() {
    var self = this;

    window.addEventListener('message', function(event) {
      // Verify origin
      if (event.origin !== WIDGET_BASE_URL) return;

      var data = event.data;
      if (!data || !data.type) return;

      switch (data.type) {
        case 'fm-call-ended':
          // Close any open modals
          var overlay = self.shadowRoot.host ?
            document.querySelector('.fm-widget-modal-overlay') :
            self.shadowRoot.querySelector('.fm-widget-modal-overlay');
          if (overlay) {
            self._closeCallModal(overlay);
          }
          break;

        case 'fm-call-success':
          // Handle successful call
          console.log('[FMWidget] Call completed successfully');
          break;
      }
    });
  };

  Widget.prototype.refresh = function() {
    this._fetchProfessionals();
  };

  Widget.prototype.destroy = function() {
    if (this.shadowRoot) {
      while (this.shadowRoot.firstChild) {
        this.shadowRoot.firstChild.remove();
      }
    }
    if (this.container) {
      this.container.innerHTML = '';
    }
  };

  // ==================== Static Methods ====================

  Widget.init = function(options) {
    return new Widget(options);
  };

  Widget.version = VERSION;

  // ==================== Auto-initialization ====================

  function autoInit() {
    // Look for elements with data-partner-id attribute
    var elements = document.querySelectorAll('[data-partner-id]');

    elements.forEach(function(el) {
      // Skip if already initialized
      if (el.dataset.fmInitialized) return;

      var options = {
        containerId: el.id || 'fm-widget-' + generateId(),
        partnerId: el.dataset.partnerId,
        theme: el.dataset.theme || 'light',
        maxProfessionals: parseInt(el.dataset.maxProfessionals) || 6,
        showFilters: el.dataset.showFilters === 'true',
        language: el.dataset.language,
        specialty: el.dataset.specialty,
        state: el.dataset.state,
        userType: el.dataset.userType,
        primaryColor: el.dataset.primaryColor,
        compactMode: el.dataset.compactMode === 'true',
      };

      // Ensure element has an ID
      if (!el.id) {
        el.id = options.containerId;
      }

      Widget.init(options);
      el.dataset.fmInitialized = 'true';
    });
  }

  // Run auto-init on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoInit);
  } else {
    // DOM is already loaded
    setTimeout(autoInit, 0);
  }

  // Also run when new elements might be added
  if (window.MutationObserver) {
    var observer = new MutationObserver(debounce(autoInit, 100));
    observer.observe(document.body || document.documentElement, {
      childList: true,
      subtree: true,
    });
  }

  // ==================== Export ====================

  window[WIDGET_NAME] = Widget;

  // Support AMD/CommonJS
  if (typeof define === 'function' && define.amd) {
    define(function() { return Widget; });
  } else if (typeof module === 'object' && module.exports) {
    module.exports = Widget;
  }

})(window, document);
