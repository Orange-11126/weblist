# 123云盘 Web API 文档

## 目录

1. [概述](#概述)
2. [认证机制](#认证机制)
3. [通用响应格式](#通用响应格式)
4. [错误码说明](#错误码说明)
5. [页面路由API](#页面路由api)
6. [认证模块API](#认证模块api)
7. [配置管理API](#配置管理api)
8. [文件管理API](#文件管理api)
9. [日志统计API](#日志统计api)

---

## 概述

### 基础信息

| 项目 | 说明 |
|------|------|
| 基础URL | `http://localhost:8000` |
| API前缀 | `/api` |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |
| 认证方式 | JWT Bearer Token |

### 技术栈

- **后端框架**: Flask 2.3.0+
- **认证方式**: JWT (PyJWT 2.4.0+)
- **跨域支持**: Flask-CORS 4.0.0+

---

## 认证机制

### JWT Token 认证

需要认证的接口需在请求头中携带JWT Token：

```
Authorization: Bearer <token>
```

### Token 获取

通过 `/api/auth/login` 接口登录获取Token。

### Token 有效期

默认有效期为24小时，可在配置文件中通过 `auth.token_expire_hours` 调整。

---

## 通用响应格式

所有API接口返回统一的JSON格式：

```json
{
    "code": 200,
    "message": "操作成功",
    "data": {
        // 响应数据
    }
}
```

### 响应字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | integer | HTTP状态码 |
| message | string | 操作结果描述 |
| data | object/null | 响应数据，失败时可能为null |

---

## 错误码说明

| 状态码 | 含义 | 说明 |
|--------|------|------|
| 200 | 成功 | 请求处理成功 |
| 400 | 请求错误 | 参数缺失或格式错误 |
| 401 | 未授权 | 未认证或Token无效/过期 |
| 404 | 未找到 | 资源不存在 |
| 500 | 服务器错误 | 内部异常 |

---

## 页面路由API

### 1. 主页

**接口名称**: 获取主页  
**请求URL**: `/`  
**HTTP方法**: GET  
**认证要求**: 无需认证

#### 功能描述

渲染并返回应用主页面。

#### 响应

返回 `index.html` 页面内容。

---

### 2. 设置页面

**接口名称**: 获取设置页面  
**请求URL**: `/settings`  
**HTTP方法**: GET  
**认证要求**: 无需认证

#### 功能描述

渲染并返回系统设置页面。

#### 响应

返回 `settings.html` 页面内容。

---

## 认证模块API

### 1. 用户登录

**接口名称**: 用户登录  
**请求URL**: `/api/auth/login`  
**HTTP方法**: POST  
**认证要求**: 无需认证

#### 功能描述

使用用户名和密码进行登录认证，成功后返回JWT Token。

#### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| username | string | 是 | - | 用户名 |
| password | string | 是 | - | 密码（明文传输，建议使用HTTPS） |

#### 请求示例

```json
{
    "username": "admin",
    "password": "your_password"
}
```

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "登录成功",
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "username": "admin"
    }
}
```

**失败响应 (401)**:
```json
{
    "code": 401,
    "message": "用户名或密码错误",
    "data": null
}
```

#### 注意事项

- 密码使用SHA256哈希进行验证
- Token需存储在客户端，用于后续需要认证的请求

---

### 2. 修改密码

**接口名称**: 修改密码  
**请求URL**: `/api/auth/password`  
**HTTP方法**: PUT  
**认证要求**: 需要JWT认证

#### 功能描述

修改当前登录用户的密码。

#### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| old_password | string | 是 | - | 原密码 |
| new_password | string | 是 | - | 新密码 |

#### 请求示例

```json
{
    "old_password": "old_password_123",
    "new_password": "new_password_456"
}
```

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "密码修改成功",
    "data": null
}
```

**失败响应 (400)**:
```json
{
    "code": 400,
    "message": "原密码错误",
    "data": null
}
```

---

### 3. 检查认证状态

**接口名称**: 检查认证状态  
**请求URL**: `/api/auth/check`  
**HTTP方法**: GET  
**认证要求**: 需要JWT认证

#### 功能描述

验证当前Token是否有效，并返回用户信息。

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "已认证",
    "data": {
        "username": "admin"
    }
}
```

**失败响应 (401)**:
```json
{
    "code": 401,
    "message": "令牌无效或已过期",
    "data": null
}
```

---

## 配置管理API

### 1. 获取完整配置

**接口名称**: 获取完整配置  
**请求URL**: `/api/config`  
**HTTP方法**: GET  
**认证要求**: 无需认证

#### 功能描述

获取系统完整配置信息，但会移除敏感的auth字段。

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "site": {
            "title": "个人网盘",
            "description": "基于123云盘的个人网盘系统"
        },
        "theme": {
            "primary_color": "#1890ff",
            "secondary_color": "#52c41a",
            "background_color": "#f5f5f5"
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
        }
    }
}
```

---

### 2. 获取配置段

**接口名称**: 获取指定配置段  
**请求URL**: `/api/config/<section>`  
**HTTP方法**: GET  
**认证要求**: 无需认证

#### 功能描述

获取指定名称的配置段内容。

#### URL参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| section | string | 是 | 配置段名称（如site、theme、upload等） |

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "title": "个人网盘",
        "description": "基于123云盘的个人网盘系统"
    }
}
```

**失败响应 (404)**:
```json
{
    "code": 404,
    "message": "配置段 xxx 不存在",
    "data": null
}
```

---

### 3. 更新完整配置

**接口名称**: 更新完整配置  
**请求URL**: `/api/config`  
**HTTP方法**: PUT  
**认证要求**: 需要JWT认证

#### 功能描述

更新系统配置，更新前会自动创建备份。

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| site | object | 否 | 站点配置 |
| theme | object | 否 | 主题配置 |
| layout | object | 否 | 布局配置 |
| upload | object | 否 | 上传配置 |
| features | object | 否 | 功能开关配置 |

#### 请求示例

```json
{
    "site": {
        "title": "我的网盘"
    },
    "theme": {
        "primary_color": "#1890ff"
    }
}
```

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "配置更新成功",
    "data": {
        "updated_fields": ["site", "theme"]
    }
}
```

#### 注意事项

- auth字段不可通过此接口修改
- 颜色值需符合HEX、RGB或HSL格式
- HTML内容会自动过滤危险标签

---

### 4. 更新配置段

**接口名称**: 更新指定配置段  
**请求URL**: `/api/config/<section>`  
**HTTP方法**: PATCH  
**认证要求**: 需要JWT认证

#### 功能描述

更新指定配置段的内容。

#### URL参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| section | string | 是 | 配置段名称 |

#### 请求示例

```json
{
    "primary_color": "#52c41a",
    "secondary_color": "#1890ff"
}
```

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "theme 配置更新成功",
    "data": {
        "primary_color": "#52c41a",
        "secondary_color": "#1890ff"
    }
}
```

---

### 5. 验证配置

**接口名称**: 验证配置格式  
**请求URL**: `/api/config/validate`  
**HTTP方法**: POST  
**认证要求**: 无需认证

#### 功能描述

验证配置数据格式是否正确，不实际保存。

#### 请求参数

传入需要验证的配置对象。

#### 请求示例

```json
{
    "theme": {
        "primary_color": "#1890ff"
    },
    "upload": {
        "max_file_size": 2147483648
    }
}
```

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "验证完成",
    "data": {
        "valid": true,
        "errors": []
    }
}
```

**验证失败响应**:
```json
{
    "code": 200,
    "message": "验证完成",
    "data": {
        "valid": false,
        "errors": [
            "颜色值 primary_color 格式不正确",
            "max_file_size 必须是正整数"
        ]
    }
}
```

---

### 6. 创建备份

**接口名称**: 创建配置备份  
**请求URL**: `/api/config/backup`  
**HTTP方法**: POST  
**认证要求**: 需要JWT认证

#### 功能描述

手动创建当前配置的备份文件。

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "备份创建成功",
    "data": {
        "backup_id": "20240115_143025"
    }
}
```

---

### 7. 列出备份

**接口名称**: 获取备份列表  
**请求URL**: `/api/config/backups`  
**HTTP方法**: GET  
**认证要求**: 需要JWT认证

#### 功能描述

获取所有配置备份文件的列表。

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "backups": [
            {
                "backup_id": "20240115_143025",
                "created_at": "2024-01-15T14:30:25",
                "size": 2048
            },
            {
                "backup_id": "20240114_100000",
                "created_at": "2024-01-14T10:00:00",
                "size": 1980
            }
        ]
    }
}
```

---

### 8. 恢复备份

**接口名称**: 恢复配置备份  
**请求URL**: `/api/config/restore/<backup_id>`  
**HTTP方法**: POST  
**认证要求**: 需要JWT认证

#### 功能描述

从指定的备份文件恢复配置。

#### URL参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| backup_id | string | 是 | 备份ID（时间戳格式，如20240115_143025） |

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "配置恢复成功",
    "data": null
}
```

**失败响应 (404)**:
```json
{
    "code": 404,
    "message": "备份文件不存在",
    "data": null
}
```

---

### 9. 获取主题配置

**接口名称**: 获取主题配置  
**请求URL**: `/api/config/theme`  
**HTTP方法**: GET  
**认证要求**: 无需认证

#### 功能描述

获取当前主题配置。

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "primary_color": "#1890ff",
        "secondary_color": "#52c41a",
        "background_color": "#f5f5f5",
        "text_color": "#333333",
        "border_color": "#d9d9d9",
        "hover_color": "#40a9ff"
    }
}
```

---

### 10. 更新主题配置

**接口名称**: 更新主题配置  
**请求URL**: `/api/config/theme`  
**HTTP方法**: PUT  
**认证要求**: 需要JWT认证

#### 功能描述

更新主题配置，颜色值需符合规范格式。

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| primary_color | string | 否 | 主色调（HEX/RGB/HSL格式） |
| secondary_color | string | 否 | 次要颜色 |
| background_color | string | 否 | 背景颜色 |
| text_color | string | 否 | 文字颜色 |
| border_color | string | 否 | 边框颜色 |
| hover_color | string | 否 | 悬停颜色 |

---

## 文件管理API

### 1. 列出文件

**接口名称**: 列出文件列表  
**请求URL**: `/api/files`  
**HTTP方法**: GET  
**认证要求**: 无需认证

#### 功能描述

获取指定目录下的文件和文件夹列表。

#### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| path | string | 否 | `/` | 目录路径 |

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "folder": [
            {
                "id": "123456",
                "name": "文档"
            },
            {
                "id": "789012",
                "name": "图片"
            }
        ],
        "file": [
            {
                "id": "345678",
                "name": "readme.txt",
                "size": "1.2KB"
            },
            {
                "id": "901234",
                "name": "video.mp4",
                "size": "1.5GB"
            }
        ]
    }
}
```

---

### 2. 分页列出文件

**接口名称**: 分页列出文件  
**请求URL**: `/api/list`  
**HTTP方法**: GET  
**认证要求**: 无需认证

#### 功能描述

分页获取文件列表，支持关键词搜索和文件类型过滤。

#### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| path | string | 否 | `/` | 目录路径 |
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 20 | 每页数量 |
| keyword | string | 否 | - | 搜索关键词 |
| file_type | string | 否 | - | 文件类型过滤（扩展名） |

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "total": 100,
        "page": 1,
        "page_size": 20,
        "folders": [...],
        "files": [...]
    }
}
```

