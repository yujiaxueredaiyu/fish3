# 贡献指南

欢迎贡献代码到 Ocean Aura 项目！

## 行为准则

请遵守 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) 中的行为准则。

## 如何贡献

### 报告问题

1. 检查是否已有相关的 issue
2. 提供详细的问题描述，包括：
   - 问题复现步骤
   - 预期行为
   - 实际行为
   - 截图或日志（如有）

### 提交代码

1. Fork 项目并克隆到本地
2. 创建新分支：`git checkout -b feature/your-feature-name`
3. 提交代码：`git commit -m "feat: add your feature"`
4. 推送到远程：`git push origin feature/your-feature-name`
5. 创建 Pull Request

### 代码规范

- 使用 `black` 进行代码格式化
- 使用 `isort` 进行导入排序
- 确保所有测试通过
- 添加必要的注释和文档

## 开发环境

### 安装依赖

```bash
pip install -e .[dev]
```

### 运行测试

```bash
python -m pytest tests/
```

### 代码格式化

```bash
black src/
isort src/
```

## Pull Request 要求

- 描述清晰的变更内容
- 关联相关的 issue（如有）
- 确保 CI 测试通过
- 保持代码风格一致

## 版本管理

项目使用语义化版本（Semantic Versioning）：
- MAJOR: 不兼容的 API 变更
- MINOR: 向后兼容的功能新增
- PATCH: 向后兼容的问题修复

## 许可证

所有贡献的代码将遵循项目的 MIT 许可证。
