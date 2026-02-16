# 123云盘项目架构文档

## 目录

1. [项目概述](#项目概述)
2. [技术栈](#技术栈)
3. [目录结构](#目录结构)
4. [分层架构设计](#分层架构设计)
5. [核心模块说明](#核心模块说明)
6. [数据流与交互](#数据流与交互)
7. [安全特性](#安全特性)
8. [配置文件说明](#配置文件说明)
9. [部署与运行](#部署与运行)

---

## 项目概述

### 项目简介

本项目是一个基于 **123云盘** 的个人网盘管理系统，提供完整的文件管理功能，包括文件浏览、上传、下载、分享、删除等操作。系统采用前后端分离架构，后端使用Python Flask框架，前端使用原生JavaScript实现。

### 主要功能

| 功能模块 | 功能描述 |
|----------|----------|
| 文件浏览 | 支持网格/列表视图，面包屑导航 |
| 文件上传 | 支持拖拽上传、进度显示、大文件分块上传 |
| 文件下载 | 获取下载链接，支持文件夹打包下载 |
| 文件分享 | 创建分享链接，支持设置提取码 |
| 文件搜索 | 按关键词搜索文件和文件夹 |
| 文件管理 | 创建文件夹、删除文件/文件夹 |
| 系统配置 | 主题定制、布局配置、功能开关 |
| 用户认证 | JWT认证、密码管理 |

---

## 技术栈

### 后端技术栈

| 技术 | 版本要求 | 用途 |
|------|----------|------|
| Python | 3.8+ | 主要编程语言 |
| Flask | >=2.3.0 | Web框架 |
| Flask-CORS | >=4.0.0 | 跨域支持 |
| PyJWT | >=2.4.0 | JWT认证 |
| Requests | >=2.28.1 | HTTP请求 |
| Werkzeug | >=2.3.0 | WSGI工具 |

### 前端技术栈

| 技术 | 用途 |
|------|------|
| 原生 JavaScript | 无框架依赖，轻量高效 |
| CSS3 | 主题切换、响应式设计 |
| HTML5 | 语义化标签 |
| Fetch API | 异步HTTP请求 |
| LocalStorage | 本地状态存储 |

---

## 目录结构

```
123pan/
├── 123pan/                    # 核心 SDK 模块
│   ├── api.py                 # 高层 API 封装
│   ├── pan123.py              # 123云盘 SDK 核心类
│   ├── sign_py.py             # 签名生成工具
│   ├── web.py                 # Web 相关功能
│   ├── example.py             # 使用示例
│   ├── requirements.txt       # SDK 依赖
│   └── settings.json          # SDK 配置
│
├── api_wrapper/               # API 包装层
│   ├── client/                # 客户端封装
│   │   ├── api_client.py      # 通用 API 客户端
│   │   └── pan123_client.py   # 123云盘专用客户端
│   ├── decorators/            # 装饰器
│   │   └── retry_decorator.py # 重试装饰器
│   └── utils/                 # 工具类
│       ├── cache_manager.py   # 缓存管理
│       └── file_utils.py      # 文件工具
│
├── business_logic/            # 业务逻辑层
│   ├── models/                # 数据模型
│   │   ├── file_model.py      # 文件模型
│   │   └── permission.py      # 权限模型
│   ├── services/              # 业务服务
│   │   ├── file_service.py    # 文件服务
│   │   ├── search_service.py  # 搜索服务
│   │   └── audit_service.py   # 审计服务
│   └── validators/            # 验证器
│       └── upload_validator.py # 上传验证器
│
├── static/                    # 静态资源
│   ├── assets/                # 静态资源文件
│   │   ├── logo.svg           # Logo
│   │   ├── favicon.svg        # 网站图标
│   │   └── default-avatar.svg # 默认头像
│   ├── config/                # 配置文件
│   │   └── config.json        # 主配置文件
│   ├── css/                   # 样式文件
│   │   ├── main.css           # 主样式
│   │   ├── themes.css         # 主题样式
│   │   └── responsive.css     # 响应式样式
│   └── js/                    # JavaScript 文件
│       ├── app.js             # 主应用逻辑
│       ├── api.js             # API 调用封装
│       ├── state.js           # 状态管理
│       ├── utils.js           # 工具函数
│       └── settings.js        # 设置页面逻辑
│
├── templates/                 # HTML 模板
│   ├── index.html             # 主页面
│   └── settings.html          # 设置页面
│
├── tests/                     # 测试文件
│   ├── test_api.py            # API 测试
│   ├── test_integration.py    # 集成测试
│   └── test_utils.py          # 工具测试
│
├── doc/                       # 项目文档
│   ├── api_document.md        # Web API 文档
│   ├── python_functions.md    # Python 函数文档
│   ├── javascript_functions.md # JavaScript 函数文档
│   └── architecture.md        # 架构文档
│
├── app.py                     # Flask 主入口文件
├── requirements.txt           # 项目依赖
└── 123pan.txt                 # 登录凭证缓存
```

---

## 分层架构设计

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    前端层 (Presentation)                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │   HTML/CSS  │ │ JavaScript  │ │  Templates  │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
├─────────────────────────────────────────────────────────────┤
│                    Web层 (Flask Routes)                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │  页面路由   │ │  API路由    │ │  认证中间件 │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
├─────────────────────────────────────────────────────────────┤
│                  业务逻辑层 (Business Logic)                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │  文件服务   │ │  搜索服务   │ │  审计服务   │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
│  ┌─────────────┐ ┌─────────────┐                            │
│  │  权限模型   │ │  数据验证   │                            │
│  └─────────────┘ └─────────────┘                            │
├─────────────────────────────────────────────────────────────┤
│                  API封装层 (API Wrapper)                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │ API客户端   │ │  缓存管理   │ │  重试装饰器 │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
├─────────────────────────────────────────────────────────────┤
│                   核心SDK层 (Core SDK)                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │   Pan123    │ │  API封装    │ │  签名工具   │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
├─────────────────────────────────────────────────────────────┤
│                  外部服务 (External API)                     │
│  ┌─────────────────────────────────────────────┐            │
│  │              123云盘 REST API               │            │
│  └─────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### 层次职责说明

| 层次 | 职责 | 关键文件 |
|------|------|----------|
| 前端层 | 用户界面渲染、交互处理 | `static/js/*.js`, `templates/*.html` |
| Web层 | HTTP请求处理、路由分发、认证 | `app.py` |
| 业务逻辑层 | 业务规则、权限控制、数据验证 | `business_logic/` |
| API封装层 | API调用封装、缓存、重试 | `api_wrapper/` |
| 核心SDK层 | 与123云盘API直接交互 | `123pan/pan123.py` |

---

## 核心模块说明

### 1. 核心 SDK 模块 (123pan/)

#### Pan123 类

**文件**: [123pan/pan123.py](../123pan/pan123.py)

与123云盘API直接交互的核心类，提供以下功能：

| 方法 | 功能 |
|------|------|
| `login()` | 用户登录 |
| `get_dir()` | 获取目录内容 |
| `link()` | 获取下载链接 |
| `download()` | 下载文件 |
| `up_load()` | 上传文件 |
| `delete_file()` | 删除文件 |
| `mkdir()` | 创建文件夹 |
| `share()` | 分享文件 |

#### API 封装函数

**文件**: [123pan/api.py](../123pan/api.py)

提供更友好的函数式API：

```python
import api as pan_api

# 登录
pan_api.login(username, password)

# 列出文件
result = pan_api.list()
result = pan_api.list_folder("/文档")

# 上传/下载
pan_api.upload(local_path, remote_path)
pan_api.parsing(file_path)

# 文件操作
pan_api.delete(path)
pan_api.create_folder(parent_path, name)
pan_api.share(path)
```

---

### 2. 业务逻辑层 (business_logic/)

#### 权限模型

**文件**: [business_logic/models/permission.py](../business_logic/models/permission.py)

```python
class UserRole(Enum):
    ADMIN = "admin"    # 管理员
    USER = "user"      # 普通用户

class Permission(Enum):
    READ = "read"      # 读取
    WRITE = "write"    # 写入
    DELETE = "delete"  # 删除
    SHARE = "share"    # 分享
    ADMIN = "admin"    # 管理权限
```

**权限矩阵**:

| 角色 | READ | WRITE | DELETE | SHARE | ADMIN |
|------|------|-------|--------|-------|-------|
| ADMIN | ✓ | ✓ | ✓ | ✓ | ✓ |
| USER | ✓ | ✗ | ✗ | ✓ | ✗ |

#### 文件服务

**文件**: [business_logic/services/file_service.py](../business_logic/services/file_service.py)

`FileOperationService` 类封装所有文件操作，集成权限验证：

```python
service = FileOperationService(config)

# 列出文件
result = service.list_files(UserRole.ADMIN, "/")

# 上传文件
result = service.upload_file(UserRole.ADMIN, local_path, remote_path)

# 删除文件
result = service.delete_file(UserRole.ADMIN, path)
```

#### 上传验证器

**文件**: [business_logic/validators/upload_validator.py](../business_logic/validators/upload_validator.py)

- `UploadValidator`: 验证文件大小和类型
- `PathValidator`: 路径安全验证

---

### 3. API 封装层 (api_wrapper/)

#### 重试装饰器

**文件**: [api_wrapper/decorators/retry_decorator.py](../api_wrapper/decorators/retry_decorator.py)

提供自动重试机制，支持指数退避策略：

```python
@retry_on_error(max_retries=3, delay=1.0, backoff=2.0)
def unstable_api_call():
    # 可能失败的API调用
    pass
```

#### 文件工具类

**文件**: [api_wrapper/utils/file_utils.py](../api_wrapper/utils/file_utils.py)

提供文件操作相关的工具方法：

- `get_file_info()`: 获取文件信息
- `format_file_size()`: 格式化文件大小
- `sanitize_filename()`: 清理文件名

---

### 4. 前端模块 (static/js/)

#### 模块组织

| 文件 | 职责 |
|------|------|
| [api.js](../static/js/api.js) | API请求封装，Token管理 |
| [app.js](../static/js/app.js) | 主应用逻辑，事件绑定，UI渲染 |
| [state.js](../static/js/state.js) | 全局状态管理 |
| [utils.js](../static/js/utils.js) | 工具函数 |

#### 主要功能

- 文件网格/列表视图切换
- 拖拽上传支持
- 右键上下文菜单
- 面包屑导航
- 文件搜索
- 模态框交互

---

## 数据流与交互

### 用户登录流程

```
┌─────────┐    POST /api/auth/login    ┌─────────┐
│  用户   │ ──────────────────────────> │ Flask   │
└─────────┘                             └─────────┘
                                              │
                                              ▼
                                        ┌─────────┐
                                        │验证密码 │
                                        │生成JWT  │
                                        └─────────┘
                                              │
                                              ▼
┌─────────┐    {token, username}       ┌─────────┐
│  用户   │ <────────────────────────── │ Flask   │
└─────────┘                             └─────────┘
     │
     │ 存储Token到LocalStorage
     ▼
┌─────────┐
│后续请求 │
│携带Token│
└─────────┘
```

### 文件上传流程

```
┌─────────┐    POST /api/upload        ┌─────────┐
│  用户   │ ──────────────────────────> │ Flask   │
│(拖拽/选择)│   FormData: file, path    │         │
└─────────┘                             └─────────┘
                                              │
                                              ▼
                                        ┌─────────┐
                                        │JWT验证  │
                                        └─────────┘
                                              │
                                              ▼
                                        ┌─────────┐
                                        │保存临时 │
                                        │文件     │
                                        └─────────┘
                                              │
                                              ▼
                                        ┌─────────┐
                                        │调用SDK  │
                                        │上传文件 │
                                        └─────────┘
                                              │
                                              ▼
┌─────────┐    {status: "success"}      ┌─────────┐
│  用户   │ <────────────────────────── │ Flask   │
└─────────┘                             └─────────┘
```

### 文件列表获取流程

```
┌─────────┐    GET /api/files?path=/   ┌─────────┐
│  用户   │ ──────────────────────────> │ Flask   │
└─────────┘                             └─────────┘
                                              │
                                              ▼
                                        ┌─────────┐
                                        │调用SDK  │
                                        │获取列表 │
                                        └─────────┘
                                              │
                                              ▼
                                        ┌─────────┐
                                        │格式化   │
                                        │数据     │
                                        └─────────┘
                                              │
                                              ▼
┌─────────┐    {folder: [], file: []}   ┌─────────┐
│  用户   │ <────────────────────────── │ Flask   │
└─────────┘                             └─────────┘
```

---

## 安全特性

### 1. JWT 认证

- 使用 JWT Token 进行用户认证
- Token 有效期可配置（默认24小时）
- Token 存储在客户端 LocalStorage

### 2. 密码安全

- 密码使用 SHA256 哈希存储
- 不存储明文密码

### 3. 输入验证

| 验证类型 | 实现位置 | 说明 |
|----------|----------|------|
| 颜色值验证 | `app.py:validate_color()` | 支持HEX、RGB、HSL格式 |
| HTML消毒 | `app.py:sanitize_html()` | 移除危险标签 |
| 路径验证 | `PathValidator` | 防止路径遍历攻击 |
| 文件类型验证 | `UploadValidator` | 限制上传文件类型 |

### 4. 路径安全

```python
PROTECTED_PATHS = ["/config", "/admin", "/system", "/logs"]

def validate_path_access(user_role, path):
    if user_role == UserRole.ADMIN:
        return True
    for protected_path in PROTECTED_PATHS:
        if path.startswith(protected_path):
            return False
    return True
```

### 5. CORS 配置

使用 Flask-CORS 配置跨域支持：

```python
from flask_cors import CORS
CORS(app)
```

---

## 配置文件说明

### 主配置文件

**文件**: [static/config/config.json](../static/config/config.json)

```json
{
    "site": {
        "title": "个人网盘",
        "description": "基于123云盘的个人网盘系统"
    },
    "theme": {
        "primary_color": "#1890ff",
        "secondary_color": "#52c41a",
        "background_color": "#f5f5f5",
        "text_color": "#333333",
        "border_color": "#d9d9d9",
        "hover_color": "#40a9ff"
    },
    "layout": {
        "header_html": "",
        "footer_html": "",
        "show_footer": true
    },
    "upload": {
        "max_file_size": 2147483648,
        "allowed_types": ["*"]
    },
    "features": {
        "enable_search": true,
        "enable_share": true,
        "enable_upload": true
    },
    "auth": {
        "admin_username": "admin",
        "admin_password_hash": "",
        "jwt_secret": "your-secret-key",
        "token_expire_hours": 24
    }
}
```

### 配置段说明

| 配置段 | 说明 |
|--------|------|
| site | 网站基本信息 |
| theme | 主题颜色配置 |
| layout | 页面布局配置 |
| upload | 上传限制配置 |
| features | 功能开关配置 |
| auth | 认证相关配置（敏感信息） |

### SDK 配置文件

**文件**: [123pan/settings.json](../123pan/settings.json)

```json
{
    "username": "your_123pan_email",
    "password": "your_123pan_password",
    "default-path": ""
}
```

---

## 部署与运行

### 环境要求

- Python 3.8+
- pip 包管理器

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

1. 编辑 `123pan/settings.json`，填入123云盘账号
2. 编辑 `static/config/config.json`，配置系统参数

### 运行

```bash
python app.py
```

应用将在 `http://0.0.0.0:8000` 启动，开启 Debug 模式。

### 生产环境部署

建议使用 Gunicorn 或 uWSGI：

```bash
# 使用 Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# 使用 uWSGI
pip install uwsgi
uwsgi --http :8000 --wsgi-file app.py --callable app
```

---

## 扩展开发

### 添加新的 API 接口

1. 在 `app.py` 中添加路由：

```python
@app.route('/api/new-endpoint', methods=['GET'])
@require_auth  # 如果需要认证
def new_endpoint():
    # 处理逻辑
    return jsonify({'code': 200, 'message': 'success', 'data': None})
```

2. 在 `static/js/api.js` 中添加调用方法：

```javascript
async newEndpoint() {
    return this.get('/new-endpoint');
}
```

### 添加新的业务服务

1. 在 `business_logic/services/` 创建新服务类
2. 继承或复用现有权限验证逻辑
3. 在 `app.py` 中引入并使用

### 添加新的前端功能

1. 在 `static/js/app.js` 添加事件处理
2. 在 `templates/index.html` 添加UI元素
3. 在 `static/css/main.css` 添加样式

---

**文档版本**: 1.0  
**最后更新**: 2024年