---

### 3. 下载文件

**接口名称**: 获取下载链接  
**请求URL**: `/api/download`  
**HTTP方法**: GET  
**认证要求**: 无需认证

#### 功能描述

获取指定文件的下载链接。

#### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| path | string | 是 | - | 文件路径 |

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "url": "https://download.123pan.com/xxx/xxx.mp4?..."
    }
}
```

**失败响应 (400)**:
```json
{
    "code": 400,
    "message": "路径不能为空",
    "data": null
}
```

---

### 4. 上传文件

**接口名称**: 上传文件  
**请求URL**: `/api/upload`  
**HTTP方法**: POST  
**认证要求**: 需要JWT认证

#### 功能描述

上传文件到指定目录。

#### 请求格式

`multipart/form-data`

#### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| file | file | 是 | - | 上传的文件 |
| path | string | 否 | `/` | 目标目录路径 |

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "上传成功",
    "data": {
        "status": "success"
    }
}
```

**失败响应 (400)**:
```json
{
    "code": 400,
    "message": "没有上传文件",
    "data": null
}
```

---

### 5. 创建文件夹

**接口名称**: 创建文件夹  
**请求URL**: `/api/folder`  
**HTTP方法**: POST  
**认证要求**: 需要JWT认证

#### 功能描述

在指定目录下创建新文件夹。

#### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| parentPath | string | 否 | `/` | 父目录路径 |
| name | string | 是 | - | 文件夹名称 |

#### 请求示例

```json
{
    "parentPath": "/文档",
    "name": "新建文件夹"
}
```

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "创建成功",
    "data": {
        "status": "success",
        "folder_id": "123456"
    }
}
```

---

### 6. 删除文件

**接口名称**: 删除文件或文件夹  
**请求URL**: `/api/files`  
**HTTP方法**: DELETE  
**认证要求**: 需要JWT认证

#### 功能描述

删除指定的文件或文件夹。

#### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| path | string | 是 | - | 文件或文件夹路径 |

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "删除成功",
    "data": {
        "status": "success"
    }
}
```

---

### 7. 分享文件

**接口名称**: 分享文件或文件夹  
**请求URL**: `/api/share`  
**HTTP方法**: POST  
**认证要求**: 需要JWT认证

#### 功能描述

创建文件或文件夹的分享链接。

#### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| path | string | 是 | - | 文件或文件夹路径 |

#### 请求示例

```json
{
    "path": "/文档/重要文件.pdf"
}
```

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "分享成功",
    "data": {
        "share_url": "https://www.123pan.com/s/xxx",
        "share_key": "xxx",
        "share_pwd": ""
    }
}
```

---

### 8. 搜索文件

**接口名称**: 搜索文件  
**请求URL**: `/api/search`  
**HTTP方法**: GET  
**认证要求**: 无需认证

#### 功能描述

在指定目录下搜索文件。

#### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| keyword | string | 是 | - | 搜索关键词 |
| path | string | 否 | `/` | 搜索目录 |

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "folders": [...],
        "files": [...],
        "total": 10
    }
}
```

