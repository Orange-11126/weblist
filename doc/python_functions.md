# Python 函数文档

## 目录

1. [核心SDK模块](#核心sdk模块)
   - [Pan123 类](#pan123-类)
   - [API封装函数](#api封装函数)
2. [Flask应用模块](#flask应用模块)
3. [业务逻辑层](#业务逻辑层)
   - [文件服务](#文件服务)
   - [权限模型](#权限模型)
   - [上传验证器](#上传验证器)
4. [API封装层](#api封装层-1)
   - [文件工具类](#文件工具类)
   - [重试装饰器](#重试装饰器)
5. [签名工具模块](#签名工具模块)

---

## 核心SDK模块

### Pan123 类

**文件位置**: [123pan/pan123.py](../123pan/pan123.py)

`Pan123` 类是与123云盘API直接交互的核心类，封装了登录、文件操作等基础功能。

#### 构造函数

```python
def __init__(
    self,
    readfile=True,
    user_name="",
    pass_word="",
    authorization="",
    input_pwd=True
)
```

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| readfile | bool | 否 | True | 是否从配置文件读取登录信息 |
| user_name | str | 否 | "" | 用户名 |
| pass_word | str | 否 | "" | 密码 |
| authorization | str | 否 | "" | 已有的授权Token |
| input_pwd | bool | 否 | True | 是否允许交互式输入密码 |

**返回值**: Pan123实例

**异常**: 当`readfile=False`且用户名或密码为空时，抛出`Exception`

**使用示例**:

```python
from pan123 import Pan123

pan = Pan123(readfile=True)
pan = Pan123(readfile=False, user_name="your_email", pass_word="your_password")
```

---

#### login 方法

```python
def login(self, max_retries=3)
```

**功能描述**: 登录123云盘账户

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| max_retries | int | 否 | 3 | 最大重试次数 |

**返回值**: 
- `200`: 登录成功
- `-1`: 登录失败（所有重试均失败）

**异常处理**: 自动处理网络异常、代理错误、超时等异常，并自动重试

**使用示例**:

```python
pan = Pan123(readfile=False, user_name="user@example.com", pass_word="password")
result = pan.login()
if result == 200:
    print("登录成功")
```

---

#### get_dir 方法

```python
def get_dir(self)
```

**功能描述**: 获取当前目录下的文件和文件夹列表

**参数说明**: 无参数

**返回值**:
- `0`: 成功
- 其他值: 失败错误码

**使用示例**:

```python
pan.get_dir()
for item in pan.list:
    print(f"{item['FileName']} - {item['Type']}")
```

---

#### link 方法

```python
def link(self, file_number, showlink=True)
```

**功能描述**: 获取文件的下载链接

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| file_number | int | 是 | - | 文件在列表中的索引（从0开始） |
| showlink | bool | 否 | True | 是否打印链接信息 |

**返回值**: 下载链接字符串，失败时返回错误码

**注意事项**: 文件索引从0开始

**使用示例**:

```python
pan.get_dir()
download_url = pan.link(0, showlink=False)
print(f"下载链接: {download_url}")
```

---

#### download 方法

```python
def download(self, file_number, download_path="download/")
```

**功能描述**: 下载指定文件到本地

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| file_number | int | 是 | - | 文件索引 |
| download_path | str | 否 | "download/" | 下载保存路径 |

**返回值**: 无返回值，直接下载文件

**使用示例**:

```python
pan.download(0, download_path="./downloads/")
```

---

#### up_load 方法

```python
def up_load(self, file_path)
```

**功能描述**: 上传本地文件到云盘

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| file_path | str | 是 | - | 本地文件路径 |

**返回值**: 无返回值，打印上传结果

**注意事项**: 
- 支持大文件分块上传
- 支持MD5秒传
- 上传前会检查文件是否存在同名文件

**使用示例**:

```python
pan.parent_file_id = 0
pan.up_load("/path/to/local/file.mp4")
```

---

#### delete_file 方法

```python
def delete_file(self, file, by_num=True, operation=True)
```

**功能描述**: 删除或恢复文件

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| file | int/dict | 是 | - | 文件索引或文件信息字典 |
| by_num | bool | 否 | True | 是否按索引查找 |
| operation | bool | 否 | True | True为删除，False为恢复 |

**返回值**: 无返回值，打印操作结果

**使用示例**:

```python
pan.delete_file(0, by_num=True, operation=True)
```

---

#### mkdir 方法

```python
def mkdir(self, dirname, remakedir=False)
```

**功能描述**: 在当前目录下创建文件夹

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| dirname | str | 是 | - | 文件夹名称 |
| remakedir | bool | 否 | False | 是否允许重建已存在的文件夹 |

**返回值**: 成功返回文件夹ID，失败返回None

**使用示例**:

```python
folder_id = pan.mkdir("新文件夹")
print(f"创建成功，ID: {folder_id}")
```

---

#### cd 方法

```python
def cd(self, dir_num)
```

**功能描述**: 切换当前目录

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| dir_num | str | 是 | - | 目录序号或命令（".."返回上级，"/"返回根目录） |

**返回值**: 无返回值

**使用示例**:

```python
pan.cd("1")
pan.cd("..")
pan.cd("/")
```

---

### API封装函数

**文件位置**: [123pan/api.py](../123pan/api.py)

提供更友好的函数式API接口。

#### login 函数

```python
def login(username=None, password=None)
```

**功能描述**: 登录123云盘

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| username | str | 否 | None | 用户名，为None时从配置文件读取 |
| password | str | 否 | None | 密码，为None时从配置文件读取 |

**返回值**: 
- 成功: `{"status": "success"}`
- 失败: `{"error": "错误信息"}`

**使用示例**:

```python
import api as pan_api

result = pan_api.login("user@example.com", "password")
if "error" not in result:
    print("登录成功")
```

---

#### list 函数

```python
def list()
```

**功能描述**: 列出当前目录下的文件和文件夹

**参数说明**: 无参数

**返回值**:
```python
{
    "folder": [{"id": "1", "name": "文件夹名"}, ...],
    "file": [{"id": "2", "name": "文件名", "size": "1.5GB"}, ...]
}
```

**使用示例**:

```python
result = pan_api.list()
for folder in result.get("folder", []):
    print(f"文件夹: {folder['name']}")
for file in result.get("file", []):
    print(f"文件: {file['name']} ({file['size']})")
```

---

#### list_folder 函数

```python
def list_folder(path)
```

**功能描述**: 列出指定目录下的文件和文件夹

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| path | str | 是 | - | 目录路径，如"/文档/工作" |

**返回值**: 与`list()`相同格式

**使用示例**:

```python
result = pan_api.list_folder("/文档")
```

---

#### parsing 函数

```python
def parsing(path)
```

**功能描述**: 解析文件获取下载链接

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| path | str | 是 | - | 文件路径 |

**返回值**:
- 成功: `{"url": "下载链接"}`
- 失败: `{"error": "错误信息"}`

**使用示例**:

```python
result = pan_api.parsing("/文档/report.pdf")
if "url" in result:
    print(f"下载链接: {result['url']}")
```

---

#### upload 函数

```python
def upload(local_path, remote_path="/")
```

**功能描述**: 上传文件到云盘

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| local_path | str | 是 | - | 本地文件路径 |
| remote_path | str | 否 | "/" | 远程目标目录 |

**返回值**:
- 成功: `{"status": "success"}`
- 失败: `{"error": "错误信息"}`

**使用示例**:

```python
result = pan_api.upload("/local/file.mp4", "/视频")
```

---

#### delete 函数

```python
def delete(path)
```

**功能描述**: 删除文件或文件夹

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| path | str | 是 | - | 文件或文件夹路径 |

**返回值**:
- 成功: `{"status": "success"}`
- 失败: `{"error": "错误信息"}`

**使用示例**:

```python
result = pan_api.delete("/文档/旧文件.txt")
```

---

#### create_folder 函数

```python
def create_folder(path, folder_name)
```

**功能描述**: 创建文件夹

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| path | str | 是 | - | 父目录路径 |
| folder_name | str | 是 | - | 新文件夹名称 |

**返回值**:
- 成功: `{"status": "success", "folder_id": "ID"}`
- 失败: `{"error": "错误信息"}`

**使用示例**:

```python
result = pan_api.create_folder("/文档", "新文件夹")
```

---

#### share 函数

```python
def share(path)
```

**功能描述**: 分享文件或文件夹

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| path | str | 是 | - | 文件或文件夹路径 |

**返回值**:
```python
{
    "share_url": "https://www.123pan.com/s/xxx",
    "share_key": "xxx",
    "share_pwd": ""
}
```

**使用示例**:

```python
result = pan_api.share("/文档/重要文件.pdf")
print(f"分享链接: {result['share_url']}")
```

---

## Flask应用模块

**文件位置**: [app.py](../app.py)

### 配置管理函数

#### load_config 函数

```python
def load_config()
```

**功能描述**: 加载系统配置文件

**参数说明**: 无参数

**返回值**: 配置字典，失败时返回`{"error": "错误信息"}`

**使用示例**:

```python
config = load_config()
site_title = config.get("site", {}).get("title", "默认标题")
```

---

#### save_config 函数

```python
def save_config(config)
```

**功能描述**: 保存配置到文件

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| config | dict | 是 | - | 配置字典 |

**返回值**: `True`成功，`False`失败

**使用示例**:

```python
config = load_config()
config["site"]["title"] = "新标题"
save_config(config)
```

---

#### validate_color 函数

```python
def validate_color(color)
```

**功能描述**: 验证颜色值格式

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| color | str | 是 | - | 颜色值字符串 |

**返回值**: `True`格式正确，`False`格式错误

**支持格式**: HEX (`#fff`, `#ffffff`), RGB (`rgb(255,255,255)`), HSL (`hsl(0,0%,100%)`)

**使用示例**:

```python
is_valid = validate_color("#1890ff")
```

---

#### sanitize_html 函数

```python
def sanitize_html(html_content)
```

**功能描述**: 清理HTML中的危险标签

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| html_content | str | 是 | - | HTML内容 |

**返回值**: 清理后的安全HTML

**过滤内容**: `<script>`, `javascript:`, `onerror=`, `onclick=`, `onload=`

**使用示例**:

```python
safe_html = sanitize_html(user_input_html)
```

---

#### create_backup 函数

```python
def create_backup()
```

**功能描述**: 创建配置备份

**参数说明**: 无参数

**返回值**: 成功返回时间戳ID，失败返回`None`

**使用示例**:

```python
backup_id = create_backup()
if backup_id:
    print(f"备份创建成功: {backup_id}")
```

---

### JWT认证函数

#### generate_token 函数

```python
def generate_token(username)
```

**功能描述**: 生成JWT认证令牌

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| username | str | 是 | - | 用户名 |

**返回值**: JWT Token字符串

**使用示例**:

```python
token = generate_token("admin")
```

---

#### verify_token 函数

```python
def verify_token(token)
```

**功能描述**: 验证JWT令牌有效性

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| token | str | 是 | - | JWT Token |

**返回值**: 有效返回payload字典，无效返回`None`

**使用示例**:

```python
payload = verify_token(token)
if payload:
    print(f"用户: {payload['username']}")
```

---

#### require_auth 装饰器

```python
@require_auth
def protected_route():
    pass
```

**功能描述**: 路由认证装饰器，保护需要登录的接口

**使用示例**:

```python
@app.route('/api/protected')
@require_auth
def protected_route():
    username = request.current_user.get('username')
    return jsonify({"message": f"Hello, {username}"})
```

---

## 业务逻辑层

### 文件服务

**文件位置**: [business_logic/services/file_service.py](../business_logic/services/file_service.py)

#### FileOperationService 类

```python
class FileOperationService:
    def __init__(self, config: Dict[str, Any])
```

**功能描述**: 文件操作服务类，集成权限验证

**构造参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| config | dict | 是 | 系统配置字典 |

---

##### list_files 方法

```python
def list_files(self, user_role: UserRole, path: str = "/") -> Dict[str, Any]
```

**功能描述**: 列出文件（带权限检查）

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| user_role | UserRole | 是 | - | 用户角色 |
| path | str | 否 | "/" | 目录路径 |

**返回值**:
```python
{
    "success": True,
    "data": {
        "folders": [...],
        "files": [...],
        "total_count": 10,
        "total_size": 1024000,
        "path": "/"
    }
}
```

---

##### upload_file 方法

```python
def upload_file(self, user_role: UserRole, local_path: str, remote_path: str) -> Dict[str, Any]
```

**功能描述**: 上传文件（带验证和权限检查）

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| user_role | UserRole | 是 | 用户角色 |
| local_path | str | 是 | 本地文件路径 |
| remote_path | str | 是 | 远程目标路径 |

**返回值**: `{"success": True/False, "data"/"error": ...}`

---

##### download_file 方法

```python
def download_file(self, user_role: UserRole, remote_path: str) -> Dict[str, Any]
```

**功能描述**: 下载文件（带权限检查）

---

##### delete_file 方法

```python
def delete_file(self, user_role: UserRole, path: str) -> Dict[str, Any]
```

**功能描述**: 删除文件（带权限检查）

---

##### create_folder 方法

```python
def create_folder(self, user_role: UserRole, parent_path: str, folder_name: str) -> Dict[str, Any]
```

**功能描述**: 创建文件夹（带权限检查）

---

##### share_file 方法

```python
def share_file(self, user_role: UserRole, path: str) -> Dict[str, Any]
```

**功能描述**: 分享文件（带权限检查）

---

### 权限模型

**文件位置**: [business_logic/models/permission.py](../business_logic/models/permission.py)

#### UserRole 枚举

```python
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
```

**功能描述**: 用户角色枚举

---

#### Permission 枚举

```python
class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    SHARE = "share"
    ADMIN = "admin"
```

**功能描述**: 权限类型枚举

---

#### check_permission 函数

```python
def check_permission(user_role: UserRole, permission: Permission) -> bool
```

**功能描述**: 检查用户是否有指定权限

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| user_role | UserRole | 是 | 用户角色 |
| permission | Permission | 是 | 权限类型 |

**返回值**: `True`有权限，`False`无权限

**使用示例**:

```python
if check_permission(UserRole.ADMIN, Permission.DELETE):
    print("管理员有删除权限")
```

---

#### validate_path_access 函数

```python
def validate_path_access(user_role: UserRole, path: str) -> bool
```

**功能描述**: 验证路径访问权限

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| user_role | UserRole | 是 | 用户角色 |
| path | str | 是 | 访问路径 |

**返回值**: `True`可访问，`False`不可访问

**保护路径**: `/config`, `/admin`, `/system`, `/logs`

---

### 上传验证器

**文件位置**: [business_logic/validators/upload_validator.py](../business_logic/validators/upload_validator.py)

#### UploadValidator 类

```python
class UploadValidator:
    def __init__(self, config: Dict[str, Any])
```

**功能描述**: 上传文件验证器

---

##### validate_upload 方法

```python
def validate_upload(self, file_name: str, file_size: int, file_type: str = None) -> Dict[str, Any]
```

**功能描述**: 验证单个文件上传

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| file_name | str | 是 | - | 文件名 |
| file_size | int | 是 | - | 文件大小（字节） |
| file_type | str | 否 | None | 文件MIME类型 |

**返回值**:
```python
{
    "valid": True/False,
    "errors": ["错误信息1", "错误信息2"]
}
```

**使用示例**:

```python
validator = UploadValidator(config)
result = validator.validate_upload("test.pdf", 1024000)
if result["valid"]:
    print("文件验证通过")
```

---

##### validate_batch_upload 方法

```python
def validate_batch_upload(self, files: List[Dict[str, Any]]) -> Dict[str, Any]
```

**功能描述**: 批量验证文件上传

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| files | list | 是 | 文件信息列表，每项包含name、size、type |

**返回值**:
```python
{
    "valid": True/False,
    "results": [...],
    "total_size": 1024000
}
```

---

#### PathValidator 类

**功能描述**: 路径验证器

##### validate_path 方法

```python
@staticmethod
def validate_path(path: str) -> Dict[str, Any]
```

**功能描述**: 验证路径格式

**返回值**: `{"valid": True/False, "errors": [...]}`

---

##### sanitize_path 方法

```python
@staticmethod
def sanitize_path(path: str) -> str
```

**功能描述**: 清理路径中的非法字符

**返回值**: 清理后的安全路径

**使用示例**:

```python
safe_path = PathValidator.sanitize_path("//test/../folder//")
print(safe_path)
```

---

## API封装层

### 文件工具类

**文件位置**: [api_wrapper/utils/file_utils.py](../api_wrapper/utils/file_utils.py)

#### FileUtils 类

提供文件操作相关的静态工具方法。

##### get_file_info 方法

```python
@staticmethod
def get_file_info(file_path: str) -> Dict[str, Any]
```

**功能描述**: 获取文件详细信息

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file_path | str | 是 | 文件路径 |

**返回值**:
```python
{
    "name": "文件名",
    "path": "完整路径",
    "size": 1024,
    "size_formatted": "1.0 KB",
    "type": "application/pdf",
    "modified": "2024-01-15T14:30:00",
    "created": "2024-01-15T10:00:00",
    "extension": "pdf",
    "is_directory": False
}
```

**使用示例**:

```python
info = FileUtils.get_file_info("/path/to/file.pdf")
print(f"文件大小: {info['size_formatted']}")
```

---

##### format_file_size 方法

```python
@staticmethod
def format_file_size(size_bytes: int) -> str
```

**功能描述**: 格式化文件大小显示

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| size_bytes | int | 是 | 字节数 |

**返回值**: 格式化的大小字符串（如 "1.5 GB"）

**使用示例**:

```python
size_str = FileUtils.format_file_size(1536000000)
print(size_str)
```

---

##### parse_size_string 方法

```python
@staticmethod
def parse_size_string(size_str: str) -> int
```

**功能描述**: 解析大小字符串为字节数

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| size_str | str | 是 | 大小字符串（如 "1.5GB"） |

**返回值**: 字节数

**使用示例**:

```python
bytes_count = FileUtils.parse_size_string("1.5GB")
print(bytes_count)
```

---

##### get_file_extension 方法

```python
@staticmethod
def get_file_extension(filename: str) -> str
```

**功能描述**: 获取文件扩展名

**返回值**: 小写的扩展名（不含点号）

---

##### is_allowed_type 方法

```python
@staticmethod
def is_allowed_type(filename: str, allowed_types: list) -> bool
```

**功能描述**: 检查文件类型是否允许

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| filename | str | 是 | 文件名 |
| allowed_types | list | 是 | 允许的扩展名列表，`['*']`表示全部允许 |

**返回值**: `True`允许，`False`不允许

---

##### get_file_icon 方法

```python
@staticmethod
def get_file_icon(extension: str) -> str
```

**功能描述**: 根据扩展名获取文件图标emoji

**返回值**: emoji字符

---

##### sanitize_filename 方法

```python
@staticmethod
def sanitize_filename(filename: str) -> str
```

**功能描述**: 清理文件名中的非法字符

**返回值**: 安全的文件名

---

### 重试装饰器

**文件位置**: [api_wrapper/decorators/retry_decorator.py](../api_wrapper/decorators/retry_decorator.py)

#### retry_on_error 装饰器

```python
def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
)
```

**功能描述**: 函数执行失败时自动重试的装饰器

**参数说明**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| max_retries | int | 否 | 3 | 最大重试次数 |
| delay | float | 否 | 1.0 | 初始延迟时间（秒） |
| backoff | float | 否 | 2.0 | 退避因子，每次重试延迟乘以此值 |
| exceptions | tuple | 否 | (Exception,) | 需要重试的异常类型 |

**返回值**: 装饰器函数

**使用示例**:

```python
@retry_on_error(max_retries=3, delay=1.0, backoff=2.0)
def unstable_api_call():
    response = requests.get("https://api.example.com/data")
    response.raise_for_status()
    return response.json()
```

---

#### get_error_message 函数

```python
def get_error_message(code: int) -> str
```

**功能描述**: 根据错误码获取错误消息

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| code | int | 是 | 错误码 |

**返回值**: 错误消息字符串

**错误码映射**:

| 错误码 | 消息 |
|--------|------|
| 401 | 认证失败，请检查API密钥 |
| 403 | 权限不足，无法访问 |
| 404 | 文件或目录不存在 |
| 429 | 请求过于频繁，请稍后再试 |
| 500 | 服务器内部错误 |
| 503 | 服务暂时不可用 |

---

## 签名工具模块

**文件位置**: [123pan/sign_py.py](../123pan/sign_py.py)

### getSign 函数

```python
def getSign(e)
```

**功能描述**: 生成API请求签名

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| e | str | 是 | API路径字符串 |

**返回值**: `[签名头名, 签名值]` 列表

**使用示例**:

```python
sign = getSign("/b/api/file/list/new")
headers[sign[0]] = sign[1]
```

---

### formatDate 函数

```python
def formatDate(t, e, n)
```

**功能描述**: 格式化日期时间

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| t | int | 是 | 时间戳 |
| e | str | 是 | 格式字符串 |
| n | int | 是 | 时区偏移 |

**返回值**: 日期字典

---

### A 函数

```python
def A(t)
```

**功能描述**: 计算字符串的CRC32哈希值

**参数说明**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| t | str | 是 | 输入字符串 |

**返回值**: CRC32哈希字符串

---

**文档版本**: 1.0  
**最后更新**: 2024年
