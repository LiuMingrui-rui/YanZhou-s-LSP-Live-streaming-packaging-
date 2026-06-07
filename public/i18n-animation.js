/**
 * 国际化和动画管理脚本
 * 提供多语言和动画效果的统一管理
 */

class I18nManager {
  constructor() {
    this.translations = {};
    this.currentLang = localStorage.getItem('app-language') || 'zh-CN';
    this.supportedLangs = ['zh-CN', 'en-US', 'ja-JP'];
  }

  /**
   * 初始化i18n（加载翻译文件）
   */
  async init() {
    try {
      const response = await fetch('/i18n.json');
      this.translations = await response.json();
      this.setLanguage(this.currentLang);
      console.log('✓ i18n 初始化成功');
    } catch (error) {
      console.error('✗ i18n 加载失败:', error);
    }
  }

  /**
   * 设置语言
   */
  setLanguage(lang) {
    if (!this.supportedLangs.includes(lang)) {
      console.warn(`语言 ${lang} 不支持，使用默认语言 zh-CN`);
      lang = 'zh-CN';
    }
    this.currentLang = lang;
    localStorage.setItem('app-language', lang);
    document.documentElement.lang = lang;
    this.updatePageLanguage();
    window.dispatchEvent(new CustomEvent('languagechange', { detail: { lang } }));
  }

  /**
   * 获取翻译文本
   */
  t(key) {
    const lang = this.translations[this.currentLang];
    return lang?.[key] ?? key;
  }

  /**
   * 获取所有翻译
   */
  getTranslations() {
    return this.translations[this.currentLang] || {};
  }

  /**
   * 更新页面所有翻译元素
   */
  updatePageLanguage() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      el.textContent = this.t(key);
    });

    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      el.placeholder = this.t(key);
    });

    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      const key = el.getAttribute('data-i18n-title');
      el.title = this.t(key);
    });
  }

  /**
   * 获取所有支持的语言
   */
  getSupportedLanguages() {
    return this.supportedLangs.map(lang => ({
      code: lang,
      name: this.translations[lang]?.name || lang
    }));
  }

  /**
   * 获取当前语言
   */
  getCurrentLanguage() {
    return this.currentLang;
  }
}

class AnimationManager {
  constructor() {
    this.animationType = localStorage.getItem('app-animation-type') || 'fade';
    this.animationSpeed = localStorage.getItem('app-animation-speed') || 'normal';
    this.animationEnabled = localStorage.getItem('app-animation-enabled') !== 'false';
    this.supportedTypes = ['fade', 'slide', 'scale', 'rotate', 'bounce'];
    this.supportedSpeeds = {
      slow: 'slow',
      normal: 'normal',
      fast: 'fast'
    };
  }

  /**
   * 初始化动画系统
   */
  init() {
    this.updateCSSVariables();
    console.log('✓ 动画系统初始化成功');
  }

  /**
   * 设置动画类型
   */
  setAnimationType(type) {
    if (!this.supportedTypes.includes(type)) {
      console.warn(`动画类型 ${type} 不支持`);
      return;
    }
    this.animationType = type;
    localStorage.setItem('app-animation-type', type);
    window.dispatchEvent(new CustomEvent('animationtypechange', { detail: { type } }));
  }

  /**
   * 设置动画速度
   */
  setAnimationSpeed(speed) {
    if (!this.supportedSpeeds[speed]) {
      console.warn(`动画速度 ${speed} 不支持`);
      return;
    }
    this.animationSpeed = speed;
    localStorage.setItem('app-animation-speed', speed);
    this.updateCSSVariables();
    window.dispatchEvent(new CustomEvent('animationspeedchange', { detail: { speed } }));
  }

  /**
   * 启用/禁用动画
   */
  setAnimationEnabled(enabled) {
    this.animationEnabled = enabled;
    localStorage.setItem('app-animation-enabled', enabled);
    if (enabled) {
      document.documentElement.classList.remove('no-animation');
    } else {
      document.documentElement.classList.add('no-animation');
    }
    window.dispatchEvent(new CustomEvent('animationenablechange', { detail: { enabled } }));
  }

  /**
   * 更新CSS变量
   */
  updateCSSVariables() {
    const speedMap = {
      slow: '1s',
      normal: '0.5s',
      fast: '0.3s'
    };
    const duration = speedMap[this.animationSpeed] || '0.5s';
    document.documentElement.style.setProperty('--animation-duration', duration);
  }

  /**
   * 为元素添加进入动画
   */
  animateIn(element, type = null) {
    if (!this.animationEnabled) {
      element.style.opacity = '1';
      return Promise.resolve();
    }

    const animType = type || this.animationType;
    const animClass = this.getAnimationClass(animType, 'in');

    return new Promise(resolve => {
      element.classList.add(animClass);
      element.addEventListener('animationend', function handler() {
        element.removeEventListener('animationend', handler);
        element.classList.remove(animClass);
        resolve();
      }, { once: true });
    });
  }

  /**
   * 为元素添加退出动画
   */
  animateOut(element, type = null) {
    if (!this.animationEnabled) {
      element.style.opacity = '0';
      return Promise.resolve();
    }

    const animType = type || this.animationType;
    const animClass = this.getAnimationClass(animType, 'out');

    return new Promise(resolve => {
      element.classList.add(animClass);
      element.addEventListener('animationend', function handler() {
        element.removeEventListener('animationend', handler);
        element.classList.remove(animClass);
        resolve();
      }, { once: true });
    });
  }

  /**
   * 获取动画类名
   */
  getAnimationClass(type, direction) {
    const typeMap = {
      fade: 'fade',
      slide: `slide-${direction === 'in' ? 'in-up' : 'out-left'}`,
      scale: 'scale',
      rotate: 'rotate',
      bounce: 'bounce'
    };
    const animName = typeMap[type] || 'fade';
    return `animate-${animName}-${direction === 'in' ? 'in' : 'out'}`;
  }

  /**
   * 切换元素可见性（带动画）
   */
  async toggleWithAnimation(element, show = null) {
    const isVisible = show ?? element.style.display !== 'none';
    
    if (isVisible) {
      await this.animateOut(element);
      element.style.display = 'none';
    } else {
      element.style.display = 'block';
      await this.animateIn(element);
    }
  }

  /**
   * 获取所有支持的动画类型
   */
  getSupportedTypes() {
    return this.supportedTypes;
  }

  /**
   * 获取当前配置
   */
  getConfig() {
    return {
      type: this.animationType,
      speed: this.animationSpeed,
      enabled: this.animationEnabled
    };
  }
}

// ════════════════════════════════════════
// 全局实例
// ════════════════════════════════════════

const i18n = new I18nManager();
const animation = new AnimationManager();

// ════════════════════════════════════════
// 快速辅助函数
// ════════════════════════════════════════

/**
 * 获取翻译文本的快速方式
 */
function t(key) {
  return i18n.t(key);
}

/**
 * 初始化所有系统
 */
async function initAllSystems() {
  await i18n.init();
  animation.init();
  console.log('✓ 所有系统初始化完成');
}

// 自动初始化（如果在浏览器环境中）
if (typeof window !== 'undefined' && document.readyState !== 'loading') {
  initAllSystems();
} else if (typeof window !== 'undefined') {
  document.addEventListener('DOMContentLoaded', initAllSystems);
}