**失败响应 (400)**:
```json
{
    "code": 400,
    "message": "搜索关键词不能为空",
    "data": null
}
```

---

## 日志统计API

### 1. 获取日志

**接口名称**: 获取操作日志  
**请求URL**: `/api/logs`  
**HTTP方法**: GET  
**认证要求**: 需要JWT认证

#### 功能描述

分页获取系统操作日志，支持时间范围过滤。

#### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 20 | 每页数量 |
| start_time | string | 否 | - | 开始时间（ISO格式） |
| end_time | string | 否 | - | 结束时间（ISO格式） |

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "logs": [
            {
                "timestamp": "2024-01-15 14:30:25",
                "level": "INFO",
                "operation": "login",
                "username": "admin",
                "ip": "192.168.1.1"
            }
        ],
        "total": 100,
        "page": 1,
        "page_size": 20
    }
}
```

---

### 2. 获取统计信息

**接口名称**: 获取文件统计  
**请求URL**: `/api/business/stats`  
**HTTP方法**: GET  
**认证要求**: 需要JWT认证

#### 功能描述

获取根目录下的文件和文件夹统计信息。

#### 响应格式

**成功响应 (200)**:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "total_files": 150,
        "total_folders": 25
    }
}
```

---

## 附录

### A. 配置结构说明

```json
{
    "site": {
        "title": "网站标题",
        "description": "网站描述"
    },
    "theme": {
        "primary_color": "主色调",
        "secondary_color": "次要颜色",
        "background_color": "背景颜色",
        "text_color": "文字颜色",
        "border_color": "边框颜色",
        "hover_color": "悬停颜色"
    },
    "layout": {
        "header_html": "自定义头部HTML",
        "footer_html": "自定义底部HTML",
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
        "admin_password_hash": "密码哈希值",
        "jwt_secret": "JWT密钥",
        "token_expire_hours": 24
    }
}
```

### B. 颜色格式规范

支持以下格式：

- **HEX**: `#1890ff`, `#fff`
- **RGB**: `rgb(24, 144, 255)`
- **HSL**: `hsl(210, 100%, 50%)`

### C. 文件大小格式

API返回的文件大小为格式化字符串，格式如下：

- 小于1KB: `xxx B`
- 小于1MB: `xxx.x KB`
- 小于1GB: `xxx.x MB`
- 大于等于1GB: `xxx.x GB`

---

**文档版本**: 1.0  
**最后更新**: 2024年
