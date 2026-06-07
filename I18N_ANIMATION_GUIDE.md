# 多语言和动画系统使用指南

## 📚 目录

1. [多语言支持(i18n)](#多语言支持)
2. [动画效果系统](#动画效果系统)
3. [前端集成示例](#前端集成示例)
4. [API文档](#api文档)

---

## 多语言支持

### 概述

系统支持以下语言：
- 🇨🇳 中文 (zh-CN) - 默认
- 🇺🇸 英文 (en-US)
- 🇯🇵 日本語 (ja-JP)

### 文件位置

- **翻译文件**: `/public/i18n.json`
- **管理脚本**: `/public/i18n-animation.js`

### 在HTML中使用

#### 1. 引入脚本

```html
<script src="/i18n-animation.js"></script>
<link rel="stylesheet" href="/animations.css">
```

#### 2. 标记可翻译元素

```html
<!-- 翻译文本内容 -->
<h1 data-i18n="title">标题</h1>
<p data-i18n="description">描述</p>

<!-- 翻译placeholder -->
<input type="text" data-i18n-placeholder="search" placeholder="搜索">

<!-- 翻译title属性 -->
<button data-i18n-title="save" title="保存">💾</button>
```

#### 3. 在JavaScript中使用

```javascript
// 获取翻译文本
const text = i18n.t('title');

// 设置语言
i18n.setLanguage('en-US');

// 获取当前语言
const currentLang = i18n.getCurrentLanguage();

// 获取所有支持的语言
const languages = i18n.getSupportedLanguages();
// 结果: [
//   { code: 'zh-CN', name: '中文' },
//   { code: 'en-US', name: 'English' },
//   { code: 'ja-JP', name: '日本語' }
// ]

// 快速翻译（全局函数）
const msg = t('save'); // 等同于 i18n.t('save')
```

### 添加新语言

编辑 `/public/i18n.json` 并添加新语言对象：

```json
{
  "zh-CN": { ... },
  "en-US": { ... },
  "new-LANG": {
    "name": "Language Name",
    "lang": "new-LANG",
    "key1": "value1",
    "key2": "value2"
  }
}
```

然后在 JavaScript 中注册：

```javascript
i18n.supportedLangs.push('new-LANG');
```

---

## 动画效果系统

### 概述

提供5种内置动画类型：

| 类型 | 效果 | 用途 |
|------|------|------|
| **fade** | 淡出/淡入 | 默认切换效果 |
| **slide** | 滑动进出 | 从侧边进入/退出 |
| **scale** | 缩放 | 突出重点 |
| **rotate** | 旋转 | 转换视角 |
| **bounce** | 弹跳 | 活泼/动感 |

### 动画速度

- **slow**: 1 秒
- **normal**: 0.5 秒（默认）
- **fast**: 0.3 秒

### 在HTML中使用

#### 1. CSS动画类

```html
<!-- 进入动画 -->
<div class="animate-fade-in">淡入效果</div>
<div class="animate-slide-in-up">从下往上滑动</div>
<div class="animate-scale-in">缩放进入</div>
<div class="animate-rotate-in">旋转进入</div>
<div class="animate-bounce-in">弹跳进入</div>

<!-- 退出动画 -->
<div class="animate-fade-out">淡出效果</div>
<div class="animate-slide-out-left">向左滑出</div>
<div class="animate-scale-out">缩放退出</div>
<div class="animate-rotate-out">旋转退出</div>
<div class="animate-bounce-out">弹跳退出</div>
```

#### 2. 过渡效果类

```html
<!-- 在元素变化时添加平滑过渡 -->
<div class="transition-all">颜色、大小、位置等所有改变都带过渡</div>
<div class="transition-opacity">只过渡透明度</div>
<div class="transition-transform">只过渡变换（位置、旋转等）</div>
<div class="transition-colors">只过渡颜色</div>
```

#### 3. 特殊效果

```html
<!-- 数字变化时的滑动效果 -->
<div class="animate-number-change">99</div>

<!-- 脉冲效果（用于提示更新或注意） -->
<div class="animate-pulse">注意这里！</div>

<!-- 禁用所有动画 -->
<div class="no-animation">关闭动画的内容</div>
```

### 在JavaScript中使用

#### 基础操作

```javascript
// 设置动画类型
animation.setAnimationType('slide');

// 设置动画速度
animation.setAnimationSpeed('fast');

// 启用/禁用动画
animation.setAnimationEnabled(true);

// 获取当前配置
const config = animation.getConfig();
// 结果: { type: 'slide', speed: 'fast', enabled: true }
```

#### 为元素添加动画

```javascript
const element = document.getElementById('my-element');

// 进入动画（返回Promise）
await animation.animateIn(element);

// 退出动画
await animation.animateOut(element);

// 使用特定动画类型
await animation.animateIn(element, 'bounce');
await animation.animateOut(element, 'rotate');
```

#### 切换可见性（带动画）

```javascript
const element = document.getElementById('panel');

// 如果显示则隐藏，如果隐藏则显示（带动画）
await animation.toggleWithAnimation(element);

// 指定显示或隐藏
await animation.toggleWithAnimation(element, true);  // 显示
await animation.toggleWithAnimation(element, false); // 隐藏
```

### 自定义动画时间

在CSS中修改变量：

```css
:root {
  --animation-duration-slow: 1.5s;
  --animation-duration-normal: 0.7s;
  --animation-duration-fast: 0.2s;
}
```

或在JavaScript中动态设置：

```javascript
document.documentElement.style.setProperty('--animation-duration', '2s');
```

---

## 前端集成示例

### 完整示例：带翻译和动画的列表

```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="/animations.css">
</head>
<body>
    <div id="list"></div>

    <script src="/i18n-animation.js"></script>
    <script>
        async function loadList() {
            // 初始化系统
            await initAllSystems();

            const items = ['Apple', 'Banana', 'Orange'];
            
            items.forEach(item => {
                const el = document.createElement('div');
                el.textContent = item;
                el.style.padding = '10px';
                el.style.margin = '5px';
                el.style.background = '#f0f0f0';
                
                // 添加进入动画
                animation.animateIn(el);
                
                document.getElementById('list').appendChild(el);
            });
        }

        loadList();
    </script>
</body>
</html>
```

### 语言切换器

```html
<select id="langSelect" onchange="switchLanguage(this.value)">
    <option value="zh-CN">中文</option>
    <option value="en-US">English</option>
    <option value="ja-JP">日本語</option>
</select>

<script>
function switchLanguage(lang) {
    i18n.setLanguage(lang);
    // 页面所有data-i18n元素会自动更新
}
</script>
```

### 动画控制面板

```html
<select onchange="animation.setAnimationType(this.value)">
    <option value="fade">淡入/淡出</option>
    <option value="slide">滑动</option>
    <option value="scale">缩放</option>
    <option value="rotate">旋转</option>
    <option value="bounce">弹跳</option>
</select>

<select onchange="animation.setAnimationSpeed(this.value)">
    <option value="slow">慢</option>
    <option value="normal" selected>正常</option>
    <option value="fast">快</option>
</select>

<label>
    启用动画：
    <input type="checkbox" checked 
           onchange="animation.setAnimationEnabled(this.checked)">
</label>
```

---

## API文档

### I18nManager 类

```javascript
const i18n = new I18nManager();

// 方法
i18n.init()                          // 初始化（加载翻译文件）
i18n.setLanguage(lang)               // 设置语言
i18n.t(key)                          // 获取翻译
i18n.getTranslations()               // 获取当前语言的所有翻译
i18n.updatePageLanguage()            // 更新页面中的所有翻译
i18n.getSupportedLanguages()         // 获取支持的语言列表
i18n.getCurrentLanguage()            // 获取当前语言代码

// 事件
document.addEventListener('languagechange', (e) => {
    console.log('语言已切换:', e.detail.lang);
});
```

### AnimationManager 类

```javascript
const animation = new AnimationManager();

// 方法
animation.init()                     // 初始化动画系统
animation.setAnimationType(type)     // 设置动画类型
animation.setAnimationSpeed(speed)   // 设置动画速度
animation.setAnimationEnabled(bool)  // 启用/禁用动画
animation.animateIn(el, type)        // 进入动画（Promise）
animation.animateOut(el, type)       // 退出动画（Promise）
animation.toggleWithAnimation(el, show) // 切换可见性（Promise）
animation.getConfig()                // 获取配置
animation.getSupportedTypes()        // 获取支持的动画类型

// 事件
document.addEventListener('animationtypechange', (e) => {
    console.log('动画类型已切换:', e.detail.type);
});

document.addEventListener('animationspeedchange', (e) => {
    console.log('动画速度已切换:', e.detail.speed);
});

document.addEventListener('animationenablechange', (e) => {
    console.log('动画启用状态:', e.detail.enabled);
});
```

### 全局函数

```javascript
t(key)                 // 快速获取翻译文本
initAllSystems()       // 初始化所有系统（i18n + animation）
```

---

## 存储机制

所有设置都自动保存在浏览器本地存储中：

```javascript
// 多语言
localStorage.getItem('app-language')        // 返回: 'zh-CN'

// 动画类型
localStorage.getItem('app-animation-type')  // 返回: 'fade'

// 动画速度
localStorage.getItem('app-animation-speed') // 返回: 'normal'

// 动画启用状态
localStorage.getItem('app-animation-enabled') // 返回: 'true'
```

用户的设置会在页面刷新后保持不变。

---

## 常见问题

### Q: 如何为已有的HTML页面添加多语言支持？

A: 
1. 在 `<head>` 中添加: `<script src="/i18n-animation.js"></script>`
2. 给需要翻译的元素添加 `data-i18n` 属性
3. 在 `/public/i18n.json` 中添加对应的翻译项

### Q: 动画会影响性能吗？

A: 动画使用 CSS 动画和 Transform，性能开销很小。可以通过禁用动画来进一步提升性能。

### Q: 如何为新的HTML页面快速集成系统？

A: 复制 `/public/settings.html` 作为模板，它已经完整集成了多语言和动画功能。

### Q: 支持哪些浏览器？

A: 现代浏览器均支持（Chrome, Firefox, Safari, Edge 及以上版本）。

---

## 更新日志

### v1.0 (2024-01-01)
- ✅ 初始发布
- ✅ 支持中文、英文、日文
- ✅ 5种内置动画效果
- ✅ 3档动画速度调节
- ✅ 完整的API文档

