# 听写练习 | Dictation Practice

一个用于教育行业的听写单词网页应用，支持中英文听写练习。

## 功能特性

- 🎯 **基础听写练习** - 使用 TTS 语音播放单词，用户输入拼写进行练习
- 📚 **词库管理** - 支持自定义添加、编辑、删除词库和单词
- 🌍 **多语言支持** - 支持中文和英文听写，界面支持中英文切换
- 📊 **学习统计** - 显示练习进度和正确率
- 💾 **本地存储** - 自定义词库保存在浏览器本地存储中

## 技术栈

- Vue 3 + Composition API
- Vite 构建工具
- Vue Router 路由管理
- Pinia 状态管理
- vue-i18n 国际化
- Web Speech API (TTS)

## 开发

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

## 部署到 Netlify

### 方法一：通过 Git 部署

1. 将项目推送到 GitHub/GitLab/Bitbucket
2. 登录 [Netlify](https://app.netlify.com)
3. 点击 "New site from Git"
4. 选择你的仓库
5. 构建设置会自动从 `netlify.toml` 读取
6. 点击 "Deploy site"

### 方法二：手动部署

1. 运行 `npm run build`
2. 登录 [Netlify](https://app.netlify.com)
3. 将 `dist` 文件夹拖放到 Netlify 的部署区域

## 项目结构

```
dictation-app/
├── public/
│   └── data/              # JSON 词库数据
│       ├── en/            # 英文词库
│       └── zh/            # 中文词库
├── src/
│   ├── assets/styles/     # 样式文件
│   ├── components/        # 组件
│   ├── views/             # 页面视图
│   ├── router/            # 路由配置
│   ├── stores/            # Pinia 状态管理
│   ├── utils/             # 工具函数
│   └── locales/           # 国际化文件
├── netlify.toml           # Netlify 配置
└── index.html
```

## 添加自定义词库

在 `public/data` 目录下创建 JSON 文件，格式如下：

```json
{
  "name": "词库名称",
  "language": "en",
  "category": "分类标识",
  "words": [
    { "word": "单词", "meaning": "释义", "phonetic": "/音标/" }
  ]
}
```

## License

MIT
