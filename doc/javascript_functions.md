# JavaScript 函数文档

## 目录

1. [API调用模块](#api调用模块)
2. [工具函数模块](#工具函数模块)
3. [应用主逻辑模块](#应用主逻辑模块)
4. [状态管理模块](#状态管理模块)

---

## API调用模块

**文件位置**: [static/js/api.js](../static/js/api.js)

`API` 对象封装了所有与后端API交互的方法。

### 属性

| 属性名 | 类型 | 说明 |
|--------|------|------|
| baseUrl | string | API基础路径，默认为 `/api` |
| token | string | JWT认证令牌，从localStorage读取 |

---

### setToken 方法

```javascript
setToken(token)
```

**功能描述**: 设置并存储认证令牌

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| token | string | 是 | JWT令牌字符串 |

**返回值**: 无

**使用示例**:

```javascript
API.setToken('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...');
```

---

### clearToken 方法

```javascript
clearToken()
```

**功能描述**: 清除认证令牌

**参数说明**: 无参数

**返回值**: 无

**使用示例**:

```javascript
API.clearToken();
```

---

### getHeaders 方法

```javascript
getHeaders()
```

**功能描述**: 获取请求头对象

**参数说明**: 无参数

**返回值**: 请求头对象

```javascript
{
    'Content-Type': 'application/json',
    'Authorization': 'Bearer xxx' // 如果有token
}
```

---

### request 方法

```javascript
async request(method, endpoint, data = null)
```

**功能描述**: 发送API请求的通用方法

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| method | string | 是 | - | HTTP方法（GET/POST/PUT/PATCH/DELETE） |
| endpoint | string | 是 | - | API端点路径 |
| data | object | 否 | null | 请求数据 |

**返回值**: Promise，解析为响应JSON对象

**异常处理**: 
- 401状态码时自动清除Token并触发`authRequired`事件
- 网络错误返回 `{code: 500, message: '网络错误', data: null}`

**使用示例**:

```javascript
const result = await API.request('GET', '/files?path=/');
if (result.code === 200) {
    console.log(result.data);
}
```

---

### HTTP方法封装

```javascript
get(endpoint)
post(endpoint, data)
put(endpoint, data)
patch(endpoint, data)
delete(endpoint)
```

**功能描述**: 对应HTTP方法的快捷封装

**使用示例**:

```javascript
const config = await API.get('/config');
const result = await API.post('/auth/login', {username: 'admin', password: '123'});
await API.put('/config', {site: {title: '新标题'}});
await API.delete('/files?path=/test.txt');
```

---

### getConfig 方法

```javascript
async getConfig()
```

**功能描述**: 获取完整配置

**返回值**: Promise

---

### getConfigSection 方法

```javascript
async getConfigSection(section)
```

**功能描述**: 获取指定配置段

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| section | string | 是 | 配置段名称 |

**返回值**: Promise

**使用示例**:

```javascript
const theme = await API.getConfigSection('theme');
```

---

### updateConfig 方法

```javascript
async updateConfig(data)
```

**功能描述**: 更新完整配置

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| data | object | 是 | 配置数据 |

**返回值**: Promise

---

### updateConfigSection 方法

```javascript
async updateConfigSection(section, data)
```

**功能描述**: 更新指定配置段

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| section | string | 是 | 配置段名称 |
| data | object | 是 | 配置数据 |

**返回值**: Promise

---

### validateConfig 方法

```javascript
async validateConfig(data)
```

**功能描述**: 验证配置格式

**返回值**: Promise，包含`valid`和`errors`字段

---

### createBackup 方法

```javascript
async createBackup()
```

**功能描述**: 创建配置备份

**返回值**: Promise

---

### getBackups 方法

```javascript
async getBackups()
```

**功能描述**: 获取备份列表

**返回值**: Promise

---

### restoreBackup 方法

```javascript
async restoreBackup(backupId)
```

**功能描述**: 恢复指定备份

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| backupId | string | 是 | 备份ID |

**返回值**: Promise

---

### login 方法

```javascript
async login(username, password)
```

**功能描述**: 用户登录

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

**返回值**: Promise

**注意事项**: 登录成功后自动存储Token

**使用示例**:

```javascript
const result = await API.login('admin', 'password');
if (result.code === 200) {
    console.log('登录成功');
}
```

---

### logout 方法

```javascript
async logout()
```

**功能描述**: 用户登出

**返回值**: Promise `{code: 200, message: '已退出登录'}`

---

### checkAuth 方法

```javascript
async checkAuth()
```

**功能描述**: 检查认证状态

**返回值**: Promise

---

### listFiles 方法

```javascript
async listFiles(path = '/')
```

**功能描述**: 获取文件列表

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| path | string | 否 | '/' | 目录路径 |

**返回值**: Promise

**使用示例**:

```javascript
const result = await API.listFiles('/文档');
if (result.code === 200) {
    console.log(result.data.folder);
    console.log(result.data.file);
}
```

---

### uploadFile 方法

```javascript
async uploadFile(formData, onProgress)
```

**功能描述**: 上传文件

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| formData | FormData | 是 | 包含file和path的表单数据 |
| onProgress | function | 否 | 上传进度回调函数 |

**返回值**: Promise

**使用示例**:

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('path', '/uploads');

const result = await API.uploadFile(formData, (progress) => {
    console.log(`上传进度: ${progress}%`);
});
```

---

### downloadFile 方法

```javascript
async downloadFile(path)
```

**功能描述**: 获取文件下载链接

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| path | string | 是 | 文件路径 |

**返回值**: Promise，包含下载URL

---

### deleteFile 方法

```javascript
async deleteFile(path)
```

**功能描述**: 删除文件

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| path | string | 是 | 文件路径 |

**返回值**: Promise

---

### createFolder 方法

```javascript
async createFolder(parentPath, name)
```

**功能描述**: 创建文件夹

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| parentPath | string | 是 | 父目录路径 |
| name | string | 是 | 文件夹名称 |

**返回值**: Promise

---

### shareFile 方法

```javascript
async shareFile(path)
```

**功能描述**: 分享文件

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| path | string | 是 | 文件路径 |

**返回值**: Promise，包含share_url、share_key

---

### searchFiles 方法

```javascript
async searchFiles(keyword, path = '/')
```

**功能描述**: 搜索文件

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| keyword | string | 是 | - | 搜索关键词 |
| path | string | 否 | '/' | 搜索目录 |

**返回值**: Promise

---

### getLogs 方法

```javascript
async getLogs(page = 1, pageSize = 20)
```

**功能描述**: 获取操作日志

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| page | number | 否 | 1 | 页码 |
| pageSize | number | 否 | 20 | 每页数量 |

**返回值**: Promise

---

## 工具函数模块

**文件位置**: [static/js/utils.js](../static/js/utils.js)

`Utils` 对象提供常用的工具函数。

### formatFileSize 方法

```javascript
formatFileSize(bytes)
```

**功能描述**: 格式化文件大小显示

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| bytes | number | 是 | 字节数 |

**返回值**: 格式化的大小字符串

**使用示例**:

```javascript
Utils.formatFileSize(1536000000);
```

---

### formatDate 方法

```javascript
formatDate(dateString)
```

**功能描述**: 格式化日期时间显示

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dateString | string | 是 | ISO日期字符串 |

**返回值**: 本地化日期字符串

**使用示例**:

```javascript
Utils.formatDate('2024-01-15T14:30:00Z');
```

---

### getFileIcon 方法

```javascript
getFileIcon(filename, isFolder = false)
```

**功能描述**: 根据文件名获取对应图标emoji

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| filename | string | 是 | - | 文件名 |
| isFolder | boolean | 否 | false | 是否为文件夹 |

**返回值**: emoji图标字符

**支持的文件类型图标**:

| 类型 | 图标 |
|------|------|
| 文件夹 | 📁 |
| PDF | 📄 |
| Word文档 | 📝 |
| Excel表格 | 📊 |
| PPT演示 | 📽️ |
| 图片 | 🖼️ |
| 视频 | 🎬 |
| 音频 | 🎵 |
| 压缩包 | 📦 |
| 文本 | 📃 |
| 代码文件 | 🐍📜🌐🎨📋 |
| 可执行文件 | ⚙️ |

**使用示例**:

```javascript
const icon = Utils.getFileIcon('document.pdf');
const folderIcon = Utils.getFileIcon('folder', true);
```

---

### debounce 方法

```javascript
debounce(func, wait)
```

**功能描述**: 创建防抖函数

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| func | function | 是 | 需要防抖的函数 |
| wait | number | 是 | 等待时间（毫秒） |

**返回值**: 防抖后的函数

**使用示例**:

```javascript
const debouncedSearch = Utils.debounce((keyword) => {
    API.searchFiles(keyword);
}, 300);

searchInput.addEventListener('input', (e) => {
    debouncedSearch(e.target.value);
});
```

---

### throttle 方法

```javascript
throttle(func, limit)
```

**功能描述**: 创建节流函数

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| func | function | 是 | 需要节流的函数 |
| limit | number | 是 | 限制时间（毫秒） |

**返回值**: 节流后的函数

**使用示例**:

```javascript
const throttledScroll = Utils.throttle(() => {
    console.log('滚动事件触发');
}, 200);

window.addEventListener('scroll', throttledScroll);
```

---

### showToast 方法

```javascript
showToast(message, type = 'success')
```

**功能描述**: 显示提示消息

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| message | string | 是 | - | 消息内容 |
| type | string | 否 | 'success' | 消息类型（success/error/warning） |

**返回值**: 无

**使用示例**:

```javascript
Utils.showToast('操作成功', 'success');
Utils.showToast('操作失败', 'error');
```

---

### showConfirm 方法

```javascript
showConfirm(title, message)
```

**功能描述**: 显示确认对话框

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| title | string | 是 | 对话框标题 |
| message | string | 是 | 对话框消息 |

**返回值**: Promise<boolean>，用户点击确定返回true，取消返回false

**使用示例**:

```javascript
const confirmed = await Utils.showConfirm('确认删除', '确定要删除此文件吗？');
if (confirmed) {
    await API.deleteFile(path);
}
```

---

### parsePath 方法

```javascript
parsePath(path)
```

**功能描述**: 解析路径

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| path | string | 是 | 文件路径 |

**返回值**: 路径解析对象

```javascript
{
    parts: ['folder1', 'folder2', 'file.txt'],
    name: 'file.txt',
    parent: '/folder1/folder2'
}
```

**使用示例**:

```javascript
const parsed = Utils.parsePath('/文档/工作/report.pdf');
console.log(parsed.name);
console.log(parsed.parent);
```

---

### buildBreadcrumb 方法

```javascript
buildBreadcrumb(path)
```

**功能描述**: 构建面包屑导航数组

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| path | string | 是 | 当前路径 |

**返回值**: 面包屑数组

```javascript
[
    { name: '根目录', path: '/' },
    { name: '文档', path: '/文档' },
    { name: '工作', path: '/文档/工作' }
]
```

**使用示例**:

```javascript
const breadcrumb = Utils.buildBreadcrumb('/文档/工作');
breadcrumb.forEach(item => {
    console.log(`${item.name} -> ${item.path}`);
});
```

---

### applyTheme 方法

```javascript
applyTheme(theme)
```

**功能描述**: 应用主题样式到页面

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| theme | object | 是 | 主题配置对象 |

**返回值**: 无

**使用示例**:

```javascript
Utils.applyTheme({
    primary_color: '#1890ff',
    background_color: '#f5f5f5'
});
```

---

### escapeHtml 方法

```javascript
escapeHtml(text)
```

**功能描述**: HTML转义，防止XSS攻击

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| text | string | 是 | 需要转义的文本 |

**返回值**: 转义后的安全文本

**使用示例**:

```javascript
const safe = Utils.escapeHtml('<script>alert("xss")</script>');
```

---

### copyToClipboard 方法

```javascript
copyToClipboard(text)
```

**功能描述**: 复制文本到剪贴板

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| text | string | 是 | 需要复制的文本 |

**返回值**: Promise

**使用示例**:

```javascript
await Utils.copyToClipboard('https://example.com/share/xxx');
Utils.showToast('链接已复制');
```

---

## 应用主逻辑模块

**文件位置**: [static/js/app.js](../static/js/app.js)

### initApp 函数

```javascript
async function initApp()
```

**功能描述**: 初始化应用

**参数说明**: 无参数

**返回值**: Promise

**执行流程**:
1. 加载保存的视图模式
2. 加载配置
3. 检查认证状态
4. 加载文件列表

---

### loadConfig 函数

```javascript
async function loadConfig()
```

**功能描述**: 加载系统配置

**返回值**: Promise

---

### applyConfig 函数

```javascript
function applyConfig(config)
```

**功能描述**: 应用配置到界面

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| config | object | 是 | 配置对象 |

**返回值**: 无

---

### checkAuth 函数

```javascript
async function checkAuth()
```

**功能描述**: 检查用户认证状态

**返回值**: Promise

---

### loadFiles 函数

```javascript
async function loadFiles(path)
```

**功能描述**: 加载指定目录的文件列表

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| path | string | 是 | 目录路径 |

**返回值**: Promise

**使用示例**:

```javascript
await loadFiles('/文档');
```

---

### renderFiles 函数

```javascript
function renderFiles(data)
```

**功能描述**: 渲染文件列表到界面

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| data | object | 是 | 文件数据对象 |

**返回值**: 无

---

### createFileItem 函数

```javascript
function createFileItem(file, isFolder)
```

**功能描述**: 创建文件项DOM元素

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | object | 是 | 文件信息对象 |
| isFolder | boolean | 是 | 是否为文件夹 |

**返回值**: DOM元素

---

### handleFileClick 函数

```javascript
function handleFileClick(file, isFolder, e)
```

**功能描述**: 处理文件单击事件

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | object | 是 | 文件信息 |
| isFolder | boolean | 是 | 是否为文件夹 |
| e | Event | 是 | 事件对象 |

**返回值**: 无

---

### handleFileDblClick 函数

```javascript
function handleFileDblClick(file, isFolder)
```

**功能描述**: 处理文件双击事件

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | object | 是 | 文件信息 |
| isFolder | boolean | 是 | 是否为文件夹 |

**返回值**: 无

**行为说明**:
- 文件夹：进入该目录
- 文件：开始下载

---

### downloadFile 函数

```javascript
async function downloadFile(file)
```

**功能描述**: 下载文件

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | object | 是 | 文件信息对象 |

**返回值**: Promise

---

### updateBreadcrumb 函数

```javascript
function updateBreadcrumb(path)
```

**功能描述**: 更新面包屑导航

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| path | string | 是 | 当前路径 |

**返回值**: 无

---

### showEmptyState 函数

```javascript
function showEmptyState()
```

**功能描述**: 显示空状态提示

**返回值**: 无

---

### updateViewMode 函数

```javascript
function updateViewMode()
```

**功能描述**: 更新视图模式（网格/列表）

**返回值**: 无

---

### showContextMenu 函数

```javascript
function showContextMenu(e, file, isFolder)
```

**功能描述**: 显示右键上下文菜单

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| e | Event | 是 | 鼠标事件 |
| file | object | 是 | 文件信息 |
| isFolder | boolean | 是 | 是否为文件夹 |

**返回值**: 无

---

### hideContextMenu 函数

```javascript
function hideContextMenu()
```

**功能描述**: 隐藏右键菜单

**返回值**: 无

---

### setupEventListeners 函数

```javascript
function setupEventListeners()
```

**功能描述**: 设置所有事件监听器

**返回值**: 无

**监听的事件**:
- 菜单切换
- 视图切换
- 登录表单提交
- 上传文件
- 创建文件夹
- 搜索
- 右键菜单操作
- 认证事件

---

### handleFileUpload 函数

```javascript
async function handleFileUpload(files)
```

**功能描述**: 处理文件上传

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| files | FileList | 是 | 文件列表 |

**返回值**: Promise

**使用示例**:

```javascript
fileInput.addEventListener('change', (e) => {
    handleFileUpload(e.target.files);
});
```

---

## 状态管理模块

**文件位置**: [static/js/state.js](../static/js/state.js)

`State` 对象管理应用的全局状态。

### 属性

| 属性名 | 类型 | 说明 |
|--------|------|------|
| currentPath | string | 当前目录路径 |
| currentView | string | 当前视图模式（grid/list） |
| config | object | 系统配置 |
| fileCache | object | 文件列表缓存 |

---

### setPath 方法

```javascript
setPath(path)
```

**功能描述**: 设置当前路径

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| path | string | 是 | 目录路径 |

**返回值**: 无

---

### setView 方法

```javascript
setView(view)
```

**功能描述**: 设置视图模式

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| view | string | 是 | 视图模式（grid/list） |

**返回值**: 无

---

### setConfig 方法

```javascript
setConfig(config)
```

**功能描述**: 设置配置

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| config | object | 是 | 配置对象 |

**返回值**: 无

---

### cacheFiles 方法

```javascript
cacheFiles(path, data)
```

**功能描述**: 缓存文件列表

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| path | string | 是 | 目录路径 |
| data | object | 是 | 文件数据 |

**返回值**: 无

---

### getCachedFiles 方法

```javascript
getCachedFiles(path)
```

**功能描述**: 获取缓存的文件列表

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| path | string | 是 | 目录路径 |

**返回值**: 缓存的文件数据，无缓存返回null

---

### clearCache 方法

```javascript
clearCache()
```

**功能描述**: 清空文件缓存

**返回值**: 无

---

### toggleFileSelection 方法

```javascript
toggleFileSelection(fileId)
```

**功能描述**: 切换文件选中状态

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| fileId | string | 是 | 文件ID |

**返回值**: 无

---

**文档版本**: 1.0  
**最后更新**: 2024年
